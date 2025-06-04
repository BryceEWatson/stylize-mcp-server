#!/usr/bin/env python3
"""
Verification script to ensure the application is working correctly after abuse prevention implementation.
"""

import sys
import os
import asyncio
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all modules can be imported."""
    logger.info("Testing imports...")
    
    try:
        # Core application modules
        from app.main import app
        from app.trial_service import TrialService
        from app.user_service import UserService
        from app.styles_service import StyleService
        
        # Protection modules (should work even if not fully configured)
        from app.fingerprint_service import DeviceFingerprintService
        from app.vpn_detection_service import VPNDetectionService
        from app.captcha_service import CAPTCHAService
        from app.risk_scoring_service import RiskScoringService
        from app.rate_limiting_service import AdvancedRateLimitingService
        from app.abuse_monitoring_service import AbuseMonitoringService
        from app.protection_middleware import AbuseProtectionMiddleware
        from app.config import security_config
        
        logger.info("✅ All imports successful")
        return True
    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
        return False

def test_fastapi_app():
    """Test FastAPI app creation."""
    logger.info("Testing FastAPI app...")
    
    try:
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        
        # Test health endpoint
        response = client.get("/health")
        assert response.status_code == 200
        
        # Test trial status (should work without auth)
        response = client.get("/trial/status")
        assert response.status_code == 200
        
        logger.info("✅ FastAPI app working correctly")
        return True
    except Exception as e:
        logger.error(f"❌ FastAPI app test failed: {e}")
        return False

async def test_trial_service():
    """Test trial service functionality."""
    logger.info("Testing trial service...")
    
    try:
        from app.trial_service import TrialService
        
        service = TrialService()
        
        # Test session creation
        session = await service.get_or_create_trial_session("192.168.1.1", "test-agent")
        assert session.session_id.startswith("trial-")
        assert session.ip_address == "192.168.1.1"
        assert session.images_used == 0
        assert session.max_images == 5
        
        # Test usage check
        can_use, usage_response = await service.check_trial_usage(session.session_id)
        assert can_use is True
        assert usage_response.images_remaining == 5
        
        logger.info("✅ Trial service working correctly")
        return True
    except Exception as e:
        logger.error(f"❌ Trial service test failed: {e}")
        return False

def test_protection_services():
    """Test protection services initialization."""
    logger.info("Testing protection services...")
    
    try:
        from app.fingerprint_service import DeviceFingerprintService
        from app.vpn_detection_service import VPNDetectionService
        from app.captcha_service import CAPTCHAService
        from app.models import SecurityConfig
        
        # Test fingerprint service
        fp_service = DeviceFingerprintService()
        hash_result = fp_service._hash_string("test")
        assert len(hash_result) == 64  # SHA-256 length
        
        # Test VPN service
        vpn_service = VPNDetectionService()
        default_assessment = vpn_service._create_default_assessment("192.168.1.1")
        assert default_assessment.ip_address == "192.168.1.1"
        
        # Test CAPTCHA service  
        captcha_service = CAPTCHAService()
        challenge_level = captcha_service.determine_challenge_level(0.1)
        assert challenge_level.value in ["none", "simple_math", "recaptcha_v2", "recaptcha_v3", "hcaptcha"]
        
        logger.info("✅ Protection services working correctly")
        return True
    except Exception as e:
        logger.error(f"❌ Protection services test failed: {e}")
        return False

def test_models():
    """Test data models."""
    logger.info("Testing data models...")
    
    try:
        from app.models import TrialSession, SecurityConfig, IPRiskAssessment
        import time
        
        # Test TrialSession model
        session = TrialSession(
            session_id="test-123",
            ip_address="192.168.1.1",
            user_agent="test-agent",
            images_used=0,
            max_images=5,
            created_at="2024-01-01T00:00:00Z",
            creation_timestamp=time.time()
        )
        assert session.session_id == "test-123"
        
        # Test SecurityConfig
        config = SecurityConfig()
        assert hasattr(config, 'fingerprinting_enabled')
        assert hasattr(config, 'high_risk_threshold')
        
        # Test IPRiskAssessment
        assessment = IPRiskAssessment(
            ip_address="192.168.1.1",
            risk_score=0.5,
            confidence=0.8
        )
        assert assessment.ip_address == "192.168.1.1"
        
        logger.info("✅ Data models working correctly")
        return True
    except Exception as e:
        logger.error(f"❌ Data models test failed: {e}")
        return False

async def main():
    """Run all verification tests."""
    logger.info("🔍 Starting application functionality verification...")
    
    tests = [
        ("Imports", test_imports),
        ("FastAPI App", test_fastapi_app),
        ("Trial Service", test_trial_service),
        ("Protection Services", test_protection_services),
        ("Data Models", test_models),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n--- Testing {test_name} ---")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info("VERIFICATION SUMMARY")
    logger.info("="*50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    total = len(results)
    logger.info(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED - Application is working correctly!")
        return True
    else:
        logger.error(f"⚠️  {total - passed} test(s) failed - Some issues detected")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)