"""
Device fingerprinting service for trial abuse prevention.
"""

import hashlib
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from fastapi import Request
import user_agents


@dataclass
class DeviceFingerprint:
    """Device fingerprint data"""
    device_fingerprint: str
    client_fingerprint: Optional[str] = None
    user_agent_hash: str = ""
    ip_address: str = ""
    timezone_offset: Optional[int] = None
    accept_language: str = ""
    accept_encoding: str = ""
    screen_resolution: Optional[str] = None
    canvas_fingerprint: Optional[str] = None
    webgl_fingerprint: Optional[str] = None


@dataclass
class FingerprintComponents:
    """Individual components used for fingerprinting"""
    ip_address: str
    user_agent_normalized: str
    accept_headers: str
    timezone_signal: str
    screen_info: str
    client_signals: str


class DeviceFingerprintService:
    """Service for generating robust device fingerprints"""
    
    def __init__(self):
        self.salt = "stylize_mcp_fingerprint_v1"
    
    def generate_server_fingerprint(self, request: Request, user_agent: str) -> DeviceFingerprint:
        """Generate server-side device fingerprint from request headers"""
        
        # Extract components
        ip_address = self.get_client_ip(request)
        ua_info = self.parse_user_agent(user_agent)
        accept_headers = self.extract_accept_headers(request)
        timezone_offset = self.extract_timezone_offset(request)
        
        # Create fingerprint components
        components = FingerprintComponents(
            ip_address=ip_address,
            user_agent_normalized=ua_info,
            accept_headers=accept_headers,
            timezone_signal=str(timezone_offset) if timezone_offset else "unknown",
            screen_info="",  # Will be populated by client
            client_signals=""  # Will be populated by client
        )
        
        # Generate server-side fingerprint
        device_fingerprint = self._generate_fingerprint_hash(components)
        
        return DeviceFingerprint(
            device_fingerprint=device_fingerprint,
            user_agent_hash=self._hash_string(user_agent),
            ip_address=ip_address,
            timezone_offset=timezone_offset,
            accept_language=request.headers.get("accept-language", ""),
            accept_encoding=request.headers.get("accept-encoding", "")
        )
    
    def combine_with_client_fingerprint(self, server_fingerprint: DeviceFingerprint, 
                                      client_data: Dict) -> DeviceFingerprint:
        """Combine server fingerprint with client-side data"""
        
        # Extract client signals
        screen_resolution = client_data.get("screen_resolution", "")
        canvas_fingerprint = client_data.get("canvas_fingerprint", "")
        webgl_fingerprint = client_data.get("webgl_fingerprint", "")
        fonts_hash = client_data.get("fonts_hash", "")
        plugins_hash = client_data.get("plugins_hash", "")
        
        # Create enhanced components
        enhanced_components = FingerprintComponents(
            ip_address=server_fingerprint.ip_address,
            user_agent_normalized=server_fingerprint.user_agent_hash,
            accept_headers=f"{server_fingerprint.accept_language}|{server_fingerprint.accept_encoding}",
            timezone_signal=str(server_fingerprint.timezone_offset or "unknown"),
            screen_info=screen_resolution,
            client_signals=f"{canvas_fingerprint}|{webgl_fingerprint}|{fonts_hash}|{plugins_hash}"
        )
        
        # Generate combined fingerprint
        combined_fingerprint = self._generate_fingerprint_hash(enhanced_components)
        
        # Update fingerprint object
        server_fingerprint.device_fingerprint = combined_fingerprint
        server_fingerprint.client_fingerprint = self._hash_string(
            f"{canvas_fingerprint}|{webgl_fingerprint}|{screen_resolution}"
        )
        server_fingerprint.screen_resolution = screen_resolution
        server_fingerprint.canvas_fingerprint = canvas_fingerprint[:32]  # Store first 32 chars
        server_fingerprint.webgl_fingerprint = webgl_fingerprint[:32]    # Store first 32 chars
        
        return server_fingerprint
    
    def get_client_ip(self, request: Request) -> str:
        """Extract real client IP address considering proxies"""
        # Check forwarded headers (common in Cloud Run)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP (original client)
            return forwarded_for.split(",")[0].strip()
        
        # Check other proxy headers
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
        
        # Fallback to direct connection
        return getattr(request.client, "host", "unknown")
    
    def parse_user_agent(self, user_agent: str) -> str:
        """Parse and normalize user agent for fingerprinting"""
        if not user_agent:
            return "unknown"
        
        try:
            ua = user_agents.parse(user_agent)
            
            # Create normalized representation
            normalized = f"{ua.browser.family}|{ua.browser.version_string}|{ua.os.family}|{ua.os.version_string}|{ua.device.family}"
            
            # Remove version micro details for stability
            normalized = re.sub(r'\.\d{3,}', '', normalized)  # Remove long version numbers
            normalized = re.sub(r'\s+', ' ', normalized)      # Normalize whitespace
            
            return self._hash_string(normalized)
            
        except Exception:
            # Fallback to simple hash if parsing fails
            return self._hash_string(user_agent[:200])  # Limit length
    
    def extract_accept_headers(self, request: Request) -> str:
        """Extract and normalize accept headers"""
        headers = []
        
        # Key headers for fingerprinting
        accept_headers = [
            "accept",
            "accept-language", 
            "accept-encoding",
            "accept-charset"
        ]
        
        for header in accept_headers:
            value = request.headers.get(header, "")
            if value:
                # Normalize by removing quality values and sorting
                value = re.sub(r';q=[\d.]+', '', value)  # Remove quality values
                value = ','.join(sorted(v.strip() for v in value.split(',') if v.strip()))
                headers.append(f"{header}:{value}")
        
        return "|".join(headers)
    
    def extract_timezone_offset(self, request: Request) -> Optional[int]:
        """Extract timezone information from headers"""
        # Try to get timezone from custom header (if client sends it)
        tz_header = request.headers.get("x-timezone-offset")
        if tz_header:
            try:
                return int(tz_header)
            except ValueError:
                pass
        
        # Could potentially use Accept-Language for rough timezone estimation
        # For now, return None and rely on client-side data
        return None
    
    def _generate_fingerprint_hash(self, components: FingerprintComponents) -> str:
        """Generate hash from fingerprint components"""
        
        # Combine all components
        fingerprint_string = "|".join([
            components.ip_address,
            components.user_agent_normalized,
            components.accept_headers,
            components.timezone_signal,
            components.screen_info,
            components.client_signals,
            self.salt
        ])
        
        return self._hash_string(fingerprint_string)
    
    def _hash_string(self, input_string: str) -> str:
        """Generate SHA-256 hash of input string"""
        return hashlib.sha256(input_string.encode('utf-8')).hexdigest()
    
    def assess_fingerprint_uniqueness(self, fingerprint: str, 
                                    recent_fingerprints: List[str]) -> float:
        """Assess how unique a fingerprint is (0.0 = very common, 1.0 = unique)"""
        if not recent_fingerprints:
            return 1.0
        
        # Count exact matches
        exact_matches = recent_fingerprints.count(fingerprint)
        total_count = len(recent_fingerprints)
        
        # Calculate uniqueness score
        frequency = exact_matches / total_count
        uniqueness = 1.0 - frequency
        
        return max(0.0, min(1.0, uniqueness))
    
    def detect_fingerprint_spoofing(self, current: DeviceFingerprint, 
                                  historical: List[DeviceFingerprint]) -> float:
        """Detect potential fingerprint spoofing (0.0 = normal, 1.0 = likely spoofed)"""
        if not historical:
            return 0.0
        
        suspicion_factors = []
        
        # Check for rapid fingerprint changes from same IP
        same_ip_fingerprints = [h for h in historical if h.ip_address == current.ip_address]
        if len(same_ip_fingerprints) > 0:
            unique_fingerprints = len(set(h.device_fingerprint for h in same_ip_fingerprints))
            if unique_fingerprints > 3:  # More than 3 different fingerprints from same IP
                suspicion_factors.append(0.7)
        
        # Check for identical fingerprints from different IPs (fingerprint sharing)
        same_fingerprint_ips = [h for h in historical if h.device_fingerprint == current.device_fingerprint]
        unique_ips = len(set(h.ip_address for h in same_fingerprint_ips))
        if unique_ips > 2:  # Same fingerprint from more than 2 IPs
            suspicion_factors.append(0.8)
        
        # Check for unrealistic client fingerprint combinations
        if current.client_fingerprint and current.canvas_fingerprint:
            # Very short or identical canvas fingerprints are suspicious
            if len(current.canvas_fingerprint) < 10:
                suspicion_factors.append(0.5)
        
        # Return average suspicion score
        return sum(suspicion_factors) / len(suspicion_factors) if suspicion_factors else 0.0


# Utility functions for request processing
def extract_fingerprint_from_request(request: Request, 
                                   client_data: Optional[Dict] = None) -> DeviceFingerprint:
    """Main function to extract fingerprint from request"""
    service = DeviceFingerprintService()
    
    # Get user agent
    user_agent = request.headers.get("user-agent", "")
    
    # Generate server-side fingerprint
    fingerprint = service.generate_server_fingerprint(request, user_agent)
    
    # Combine with client data if available
    if client_data:
        fingerprint = service.combine_with_client_fingerprint(fingerprint, client_data)
    
    return fingerprint


def validate_client_fingerprint_data(data: Dict) -> bool:
    """Validate client fingerprint data structure"""
    required_fields = ["screen_resolution", "canvas_fingerprint", "webgl_fingerprint"]
    
    if not isinstance(data, dict):
        return False
    
    for field in required_fields:
        if field not in data or not isinstance(data[field], str):
            return False
    
    # Basic validation of data formats
    screen_res = data.get("screen_resolution", "")
    if screen_res and not re.match(r'^\d+x\d+$', screen_res):
        return False
    
    return True