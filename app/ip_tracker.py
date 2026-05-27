# -*- coding: utf-8 -*-
# =============================================================================
# ip_tracker.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

"""
IP violation tracker for automatic bot blocking.
Tracks per-IP statistics and auto-blocks/offends based on configurable thresholds.
"""

import asyncio
import ipaddress
import json
import logging
import time
import socket
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Dict, List, Optional

from app.config import settings
from app.ip_blocklist import blocklist

logger = logging.getLogger("nsis")


@dataclass
class IPStats:
    """Statistics for a single IP address."""
    rate_violations: int = 0
    error_count: int = 0
    request_count: int = 0
    violation_score: float = 0.0
    first_seen: float = field(default_factory=time.time)
    last_offense: float = 0.0
    is_auto_blocked: bool = False
    blocked_at: float = 0.0
    block_count: int = 0


class IPTracker:
    """
    Tracks IP address behavior and auto-blocks/offends based on thresholds.
    Uses sliding window approach with TTL-based expiration.
    """

    def __init__(self):
        self._stats: Dict[str, IPStats] = defaultdict(IPStats)
        self._lock = Lock()

        # Load config
        self.enabled = getattr(settings, 'auto_block_enabled', True)
        self.threshold = getattr(settings, 'auto_block_threshold', 10)
        self.window_seconds = getattr(settings, 'auto_block_window_minutes', 60) * 60

        # Tiered blocking: base duration is 1 minute, doubles each time (1, 2, 4, 8...)
        self.base_block_duration_seconds = 60  # 1 minute base

        # Weights for violation scoring
        self.rate_violation_weight = getattr(settings, 'auto_block_rate_violations_weight', 5)
        self.error_weight = getattr(settings, 'auto_block_errors_weight', 2)
        self.volume_weight = getattr(settings, 'auto_block_request_volume_weight', 500)

        # Persistence
        self._persistence_path = Path(settings.log_dir) / "auto_blocked_ips.json"

        # Parse safe IP ranges (CIDR notation)
        self._safe_ip_ranges: List[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
        safe_ip_ranges_str = getattr(settings, 'safe_ip_ranges', '')
        if safe_ip_ranges_str:
            for cidr in safe_ip_ranges_str.split(','):
                cidr = cidr.strip()
                if cidr:
                    try:
                        self._safe_ip_ranges.append(ipaddress.ip_network(cidr, strict=False))
                    except ValueError as e:
                        logger.warning(f"Invalid CIDR in safe_ip_ranges: {cidr} - {e}")
            if self._safe_ip_ranges:
                logger.info(f"Loaded {len(self._safe_ip_ranges)} safe IP ranges: {[str(r) for r in self._safe_ip_ranges]}")
            else:
                logger.info("No safe IP ranges configured - all IPs can be auto-blocked")

        # Check if running on a safe host - disable auto blocking
        hostname = socket.gethostname()
        safe_hosts = getattr(settings, 'safe_hosts', '')
        safe_host_list = [h.strip() for h in safe_hosts.split(',') if h.strip()]
        if hostname in safe_host_list:
            self.enabled = False
            logger.info(f"Auto blocking disabled for safe host: {hostname}")

        logger.info(
            f"IP Tracker initialized: enabled={self.enabled}, threshold={self.threshold}, "
            f"window={self.window_seconds}s, tiered blocking base={self.base_block_duration_seconds}s"
        )

    def _is_ip_safe(self, ip: str) -> bool:
        """Check if an IP address is in a safe (whitelisted) range."""
        if not self._safe_ip_ranges:
            return False
        try:
            ip_obj = ipaddress.ip_address(ip)
            return any(ip_obj in network for network in self._safe_ip_ranges)
        except ValueError:
            return False

    def _calculate_block_duration(self, block_count: int) -> float:
        """
        Calculate block duration based on block count using exponential backoff.
        First block: 1 minute, second: 2 minutes, third: 4 minutes, etc.

        Args:
            block_count: Number of times the IP has been blocked

        Returns:
            Block duration in seconds
        """
        # Duration doubles each time: 2^(block_count-1) * base_duration
        # block_count=1 -> 1 minute, block_count=2 -> 2 minutes, etc.
        return self.base_block_duration_seconds * (2 ** (block_count - 1))

    def _ensure_dir(self):
        """Ensure the persistence directory exists."""
        self._persistence_path.parent.mkdir(parents=True, exist_ok=True)

    def _load_persistence(self) -> Dict[str, dict]:
        """Load auto-blocked IPs from disk."""
        if not self._persistence_path.exists():
            return {}
        try:
            with open(self._persistence_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load auto-blocked IPs: {e}")
            return {}

    def _save_persistence(self, data: Dict[str, dict]):
        """Save auto-blocked IPs to disk."""
        self._ensure_dir()
        try:
            with open(self._persistence_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save auto-blocked IPs: {e}")

    def _restore_auto_blocked(self):
        """Restore auto-blocked IPs from persistence on startup."""
        # Create empty placeholder file if it doesn't exist
        if not self._persistence_path.exists():
            self._save_persistence({})

        data = self._load_persistence()
        current_time = time.time()
        restored_count = 0

        for ip, info in data.items():
            block_count = info.get('block_count', 1)
            block_duration = self._calculate_block_duration(block_count)
            blocked_at = info.get('blocked_at', 0)

            # Check if block duration has passed - if so, don't restore
            if current_time - blocked_at < block_duration:
                stats = IPStats(
                    rate_violations=info.get('rate_violations', 0),
                    error_count=info.get('error_count', 0),
                    request_count=info.get('request_count', 0),
                    violation_score=info.get('violation_score', self.threshold),
                    is_auto_blocked=True,
                    blocked_at=blocked_at,
                    block_count=block_count,
                )
                self._stats[ip] = stats
                blocklist.add_ip(ip)
                blocklist.set_block_duration(ip, block_duration)
                restored_count += 1
            else:
                # Block duration has passed, remove from persistence
                logger.info(f"Auto-unblocking {ip} (block duration expired during shutdown)")

        if restored_count > 0:
            logger.info(f"Restored {restored_count} auto-blocked IPs from persistence")

    def record_request(self, ip: str) -> None:
        """Record a request from an IP."""
        if not self.enabled:
            return

        with self._lock:
            self._stats[ip].request_count += 1
            if self._stats[ip].first_seen == 0:
                self._stats[ip].first_seen = time.time()

    def record_rate_violation(self, ip: str) -> None:
        """Record a rate limit violation for an IP."""
        if not self.enabled:
            return

        with self._lock:
            stats = self._stats[ip]
            stats.rate_violations += 1
            stats.violation_score += self.rate_violation_weight
            stats.last_offense = time.time()

            if not stats.is_auto_blocked and stats.violation_score >= self.threshold:
                self._auto_block_ip(ip, stats)

    def record_error(self, ip: str) -> None:
        """Record an error response for an IP."""
        if not self.enabled:
            return

        with self._lock:
            stats = self._stats[ip]
            stats.error_count += 1
            stats.violation_score += self.error_weight
            stats.last_offense = time.time()

            if not stats.is_auto_blocked and stats.violation_score >= self.threshold:
                self._auto_block_ip(ip, stats)

    def record_high_volume(self, ip: str) -> None:
        """Record high request volume for an IP."""
        if not self.enabled:
            return

        with self._lock:
            stats = self._stats[ip]
            stats.violation_score += self.volume_weight
            stats.last_offense = time.time()

            if not stats.is_auto_blocked and stats.violation_score >= self.threshold:
                self._auto_block_ip(ip, stats)

    def _auto_block_ip(self, ip: str, stats: IPStats) -> None:
        """Auto-block an IP address with tiered duration based on block count."""
        # Skip blocking for safe/whitelisted IPs
        if self._is_ip_safe(ip):
            logger.debug(f"Skipping auto-block for safe IP range: {ip}")
            return

        # Increment block count (starts at 1 for first block)
        stats.block_count += 1
        block_duration = self._calculate_block_duration(stats.block_count)

        stats.is_auto_blocked = True
        stats.blocked_at = time.time()
        blocklist.add_ip(ip)
        blocklist.set_block_duration(ip, block_duration)

        duration_minutes = block_duration / 60
        logger.warning(
            f"Auto-blocking IP {ip}: score={stats.violation_score:.1f}, "
            f"block_count={stats.block_count}, duration={duration_minutes:.0f}min, "
            f"rate_violations={stats.rate_violations}, errors={stats.error_count}"
        )

        # Save to persistence
        self._save_auto_blocked_ip(ip, stats)

    def _save_auto_blocked_ip(self, ip: str, stats: IPStats):
        """Save auto-blocked IP to persistence."""
        data = self._load_persistence()
        data[ip] = {
            'rate_violations': stats.rate_violations,
            'error_count': stats.error_count,
            'request_count': stats.request_count,
            'violation_score': stats.violation_score,
            'blocked_at': stats.blocked_at,
            'block_count': stats.block_count,
        }
        self._save_persistence(data)

    def _remove_auto_blocked_ip(self, ip: str):
        """Remove auto-blocked IP from persistence."""
        data = self._load_persistence()
        if ip in data:
            del data[ip]
            self._save_persistence(data)

    def check_auto_unblock(self) -> list:
        """
        Check for IPs that have served their block duration and auto-unblock them.
        Uses tiered blocking: 1min, 2min, 4min, 8min... based on block count.
        Called periodically (e.g., every minute).
        """
        if not self.enabled:
            return []

        current_time = time.time()
        unblocked: list = []

        with self._lock:
            for ip, stats in list(self._stats.items()):
                if stats.is_auto_blocked:
                    # Calculate tiered block duration based on block count
                    block_duration = self._calculate_block_duration(stats.block_count)
                    time_since_blocked = current_time - stats.blocked_at

                    if time_since_blocked >= block_duration:
                        # Check if there were new offenses during block period
                        if stats.last_offense > stats.blocked_at:
                            # New offenses detected - re-block with incremented count immediately
                            stats.block_count += 1
                            new_duration = self._calculate_block_duration(stats.block_count)
                            stats.blocked_at = time.time()  # Start blocking from NOW, not last offense
                            stats.violation_score = 0  # Reset score after re-block
                            blocklist.set_block_duration(ip, new_duration)
                            self._save_auto_blocked_ip(ip, stats)  # Persist the updated block_count
                            logger.info(f"IP {ip} had new offenses - re-blocking with count={stats.block_count}, duration={new_duration/60:.0f}min")
                            # Keep blocked - don't add to unblocked list
                        else:
                            # No new offenses, unblock and reset block count
                            stats.is_auto_blocked = False
                            blocklist.remove_ip(ip)
                            logger.info(f"Auto-unblocking IP {ip} (block duration expired)")
                            unblocked.append(ip)
                            self._remove_auto_blocked_ip(ip)

        return unblocked

    def cleanup_old_stats(self) -> int:
        """
        Remove or reset stats for IPs that haven't been seen in a while.
        Called periodically.

        - Reset block_count to 0 if no offenses for window_seconds (grace period)
        - Delete stats entirely if no activity for 2x the window
        """
        if not self.enabled:
            return 0

        current_time = time.time()
        cleaned = 0
        reset = 0

        with self._lock:
            for ip, stats in list(self._stats.items()):
                # Skip auto-blocked IPs
                if stats.is_auto_blocked:
                    continue

                # Reset block_count if no offenses for window_seconds (grace period)
                if stats.block_count > 0 and (current_time - stats.last_offense > self.window_seconds):
                    stats.block_count = 0
                    reset += 1
                    logger.debug(f"Reset block_count for IP {ip} (grace period expired)")

                # Remove stats entirely if no activity for 2x the window
                if current_time - stats.last_offense > self.window_seconds * 2:
                    del self._stats[ip]
                    cleaned += 1

        return cleaned

    def get_stats(self, ip: str) -> Optional[IPStats]:
        """Get statistics for an IP."""
        with self._lock:
            return self._stats.get(ip)

    def get_all_stats(self) -> Dict[str, IPStats]:
        """Get all IP statistics."""
        with self._lock:
            return dict(self._stats)

    async def start_periodic_tasks(self):
        """Start the background task for periodic auto-unblock checks and cleanup."""
        async def _periodic_loop():
            while True:
                try:
                    self.check_auto_unblock()
                    self.cleanup_old_stats()
                except Exception as e:
                    logger.error(f"Error in IP tracker periodic task: {e}")
                await asyncio.sleep(60)  # Run every 60 seconds

        self._periodic_task = asyncio.create_task(_periodic_loop())
        logger.info("IP Tracker periodic tasks started")

    async def stop_periodic_tasks(self):
        """Stop the background task."""
        if hasattr(self, '_periodic_task') and self._periodic_task:
            self._periodic_task.cancel()
            try:
                await self._periodic_task
            except asyncio.CancelledError:
                pass
        logger.info("IP Tracker periodic tasks stopped")


# Global tracker instance
tracker = IPTracker()


async def initialize_tracker():
    """Initialize the tracker at startup."""
    logger.info("Initializing IP Tracker...")
    tracker._restore_auto_blocked()
    await tracker.start_periodic_tasks()
    logger.info("IP Tracker initialized.")


async def shutdown_tracker():
    """Shutdown the tracker and stop periodic tasks."""
    await tracker.stop_periodic_tasks()
    logger.info("IP Tracker shutdown complete.")


async def check_auto_unblock():
    """Periodic task to check for auto-unblocks."""
    tracker.check_auto_unblock()


async def cleanup_tracker():
    """Periodic task to clean up old stats."""
    tracker.cleanup_old_stats()
