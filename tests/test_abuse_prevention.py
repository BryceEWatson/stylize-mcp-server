"""
Tests for abuse prevention systems.
"""

import pytest
import time
from unittest.mock import Mock, AsyncMock, patch
from app.models import SecurityConfig, TrialSession, IPRiskAssessment, VerificationChallenge
from app.fingerprint_service import DeviceFingerprintService, DeviceFingerprint
from app.vpn_detection_service import VPNDetectionService
from app.captcha_service import CAPTCHAService
from app.behavior_analysis_service import BehaviorAnalysisService, RequestEvent
from app.risk_scoring_service import RiskScoringService
from app.rate_limiting_service import AdvancedRateLimitingService, RateLimitType
from app.abuse_monitoring_service import AbuseMonitoringService


class TestDeviceFingerprintService:
    """Test device fingerprinting functionality."""
    
    def setup_method(self):
        self.service = DeviceFingerprintService()
    
    def test_hash_string(self):
        """Test string hashing consistency."""
        input_str = "test_string"
        hash1 = self.service._hash_string(input_str)
        hash2 = self.service._hash_string(input_str)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length
    
    def test_parse_user_agent(self):
        """Test user agent parsing."""
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        result = self.service.parse_user_agent(user_agent)
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_fingerprint_uniqueness_assessment(self):
        """Test fingerprint uniqueness scoring."""
        fingerprint = "test_fingerprint_123"
        recent_fingerprints = ["other_fp_1", "other_fp_2", "test_fingerprint_123"]
        
        uniqueness = self.service.assess_fingerprint_uniqueness(fingerprint, recent_fingerprints)
        
        assert 0.0 <= uniqueness <= 1.0
        assert uniqueness < 1.0  # Should be less than 1 since it appears in recent list
    
    def test_spoofing_detection(self):
        """Test fingerprint spoofing detection."""
        current_fp = DeviceFingerprint(
            device_fingerprint="current_fp",
            ip_address="192.168.1.1",
            canvas_fingerprint="short"  # Suspicious short fingerprint
        )
        
        historical = [
            DeviceFingerprint(device_fingerprint="fp1", ip_address="192.168.1.1"),
            DeviceFingerprint(device_fingerprint="fp2", ip_address="192.168.1.1"),
            DeviceFingerprint(device_fingerprint="fp3", ip_address="192.168.1.1")
        ]
        
        suspicion = self.service.detect_fingerprint_spoofing(current_fp, historical)
        
        assert 0.0 <= suspicion <= 1.0
        assert suspicion > 0.0  # Should detect some suspicion due to short canvas fingerprint


class TestVPNDetectionService:
    """Test VPN detection functionality."""
    
    def setup_method(self):
        self.service = VPNDetectionService()
    
    @pytest.mark.asyncio
    async def test_assess_ip_risk_basic(self):
        """Test basic IP risk assessment."""
        test_ip = "8.8.8.8"  # Google DNS
        
        assessment = await self.service.assess_ip_risk(test_ip)
        
        assert isinstance(assessment, IPRiskAssessment)
        assert assessment.ip_address == test_ip
        assert 0.0 <= assessment.risk_score <= 1.0
        assert 0.0 <= assessment.confidence <= 1.0
    
    def test_ip_in_known_ranges(self):
        """Test IP range checking."""
        test_ip = "192.168.1.1"
        test_ranges = {"192.168.0.0/16", "10.0.0.0/8"}
        
        result = self.service._ip_in_known_ranges(test_ip, test_ranges)
        assert result is True
        
        external_ip = "8.8.8.8"
        result = self.service._ip_in_known_ranges(external_ip, test_ranges)
        assert result is False
    
    def test_cache_functionality(self):
        """Test assessment caching."""
        test_ip = "1.2.3.4"
        
        # Create mock assessment
        assessment = IPRiskAssessment(
            ip_address=test_ip,
            risk_score=0.5,
            confidence=0.8
        )
        
        # Cache the assessment
        self.service._cache_assessment(test_ip, assessment)
        
        # Retrieve from cache
        cached = self.service._get_cached_assessment(test_ip)
        
        assert cached is not None
        assert cached.ip_address == test_ip
        assert cached.risk_score == 0.5


