import tweepy
from typing import List, Dict, Any, Optional
from app.config import settings
from datetime import datetime, timedelta


class XAPIClient:
    """Client for X (Twitter) API v2 for real-time signals and trend monitoring"""

    def __init__(self):
        self.api_key = settings.X_API_KEY
        self.api_secret = settings.X_API_SECRET
        self.access_token = settings.X_ACCESS_TOKEN
        self.access_token_secret = settings.X_ACCESS_TOKEN_SECRET
        self.bearer_token = settings.X_BEARER_TOKEN

        # Initialize Tweepy client
        self.client = tweepy.Client(
            bearer_token=self.bearer_token,
            consumer_key=self.api_key,
            consumer_secret=self.api_secret,
            access_token=self.access_token,
            access_token_secret=self.access_token_secret,
            wait_on_rate_limit=True
        )

    async def get_entity_mention_count(self, entity: str, hours: int = 24) -> int:
        """
        Get the number of mentions of an entity in recent tweets

        Args:
            entity: The entity name to search for
            hours: Number of hours to look back

        Returns:
            Count of mentions
        """
        # Calculate start time
        start_time = datetime.utcnow() - timedelta(hours=hours)

        try:
            # Search recent tweets mentioning the entity
            response = self.client.search_recent_tweets(
                query=f'"{entity}"',
                start_time=start_time,
                max_results=100,
                tweet_fields=['created_at', 'public_metrics']
            )

            if not response.data:
                return 0

            return len(response.data)

        except Exception as e:
            print(f"Error fetching mention count for {entity}: {e}")
            return 0

    async def get_entity_velocity(self, entity: str) -> Dict[str, Any]:
        """
        Calculate mention velocity (change in mention rate) for an entity

        Args:
            entity: The entity name

        Returns:
            Dictionary with velocity metrics
        """
        # Get counts for different time windows
        last_hour = await self.get_entity_mention_count(entity, hours=1)
        last_6_hours = await self.get_entity_mention_count(entity, hours=6)
        last_24_hours = await self.get_entity_mention_count(entity, hours=24)

        # Calculate rates per hour
        rate_1h = last_hour
        rate_6h = last_6_hours / 6.0
        rate_24h = last_24_hours / 24.0

        # Calculate velocity (acceleration)
        # If current rate is much higher than average, entity is trending
        velocity_score = 0.0
        if rate_24h > 0:
            velocity_score = (rate_1h - rate_24h) / rate_24h

        return {
            "entity": entity,
            "mentions_1h": last_hour,
            "mentions_6h": last_6_hours,
            "mentions_24h": last_24_hours,
            "rate_per_hour_1h": rate_1h,
            "rate_per_hour_6h": rate_6h,
            "rate_per_hour_24h": rate_24h,
            "velocity_score": velocity_score,
            "is_trending": velocity_score > 2.0,  # More than 2x normal rate
            "timestamp": datetime.utcnow().isoformat()
        }

    async def get_trending_topics(self, woeid: int = 1) -> List[Dict[str, Any]]:
        """
        Get trending topics (requires API v1.1, included for completeness)

        Args:
            woeid: Where On Earth ID (1 = worldwide)

        Returns:
            List of trending topics
        """
        try:
            # Note: This requires API v1.1 which may need additional setup
            # This is a placeholder for the structure
            trends = []
            # In production, implement using tweepy.API with v1.1 endpoints
            return trends
        except Exception as e:
            print(f"Error fetching trending topics: {e}")
            return []

    async def monitor_entity_mentions(self, entity: str, callback=None) -> None:
        """
        Set up a filtered stream to monitor entity mentions in real-time

        Args:
            entity: The entity to monitor
            callback: Callback function to handle new mentions

        Note: This requires maintaining a persistent connection.
        In production, this should run in a separate worker process.
        """
        # This is a placeholder for filtered stream implementation
        # In production, use tweepy.StreamingClient with filters
        pass

    def check_rate_limit_status(self) -> Dict[str, Any]:
        """Check current rate limit status"""
        try:
            rate_limit = self.client.get_users_mentions
            # Return rate limit info
            return {
                "remaining": "check_response_headers",
                "reset_time": "check_response_headers"
            }
        except Exception as e:
            return {"error": str(e)}


# Singleton instance
x_api_client = XAPIClient()
