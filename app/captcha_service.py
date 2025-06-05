"""
CAPTCHA and human verification service for trial abuse prevention.
"""

import hashlib
import logging
import os
import random

import httpx

from app.models import VerificationChallenge

logger = logging.getLogger(__name__)


class CAPTCHAService:
    """Service for progressive human verification challenges."""

    def __init__(self):
        # API keys for various CAPTCHA services
        self.recaptcha_secret = os.getenv('RECAPTCHA_SECRET_KEY')
        self.recaptcha_site_key = os.getenv('RECAPTCHA_SITE_KEY')
        self.hcaptcha_secret = os.getenv('HCAPTCHA_SECRET_KEY')
        self.hcaptcha_site_key = os.getenv('HCAPTCHA_SITE_KEY')

        # Timeout settings
        self.api_timeout = int(os.getenv('CAPTCHA_API_TIMEOUT', '10'))

        # Simple math challenges cache
        self.math_challenges: dict[str, int] = {}

        # Challenge thresholds
        self.risk_thresholds = {
            VerificationChallenge.NONE: 0.0,
            VerificationChallenge.SIMPLE_MATH: 0.3,
            VerificationChallenge.RECAPTCHA_V2: 0.6,
            VerificationChallenge.RECAPTCHA_V3: 0.8,
            VerificationChallenge.HCAPTCHA: 0.7,
            VerificationChallenge.EMAIL_VERIFICATION: 0.9
        }

    def determine_challenge_level(self, risk_score: float,
                                 previous_failures: int = 0) -> VerificationChallenge:
        """Determine appropriate challenge level based on risk score."""

        # Increase challenge level based on previous failures
        adjusted_risk = min(risk_score + (previous_failures * 0.1), 1.0)

        if adjusted_risk < self.risk_thresholds[VerificationChallenge.SIMPLE_MATH]:
            return VerificationChallenge.NONE
        elif adjusted_risk < self.risk_thresholds[VerificationChallenge.RECAPTCHA_V2]:
            return VerificationChallenge.SIMPLE_MATH
        elif adjusted_risk < self.risk_thresholds[VerificationChallenge.RECAPTCHA_V3]:
            return VerificationChallenge.RECAPTCHA_V2
        elif adjusted_risk < self.risk_thresholds[VerificationChallenge.EMAIL_VERIFICATION]:
            # Prefer hCaptcha for high-risk users (often more accessible)
            return VerificationChallenge.HCAPTCHA if self.hcaptcha_secret else VerificationChallenge.RECAPTCHA_V3
        else:
            return VerificationChallenge.EMAIL_VERIFICATION

    def generate_simple_math_challenge(self, session_id: str) -> dict[str, str]:
        """Generate a simple math challenge for basic bot detection."""

        # Generate random simple math problem
        num1 = random.randint(1, 20)
        num2 = random.randint(1, 20)
        operation = random.choice(['+', '-'])

        if operation == '+':
            answer = num1 + num2
            question = f"What is {num1} + {num2}?"
        else:
            # Ensure non-negative result for subtraction
            if num1 < num2:
                num1, num2 = num2, num1
            answer = num1 - num2
            question = f"What is {num1} - {num2}?"

        # Store answer with session ID
        challenge_id = self._generate_challenge_id(session_id)
        self.math_challenges[challenge_id] = answer

        return {
            'challenge_id': challenge_id,
            'question': question,
            'type': 'simple_math'
        }

    def validate_simple_math_challenge(self, challenge_id: str,
                                     user_answer: str) -> bool:
        """Validate simple math challenge answer."""

        if challenge_id not in self.math_challenges:
            logger.warning(f"Math challenge not found: {challenge_id}")
            return False

        try:
            correct_answer = self.math_challenges[challenge_id]
            user_answer_int = int(user_answer.strip())

            # Remove challenge after validation attempt
            del self.math_challenges[challenge_id]

            return user_answer_int == correct_answer

        except (ValueError, KeyError) as e:
            logger.warning(f"Error validating math challenge {challenge_id}: {e}")
            return False

    async def validate_recaptcha_v2(self, response_token: str,
                                   user_ip: str = None) -> bool:
        """Validate reCAPTCHA v2 response."""

        if not self.recaptcha_secret:
            logger.warning("reCAPTCHA secret key not configured")
            return False

        try:
            url = "https://www.google.com/recaptcha/api/siteverify"
            data = {
                'secret': self.recaptcha_secret,
                'response': response_token
            }

            if user_ip:
                data['remoteip'] = user_ip

            async with httpx.AsyncClient(timeout=self.api_timeout) as client:
                response = await client.post(url, data=data)
                response.raise_for_status()
                result = response.json()

            success = result.get('success', False)

            if not success:
                error_codes = result.get('error-codes', [])
                logger.warning(f"reCAPTCHA v2 validation failed: {error_codes}")

            return success

        except Exception as e:
            logger.error(f"Error validating reCAPTCHA v2: {e}")
            return False

    async def validate_recaptcha_v3(self, response_token: str,
                                   expected_action: str = "trial_create",
                                   min_score: float = 0.5,
                                   user_ip: str = None) -> tuple[bool, float]:
        """Validate reCAPTCHA v3 response and return score."""

        if not self.recaptcha_secret:
            logger.warning("reCAPTCHA secret key not configured")
            return False, 0.0

        try:
            url = "https://www.google.com/recaptcha/api/siteverify"
            data = {
                'secret': self.recaptcha_secret,
                'response': response_token
            }

            if user_ip:
                data['remoteip'] = user_ip

            async with httpx.AsyncClient(timeout=self.api_timeout) as client:
                response = await client.post(url, data=data)
                response.raise_for_status()
                result = response.json()

            success = result.get('success', False)
            score = result.get('score', 0.0)
            action = result.get('action', '')

            if not success:
                error_codes = result.get('error-codes', [])
                logger.warning(f"reCAPTCHA v3 validation failed: {error_codes}")
                return False, 0.0

            # Verify action matches expected
            if action != expected_action:
                logger.warning(f"reCAPTCHA v3 action mismatch: expected {expected_action}, got {action}")
                return False, score

            # Check if score meets minimum threshold
            passed = score >= min_score

            if not passed:
                logger.info(f"reCAPTCHA v3 score too low: {score} < {min_score}")

            return passed, score

        except Exception as e:
            logger.error(f"Error validating reCAPTCHA v3: {e}")
            return False, 0.0

    async def validate_hcaptcha(self, response_token: str,
                               user_ip: str = None) -> bool:
        """Validate hCaptcha response."""

        if not self.hcaptcha_secret:
            logger.warning("hCaptcha secret key not configured")
            return False

        try:
            url = "https://hcaptcha.com/siteverify"
            data = {
                'secret': self.hcaptcha_secret,
                'response': response_token
            }

            if user_ip:
                data['remoteip'] = user_ip

            async with httpx.AsyncClient(timeout=self.api_timeout) as client:
                response = await client.post(url, data=data)
                response.raise_for_status()
                result = response.json()

            success = result.get('success', False)

            if not success:
                error_codes = result.get('error-codes', [])
                logger.warning(f"hCaptcha validation failed: {error_codes}")

            return success

        except Exception as e:
            logger.error(f"Error validating hCaptcha: {e}")
            return False

    async def validate_challenge(self, challenge_type: VerificationChallenge,
                               response_data: dict) -> tuple[bool, float]:
        """Validate any type of challenge response."""

        if challenge_type == VerificationChallenge.NONE:
            return True, 1.0

        elif challenge_type == VerificationChallenge.SIMPLE_MATH:
            challenge_id = response_data.get('challenge_id')
            user_answer = response_data.get('answer')

            if not challenge_id or user_answer is None:
                return False, 0.0

            success = self.validate_simple_math_challenge(challenge_id, str(user_answer))
            return success, 1.0 if success else 0.0

        elif challenge_type == VerificationChallenge.RECAPTCHA_V2:
            response_token = response_data.get('recaptcha_response')
            user_ip = response_data.get('user_ip')

            if not response_token:
                return False, 0.0

            success = await self.validate_recaptcha_v2(response_token, user_ip)
            return success, 1.0 if success else 0.0

        elif challenge_type == VerificationChallenge.RECAPTCHA_V3:
            response_token = response_data.get('recaptcha_response')
            user_ip = response_data.get('user_ip')
            action = response_data.get('action', 'trial_create')
            min_score = response_data.get('min_score', 0.5)

            if not response_token:
                return False, 0.0

            success, score = await self.validate_recaptcha_v3(
                response_token, action, min_score, user_ip
            )
            return success, score

        elif challenge_type == VerificationChallenge.HCAPTCHA:
            response_token = response_data.get('hcaptcha_response')
            user_ip = response_data.get('user_ip')

            if not response_token:
                return False, 0.0

            success = await self.validate_hcaptcha(response_token, user_ip)
            return success, 1.0 if success else 0.0

        elif challenge_type == VerificationChallenge.EMAIL_VERIFICATION:
            # Email verification would be handled by a separate service
            # For now, just check if email verification was completed
            verified = response_data.get('email_verified', False)
            return verified, 1.0 if verified else 0.0

        else:
            logger.warning(f"Unknown challenge type: {challenge_type}")
            return False, 0.0

    def get_challenge_config(self, challenge_type: VerificationChallenge) -> dict:
        """Get configuration needed for client-side challenge implementation."""

        config = {'type': challenge_type.value}

        if challenge_type == VerificationChallenge.RECAPTCHA_V2:
            config.update({
                'site_key': self.recaptcha_site_key,
                'url': 'https://www.google.com/recaptcha/api.js'
            })

        elif challenge_type == VerificationChallenge.RECAPTCHA_V3:
            config.update({
                'site_key': self.recaptcha_site_key,
                'url': 'https://www.google.com/recaptcha/api.js',
                'action': 'trial_create'
            })

        elif challenge_type == VerificationChallenge.HCAPTCHA:
            config.update({
                'site_key': self.hcaptcha_site_key,
                'url': 'https://js.hcaptcha.com/1/api.js'
            })

        return config

    def _generate_challenge_id(self, session_id: str) -> str:
        """Generate unique challenge ID."""
        import time
        data = f"{session_id}:{time.time()}:{random.randint(1000, 9999)}"
        return hashlib.md5(data.encode()).hexdigest()

    def cleanup_expired_challenges(self, max_age_seconds: int = 300):
        """Clean up expired math challenges (5 minute default)."""
        # This is a simplified cleanup - in production you'd track timestamps
        if len(self.math_challenges) > 1000:
            # Remove oldest half of challenges
            items_to_remove = len(self.math_challenges) // 2
            keys_to_remove = list(self.math_challenges.keys())[:items_to_remove]
            for key in keys_to_remove:
                del self.math_challenges[key]

    def get_service_stats(self) -> dict:
        """Get service statistics."""
        return {
            'active_math_challenges': len(self.math_challenges),
            'configured_services': {
                'recaptcha_v2': bool(self.recaptcha_secret and self.recaptcha_site_key),
                'recaptcha_v3': bool(self.recaptcha_secret and self.recaptcha_site_key),
                'hcaptcha': bool(self.hcaptcha_secret and self.hcaptcha_site_key)
            },
            'risk_thresholds': self.risk_thresholds
        }


# Singleton instance
_captcha_service = None


def get_captcha_service() -> CAPTCHAService:
    """Get singleton CAPTCHA service instance."""
    global _captcha_service
    if _captcha_service is None:
        _captcha_service = CAPTCHAService()
    return _captcha_service