class TestCAPTCHAService:
    """Test CAPTCHA service functionality."""
    
    def setup_method(self):
        self.service = CAPTCHAService()
    
    def test_determine_challenge_level(self):
        """Test challenge level determination."""
        # Low risk
        challenge = self.service.determine_challenge_level(0.1)
        assert challenge == VerificationChallenge.NONE
        
        # Medium risk
        challenge = self.service.determine_challenge_level(0.4)
        assert challenge == VerificationChallenge.SIMPLE_MATH
        
        # High risk
        challenge = self.service.determine_challenge_level(0.8)
        assert challenge in [VerificationChallenge.HCAPTCHA, VerificationChallenge.RECAPTCHA_V3]
    
    def test_generate_simple_math_challenge(self):
        """Test simple math challenge generation."""
        session_id = "test_session"
        challenge = self.service.generate_simple_math_challenge(session_id)
        
        assert 'challenge_id' in challenge
        assert 'question' in challenge
        assert 'type' in challenge
        assert challenge['type'] == 'simple_math'
        
        # Question should contain numbers and operators
        question = challenge['question']
        assert any(char.isdigit() for char in question)
        assert any(op in question for op in ['+', '-'])
    
    def test_validate_simple_math_challenge(self):
        """Test simple math challenge validation."""
        session_id = "test_session"
        challenge = self.service.generate_simple_math_challenge(session_id)
        challenge_id = challenge['challenge_id']
        
        # Extract answer from question for testing
        question = challenge['question']
        # Parse "What is X + Y?" or "What is X - Y?"
        import re
        match = re.search(r'What is (\d+) ([\+\-]) (\d+)\?', question)
        assert match is not None
        
        num1, op, num2 = int(match.group(1)), match.group(2), int(match.group(3))
        correct_answer = num1 + num2 if op == '+' else num1 - num2
        
        # Test correct answer
        result = self.service.validate_simple_math_challenge(challenge_id, str(correct_answer))
        assert result is True
        
        # Test incorrect answer
        challenge2 = self.service.generate_simple_math_challenge(session_id + "2")
        result = self.service.validate_simple_math_challenge(challenge2['challenge_id'], str(correct_answer + 999))
        assert result is False


class TestBehaviorAnalysisService:
    """Test behavioral analysis functionality."""
    
    def setup_method(self):
        self.service = BehaviorAnalysisService()
    
    def test_add_request_event(self):
        """Test adding request events."""
        session_id = "test_session"
        event = RequestEvent(
            timestamp=time.time(),
            endpoint="/test",
            user_agent="test_agent",
            session_id=session_id,
            ip_address="1.2.3.4",
            response_time=100.0,
            status_code=200
        )
        
        self.service.add_request_event(event)
        
        assert session_id in self.service.session_cache
        assert len(self.service.session_cache[session_id]) == 1
    
    def test_timing_regularity_scoring(self):
        """Test timing regularity analysis."""
        # Create pattern with regular intervals (bot-like)
        pattern = Mock()
        pattern.request_intervals = [1.0, 1.0, 1.0, 1.0, 1.0]  # Very regular
        
        score = self.service._score_timing_regularity(pattern)
        assert score > 0.5  # Should detect high regularity as suspicious
        
        # Create pattern with irregular intervals (human-like)
        pattern.request_intervals = [1.0, 3.5, 0.8, 5.2, 2.1]  # Irregular
        score = self.service._score_timing_regularity(pattern)
        assert score < 0.5  # Should be less suspicious
    
    def test_rapid_consumption_scoring(self):
        """Test rapid consumption pattern detection."""
        pattern = Mock()
        pattern.request_intervals = [0.1, 0.1, 0.1, 0.1]  # Very fast
        pattern.total_requests = 5
        pattern.session_duration = 1.0  # 5 requests in 1 second
        
        score = self.service._score_rapid_consumption(pattern)
        assert score > 0.5  # Should detect rapid consumption
    
    def test_session_analysis(self):
        """Test complete session analysis."""
        session_id = "test_session"
        
        # Add multiple events with bot-like pattern
        base_time = time.time()
        for i in range(5):
            event = RequestEvent(
                timestamp=base_time + i * 1.0,  # Regular 1-second intervals
                endpoint="/test",
                user_agent="test_agent",
                session_id=session_id,
                ip_address="1.2.3.4",
                response_time=50.0,
                status_code=200
            )
            self.service.add_request_event(event)
        
        analysis = self.service.analyze_session_behavior(session_id)
        
        assert analysis.session_id == session_id
        assert analysis.analyzed_requests == 5
        assert 0.0 <= analysis.overall_bot_probability <= 1.0


