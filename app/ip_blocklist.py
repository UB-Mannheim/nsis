# -*- coding: utf-8 -*-
# =============================================================================
# ip_blocklist.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

"""
IP-based blocking for nsis API.
Manages a blocklist of IP addresses that are denied access to the API.
"""

import logging
from typing import Dict, Set, Optional
from fastapi import Request, HTTPException, status
from app.config import settings

logger = logging.getLogger("nsis")


class IPBlocklist:
    """
    Manages blocked IP addresses for the API.
    Supports both CIDR notation for ranges and exact IP matching.
    """

    @staticmethod
    def _parse_list(value: Optional[str]) -> list:
        """Parse a comma-separated string into a list, filtering empty strings."""
        if not value:
            return []
        return [item.strip() for item in value.split(",") if item.strip()]

    def __init__(self):
        self._blocked_ips: Set[str] = set(self._parse_list(settings.blocked_ips))
        self._blocked_ranges: Set[str] = set(self._parse_list(settings.blocked_ip_ranges))
        # Block duration cache for tiered blocking: {ip: duration_seconds}
        self._block_durations: Dict[str, float] = {}
        logger.info(f"IP blocklist initialized with {len(self._blocked_ips)} IPs and {len(self._blocked_ranges)} ranges")

    def _is_ip_in_range(self, ip: str, cidr: str) -> bool:
        """Check if an IP address is within a CIDR range."""
        import ipaddress
        try:
            return ipaddress.ip_address(ip) in ipaddress.ip_network(cidr, strict=False)
        except ValueError:
            return False

    def is_blocked(self, ip: str) -> bool:
        """Check if an IP address is blocked."""
        if not ip:
            return False

        # Check exact matches
        if ip in self._blocked_ips:
            return True

        # Check CIDR ranges
        for cidr in self._blocked_ranges:
            if self._is_ip_in_range(ip, cidr):
                return True

        return False

    def add_ip(self, ip: str) -> None:
        """Add an IP address to the blocklist."""
        self._blocked_ips.add(ip)
        logger.info(f"IP {ip} added to blocklist")

    def remove_ip(self, ip: str) -> None:
        """Remove an IP address from the blocklist."""
        self._blocked_ips.discard(ip)
        logger.info(f"IP {ip} removed from blocklist")

    def add_range(self, cidr: str) -> None:
        """Add a CIDR range to the blocklist."""
        self._blocked_ranges.add(cidr)
        logger.info(f"IP range {cidr} added to blocklist")

    def set_block_duration(self, ip: str, duration_seconds: float) -> None:
        """Set the blocking duration for an IP (for tiered blocking)."""
        self._block_durations[ip] = duration_seconds

    def get_block_duration(self, ip: str) -> Optional[float]:
        """Get the blocking duration for an IP (for tiered blocking)."""
        return self._block_durations.get(ip)

    def get_blocked_count(self) -> int:
        """Get the number of blocked IPs/ranges."""
        return len(self._blocked_ips) + len(self._blocked_ranges)


# Global blocklist instance
blocklist = IPBlocklist()


async def check_ip_blocked(request: Request) -> Optional[str]:
    """
    Dependency that checks if the client IP is blocked.
    Raises HTTPException 403 if blocked, returns None if allowed.
    """
    client_ip = request.client.host if request.client else None

    # Skip IP blocking for localhost / 127.0.0.1
    if client_ip and client_ip in ("127.0.0.1", "::1", "localhost"):
        return client_ip

    if client_ip and blocklist.is_blocked(client_ip):
        logger.warning(f"Blocked IP attempted access: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "IP_BLOCKED",
                    "message": "Access denied for your IP address."
                }
            }
        )

    return client_ip
