from neo4j import AsyncGraphDatabase, AsyncDriver
from typing import List, Dict, Any, Optional
from app.config import settings
from app.models.claim import ClaimNode, ClaimWithDependencies, ClaimImpact, VulnerableClaim
from uuid import UUID
from datetime import datetime


class Neo4jClient:
    """Client for Neo4j graph database operations"""

    def __init__(self):
        self.uri = settings.NEO4J_URI
        self.user = settings.NEO4J_USER
        self.password = settings.NEO4J_PASSWORD
        self.database = settings.NEO4J_DATABASE
        self.driver: Optional[AsyncDriver] = None

    async def connect(self):
        """Initialize connection to Neo4j"""
        self.driver = AsyncGraphDatabase.driver(
            self.uri,
            auth=(self.user, self.password)
        )
        # Verify connectivity
        await self.driver.verify_connectivity()

    async def close(self):
        """Close Neo4j connection"""
        if self.driver:
            await self.driver.close()

    async def create_claim_node(self, claim: ClaimNode) -> ClaimNode:
        """Create a new claim node in the graph"""
        async with self.driver.session(database=self.database) as session:
            result = await session.run(
                """
                CREATE (c:Claim {
                    id: $id,
                    text: $text,
                    sourceUrl: $source_url,
                    articleId: $article_id,
                    extractedAt: $extracted_at,
                    decayScore: $decay_score,
                    halfLifeDays: $half_life_days,
                    isImmutable: $is_immutable,
                    contradictionCount: $contradiction_count,
                    language: $language
                })
                RETURN c
                """,
                id=str(claim.id),
                text=claim.text,
                source_url=claim.source_url,
                article_id=claim.article_id,
                extracted_at=claim.extracted_at.isoformat(),
                decay_score=claim.decay_score,
                half_life_days=claim.half_life_days,
                is_immutable=claim.is_immutable,
                contradiction_count=claim.contradiction_count,
                language=claim.language
            )
            await result.single()
            return claim

    async def create_support_relationship(self, supporting_claim_id: UUID, supported_claim_id: UUID, weight: float = 1.0):
        """Create a SUPPORTS relationship between two claims"""
        async with self.driver.session(database=self.database) as session:
            await session.run(
                """
                MATCH (a:Claim {id: $supporting_id})
                MATCH (b:Claim {id: $supported_id})
                MERGE (a)-[r:SUPPORTS {weight: $weight}]->(b)
                RETURN r
                """,
                supporting_id=str(supporting_claim_id),
                supported_id=str(supported_claim_id),
                weight=weight
            )

    async def get_claim_by_id(self, claim_id: UUID) -> Optional[ClaimNode]:
        """Retrieve a claim by its ID"""
        async with self.driver.session(database=self.database) as session:
            result = await session.run(
                """
                MATCH (c:Claim {id: $id})
                RETURN c
                """,
                id=str(claim_id)
            )
            record = await result.single()
            if not record:
                return None

            node = record["c"]
            return self._node_to_claim(node)

    async def get_claim_with_dependencies(self, claim_id: UUID) -> Optional[ClaimWithDependencies]:
        """Get claim with its immediate dependencies and dependents"""
        async with self.driver.session(database=self.database) as session:
            result = await session.run(
                """
                MATCH (c:Claim {id: $id})
                OPTIONAL MATCH (c)-[:SUPPORTS]->(supported:Claim)
                OPTIONAL MATCH (supporter:Claim)-[:SUPPORTS]->(c)
                RETURN c, collect(DISTINCT supported) as supports, collect(DISTINCT supporter) as supported_by
                """,
                id=str(claim_id)
            )
            record = await result.single()
            if not record:
                return None

            claim = self._node_to_claim(record["c"])
            supports = [self._node_to_claim(n) for n in record["supports"] if n is not None]
            supported_by = [self._node_to_claim(n) for n in record["supported_by"] if n is not None]

            return ClaimWithDependencies(
                **claim.model_dump(),
                supports=supports,
                supported_by=supported_by
            )

    async def get_downstream_impact(self, claim_id: UUID) -> ClaimImpact:
        """Calculate downstream impact of a claim"""
        async with self.driver.session(database=self.database) as session:
            result = await session.run(
                """
                MATCH path = (c:Claim {id: $id})-[:SUPPORTS*]->(affected:Claim)
                WITH c, collect(DISTINCT affected.id) as affected_ids, count(DISTINCT affected) as count
                RETURN affected_ids, count
                """,
                id=str(claim_id)
            )
            record = await result.single()

            if not record or record["count"] == 0:
                return ClaimImpact(
                    claim_id=claim_id,
                    downstream_impact_score=0.0,
                    affected_claims=[],
                    affected_claims_count=0
                )

            affected_ids = [UUID(aid) for aid in record["affected_ids"]]
            count = record["count"]

            # Simple impact score based on affected claims count (can be more sophisticated)
            impact_score = min(count / 100.0, 1.0)  # Normalize to 0-1

            return ClaimImpact(
                claim_id=claim_id,
                downstream_impact_score=impact_score,
                affected_claims=affected_ids,
                affected_claims_count=count
            )

    async def get_vulnerable_claims(self, limit: int = 50, offset: int = 0) -> List[VulnerableClaim]:
        """Get most vulnerable claims sorted by vulnerability score"""
        async with self.driver.session(database=self.database) as session:
            result = await session.run(
                """
                MATCH (c:Claim)
                WHERE NOT c.isImmutable
                OPTIONAL MATCH (c)-[r:SUPPORTS]->()
                WITH c, sum(r.weight) as dependency_weight
                WITH c, COALESCE(dependency_weight, 0.0) as dep_weight,
                     (c.decayScore * COALESCE(dependency_weight, 1.0) * (c.contradictionCount + 1)) as vulnerability
                RETURN c, dep_weight, vulnerability
                ORDER BY vulnerability DESC
                SKIP $offset
                LIMIT $limit
                """,
                offset=offset,
                limit=limit
            )

            vulnerable_claims = []
            async for record in result:
                claim = self._node_to_claim(record["c"])
                dep_weight = record["dep_weight"]
                vulnerability = record["vulnerability"]

                vulnerable_claim = VulnerableClaim(
                    **claim.model_dump(),
                    dependency_weight=dep_weight,
                    vulnerability_score=min(vulnerability, 1.0)
                )
                vulnerable_claims.append(vulnerable_claim)

            return vulnerable_claims

    async def update_decay_score(self, claim_id: UUID, decay_score: float, half_life_days: int):
        """Update the decay score and half-life for a claim"""
        async with self.driver.session(database=self.database) as session:
            await session.run(
                """
                MATCH (c:Claim {id: $id})
                SET c.decayScore = $decay_score, c.halfLifeDays = $half_life_days
                """,
                id=str(claim_id),
                decay_score=decay_score,
                half_life_days=half_life_days
            )

    async def increment_contradiction_count(self, claim_id: UUID):
        """Increment the contradiction count for a claim"""
        async with self.driver.session(database=self.database) as session:
            await session.run(
                """
                MATCH (c:Claim {id: $id})
                SET c.contradictionCount = c.contradictionCount + 1
                """,
                id=str(claim_id)
            )

    async def create_indexes(self):
        """Create indexes for performance optimization"""
        async with self.driver.session(database=self.database) as session:
            # Index on claim ID
            await session.run("CREATE INDEX claim_id_index IF NOT EXISTS FOR (c:Claim) ON (c.id)")
            # Index on article ID
            await session.run("CREATE INDEX article_id_index IF NOT EXISTS FOR (c:Claim) ON (c.articleId)")
            # Index on decay score
            await session.run("CREATE INDEX decay_score_index IF NOT EXISTS FOR (c:Claim) ON (c.decayScore)")
            # Index on contradiction count
            await session.run("CREATE INDEX contradiction_count_index IF NOT EXISTS FOR (c:Claim) ON (c.contradictionCount)")

    def _node_to_claim(self, node) -> ClaimNode:
        """Convert Neo4j node to ClaimNode model"""
        return ClaimNode(
            id=UUID(node["id"]),
            text=node["text"],
            source_url=node["sourceUrl"],
            article_id=node["articleId"],
            extracted_at=datetime.fromisoformat(node["extractedAt"]),
            decay_score=node["decayScore"],
            half_life_days=node["halfLifeDays"],
            is_immutable=node["isImmutable"],
            contradiction_count=node["contradictionCount"],
            language=node["language"]
        )


# Singleton instance
neo4j_client = Neo4jClient()