class TestRiskScoringService:
    """Test risk scoring functionality."""
    
    def setup_method(self):
        self.config = SecurityConfig()
        self.service = RiskScoringService(self.config)
    
    def test_calculate_ip_risk_score(self):
        """Test IP risk score calculation."""
        # High-risk IP assessment
        high_risk_assessment = IPRiskAssessment(
            ip_address="1.2.3.4",
            is_vpn=True,
            is_proxy=True,
            risk_score=0.9,
            confidence=0.8
        )
        
        score = self.service._calculate_ip_risk_score(high_risk_assessment)
        assert score > 0.5  # Should be high risk
        
        # Low-risk IP assessment
        low_risk_assessment = IPRiskAssessment(
            ip_address="8.8.8.8",
            is_vpn=False,
            is_proxy=False,
            risk_score=0.1,
            confidence=0.9
        )
        
        score = self.service._calculate_ip_risk_score(low_risk_assessment)
        assert score < 0.3  # Should be low risk
    
    def test_determine_risk_level(self):
        """Test risk level determination."""
        assert self.service._determine_risk_level(0.1) == 'low'
        assert self.service._determine_risk_level(0.5) == 'medium'
        assert self.service._determine_risk_level(0.7) == 'high'
        assert self.service._determine_risk_level(0.9) == 'critical'
    
    def test_determine_recommended_action(self):
        """Test recommended action determination."""
        # Mock risk factors
        risk_factors = Mock()
        
        action = self.service._determine_recommended_action(0.1, risk_factors)
        assert action == 'allow'
        
        action = self.service._determine_recommended_action(0.4, risk_factors)
        assert action == 'challenge'
        
        action = self.service._determine_recommended_action(0.9, risk_factors)
        assert action in ['block_temporary', 'block_permanent']


class TestRateLimitingService:
    """Test rate limiting functionality."""
    
    def setup_method(self):
        self.config = SecurityConfig()
        self.service = AdvancedRateLimitingService(self.config)
    
    @pytest.mark.asyncio
    async def test_rate_limit_check(self):
        """Test basic rate limit checking."""
        identifier = "test_user"
        limit_type = RateLimitType.API_REQUESTS
        
        # First request should be allowed
        result = await self.service.check_rate_limits(limit_type, identifier, 1.0)
        assert result.allowed is True
        
        # Simulate multiple rapid requests
        for _ in range(60):  # Exceed the default limit
            await self.service.check_rate_limits(limit_type, identifier, 1.0)
        
        # Next request should be blocked
        result = await self.service.check_rate_limits(limit_type, identifier, 1.0)
        assert result.allowed is False
        assert result.retry_after is not None
    
    @pytest.mark.asyncio
    async def test_risk_based_adjustment(self):
        """Test risk-based rate limit adjustment."""
        identifier = "risky_user"
        limit_type = RateLimitType.TRIAL_CREATION_IP
        
        # Low risk - normal limits
        result = await self.service.check_rate_limits(limit_type, identifier, 1.0)
        original_limit = result.limit
        
        # High risk - reduced limits
        result = await self.service.check_rate_limits(limit_type, identifier + "_high", 3.0)
        adjusted_limit = result.limit
        
        assert adjusted_limit < original_limit
    
    @pytest.mark.asyncio
    async def test_multiple_limit_checks(self):
        """Test checking multiple rate limits concurrently."""
        checks = [
            (RateLimitType.API_REQUESTS, "user1", 1.0),
            (RateLimitType.IMAGE_GENERATION, "user2", 1.0),
            (RateLimitType.TRIAL_CREATION_IP, "user3", 1.0)
        ]
        
        results = await self.service.check_multiple_limits(checks)
        
        assert len(results) == 3
        for result in results:
            assert hasattr(result, 'allowed')
            assert hasattr(result, 'current_usage')
            assert hasattr(result, 'limit')


