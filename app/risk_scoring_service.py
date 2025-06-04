"""
Risk scoring service that combines all abuse prevention signals into unified risk assessment.
"""

import time
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from app.models import (
    IPRiskAssessment, BehaviorAnalysis, TrialSession, 
    SecurityConfig, VerificationChallenge
)
from app.fingerprint_service import DeviceFingerprint
from app.vpn_detection_service import get_vpn_detection_service
from app.behavior_analysis_service import get_behavior_analysis_service
from app.captcha_service import get_captcha_service

logger = logging.getLogger(__name__)


@dataclass
class RiskFactors:
    """Individual risk factors contributing to overall score."""
    ip_risk_score: float = 0.0
    vpn_proxy_score: float = 0.0
    fingerprint_risk_score: float = 0.0
    behavior_risk_score: float = 0.0
    rate_limit_score: float = 0.0
    geolocation_score: float = 0.0
    timing_score: float = 0.0
    historical_score: float = 0.0


@dataclass
class RiskAssessment:
    """Complete risk assessment result."""
    session_id: str
    overall_risk_score: float
    risk_level: str  # 'low', 'medium', 'high', 'critical'
    recommended_action: str
    required_challenge: VerificationChallenge
    risk_factors: RiskFactors
    confidence: float
    assessment_timestamp: float
    flagged_reasons: List[str]


