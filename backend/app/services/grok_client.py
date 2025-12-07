import httpx
from typing import List, Dict, Any
from app.config import settings
from app.models.claim import ClaimCreate
import json


class GrokClient:
    """Client for Grok API (xAI) for claim extraction and synthesis"""

    def __init__(self):
        self.api_key = settings.GROK_API_KEY
        self.api_base = settings.GROK_API_BASE
        self.model = settings.GROK_MODEL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def extract_claims(self, article_text: str, article_id: str, source_urls: List[str]) -> List[ClaimCreate]:
        """
        Extract structured claims from article text using Grok API

        Args:
            article_text: The full text of the article
            article_id: ID of the article
            source_urls: List of source URLs cited in the article

        Returns:
            List of ClaimCreate objects
        """
        prompt = self._build_extraction_prompt(article_text, source_urls)

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.api_base}/chat/completions",
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an expert at extracting factual claims from encyclopedia articles. Extract individual, atomic claims with their sources and classify them as mutable or immutable."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.3,
                    "response_format": {"type": "json_object"}
                }
            )
            response.raise_for_status()
            result = response.json()

        # Parse the response
        claims_data = json.loads(result["choices"][0]["message"]["content"])
        claims = []

        for claim_dict in claims_data.get("claims", []):
            claim = ClaimCreate(
                text=claim_dict["assertion"],
                source_url=claim_dict.get("source", source_urls[0] if source_urls else ""),
                article_id=article_id,
                is_immutable=claim_dict.get("temporal_classification") == "immutable",
                confidence_level=claim_dict.get("confidence", 0.5),
                language=claim_dict.get("language", "en")
            )
            claims.append(claim)

        return claims

    def _build_extraction_prompt(self, article_text: str, source_urls: List[str]) -> str:
        """Build the prompt for claim extraction"""
        sources_text = "\n".join([f"- {url}" for url in source_urls])

        return f"""Extract all factual claims from the following encyclopedia article. For each claim, provide:
1. The assertion (a single, atomic fact)
2. The cited source (from the provided URLs or inferred)
3. Confidence level (0.0 to 1.0)
4. Temporal classification: "mutable" (likely to change over time) or "immutable" (timeless fact)
5. Language (ISO code)

Sources:
{sources_text}

Article:
{article_text}

Return a JSON object with this structure:
{{
  "claims": [
    {{
      "assertion": "string",
      "source": "string",
      "confidence": 0.0-1.0,
      "temporal_classification": "mutable" or "immutable",
      "language": "en"
    }}
  ]
}}
"""

    async def synthesize_claim_update(self, original_claim: str, contradicting_sources: List[Dict[str, Any]]) -> str:
        """
        Synthesize an updated claim text based on contradicting sources

        Args:
            original_claim: The original claim text
            contradicting_sources: List of contradicting source objects

        Returns:
            Synthesized updated claim text
        """
        sources_text = "\n\n".join([
            f"Source {i+1} ({src['language']}): {src['text']}\nURL: {src['url']}"
            for i, src in enumerate(contradicting_sources)
        ])

        prompt = f"""Original claim: {original_claim}

Contradicting sources found:
{sources_text}

Based on these contradicting sources, synthesize an updated, more accurate version of the claim. If the original claim is clearly false, provide the corrected version. If the truth is nuanced, provide a balanced statement.

Return only the updated claim text, nothing else."""

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.api_base}/chat/completions",
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an expert fact-checker who synthesizes accurate claims from multiple sources."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.2
                }
            )
            response.raise_for_status()
            result = response.json()

        return result["choices"][0]["message"]["content"].strip()


# Singleton instance
grok_client = GrokClient()