class TestAbuseMonitoringService:
    """Test abuse monitoring functionality."""
    
    def setup_method(self):
        self.config = SecurityConfig()
        self.service = AbuseMonitoringService(self.config)
    
    @pytest.mark.asyncio
    async def test_log_abuse_event(self):
        """Test logging abuse events."""
        from app.models import AbuseEvent
        
        event = AbuseEvent(
            event_id="test_event",
            event_type="test_abuse",
            ip_address="1.2.3.4",
            user_agent="test_agent",
            timestamp="2024-01-01T00:00:00Z",
            details={"test": "data"}
        )
        
        await self.service.log_abuse_event(event)
        
        assert len(self.service.events) == 1
        assert self.service.events[0].event_id == "test_event"
    
    @pytest.mark.asyncio
    async def test_metrics_collection(self):
        """Test metrics collection."""
        # Add some test events
        from app.models import AbuseEvent
        
        events = [
            AbuseEvent(
                event_id=f"event_{i}",
                event_type="trial_created",
                ip_address="1.2.3.4",
                user_agent="test",
                timestamp=str(time.time()),
                details={}
            )
            for i in range(5)
        ]
        
        for event in events:
            await self.service.log_abuse_event(event)
        
        metrics = await self.service._collect_metrics()
        
        assert metrics.trial_creation_rate >= 0
        assert metrics.timestamp > 0
    
    def test_get_monitoring_stats(self):
        """Test monitoring statistics."""
        stats = self.service.get_monitoring_stats()
        
        assert 'monitoring_enabled' in stats
        assert 'total_events_logged' in stats
        assert isinstance(stats['configured_webhooks'], dict)


@pytest.fixture
def mock_request():
    """Create a mock request for testing."""
    request = Mock()
    request.headers = {
        'user-agent': 'Mozilla/5.0 (Test Browser)',
        'x-forwarded-for': '192.168.1.1',
        'accept-language': 'en-US,en;q=0.9'
    }
    request.client = Mock()
    request.client.host = '192.168.1.1'
    return request


class TestIntegration:
    """Integration tests for abuse prevention systems."""
    
    @pytest.mark.asyncio
    async def test_full_trial_creation_flow(self, mock_request):
        """Test complete trial creation with protection."""
        # This would test the full integration but requires more setup
        # For now, test individual components work together
        
        # Test fingerprint extraction
        fingerprint_service = DeviceFingerprintService()
        
        user_agent = mock_request.headers.get('user-agent')
        fingerprint = fingerprint_service.generate_server_fingerprint(mock_request, user_agent)
        
        assert fingerprint.device_fingerprint is not None
        assert fingerprint.ip_address == '192.168.1.1'
        
        # Test VPN detection
        vpn_service = VPNDetectionService()
        ip_assessment = await vpn_service.assess_ip_risk('192.168.1.1')
        
        assert isinstance(ip_assessment, IPRiskAssessment)
        
        # Test risk scoring
        config = SecurityConfig()
        risk_service = RiskScoringService(config)
        
        # Create a mock trial session
        trial_session = TrialSession(
            session_id="test_session",
            ip_address="192.168.1.1",
            user_agent=user_agent,
            device_fingerprint=fingerprint.device_fingerprint,
            creation_timestamp=time.time(),
            images_used=0,
            max_images=5,
            created_at="2024-01-01T00:00:00Z"
        )
        
        risk_assessment = await risk_service.assess_trial_session_risk(trial_session, fingerprint)
        
        assert risk_assessment.session_id == "test_session"
        assert 0.0 <= risk_assessment.overall_risk_score <= 1.0
        assert risk_assessment.risk_level in ['low', 'medium', 'high', 'critical']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])