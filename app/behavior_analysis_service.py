"""
Behavioral analysis service for detecting automated/bot behavior in trial sessions.
"""

import statistics
import time
import math
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from app.models import BehaviorAnalysis

logger = logging.getLogger(__name__)


@dataclass
class RequestEvent:
    """Individual request event for analysis."""
    timestamp: float
    endpoint: str
    user_agent: str
    session_id: str
    ip_address: str
    response_time: float
    status_code: int
    request_size: int = 0
    response_size: int = 0
    mouse_events: List[Dict] = None
    keyboard_events: List[Dict] = None


@dataclass
class SessionPattern:
    """Analyzed patterns for a session."""
    request_intervals: List[float]
    endpoints_accessed: List[str]
    user_agents_used: List[str]
    total_requests: int
    session_duration: float
    error_rate: float
    average_response_time: float


class BehaviorAnalysisService:
    """Service for analyzing user behavior to detect automation."""
    
    def __init__(self):
        # Thresholds for bot detection
        self.timing_regularity_threshold = 0.7  # High regularity = suspicious
        self.rapid_consumption_threshold = 0.8   # Very fast usage = suspicious
        self.min_requests_for_analysis = 3       # Need at least 3 requests
        
        # Typical human behavior patterns
        self.human_interval_variance = 0.3       # Humans vary timing by ~30%
        self.human_min_interval = 2.0           # Humans rarely go faster than 2 seconds
        self.human_max_burst_size = 3           # Humans rarely make >3 rapid requests
        
        # Session data cache
        self.session_cache: Dict[str, List[RequestEvent]] = {}
    
    def add_request_event(self, event: RequestEvent):
        """Add a request event for analysis."""
        session_id = event.session_id
        
        if session_id not in self.session_cache:
            self.session_cache[session_id] = []
        
        self.session_cache[session_id].append(event)
        
        # Keep only recent events (last 100 per session)
        if len(self.session_cache[session_id]) > 100:
            self.session_cache[session_id] = self.session_cache[session_id][-100:]
    
    def analyze_session_behavior(self, session_id: str) -> BehaviorAnalysis:
        """Analyze behavior patterns for a session."""
        
        events = self.session_cache.get(session_id, [])
        
        if len(events) < self.min_requests_for_analysis:
            return BehaviorAnalysis(
                session_id=session_id,
                timing_regularity_score=0.0,
                rapid_consumption_score=0.0,
                interaction_naturalness_score=0.0,
                overall_bot_probability=0.0,
                analyzed_requests=len(events)
            )
        
        # Extract patterns
        pattern = self._extract_session_pattern(events)
        
        # Calculate individual scores
        timing_score = self._score_timing_regularity(pattern)
        consumption_score = self._score_rapid_consumption(pattern)
        interaction_score = self._score_interaction_naturalness(events)
        
        # Calculate overall bot probability
        overall_score = self._calculate_overall_bot_probability(
            timing_score, consumption_score, interaction_score
        )
        
        return BehaviorAnalysis(
            session_id=session_id,
            timing_regularity_score=timing_score,
            rapid_consumption_score=consumption_score,
            interaction_naturalness_score=interaction_score,
            overall_bot_probability=overall_score,
            analyzed_requests=len(events)
        )
    
    def _extract_session_pattern(self, events: List[RequestEvent]) -> SessionPattern:
        """Extract behavioral patterns from request events."""
        
        if not events:
            return SessionPattern([], [], [], 0, 0.0, 0.0, 0.0)
        
        # Calculate request intervals
        intervals = []
        for i in range(1, len(events)):
            interval = events[i].timestamp - events[i-1].timestamp
            intervals.append(interval)
        
        # Collect unique values
        endpoints = list(set(event.endpoint for event in events))
        user_agents = list(set(event.user_agent for event in events))
        
        # Calculate error rate
        error_count = sum(1 for event in events if event.status_code >= 400)
        error_rate = error_count / len(events) if events else 0.0
        
        # Calculate session duration
        duration = events[-1].timestamp - events[0].timestamp if len(events) > 1 else 0.0
        
        # Calculate average response time
        avg_response_time = statistics.mean(event.response_time for event in events)
        
        return SessionPattern(
            request_intervals=intervals,
            endpoints_accessed=endpoints,
            user_agents_used=user_agents,
            total_requests=len(events),
            session_duration=duration,
            error_rate=error_rate,
            average_response_time=avg_response_time
        )
    
    def _score_timing_regularity(self, pattern: SessionPattern) -> float:
        """Score timing pattern regularity (higher = more bot-like)."""
        
        intervals = pattern.request_intervals
        if len(intervals) < 2:
            return 0.0
        
        try:
            # Calculate coefficient of variation
            mean_interval = statistics.mean(intervals)
            if mean_interval == 0:
                return 1.0  # Zero intervals are highly suspicious
            
            std_dev = statistics.stdev(intervals)
            coefficient_of_variation = std_dev / mean_interval
            
            # Low variation = high regularity = suspicious
            regularity_score = max(0, 1.0 - (coefficient_of_variation / self.human_interval_variance))
            
            # Very fast regular intervals are extra suspicious
            if mean_interval < self.human_min_interval:
                regularity_score = min(1.0, regularity_score + 0.3)
            
            # Check for exact intervals (extremely suspicious)
            unique_intervals = len(set(intervals))
            if unique_intervals == 1 and len(intervals) > 3:
                regularity_score = 0.95  # Almost certainly a bot
            
            return min(1.0, regularity_score)
            
        except statistics.StatisticsError:
            return 0.0
    
    def _score_rapid_consumption(self, pattern: SessionPattern) -> float:
        """Score rapid consumption patterns (higher = more suspicious)."""
        
        intervals = pattern.request_intervals
        if not intervals:
            return 0.0
        
        score_factors = []
        
        # Factor 1: Very short intervals
        short_intervals = [i for i in intervals if i < self.human_min_interval]
        if intervals:
            short_interval_ratio = len(short_intervals) / len(intervals)
            score_factors.append(short_interval_ratio)
        
        # Factor 2: Burst patterns (many requests in short time)
        burst_score = self._analyze_burst_patterns(intervals)
        score_factors.append(burst_score)
        
        # Factor 3: Overall request rate
        if pattern.session_duration > 0:
            requests_per_minute = (pattern.total_requests / pattern.session_duration) * 60
            # More than 10 requests per minute is suspicious for trial users
            rate_score = min(1.0, max(0, (requests_per_minute - 5) / 10))
            score_factors.append(rate_score)
        
        # Factor 4: No "thinking time" between actions
        thinking_time_score = self._analyze_thinking_time(intervals)
        score_factors.append(thinking_time_score)
        
        return min(1.0, sum(score_factors) / len(score_factors))
    
    def _score_interaction_naturalness(self, events: List[RequestEvent]) -> float:
        """Score naturalness of user interactions (higher = less natural)."""
        
        if not events:
            return 0.0
        
        score_factors = []
        
        # Factor 1: User agent consistency
        unique_user_agents = len(set(event.user_agent for event in events))
        if unique_user_agents > 1:
            # Changing user agents mid-session is suspicious
            score_factors.append(0.7)
        else:
            score_factors.append(0.0)
        
        # Factor 2: Endpoint access patterns
        endpoint_score = self._analyze_endpoint_patterns(events)
        score_factors.append(endpoint_score)
        
        # Factor 3: Error handling behavior
        error_score = self._analyze_error_handling(events)
        score_factors.append(error_score)
        
        # Factor 4: Request size patterns
        size_score = self._analyze_request_sizes(events)
        score_factors.append(size_score)
        
        return min(1.0, sum(score_factors) / len(score_factors))
    
    def _analyze_burst_patterns(self, intervals: List[float]) -> float:
        """Analyze burst patterns in request intervals."""
        
        if len(intervals) < 3:
            return 0.0
        
        # Find consecutive short intervals (bursts)
        burst_count = 0
        current_burst_size = 0
        
        for interval in intervals:
            if interval < self.human_min_interval:
                current_burst_size += 1
            else:
                if current_burst_size > self.human_max_burst_size:
                    burst_count += 1
                current_burst_size = 0
        
        # Check final burst
        if current_burst_size > self.human_max_burst_size:
            burst_count += 1
        
        # Score based on number of suspicious bursts
        return min(1.0, burst_count / max(1, len(intervals) // 5))
    
    def _analyze_thinking_time(self, intervals: List[float]) -> float:
        """Analyze if there's appropriate 'thinking time' between requests."""
        
        if not intervals:
            return 0.0
        
        # Humans typically have some variance and longer pauses
        # Very consistent short intervals suggest automation
        
        quick_intervals = [i for i in intervals if i < 1.0]  # Less than 1 second
        if len(quick_intervals) / len(intervals) > 0.8:  # 80% of requests very fast
            return 0.8
        
        # Look for lack of natural pauses
        long_pauses = [i for i in intervals if i > 10.0]  # More than 10 seconds
        if len(long_pauses) == 0 and len(intervals) > 5:
            return 0.6  # No thinking time at all
        
        return 0.0
    
    def _analyze_endpoint_patterns(self, events: List[RequestEvent]) -> float:
        """Analyze endpoint access patterns for bot-like behavior."""
        
        endpoints = [event.endpoint for event in events]
        
        # Bots often follow very predictable patterns
        if len(set(endpoints)) == 1 and len(endpoints) > 5:
            # Accessing the same endpoint repeatedly
            return 0.7
        
        # Look for systematic scanning patterns
        if self._detect_scanning_pattern(endpoints):
            return 0.9
        
        return 0.0
    
    def _analyze_error_handling(self, events: List[RequestEvent]) -> float:
        """Analyze how errors are handled (bots often ignore errors)."""
        
        # Look for continued requests after errors
        error_indices = [i for i, event in enumerate(events) if event.status_code >= 400]
        
        if not error_indices:
            return 0.0
        
        # Check if requests continue immediately after errors
        immediate_retries = 0
        for error_idx in error_indices:
            if error_idx < len(events) - 1:
                next_event = events[error_idx + 1]
                time_gap = next_event.timestamp - events[error_idx].timestamp
                if time_gap < 2.0:  # Less than 2 seconds after error
                    immediate_retries += 1
        
        if error_indices and immediate_retries / len(error_indices) > 0.5:
            return 0.6  # More than half of errors followed by immediate retry
        
        return 0.0
    
    def _analyze_request_sizes(self, events: List[RequestEvent]) -> float:
        """Analyze request size patterns."""
        
        sizes = [event.request_size for event in events if event.request_size > 0]
        
        if len(sizes) < 3:
            return 0.0
        
        # Bots often have very consistent request sizes
        try:
            unique_sizes = len(set(sizes))
            if unique_sizes == 1 and len(sizes) > 3:
                return 0.5  # All requests exactly the same size
        except:
            pass
        
        return 0.0
    
    def _detect_scanning_pattern(self, endpoints: List[str]) -> bool:
        """Detect systematic scanning patterns."""
        
        # Look for systematic enumeration patterns
        # This is a simplified implementation
        
        if len(endpoints) < 5:
            return False
        
        # Check for sequential access to different endpoints
        unique_endpoints = list(set(endpoints))
        if len(unique_endpoints) >= len(endpoints) * 0.8:
            # Most requests are to different endpoints = scanning
            return True
        
        return False
    
    def _calculate_overall_bot_probability(self, timing_score: float, 
                                         consumption_score: float,
                                         interaction_score: float) -> float:
        """Calculate overall bot probability from individual scores."""
        
        # Weighted combination of scores
        weights = {
            'timing': 0.4,      # Timing is most important
            'consumption': 0.35, # Consumption patterns are very telling
            'interaction': 0.25  # Interaction naturalness
        }
        
        weighted_score = (
            timing_score * weights['timing'] +
            consumption_score * weights['consumption'] +
            interaction_score * weights['interaction']
        )
        
        # Apply non-linear scaling to make extreme values more definitive
        if weighted_score > 0.8:
            weighted_score = min(1.0, weighted_score + 0.1)
        elif weighted_score < 0.2:
            weighted_score = max(0.0, weighted_score - 0.1)
        
        return min(1.0, max(0.0, weighted_score))
    
    def get_session_summary(self, session_id: str) -> Dict:
        """Get summary of session behavior for debugging."""
        
        events = self.session_cache.get(session_id, [])
        analysis = self.analyze_session_behavior(session_id)
        
        if not events:
            return {'session_id': session_id, 'no_data': True}
        
        pattern = self._extract_session_pattern(events)
        
        return {
            'session_id': session_id,
            'total_requests': len(events),
            'session_duration': pattern.session_duration,
            'unique_endpoints': len(pattern.endpoints_accessed),
            'error_rate': pattern.error_rate,
            'avg_interval': statistics.mean(pattern.request_intervals) if pattern.request_intervals else 0,
            'interval_variance': statistics.variance(pattern.request_intervals) if len(pattern.request_intervals) > 1 else 0,
            'analysis': analysis,
            'first_request': events[0].timestamp,
            'last_request': events[-1].timestamp
        }
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Clean up old session data."""
        
        current_time = time.time()
        cutoff_time = current_time - (max_age_hours * 3600)
        
        sessions_to_remove = []
        
        for session_id, events in self.session_cache.items():
            if events and events[-1].timestamp < cutoff_time:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.session_cache[session_id]
        
        logger.info(f"Cleaned up {len(sessions_to_remove)} old behavior analysis sessions")


# Singleton instance
_behavior_analysis_service = None


def get_behavior_analysis_service() -> BehaviorAnalysisService:
    """Get singleton behavior analysis service instance."""
    global _behavior_analysis_service
    if _behavior_analysis_service is None:
        _behavior_analysis_service = BehaviorAnalysisService()
    return _behavior_analysis_service