class RiskScoringService:
    """Central service for computing unified risk scores."""
    
    def __init__(self, config: Optional[SecurityConfig] = None):
        self.config = config or SecurityConfig()
        
        # Risk factor weights
        self.weights = {
            'ip_risk': 0.25,           # VPN/proxy detection
            'fingerprint_risk': 0.20,  # Device fingerprinting
            'behavior_risk': 0.30,     # Behavioral analysis
            'rate_limit': 0.15,        # Rate limiting violations
            'historical': 0.10         # Historical patterns
        }
        
        # Risk level thresholds
        self.risk_levels = {
            'low': (0.0, 0.3),
            'medium': (0.3, 0.6),
            'high': (0.6, 0.8),
            'critical': (0.8, 1.0)
        }
        
        # Action thresholds
        self.action_thresholds = {
            'allow': 0.3,
            'challenge': 0.5,
            'block_temporary': 0.8,
            'block_permanent': 0.95
        }
        
        # Services
        self.vpn_service = get_vpn_detection_service()
        self.behavior_service = get_behavior_analysis_service()
        self.captcha_service = get_captcha_service()
        
        # Cache for recent assessments
        self.assessment_cache: Dict[str, RiskAssessment] = {}
        self.cache_duration = 300  # 5 minutes
    
    async def assess_trial_session_risk(self, 
                                      session: TrialSession,
                                      fingerprint: Optional[DeviceFingerprint] = None,
                                      request_history: Optional[List] = None) -> RiskAssessment:
        """Comprehensive risk assessment for a trial session."""
        
        # Check cache first
        cache_key = f"{session.session_id}_{int(time.time() // 60)}"  # Cache per minute
        if cache_key in self.assessment_cache:
            cached = self.assessment_cache[cache_key]
            if time.time() - cached.assessment_timestamp < self.cache_duration:
                return cached
        
        # Collect all risk factors
        risk_factors = await self._collect_risk_factors(session, fingerprint, request_history)
        
        # Calculate overall risk score
        overall_score = self._calculate_overall_score(risk_factors)
        
        # Determine risk level and actions
        risk_level = self._determine_risk_level(overall_score)
        recommended_action = self._determine_recommended_action(overall_score, risk_factors)
        required_challenge = self._determine_required_challenge(overall_score, session)
        
        # Calculate confidence
        confidence = self._calculate_confidence(risk_factors)
        
        # Generate flagged reasons
        flagged_reasons = self._generate_flagged_reasons(risk_factors, overall_score)
        
        # Create assessment
        assessment = RiskAssessment(
            session_id=session.session_id,
            overall_risk_score=overall_score,
            risk_level=risk_level,
            recommended_action=recommended_action,
            required_challenge=required_challenge,
            risk_factors=risk_factors,
            confidence=confidence,
            assessment_timestamp=time.time(),
            flagged_reasons=flagged_reasons
        )
        
        # Cache the assessment
        self.assessment_cache[cache_key] = assessment
        
        return assessment
    
    async def _collect_risk_factors(self, 
                                   session: TrialSession,
                                   fingerprint: Optional[DeviceFingerprint],
                                   request_history: Optional[List]) -> RiskFactors:
        """Collect individual risk factors from all sources."""
        
        # IP risk assessment
        ip_assessment = await self.vpn_service.assess_ip_risk(session.ip_address)
        ip_risk_score = self._calculate_ip_risk_score(ip_assessment)
        
        # Fingerprint risk assessment
        fingerprint_risk_score = self._calculate_fingerprint_risk_score(fingerprint, session)
        
        # Behavioral analysis
        behavior_analysis = self.behavior_service.analyze_session_behavior(session.session_id)
        behavior_risk_score = behavior_analysis.overall_bot_probability
        
        # Rate limiting score
        rate_limit_score = self._calculate_rate_limit_score(session)
        
        # Historical patterns
        historical_score = self._calculate_historical_risk_score(session)
        
        return RiskFactors(
            ip_risk_score=ip_risk_score,
            vpn_proxy_score=ip_assessment.risk_score,
            fingerprint_risk_score=fingerprint_risk_score,
            behavior_risk_score=behavior_risk_score,
            rate_limit_score=rate_limit_score,
            geolocation_score=self._calculate_geolocation_score(ip_assessment),
            timing_score=self._calculate_timing_score(session),
            historical_score=historical_score
        )
    
    def _calculate_ip_risk_score(self, ip_assessment: IPRiskAssessment) -> float:
        """Calculate risk score from IP assessment."""
        
        score = 0.0
        
        # VPN/Proxy detection
        if ip_assessment.is_vpn:
            score += 0.7
        if ip_assessment.is_proxy:
            score += 0.6
        if ip_assessment.is_tor:
            score += 0.9
        if ip_assessment.is_datacenter:
            score += 0.4
        
        # Base risk score from external services
        score += ip_assessment.risk_score * 0.5
        
        # Apply confidence weighting
        score *= ip_assessment.confidence
        
        return min(1.0, score)
    
    def _calculate_fingerprint_risk_score(self, 
                                        fingerprint: Optional[DeviceFingerprint],
                                        session: TrialSession) -> float:
        """Calculate risk score from fingerprint analysis."""
        
        if not fingerprint:
            return 0.3  # Missing fingerprint is moderately suspicious
        
        score = 0.0
        
        # Check for fingerprint spoofing indicators
        if not fingerprint.client_fingerprint:
            score += 0.4  # No client fingerprint
        
        # Very short or suspicious fingerprints
        if fingerprint.canvas_fingerprint and len(fingerprint.canvas_fingerprint) < 10:
            score += 0.5
        
        if fingerprint.webgl_fingerprint and len(fingerprint.webgl_fingerprint) < 10:
            score += 0.5
        
        # Inconsistent screen resolution
        if fingerprint.screen_resolution:
            if not self._validate_screen_resolution(fingerprint.screen_resolution):
                score += 0.3
        
        # Fingerprint reuse across sessions (would need historical data)
        # This would be implemented with database queries in production
        
        return min(1.0, score)
    
    def _calculate_rate_limit_score(self, session: TrialSession) -> float:
        """Calculate risk score from rate limiting violations."""
        
        score = 0.0
        
        # Rapid session creation
        if hasattr(session, 'creation_timestamp'):
            current_time = time.time()
            if current_time - session.creation_timestamp < 60:  # Created less than 1 min ago
                score += 0.2
        
        # High request frequency
        if hasattr(session, 'request_timestamps') and session.request_timestamps:
            recent_requests = [
                ts for ts in session.request_timestamps 
                if time.time() - ts < 300  # Last 5 minutes
            ]
            if len(recent_requests) > 10:  # More than 10 requests in 5 minutes
                score += 0.4
        
        # Usage pattern analysis
        if session.images_used > 3 and hasattr(session, 'creation_timestamp'):
            time_since_creation = time.time() - session.creation_timestamp
            if time_since_creation < 300:  # Less than 5 minutes
                score += 0.6  # Very rapid consumption
        
        return min(1.0, score)
    
    def _calculate_geolocation_score(self, ip_assessment: IPRiskAssessment) -> float:
        """Calculate risk score from geolocation analysis."""
        
        score = 0.0
        
        # High-risk countries (simplified)
        high_risk_countries = {'CN', 'RU', 'IR', 'KP', 'BY'}
        if ip_assessment.country_code in high_risk_countries:
            score += 0.3
        
        # Suspicious ASN patterns
        if ip_assessment.asn:
            # Known VPN/proxy ASNs would be checked here
            pass
        
        return min(1.0, score)
    
    def _calculate_timing_score(self, session: TrialSession) -> float:
        """Calculate risk score from timing patterns."""
        
        score = 0.0
        
        # Very new session making requests immediately
        if hasattr(session, 'creation_timestamp'):
            time_since_creation = time.time() - session.creation_timestamp
            if time_since_creation < 30 and session.images_used > 0:  # Started using within 30 seconds
                score += 0.4
        
        # Requests outside normal hours (basic heuristic)
        import datetime
        current_hour = datetime.datetime.now().hour
        if current_hour < 6 or current_hour > 23:  # Late night/early morning
            score += 0.2
        
        return min(1.0, score)
    
    def _calculate_historical_risk_score(self, session: TrialSession) -> float:
        """Calculate risk score from historical patterns."""
        
        # This would analyze historical patterns for the IP/fingerprint
        # For now, return basic score based on existing session data
        
        score = 0.0
        
        # Check if already flagged
        if session.is_flagged:
            score += 0.8
        
        # Existing risk score
        score += session.risk_score * 0.5
        
        return min(1.0, score)
    
    def _calculate_overall_score(self, risk_factors: RiskFactors) -> float:
        """Calculate weighted overall risk score."""
        
        weighted_score = (
            risk_factors.ip_risk_score * self.weights['ip_risk'] +
            risk_factors.fingerprint_risk_score * self.weights['fingerprint_risk'] +
            risk_factors.behavior_risk_score * self.weights['behavior_risk'] +
            risk_factors.rate_limit_score * self.weights['rate_limit'] +
            risk_factors.historical_score * self.weights['historical']
        )
        
        # Apply non-linear scaling for extreme values
        if weighted_score > 0.8:
            weighted_score = min(1.0, weighted_score + 0.1)
        elif weighted_score > 0.6:
            weighted_score = min(1.0, weighted_score + 0.05)
        
        return min(1.0, max(0.0, weighted_score))
    
    def _determine_risk_level(self, score: float) -> str:
        """Determine risk level from score."""
        
        for level, (min_score, max_score) in self.risk_levels.items():
            if min_score <= score < max_score:
                return level
        
        return 'critical'  # Fallback for score >= 1.0
    
    def _determine_recommended_action(self, score: float, risk_factors: RiskFactors) -> str:
        """Determine recommended action based on risk score."""
        
        if score < self.action_thresholds['allow']:
            return 'allow'
        elif score < self.action_thresholds['challenge']:
            return 'challenge'
        elif score < self.action_thresholds['block_temporary']:
            return 'block_temporary'
        else:
            return 'block_permanent'
    
    def _determine_required_challenge(self, score: float, session: TrialSession) -> VerificationChallenge:
        """Determine required verification challenge."""
        
        # Consider previous challenges passed
        previous_challenges = getattr(session, 'verification_challenges_passed', 0)
        
        return self.captcha_service.determine_challenge_level(score, previous_challenges)
    
    def _calculate_confidence(self, risk_factors: RiskFactors) -> float:
        """Calculate confidence in the risk assessment."""
        
        # Base confidence on availability of data
        confidence_factors = []
        
        # IP assessment confidence
        if risk_factors.ip_risk_score > 0:
            confidence_factors.append(0.8)
        else:
            confidence_factors.append(0.4)
        
        # Fingerprint availability
        if risk_factors.fingerprint_risk_score > 0:
            confidence_factors.append(0.9)
        else:
            confidence_factors.append(0.3)
        
        # Behavioral analysis (needs multiple requests)
        if risk_factors.behavior_risk_score > 0:
            confidence_factors.append(0.85)
        else:
            confidence_factors.append(0.5)
        
        return sum(confidence_factors) / len(confidence_factors)
    
    def _generate_flagged_reasons(self, risk_factors: RiskFactors, overall_score: float) -> List[str]:
        """Generate human-readable reasons for flagging."""
        
        reasons = []
        
        if risk_factors.vpn_proxy_score > 0.5:
            reasons.append("VPN/proxy detected")
        
        if risk_factors.behavior_risk_score > 0.7:
            reasons.append("Automated behavior detected")
        
        if risk_factors.fingerprint_risk_score > 0.6:
            reasons.append("Suspicious device fingerprint")
        
        if risk_factors.rate_limit_score > 0.5:
            reasons.append("Rate limit violations")
        
        if risk_factors.timing_score > 0.4:
            reasons.append("Suspicious timing patterns")
        
        if overall_score > 0.8:
            reasons.append("High overall risk score")
        
        return reasons
    
    def _validate_screen_resolution(self, resolution: str) -> bool:
        """Validate screen resolution format and reasonableness."""
        
        try:
            parts = resolution.split('x')
            if len(parts) >= 2:
                width = int(parts[0])
                height = int(parts[1])
                
                # Basic sanity checks
                if width < 100 or height < 100:  # Too small
                    return False
                if width > 10000 or height > 10000:  # Too large
                    return False
                
                return True
        except (ValueError, AttributeError):
            return False
        
        return False
    
    def update_session_risk(self, session_id: str, new_risk_data: Dict) -> None:
        """Update risk assessment with new data."""
        
        # Remove cached assessments for this session
        keys_to_remove = [key for key in self.assessment_cache.keys() if key.startswith(session_id)]
        for key in keys_to_remove:
            del self.assessment_cache[key]
    
    def get_risk_statistics(self) -> Dict:
        """Get risk scoring statistics."""
        
        current_time = time.time()
        recent_assessments = [
            assessment for assessment in self.assessment_cache.values()
            if current_time - assessment.assessment_timestamp < 3600  # Last hour
        ]
        
        if not recent_assessments:
            return {'no_data': True}
        
        risk_levels = {}
        for assessment in recent_assessments:
            level = assessment.risk_level
            risk_levels[level] = risk_levels.get(level, 0) + 1
        
        avg_risk_score = sum(a.overall_risk_score for a in recent_assessments) / len(recent_assessments)
        avg_confidence = sum(a.confidence for a in recent_assessments) / len(recent_assessments)
        
        return {
            'total_assessments': len(recent_assessments),
            'risk_level_distribution': risk_levels,
            'average_risk_score': avg_risk_score,
            'average_confidence': avg_confidence,
            'cache_size': len(self.assessment_cache)
        }
    
    def cleanup_cache(self):
        """Clean up expired cache entries."""
        
        current_time = time.time()
        expired_keys = [
            key for key, assessment in self.assessment_cache.items()
            if current_time - assessment.assessment_timestamp > self.cache_duration
        ]
        
        for key in expired_keys:
            del self.assessment_cache[key]


# Singleton instance
_risk_scoring_service = None


def get_risk_scoring_service(config: Optional[SecurityConfig] = None) -> RiskScoringService:
    """Get singleton risk scoring service instance."""
    global _risk_scoring_service
    if _risk_scoring_service is None:
        _risk_scoring_service = RiskScoringService(config)
    return _risk_scoring_service