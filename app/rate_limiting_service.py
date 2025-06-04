"""
Advanced rate limiting service for trial abuse prevention.
"""

import asyncio
import time
import hashlib
import logging
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import os
from app.models import RateLimitResult, SecurityConfig

logger = logging.getLogger(__name__)


class RateLimitType(str, Enum):
    """Types of rate limits."""
    TRIAL_CREATION_IP = "trial_creation_ip"
    TRIAL_CREATION_FINGERPRINT = "trial_creation_fingerprint"
    IMAGE_GENERATION = "image_generation"
    API_REQUESTS = "api_requests"
    SUSPICIOUS_IP_PENALTY = "suspicious_ip_penalty"
    GLOBAL_TRIAL_CREATION = "global_trial_creation"


@dataclass
class RateLimitRule:
    """Rate limit rule definition."""
    limit_type: RateLimitType
    max_requests: int
    window_seconds: int
    identifier_key: str
    description: str
    risk_multiplier_enabled: bool = True


@dataclass
class RateLimitState:
    """Current state of a rate limit."""
    count: int
    first_request_time: float
    last_request_time: float
    reset_time: float


class InMemoryRateLimiter:
    """In-memory rate limiter (fallback when Redis unavailable)."""
    
    def __init__(self):
        self.state: Dict[str, RateLimitState] = {}
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
    
    def check_limit(self, key: str, limit: int, window: int) -> Tuple[bool, int, int]:
        """Check if request is within rate limit."""
        
        current_time = time.time()
        
        # Periodic cleanup
        if current_time - self.last_cleanup > self.cleanup_interval:
            self._cleanup_expired_entries(current_time)
            self.last_cleanup = current_time
        
        # Get or create state
        if key not in self.state:
            self.state[key] = RateLimitState(
                count=1,
                first_request_time=current_time,
                last_request_time=current_time,
                reset_time=current_time + window
            )
            return True, 1, limit
        
        state = self.state[key]
        
        # Check if window has expired
        if current_time >= state.reset_time:
            # Reset window
            state.count = 1
            state.first_request_time = current_time
            state.last_request_time = current_time
            state.reset_time = current_time + window
            return True, 1, limit
        
        # Within window - check limit
        if state.count >= limit:
            return False, state.count, limit
        
        # Increment count
        state.count += 1
        state.last_request_time = current_time
        
        return True, state.count, limit
    
    def _cleanup_expired_entries(self, current_time: float):
        """Remove expired rate limit entries."""
        
        expired_keys = [
            key for key, state in self.state.items()
            if current_time >= state.reset_time + 3600  # Keep for 1 hour after expiry
        ]
        
        for key in expired_keys:
            del self.state[key]
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired rate limit entries")


class RedisRateLimiter:
    """Redis-based rate limiter (preferred when available)."""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def check_limit(self, key: str, limit: int, window: int) -> Tuple[bool, int, int]:
        """Check rate limit using Redis."""
        
        try:
            current_time = time.time()
            
            # Use sliding window log approach
            pipe = self.redis.pipeline()
            
            # Remove old entries
            pipe.zremrangebyscore(key, 0, current_time - window)
            
            # Count current entries
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {str(current_time): current_time})
            
            # Set expiry
            pipe.expire(key, window + 60)  # Extra buffer
            
            results = await pipe.execute()
            current_count = results[1] + 1  # +1 for the current request
            
            if current_count > limit:
                # Remove the request we just added since it's over limit
                await self.redis.zrem(key, str(current_time))
                return False, current_count - 1, limit
            
            return True, current_count, limit
            
        except Exception as e:
            logger.error(f"Redis rate limiting error: {e}")
            # Fallback to allowing request
            return True, 0, limit


