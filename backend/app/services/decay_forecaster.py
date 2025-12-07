from typing import Dict, Any, Tuple
import math
from datetime import datetime, timedelta
from app.services.x_api_client import x_api_client


class DecayForecaster:
    """Service for predicting claim decay and calculating half-life"""

    def __init__(self):
        self.base_half_life_immutable = 3650  # 10 years for immutable claims
        self.base_half_life_mutable = 365  # 1 year for mutable claims

    async def calculate_decay_score(
        self,
        claim_text: str,
        is_immutable: bool,
        extracted_at: datetime,
        check_trending: bool = True
    ) -> Tuple[float, int]:
        """
        Calculate decay score and half-life for a claim

        Args:
            claim_text: The claim text
            is_immutable: Whether the claim is classified as immutable
            extracted_at: When the claim was extracted
            check_trending: Whether to check X API for trending signals

        Returns:
            Tuple of (decay_score, half_life_days)
        """
        # Base half-life depends on mutability
        if is_immutable:
            half_life_days = self.base_half_life_immutable
            base_decay_score = 0.1  # Very low decay for immutable claims
        else:
            half_life_days = self.base_half_life_mutable
            base_decay_score = 0.5  # Moderate decay for mutable claims

        # Calculate age-based decay
        age_days = (datetime.utcnow() - extracted_at).days
        age_decay_factor = self._calculate_decay_factor(age_days, half_life_days)

        # Check for trending signals (velocity boost)
        velocity_boost = 0.0
        if check_trending and not is_immutable:
            velocity_boost = await self._check_trending_boost(claim_text)

        # Combine factors
        final_decay_score = min(base_decay_score + age_decay_factor + velocity_boost, 1.0)

        # Adjust half-life based on velocity
        if velocity_boost > 0.3:
            # If trending, reduce half-life (faster decay)
            half_life_days = int(half_life_days * 0.5)

        return final_decay_score, half_life_days

    def _calculate_decay_factor(self, age_days: int, half_life_days: int) -> float:
        """
        Calculate decay factor based on age and half-life using exponential decay formula

        Args:
            age_days: Age of the claim in days
            half_life_days: Half-life of the claim in days

        Returns:
            Decay factor (0.0 to 1.0)
        """
        if half_life_days == 0:
            return 0.0

        # Exponential decay: N(t) = N0 * (1/2)^(t/t_half)
        # We invert this to get a "decay score" where higher = more decayed
        decay_remaining = math.pow(0.5, age_days / half_life_days)
        decay_score = 1.0 - decay_remaining

        return min(decay_score, 0.5)  # Cap at 0.5 for age factor alone

    async def _check_trending_boost(self, claim_text: str) -> float:
        """
        Check if entities in the claim are trending and calculate velocity boost

        Args:
            claim_text: The claim text

        Returns:
            Velocity boost factor (0.0 to 0.5)
        """
        # Extract potential entity names (simplified - in production, use NER)
        # For now, we'll look for capitalized words
        words = claim_text.split()
        potential_entities = [
            word.strip('.,!?;:')
            for word in words
            if word and word[0].isupper() and len(word) > 3
        ]

        if not potential_entities:
            return 0.0

        # Check velocity for the first few entities (to avoid rate limits)
        max_entities_to_check = 3
        total_velocity = 0.0
        entities_checked = 0

        for entity in potential_entities[:max_entities_to_check]:
            try:
                velocity_data = await x_api_client.get_entity_velocity(entity)
                if velocity_data.get("is_trending", False):
                    total_velocity += min(velocity_data.get("velocity_score", 0.0) / 10.0, 0.5)
                    entities_checked += 1
            except Exception as e:
                # If API fails, continue without velocity boost
                print(f"Error checking velocity for {entity}: {e}")
                continue

        # Average velocity boost
        if entities_checked > 0:
            return min(total_velocity / entities_checked, 0.5)

        return 0.0

    def calculate_vulnerability_score(
        self,
        decay_score: float,
        dependency_weight: float,
        contradiction_count: int
    ) -> float:
        """
        Calculate overall vulnerability score for triage prioritization

        Args:
            decay_score: Decay score (0-1)
            dependency_weight: Sum of support relationship weights
            contradiction_count: Number of contradictions found

        Returns:
            Vulnerability score (0-1+)
        """
        # Formula: decay × dependency_weight × (contradictions + 1)
        # Normalized to be mostly in 0-1 range but can exceed 1 for critical cases
        vulnerability = decay_score * dependency_weight * (contradiction_count + 1)

        return vulnerability

    async def batch_calculate_decay(
        self,
        claims: list[Dict[str, Any]],
        check_trending: bool = False
    ) -> list[Tuple[float, int]]:
        """
        Calculate decay scores for multiple claims in batch

        Args:
            claims: List of claim dictionaries with text, is_immutable, extracted_at
            check_trending: Whether to check trending (slower)

        Returns:
            List of (decay_score, half_life_days) tuples
        """
        results = []

        for claim in claims:
            decay_score, half_life = await self.calculate_decay_score(
                claim_text=claim["text"],
                is_immutable=claim["is_immutable"],
                extracted_at=claim["extracted_at"],
                check_trending=check_trending
            )
            results.append((decay_score, half_life))

        return results


# Singleton instance
decay_forecaster = DecayForecaster()
