"""
VPN and proxy detection service for trial abuse prevention.
"""

import asyncio
import logging
import os
import time

import geoip2.database
import geoip2.errors
import httpx

from app.models import IPRiskAssessment

logger = logging.getLogger(__name__)


class VPNDetectionService:
    """Service for detecting VPN, proxy, and other suspicious IP addresses."""

    def __init__(self):
        self.timeout = int(os.getenv('VPN_DETECTION_TIMEOUT', '5'))
        self.cache_duration = int(os.getenv('VPN_CACHE_DURATION', '3600'))  # 1 hour
        self.cache: dict[str, tuple] = {}  # ip -> (assessment, timestamp)

        # API configurations
        self.ipqualityscore_key = os.getenv('IPQUALITYSCORE_API_KEY')
        self.proxycheck_key = os.getenv('PROXYCHECK_API_KEY')
        self.enable_paid_apis = os.getenv('VPN_DETECTION_PAID_APIS', 'false').lower() == 'true'

        # Known VPN/proxy ranges (basic detection)
        self.known_vpn_ranges = self._load_known_vpn_ranges()
        self.known_datacenter_asns = self._load_datacenter_asns()

        # GeoIP database path (optional)
        self.geoip_db_path = os.getenv('GEOIP_DATABASE_PATH')
        self.geoip_reader = self._init_geoip_reader()

    async def assess_ip_risk(self, ip_address: str) -> IPRiskAssessment:
        """Comprehensive IP risk assessment using multiple detection methods."""

        # Check cache first
        cached = self._get_cached_assessment(ip_address)
        if cached:
            return cached

        # Perform multiple risk assessments in parallel
        assessments = await asyncio.gather(
            self._check_known_vpn_ranges(ip_address),
            self._check_datacenter_hosting(ip_address),
            self._check_geolocation_analysis(ip_address),
            self._check_external_apis(ip_address) if self.enable_paid_apis else self._create_default_assessment_async(ip_address),
            return_exceptions=True
        )

        # Combine results
        final_assessment = self._combine_assessments(ip_address, assessments)

        # Cache the result
        self._cache_assessment(ip_address, final_assessment)

        return final_assessment

    def _get_cached_assessment(self, ip_address: str) -> IPRiskAssessment | None:
        """Get cached assessment if still valid."""
        if ip_address in self.cache:
            assessment, timestamp = self.cache[ip_address]
            if time.time() - timestamp < self.cache_duration:
                return assessment
            else:
                # Remove expired cache entry
                del self.cache[ip_address]
        return None

    def _cache_assessment(self, ip_address: str, assessment: IPRiskAssessment):
        """Cache assessment result."""
        self.cache[ip_address] = (assessment, time.time())

        # Clean up old cache entries periodically
        if len(self.cache) > 1000:
            self._cleanup_cache()

    def _cleanup_cache(self):
        """Remove expired cache entries."""
        current_time = time.time()
        expired_keys = [
            ip for ip, (_, timestamp) in self.cache.items()
            if current_time - timestamp > self.cache_duration
        ]
        for key in expired_keys:
            del self.cache[key]

    async def _check_known_vpn_ranges(self, ip_address: str) -> IPRiskAssessment:
        """Check against known VPN/proxy IP ranges."""
        try:
            # Simple IP range checking (this would be expanded with real data)
            is_vpn = self._ip_in_known_ranges(ip_address, self.known_vpn_ranges)

            return IPRiskAssessment(
                ip_address=ip_address,
                is_vpn=is_vpn,
                is_proxy=is_vpn,  # For simplicity, treat VPN and proxy the same
                is_tor=False,  # Would need Tor exit node list
                is_datacenter=False,
                risk_score=0.8 if is_vpn else 0.0,
                confidence=0.6 if is_vpn else 0.3
            )
        except Exception as e:
            logger.warning(f"Error checking known VPN ranges for {ip_address}: {e}")
            return self._create_default_assessment(ip_address)

    async def _check_datacenter_hosting(self, ip_address: str) -> IPRiskAssessment:
        """Check if IP is from a datacenter (common for VPNs/proxies)."""
        try:
            if not self.geoip_reader:
                return self._create_default_assessment(ip_address)

            response = self.geoip_reader.asn(ip_address)
            asn_number = response.autonomous_system_number
            asn_org = response.autonomous_system_organization or ""

            # Check if ASN is known datacenter
            is_datacenter = (
                asn_number in self.known_datacenter_asns or
                any(keyword in asn_org.lower() for keyword in [
                    'datacenter', 'hosting', 'cloud', 'server', 'vps',
                    'amazon', 'google', 'microsoft', 'digital ocean'
                ])
            )

            return IPRiskAssessment(
                ip_address=ip_address,
                is_vpn=False,
                is_proxy=False,
                is_tor=False,
                is_datacenter=is_datacenter,
                risk_score=0.4 if is_datacenter else 0.0,
                confidence=0.7 if is_datacenter else 0.5,
                asn=str(asn_number),
                isp=asn_org
            )

        except Exception as e:
            logger.warning(f"Error checking datacenter hosting for {ip_address}: {e}")
            return self._create_default_assessment(ip_address)

    async def _check_geolocation_analysis(self, ip_address: str) -> IPRiskAssessment:
        """Analyze geolocation for suspicious patterns."""
        try:
            if not self.geoip_reader:
                return self._create_default_assessment(ip_address)

            response = self.geoip_reader.city(ip_address)
            country_code = response.country.iso_code

            # Countries with high VPN usage (simplified heuristic)
            high_vpn_countries = {'CN', 'RU', 'IR', 'KP', 'BY'}

            risk_score = 0.3 if country_code in high_vpn_countries else 0.0

            return IPRiskAssessment(
                ip_address=ip_address,
                is_vpn=False,
                is_proxy=False,
                is_tor=False,
                is_datacenter=False,
                risk_score=risk_score,
                confidence=0.4,
                country_code=country_code
            )

        except Exception as e:
            logger.warning(f"Error checking geolocation for {ip_address}: {e}")
            return self._create_default_assessment(ip_address)

    async def _check_external_apis(self, ip_address: str) -> IPRiskAssessment:
        """Check external VPN detection APIs."""
        try:
            # Try multiple APIs in parallel
            api_results = await asyncio.gather(
                self._check_ipqualityscore(ip_address) if self.ipqualityscore_key else None,
                self._check_proxycheck(ip_address) if self.proxycheck_key else None,
                return_exceptions=True
            )

            # Combine API results
            combined_result = self._combine_api_results(ip_address, api_results)
            return combined_result

        except Exception as e:
            logger.warning(f"Error checking external APIs for {ip_address}: {e}")
            return self._create_default_assessment(ip_address)

    async def _check_ipqualityscore(self, ip_address: str) -> IPRiskAssessment | None:
        """Check IPQualityScore API."""
        if not self.ipqualityscore_key:
            return None

        try:
            url = f"https://ipqualityscore.com/api/json/ip/{self.ipqualityscore_key}/{ip_address}"
            params = {
                'strictness': 1,
                'allow_public_access_points': True,
                'fast': True
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

            if data.get('success'):
                return IPRiskAssessment(
                    ip_address=ip_address,
                    is_vpn=data.get('vpn', False),
                    is_proxy=data.get('proxy', False),
                    is_tor=data.get('tor', False),
                    is_datacenter=data.get('recent_abuse', False),
                    risk_score=min(data.get('fraud_score', 0) / 100, 1.0),
                    confidence=0.8,
                    country_code=data.get('country_code'),
                    isp=data.get('ISP')
                )

        except Exception as e:
            logger.warning(f"IPQualityScore API error for {ip_address}: {e}")

        return None

    async def _check_proxycheck(self, ip_address: str) -> IPRiskAssessment | None:
        """Check ProxyCheck.io API."""
        if not self.proxycheck_key:
            return None

        try:
            url = f"https://proxycheck.io/v2/{ip_address}"
            params = {
                'key': self.proxycheck_key,
                'vpn': 1,
                'asn': 1,
                'risk': 1,
                'format': 'json'
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

            ip_data = data.get(ip_address, {})
            if ip_data.get('status') == 'ok':
                return IPRiskAssessment(
                    ip_address=ip_address,
                    is_vpn=ip_data.get('proxy') == 'yes',
                    is_proxy=ip_data.get('proxy') == 'yes',
                    is_tor=ip_data.get('type') == 'TOR',
                    is_datacenter=False,
                    risk_score=min(ip_data.get('risk', 0) / 100, 1.0),
                    confidence=0.8,
                    country_code=ip_data.get('country'),
                    asn=ip_data.get('asn')
                )

        except Exception as e:
            logger.warning(f"ProxyCheck API error for {ip_address}: {e}")

        return None

    def _combine_assessments(self, ip_address: str, assessments: list) -> IPRiskAssessment:
        """Combine multiple assessment results into final verdict."""

        # Filter out exceptions and None results
        valid_assessments = [
            a for a in assessments
            if isinstance(a, IPRiskAssessment)
        ]

        if not valid_assessments:
            return self._create_default_assessment(ip_address)

        # Combine flags (OR logic - if any source says it's VPN, consider it VPN)
        is_vpn = any(a.is_vpn for a in valid_assessments)
        is_proxy = any(a.is_proxy for a in valid_assessments)
        is_tor = any(a.is_tor for a in valid_assessments)
        is_datacenter = any(a.is_datacenter for a in valid_assessments)

        # Combine risk scores (weighted average by confidence)
        total_weighted_score = sum(a.risk_score * a.confidence for a in valid_assessments)
        total_confidence = sum(a.confidence for a in valid_assessments)

        final_risk_score = total_weighted_score / total_confidence if total_confidence > 0 else 0.0
        final_confidence = min(total_confidence / len(valid_assessments), 1.0)

        # Get additional data from most confident source
        best_source = max(valid_assessments, key=lambda a: a.confidence)

        return IPRiskAssessment(
            ip_address=ip_address,
            is_vpn=is_vpn,
            is_proxy=is_proxy,
            is_tor=is_tor,
            is_datacenter=is_datacenter,
            risk_score=final_risk_score,
            confidence=final_confidence,
            country_code=best_source.country_code,
            asn=best_source.asn,
            isp=best_source.isp
        )

    def _combine_api_results(self, ip_address: str, api_results: list) -> IPRiskAssessment:
        """Combine results from external APIs."""
        valid_results = [r for r in api_results if isinstance(r, IPRiskAssessment)]

        if not valid_results:
            return self._create_default_assessment(ip_address)

        # Use similar combination logic as _combine_assessments
        return self._combine_assessments(ip_address, valid_results)

    def _create_default_assessment(self, ip_address: str) -> IPRiskAssessment:
        """Create default assessment when other methods fail."""
        return IPRiskAssessment(
            ip_address=ip_address,
            is_vpn=False,
            is_proxy=False,
            is_tor=False,
            is_datacenter=False,
            risk_score=0.0,
            confidence=0.1
        )

    async def _create_default_assessment_async(self, ip_address: str) -> IPRiskAssessment:
        """Create default assessment when other methods fail (async version)."""
        return self._create_default_assessment(ip_address)

    def _ip_in_known_ranges(self, ip_address: str, ranges: set[str]) -> bool:
        """Check if IP is in known ranges (simplified implementation)."""
        # This is a simplified implementation
        # In production, you'd use a proper IP range library like netaddr
        try:
            import ipaddress
            ip = ipaddress.ip_address(ip_address)

            for range_str in ranges:
                try:
                    network = ipaddress.ip_network(range_str, strict=False)
                    if ip in network:
                        return True
                except ValueError:
                    continue

        except Exception as e:
            logger.warning(f"Error checking IP ranges for {ip_address}: {e}")

        return False

    def _load_known_vpn_ranges(self) -> set[str]:
        """Load known VPN IP ranges from configuration."""
        # In production, this would load from a regularly updated database
        # For now, return a small sample of known ranges
        return {
            '5.2.64.0/22',      # NordVPN
            '103.86.96.0/23',   # ExpressVPN
            '37.120.128.0/19',  # Surfshark
            # Add more ranges as needed
        }

    def _load_datacenter_asns(self) -> set[int]:
        """Load known datacenter ASNs."""
        # Sample of major datacenter/cloud provider ASNs
        return {
            16509,  # Amazon
            15169,  # Google
            8075,   # Microsoft
            14061,  # DigitalOcean
            20473,  # Choopa (Vultr)
            63949,  # Linode
        }

    def _init_geoip_reader(self):
        """Initialize GeoIP database reader if available."""
        if self.geoip_db_path and os.path.exists(self.geoip_db_path):
            try:
                return geoip2.database.Reader(self.geoip_db_path)
            except Exception as e:
                logger.warning(f"Failed to initialize GeoIP reader: {e}")
        return None

    def get_detection_stats(self) -> dict:
        """Get statistics about VPN detection performance."""
        return {
            'cache_size': len(self.cache),
            'cache_hit_rate': self._calculate_cache_hit_rate(),
            'apis_enabled': {
                'ipqualityscore': bool(self.ipqualityscore_key),
                'proxycheck': bool(self.proxycheck_key),
                'geoip': bool(self.geoip_reader)
            }
        }

    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate (simplified)."""
        # This would need more sophisticated tracking in production
        return 0.0


# Singleton instance
_vpn_detection_service = None


def get_vpn_detection_service() -> VPNDetectionService:
    """Get singleton VPN detection service instance."""
    global _vpn_detection_service
    if _vpn_detection_service is None:
        _vpn_detection_service = VPNDetectionService()
    return _vpn_detection_service
