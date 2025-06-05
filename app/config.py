"""
Configuration management for security and abuse prevention features.
"""

import os

from app.models import SecurityConfig


def load_security_config() -> SecurityConfig:
    """Load security configuration from environment variables."""

    return SecurityConfig(
        # Feature toggles
        fingerprinting_enabled=_get_bool_env('FINGERPRINTING_ENABLED', True),
        vpn_detection_enabled=_get_bool_env('VPN_DETECTION_ENABLED', True),
        behavior_analysis_enabled=_get_bool_env('BEHAVIOR_ANALYSIS_ENABLED', True),
        captcha_enabled=_get_bool_env('CAPTCHA_ENABLED', True),
        rate_limiting_enabled=_get_bool_env('RATE_LIMITING_ENABLED', True),
        abuse_monitoring_enabled=_get_bool_env('ABUSE_MONITORING_ENABLED', True),

        # Risk thresholds
        high_risk_threshold=_get_float_env('HIGH_RISK_THRESHOLD', 0.7),
        captcha_threshold=_get_float_env('CAPTCHA_THRESHOLD', 0.5),
        block_threshold=_get_float_env('BLOCK_THRESHOLD', 0.9),

        # Rate limits
        trial_creation_per_ip_per_hour=_get_int_env('TRIAL_CREATION_PER_IP_PER_HOUR', 3),
        trial_creation_per_fingerprint_per_hour=_get_int_env('TRIAL_CREATION_PER_FINGERPRINT_PER_HOUR', 1),
        image_generation_per_minute=_get_int_env('IMAGE_GENERATION_PER_MINUTE', 2),

        # VPN detection settings
        vpn_api_timeout_seconds=_get_int_env('VPN_DETECTION_TIMEOUT', 5),
        vpn_cache_duration_seconds=_get_int_env('VPN_CACHE_DURATION', 3600),

        # Fingerprint settings
        fingerprint_uniqueness_threshold=_get_float_env('FINGERPRINT_UNIQUENESS_THRESHOLD', 0.8),
        fingerprint_spoofing_threshold=_get_float_env('FINGERPRINT_SPOOFING_THRESHOLD', 0.6)
    )


def _get_bool_env(key: str, default: bool) -> bool:
    """Get boolean environment variable."""
    value = os.getenv(key)
    if value is None:
        return default
    return value.lower() in ('true', '1', 'yes', 'on')


def _get_int_env(key: str, default: int) -> int:
    """Get integer environment variable."""
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _get_float_env(key: str, default: float) -> float:
    """Get float environment variable."""
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def get_vpn_api_config() -> dict:
    """Get VPN detection API configuration."""
    return {
        'ipqualityscore_key': os.getenv('IPQUALITYSCORE_API_KEY'),
        'proxycheck_key': os.getenv('PROXYCHECK_API_KEY'),
        'timeout': _get_int_env('VPN_DETECTION_TIMEOUT', 5),
        'enabled': _get_bool_env('VPN_DETECTION_PAID_APIS', False)
    }


def get_captcha_config() -> dict:
    """Get CAPTCHA service configuration."""
    return {
        'recaptcha_secret': os.getenv('RECAPTCHA_SECRET_KEY'),
        'recaptcha_site_key': os.getenv('RECAPTCHA_SITE_KEY'),
        'hcaptcha_secret': os.getenv('HCAPTCHA_SECRET_KEY'),
        'hcaptcha_site_key': os.getenv('HCAPTCHA_SITE_KEY'),
        'timeout': _get_int_env('CAPTCHA_API_TIMEOUT', 10)
    }


def get_monitoring_config() -> dict:
    """Get abuse monitoring configuration."""
    return {
        'slack_webhook': os.getenv('ABUSE_ALERT_SLACK_WEBHOOK'),
        'discord_webhook': os.getenv('ABUSE_ALERT_DISCORD_WEBHOOK'),
        'email_webhook': os.getenv('ABUSE_ALERT_EMAIL_WEBHOOK'),
        'enabled': _get_bool_env('ABUSE_MONITORING_ENABLED', True)
    }


def get_redis_config() -> dict | None:
    """Get Redis configuration if available."""
    redis_url = os.getenv('REDIS_URL')
    if not redis_url:
        return None

    return {
        'url': redis_url,
        'password': os.getenv('REDIS_PASSWORD'),
        'decode_responses': True
    }


def get_geoip_config() -> str | None:
    """Get GeoIP database path if configured."""
    path = os.getenv('GEOIP_DATABASE_PATH')
    if path and os.path.exists(path):
        return path
    return None


def is_development() -> bool:
    """Check if running in development mode."""
    return _get_bool_env('DEBUG', False) or os.getenv('ENVIRONMENT', 'production') == 'development'


def get_log_level() -> str:
    """Get logging level."""
    return os.getenv('LOG_LEVEL', 'INFO').upper()


# Global configuration instance
security_config = load_security_config()