class AdvancedRateLimitingService:
    """Advanced rate limiting with multiple dimensions and risk-based adjustments."""
    
    def __init__(self, config: Optional[SecurityConfig] = None, redis_client=None):
        self.config = config or SecurityConfig()
        self.redis_client = redis_client
        
        # Initialize rate limiter
        if redis_client:
            self.rate_limiter = RedisRateLimiter(redis_client)
        else:
            self.rate_limiter = InMemoryRateLimiter()
            logger.warning("Using in-memory rate limiter - Redis not available")
        
        # Define rate limit rules
        self.rules = {
            RateLimitType.TRIAL_CREATION_IP: RateLimitRule(
                limit_type=RateLimitType.TRIAL_CREATION_IP,
                max_requests=self.config.trial_creation_per_ip_per_hour,
                window_seconds=3600,
                identifier_key="ip_address",
                description="Trial session creation per IP address per hour"
            ),
            RateLimitType.TRIAL_CREATION_FINGERPRINT: RateLimitRule(
                limit_type=RateLimitType.TRIAL_CREATION_FINGERPRINT,
                max_requests=self.config.trial_creation_per_fingerprint_per_hour,
                window_seconds=3600,
                identifier_key="device_fingerprint",
                description="Trial session creation per device fingerprint per hour"
            ),
            RateLimitType.IMAGE_GENERATION: RateLimitRule(
                limit_type=RateLimitType.IMAGE_GENERATION,
                max_requests=self.config.image_generation_per_minute,
                window_seconds=60,
                identifier_key="session_id",
                description="Image generation per session per minute"
            ),
            RateLimitType.API_REQUESTS: RateLimitRule(
                limit_type=RateLimitType.API_REQUESTS,
                max_requests=60,
                window_seconds=60,
                identifier_key="ip_address",
                description="General API requests per IP per minute"
            ),
            RateLimitType.SUSPICIOUS_IP_PENALTY: RateLimitRule(
                limit_type=RateLimitType.SUSPICIOUS_IP_PENALTY,
                max_requests=1,
                window_seconds=7200,  # 2 hours
                identifier_key="ip_address",
                description="Penalty rate limit for suspicious IPs",
                risk_multiplier_enabled=False  # Fixed penalty
            ),
            RateLimitType.GLOBAL_TRIAL_CREATION: RateLimitRule(
                limit_type=RateLimitType.GLOBAL_TRIAL_CREATION,
                max_requests=100,
                window_seconds=3600,
                identifier_key="global",
                description="Global trial creation rate limit per hour"
            )
        }
        
        # Statistics
        self.stats = {
            'total_checks': 0,
            'total_blocks': 0,
            'blocks_by_type': {rule_type.value: 0 for rule_type in RateLimitType}
        }
    
    async def check_rate_limits(self, 
                               limit_type: RateLimitType,
                               identifier: str,
                               risk_multiplier: float = 1.0) -> RateLimitResult:
        """Check if request is within rate limits."""
        
        self.stats['total_checks'] += 1
        
        if limit_type not in self.rules:
            logger.warning(f"Unknown rate limit type: {limit_type}")
            return RateLimitResult(allowed=True, current_usage=0, limit=0, window_seconds=0)
        
        rule = self.rules[limit_type]
        
        # Calculate adjusted limit based on risk
        adjusted_limit = rule.max_requests
        if rule.risk_multiplier_enabled and risk_multiplier > 1.0:
            adjusted_limit = max(1, int(rule.max_requests / risk_multiplier))
        
        # Create rate limit key
        rate_limit_key = self._create_rate_limit_key(limit_type, identifier)
        
        # Check rate limit
        if isinstance(self.rate_limiter, RedisRateLimiter):
            allowed, current_count, limit = await self.rate_limiter.check_limit(
                rate_limit_key, adjusted_limit, rule.window_seconds
            )
        else:
            allowed, current_count, limit = self.rate_limiter.check_limit(
                rate_limit_key, adjusted_limit, rule.window_seconds
            )
        
        if not allowed:
            self.stats['total_blocks'] += 1
            self.stats['blocks_by_type'][limit_type.value] += 1
            
            logger.info(f"Rate limit exceeded: {limit_type.value} for {identifier} "
                       f"({current_count}/{adjusted_limit} in {rule.window_seconds}s)")
        
        retry_after = rule.window_seconds if not allowed else None
        
        return RateLimitResult(
            allowed=allowed,
            current_usage=current_count,
            limit=adjusted_limit,
            retry_after=retry_after,
            window_seconds=rule.window_seconds
        )
    
    async def check_multiple_limits(self, 
                                   checks: List[Tuple[RateLimitType, str, float]]) -> List[RateLimitResult]:
        """Check multiple rate limits concurrently."""
        
        tasks = [
            self.check_rate_limits(limit_type, identifier, risk_multiplier)
            for limit_type, identifier, risk_multiplier in checks
        ]
        
        return await asyncio.gather(*tasks)
    
    async def check_trial_creation_limits(self, 
                                        ip_address: str,
                                        device_fingerprint: Optional[str] = None,
                                        risk_score: float = 0.0) -> Dict[str, RateLimitResult]:
        """Check all rate limits relevant to trial creation."""
        
        risk_multiplier = max(1.0, risk_score * 3)  # Convert 0-1 risk to 1-3 multiplier
        
        checks = [
            (RateLimitType.TRIAL_CREATION_IP, ip_address, risk_multiplier),
            (RateLimitType.GLOBAL_TRIAL_CREATION, "global", 1.0)  # Global limit not risk-adjusted
        ]
        
        if device_fingerprint:
            checks.append((RateLimitType.TRIAL_CREATION_FINGERPRINT, device_fingerprint, risk_multiplier))
        
        # Apply penalty for suspicious IPs
        if risk_score > 0.7:
            checks.append((RateLimitType.SUSPICIOUS_IP_PENALTY, ip_address, 1.0))
        
        results = await self.check_multiple_limits(checks)
        
        # Map results to meaningful names
        result_map = {
            'ip_limit': results[0],
            'global_limit': results[1]
        }
        
        if device_fingerprint:
            result_map['fingerprint_limit'] = results[2]
            if risk_score > 0.7:
                result_map['penalty_limit'] = results[3]
        elif risk_score > 0.7:
            result_map['penalty_limit'] = results[2]
        
        return result_map
    
    async def check_image_generation_limits(self, 
                                          session_id: str,
                                          ip_address: str,
                                          risk_score: float = 0.0) -> Dict[str, RateLimitResult]:
        """Check rate limits for image generation."""
        
        risk_multiplier = max(1.0, risk_score * 2)  # More lenient for image generation
        
        checks = [
            (RateLimitType.IMAGE_GENERATION, session_id, risk_multiplier),
            (RateLimitType.API_REQUESTS, ip_address, risk_multiplier)
        ]
        
        results = await self.check_multiple_limits(checks)
        
        return {
            'session_limit': results[0],
            'ip_api_limit': results[1]
        }
    
    def _create_rate_limit_key(self, limit_type: RateLimitType, identifier: str) -> str:
        """Create a unique key for rate limiting."""
        
        # Hash the identifier for privacy and consistent key length
        identifier_hash = hashlib.sha256(identifier.encode()).hexdigest()[:16]
        
        return f"rate_limit:{limit_type.value}:{identifier_hash}"
    
    async def reset_rate_limit(self, limit_type: RateLimitType, identifier: str) -> bool:
        """Reset rate limit for a specific identifier (admin function)."""
        
        rate_limit_key = self._create_rate_limit_key(limit_type, identifier)
        
        try:
            if isinstance(self.rate_limiter, RedisRateLimiter):
                await self.redis_client.delete(rate_limit_key)
            else:
                if rate_limit_key in self.rate_limiter.state:
                    del self.rate_limiter.state[rate_limit_key]
            
            logger.info(f"Reset rate limit: {limit_type.value} for {identifier}")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting rate limit: {e}")
            return False
    
    async def get_rate_limit_status(self, 
                                   limit_type: RateLimitType, 
                                   identifier: str) -> Dict:
        """Get current rate limit status without incrementing count."""
        
        rate_limit_key = self._create_rate_limit_key(limit_type, identifier)
        rule = self.rules[limit_type]
        
        try:
            if isinstance(self.rate_limiter, RedisRateLimiter):
                current_time = time.time()
                count = await self.redis_client.zcount(
                    rate_limit_key, 
                    current_time - rule.window_seconds, 
                    current_time
                )
                ttl = await self.redis_client.ttl(rate_limit_key)
            else:
                if rate_limit_key in self.rate_limiter.state:
                    state = self.rate_limiter.state[rate_limit_key]
                    current_time = time.time()
                    if current_time < state.reset_time:
                        count = state.count
                        ttl = int(state.reset_time - current_time)
                    else:
                        count = 0
                        ttl = 0
                else:
                    count = 0
                    ttl = 0
            
            return {
                'limit_type': limit_type.value,
                'current_count': count,
                'max_limit': rule.max_requests,
                'window_seconds': rule.window_seconds,
                'time_until_reset': ttl,
                'requests_remaining': max(0, rule.max_requests - count)
            }
            
        except Exception as e:
            logger.error(f"Error getting rate limit status: {e}")
            return {
                'limit_type': limit_type.value,
                'error': str(e)
            }
    
    def get_statistics(self) -> Dict:
        """Get rate limiting statistics."""
        
        return {
            'total_checks': self.stats['total_checks'],
            'total_blocks': self.stats['total_blocks'],
            'block_rate': self.stats['total_blocks'] / max(1, self.stats['total_checks']),
            'blocks_by_type': self.stats['blocks_by_type'],
            'active_rules': len(self.rules),
            'limiter_type': 'redis' if isinstance(self.rate_limiter, RedisRateLimiter) else 'memory'
        }
    
    def update_rule(self, limit_type: RateLimitType, max_requests: int, window_seconds: int):
        """Update a rate limiting rule (admin function)."""
        
        if limit_type in self.rules:
            rule = self.rules[limit_type]
            rule.max_requests = max_requests
            rule.window_seconds = window_seconds
            
            logger.info(f"Updated rate limit rule: {limit_type.value} -> {max_requests}/{window_seconds}s")
        else:
            logger.warning(f"Cannot update unknown rate limit type: {limit_type}")
    
    async def get_top_rate_limited_identifiers(self, limit_type: RateLimitType, 
                                             top_n: int = 10) -> List[Dict]:
        """Get top rate-limited identifiers for analysis."""
        
        # This would require more sophisticated tracking in production
        # For now, return empty list
        return []


# Singleton instance
_rate_limiting_service = None


def get_rate_limiting_service(config: Optional[SecurityConfig] = None, 
                            redis_client=None) -> AdvancedRateLimitingService:
    """Get singleton rate limiting service instance."""
    global _rate_limiting_service
    if _rate_limiting_service is None:
        _rate_limiting_service = AdvancedRateLimitingService(config, redis_client)
    return _rate_limiting_service