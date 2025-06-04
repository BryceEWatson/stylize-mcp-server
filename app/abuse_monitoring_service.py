"""
Abuse monitoring and alerting service for real-time threat detection.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
import httpx
import os
from app.models import AbuseEvent, SecurityConfig

logger = logging.getLogger(__name__)


@dataclass
class AlertThreshold:
    """Alert threshold configuration."""
    metric: str
    threshold_value: float
    window_minutes: int
    severity: str
    description: str


@dataclass
class MonitoringMetrics:
    """Current monitoring metrics."""
    timestamp: float
    trial_creation_rate: float
    high_risk_session_rate: float
    vpn_detection_rate: float
    captcha_failure_rate: float
    blocked_request_rate: float
    unique_ips_per_hour: int
    average_risk_score: float


class AbuseMonitoringService:
    """Service for monitoring abuse patterns and sending alerts."""
    
    def __init__(self, config: Optional[SecurityConfig] = None):
        self.config = config or SecurityConfig()
        
        # Alert configuration
        self.alert_webhooks = {
            'slack': os.getenv('ABUSE_ALERT_SLACK_WEBHOOK'),
            'discord': os.getenv('ABUSE_ALERT_DISCORD_WEBHOOK'),
            'email': os.getenv('ABUSE_ALERT_EMAIL_WEBHOOK')
        }
        
        # Alert thresholds
        self.thresholds = {
            'trial_spike': AlertThreshold(
                metric='trial_creation_rate',
                threshold_value=20.0,  # 20+ trials per minute
                window_minutes=5,
                severity='high',
                description='Unusual spike in trial session creation'
            ),
            'high_risk_concentration': AlertThreshold(
                metric='high_risk_session_rate',
                threshold_value=10.0,  # 10+ high-risk sessions per minute
                window_minutes=10,
                severity='high',
                description='High concentration of risky trial sessions'
            ),
            'vpn_surge': AlertThreshold(
                metric='vpn_detection_rate',
                threshold_value=50.0,  # 50%+ VPN usage
                window_minutes=15,
                severity='medium',
                description='Unusual increase in VPN/proxy usage'
            ),
            'captcha_attacks': AlertThreshold(
                metric='captcha_failure_rate',
                threshold_value=80.0,  # 80%+ failure rate
                window_minutes=10,
                severity='high',
                description='Potential automated CAPTCHA solving attempts'
            ),
            'blocking_surge': AlertThreshold(
                metric='blocked_request_rate',
                threshold_value=30.0,  # 30%+ blocked
                window_minutes=5,
                severity='medium',
                description='High rate of blocked requests'
            ),
            'distributed_attack': AlertThreshold(
                metric='unique_ips_per_hour',
                threshold_value=100,   # 100+ unique IPs per hour
                window_minutes=60,
                severity='high',
                description='Potential distributed attack from many IPs'
            )
        }
        
        # Event storage
        self.events: List[AbuseEvent] = []
        self.max_events = 10000  # Keep last 10k events in memory
        
        # Metrics tracking
        self.metrics_history: List[MonitoringMetrics] = []
        self.max_metrics = 1440  # Keep 24 hours of minute-by-minute metrics
        
        # Alert state
        self.active_alerts: Set[str] = set()
        self.alert_cooldowns: Dict[str, float] = {}
        self.cooldown_duration = 3600  # 1 hour cooldown per alert type
        
        # Background monitoring task
        self.monitoring_task = None
        self.monitoring_enabled = self.config.abuse_monitoring_enabled
    
    async def start_monitoring(self):
        """Start background monitoring task."""
        if self.monitoring_enabled and not self.monitoring_task:
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            logger.info("Abuse monitoring service started")
    
    async def stop_monitoring(self):
        """Stop background monitoring task."""
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            self.monitoring_task = None
            logger.info("Abuse monitoring service stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while True:
            try:
                # Collect current metrics
                metrics = await self._collect_metrics()
                self.metrics_history.append(metrics)
                
                # Trim metrics history
                if len(self.metrics_history) > self.max_metrics:
                    self.metrics_history = self.metrics_history[-self.max_metrics:]
                
                # Check thresholds
                await self._check_alert_thresholds(metrics)
                
                # Cleanup old events
                self._cleanup_old_events()
                
                # Wait before next check
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)
    
    async def log_abuse_event(self, event: AbuseEvent):
        """Log an abuse event for monitoring."""
        
        self.events.append(event)
        
        # Trim events if too many
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events:]
        
        # Check for immediate critical alerts
        await self._check_critical_event(event)
        
        logger.info(f"Logged abuse event: {event.event_type} from {event.ip_address}")
    
    async def _collect_metrics(self) -> MonitoringMetrics:
        """Collect current monitoring metrics."""
        
        current_time = time.time()
        one_hour_ago = current_time - 3600
        one_minute_ago = current_time - 60
        
        # Filter recent events
        recent_events_hour = [e for e in self.events if float(e.timestamp) > one_hour_ago]
        recent_events_minute = [e for e in self.events if float(e.timestamp) > one_minute_ago]
        
        # Calculate metrics
        trial_creation_events = [e for e in recent_events_minute if e.event_type == 'trial_created']
        high_risk_events = [e for e in recent_events_minute if e.event_type == 'high_risk_session']
        vpn_events = [e for e in recent_events_minute if e.event_type == 'vpn_detected']
        captcha_failure_events = [e for e in recent_events_minute if e.event_type == 'captcha_failed']
        blocked_events = [e for e in recent_events_minute if e.event_type == 'request_blocked']
        
        # Calculate rates per minute
        trial_creation_rate = len(trial_creation_events)
        high_risk_session_rate = len(high_risk_events)
        vpn_detection_rate = (len(vpn_events) / max(1, len(trial_creation_events))) * 100
        captcha_failure_rate = (len(captcha_failure_events) / max(1, len(recent_events_minute))) * 100
        blocked_request_rate = (len(blocked_events) / max(1, len(recent_events_minute))) * 100
        
        # Unique IPs in last hour
        unique_ips = len(set(e.ip_address for e in recent_events_hour))
        
        # Average risk score (would need to be passed in events)
        risk_scores = [
            float(e.details.get('risk_score', 0)) 
            for e in recent_events_minute 
            if 'risk_score' in e.details
        ]
        average_risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else 0.0
        
        return MonitoringMetrics(
            timestamp=current_time,
            trial_creation_rate=trial_creation_rate,
            high_risk_session_rate=high_risk_session_rate,
            vpn_detection_rate=vpn_detection_rate,
            captcha_failure_rate=captcha_failure_rate,
            blocked_request_rate=blocked_request_rate,
            unique_ips_per_hour=unique_ips,
            average_risk_score=average_risk_score
        )
    
    async def _check_alert_thresholds(self, current_metrics: MonitoringMetrics):
        """Check if any alert thresholds are exceeded."""
        
        for alert_name, threshold in self.thresholds.items():
            # Skip if alert is in cooldown
            if alert_name in self.alert_cooldowns:
                if time.time() < self.alert_cooldowns[alert_name]:
                    continue
                else:
                    del self.alert_cooldowns[alert_name]
            
            # Get metric value
            metric_value = getattr(current_metrics, threshold.metric, 0)
            
            # Check threshold
            if metric_value >= threshold.threshold_value:
                # Check if this is a sustained threshold breach
                if await self._is_sustained_breach(threshold, current_metrics):
                    await self._trigger_alert(alert_name, threshold, metric_value)
    
    async def _is_sustained_breach(self, threshold: AlertThreshold, 
                                 current_metrics: MonitoringMetrics) -> bool:
        """Check if threshold breach is sustained over the required window."""
        
        window_start = current_metrics.timestamp - (threshold.window_minutes * 60)
        
        # Get metrics in the window
        window_metrics = [
            m for m in self.metrics_history 
            if m.timestamp >= window_start
        ]
        
        if len(window_metrics) < threshold.window_minutes // 2:  # Need at least half the window
            return False
        
        # Check if threshold is exceeded for majority of window
        breaches = [
            m for m in window_metrics 
            if getattr(m, threshold.metric, 0) >= threshold.threshold_value
        ]
        
        breach_rate = len(breaches) / len(window_metrics)
        return breach_rate >= 0.6  # 60% of window must be in breach
    
    async def _trigger_alert(self, alert_name: str, threshold: AlertThreshold, 
                           current_value: float):
        """Trigger an alert notification."""
        
        # Add to active alerts
        self.active_alerts.add(alert_name)
        
        # Set cooldown
        self.alert_cooldowns[alert_name] = time.time() + self.cooldown_duration
        
        # Create alert message
        alert_data = {
            'alert_name': alert_name,
            'severity': threshold.severity,
            'description': threshold.description,
            'metric': threshold.metric,
            'current_value': current_value,
            'threshold': threshold.threshold_value,
            'window_minutes': threshold.window_minutes,
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'Stylize MCP Server - Abuse Monitoring'
        }
        
        # Send notifications
        await self._send_alert_notifications(alert_data)
        
        # Log the alert
        logger.warning(f"ABUSE ALERT: {alert_name} - {threshold.description} "
                      f"(current: {current_value}, threshold: {threshold.threshold_value})")
    
    async def _send_alert_notifications(self, alert_data: Dict):
        """Send alert notifications to configured channels."""
        
        tasks = []
        
        # Slack notification
        if self.alert_webhooks['slack']:
            tasks.append(self._send_slack_alert(alert_data))
        
        # Discord notification
        if self.alert_webhooks['discord']:
            tasks.append(self._send_discord_alert(alert_data))
        
        # Email notification (would integrate with email service)
        if self.alert_webhooks['email']:
            tasks.append(self._send_email_alert(alert_data))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _send_slack_alert(self, alert_data: Dict):
        """Send alert to Slack."""
        
        try:
            color = {
                'low': 'good',
                'medium': 'warning', 
                'high': 'danger',
                'critical': 'danger'
            }.get(alert_data['severity'], 'warning')
            
            message = {
                'attachments': [{
                    'color': color,
                    'title': f"🚨 Abuse Alert: {alert_data['alert_name']}",
                    'text': alert_data['description'],
                    'fields': [
                        {
                            'title': 'Metric',
                            'value': alert_data['metric'],
                            'short': True
                        },
                        {
                            'title': 'Current Value', 
                            'value': f"{alert_data['current_value']:.2f}",
                            'short': True
                        },
                        {
                            'title': 'Threshold',
                            'value': f"{alert_data['threshold']:.2f}",
                            'short': True
                        },
                        {
                            'title': 'Window',
                            'value': f"{alert_data['window_minutes']} minutes",
                            'short': True
                        }
                    ],
                    'footer': 'Stylize MCP Server',
                    'ts': time.time()
                }]
            }
            
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    self.alert_webhooks['slack'],
                    json=message
                )
                response.raise_for_status()
                
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
    
    async def _send_discord_alert(self, alert_data: Dict):
        """Send alert to Discord."""
        
        try:
            color = {
                'low': 0x00ff00,
                'medium': 0xffff00,
                'high': 0xff0000,
                'critical': 0x8b0000
            }.get(alert_data['severity'], 0xffff00)
            
            embed = {
                'title': f"🚨 Abuse Alert: {alert_data['alert_name']}",
                'description': alert_data['description'],
                'color': color,
                'fields': [
                    {
                        'name': 'Metric',
                        'value': alert_data['metric'],
                        'inline': True
                    },
                    {
                        'name': 'Current Value',
                        'value': f"{alert_data['current_value']:.2f}",
                        'inline': True
                    },
                    {
                        'name': 'Threshold',
                        'value': f"{alert_data['threshold']:.2f}",
                        'inline': True
                    }
                ],
                'timestamp': alert_data['timestamp'],
                'footer': {
                    'text': 'Stylize MCP Server'
                }
            }
            
            message = {
                'embeds': [embed]
            }
            
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    self.alert_webhooks['discord'],
                    json=message
                )
                response.raise_for_status()
                
        except Exception as e:
            logger.error(f"Failed to send Discord alert: {e}")
    
    async def _send_email_alert(self, alert_data: Dict):
        """Send alert via email (placeholder)."""
        
        # This would integrate with an email service like SendGrid, SES, etc.
        logger.info(f"Email alert would be sent: {alert_data['alert_name']}")
    
    async def _check_critical_event(self, event: AbuseEvent):
        """Check for events that require immediate alerting."""
        
        critical_events = {
            'high_risk_session_created',
            'multiple_trial_creation_detected',
            'captcha_bypass_attempt',
            'rate_limit_exceeded_severely'
        }
        
        if event.event_type in critical_events:
            alert_data = {
                'alert_name': f"critical_{event.event_type}",
                'severity': 'critical',
                'description': f"Critical event detected: {event.event_type}",
                'event_details': event.details,
                'ip_address': event.ip_address,
                'timestamp': event.timestamp,
                'service': 'Stylize MCP Server - Abuse Monitoring'
            }
            
            await self._send_alert_notifications(alert_data)
    
    def _cleanup_old_events(self):
        """Remove events older than 24 hours."""
        
        cutoff_time = time.time() - 86400  # 24 hours
        
        original_count = len(self.events)
        self.events = [e for e in self.events if float(e.timestamp) > cutoff_time]
        
        cleaned_count = original_count - len(self.events)
        if cleaned_count > 0:
            logger.debug(f"Cleaned up {cleaned_count} old abuse events")
    
    def get_monitoring_stats(self) -> Dict:
        """Get current monitoring statistics."""
        
        current_time = time.time()
        recent_metrics = [m for m in self.metrics_history if current_time - m.timestamp < 3600]
        
        if not recent_metrics:
            return {'no_data': True}
        
        latest_metrics = recent_metrics[-1] if recent_metrics else None
        
        return {
            'monitoring_enabled': self.monitoring_enabled,
            'active_alerts': list(self.active_alerts),
            'total_events_logged': len(self.events),
            'events_last_hour': len([e for e in self.events if current_time - float(e.timestamp) < 3600]),
            'metrics_history_size': len(self.metrics_history),
            'configured_webhooks': {k: bool(v) for k, v in self.alert_webhooks.items()},
            'alert_thresholds': {k: v.threshold_value for k, v in self.thresholds.items()},
            'latest_metrics': {
                'timestamp': latest_metrics.timestamp,
                'trial_creation_rate': latest_metrics.trial_creation_rate,
                'high_risk_session_rate': latest_metrics.high_risk_session_rate,
                'vpn_detection_rate': latest_metrics.vpn_detection_rate,
                'blocked_request_rate': latest_metrics.blocked_request_rate,
                'unique_ips_per_hour': latest_metrics.unique_ips_per_hour,
                'average_risk_score': latest_metrics.average_risk_score
            } if latest_metrics else None
        }
    
    def get_recent_events(self, event_type: Optional[str] = None, 
                         limit: int = 100) -> List[AbuseEvent]:
        """Get recent abuse events."""
        
        events = self.events
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        # Sort by timestamp (most recent first)
        events = sorted(events, key=lambda e: float(e.timestamp), reverse=True)
        
        return events[:limit]


# Singleton instance
_abuse_monitoring_service = None


def get_abuse_monitoring_service(config: Optional[SecurityConfig] = None) -> AbuseMonitoringService:
    """Get singleton abuse monitoring service instance."""
    global _abuse_monitoring_service
    if _abuse_monitoring_service is None:
        _abuse_monitoring_service = AbuseMonitoringService(config)
    return _abuse_monitoring_service