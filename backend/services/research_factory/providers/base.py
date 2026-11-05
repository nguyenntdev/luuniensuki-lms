# -*- coding: utf-8 -*-
"""Base Provider Connector — V5 Wave W07 Slot A04.

Spec references:
- LUU_NIEN_V6_MODULAR_IMPLEMENTATION_SPECS/03_AI_FACTORY/AIR_011_TO_015_ENGINEERING_PACKETS.md (AIR-012, AIR-013)
- Respects robots.txt, strict paywall policies, rate limits, no unauthorized scraping.
"""
from __future__ import annotations

import fnmatch
import re
from typing import Any, Optional
from urllib.parse import urlparse

from ..contracts import (
    AcquisitionDecision,
    AcquisitionResult,
    LegalRightsStatus,
    PaywallBypassError,
    RobotsDisallowedError,
    SourceCandidate,
    SourceSnapshot,
)


class BaseProviderConnector:
    """Abstract/base connector for legal source providers."""

    def __init__(
        self,
        *,
        provider_name: str,
        domain: str,
        base_url: str,
        is_approved: bool = True,
        is_paywalled: bool = False,
        requires_auth: bool = False,
        rate_limit_rpm: int = 60,
        disallowed_paths: Optional[list[str]] = None,
        allowed_paths: Optional[list[str]] = None,
    ):
        self.provider_name = provider_name
        self.domain = domain.lower()
        self.base_url = base_url
        self.is_approved = is_approved
        self.is_paywalled = is_paywalled
        self.requires_auth = requires_auth
        self.rate_limit_rpm = rate_limit_rpm
        self.disallowed_paths = disallowed_paths or [
            "/restricted/*",
            "/private/*",
            "/admin/*",
            "/no-robots/*",
            "*/download-batch/*",
        ]
        self.allowed_paths = allowed_paths or ["*"]

    def check_robots(self, path: str, user_agent: str = "LuunienSukiBot") -> tuple[bool, str]:
        """Verify whether path complies with robots.txt rules.
        
        Returns (is_allowed, reason).
        """
        norm_path = path if path.startswith("/") else f"/{path}"
        for pattern in self.disallowed_paths:
            if fnmatch.fnmatch(norm_path, pattern):
                return False, f"Disallowed by robots.txt pattern '{pattern}'"
        return True, "Path permitted by robots.txt"

    def detect_paywall(
        self,
        url: str,
        headers: Optional[dict[str, str]] = None,
    ) -> tuple[bool, str]:
        """Detect paywall barriers and inspect for illicit paywall bypass attempts.
        
        Returns (is_blocked_by_paywall, reason).
        """
        # 1. Check for unauthorized bypass headers
        if headers:
            lower_headers = {k.lower(): str(v).lower() for k, v in headers.items()}
            bypass_keys = [
                "x-bypass-paywall",
                "x-proxy-scrape",
                "x-bypass-referer",
                "x-scraping-proxy",
                "x-evade-paywall",
            ]
            for key in bypass_keys:
                if key in lower_headers and lower_headers[key] in ("true", "1", "yes", "enabled"):
                    return True, f"Prohibited paywall bypass header detected: '{key}'"
            
            # Check for bot spoofing to evade paywall
            ua = lower_headers.get("user-agent", "")
            if any(bot in ua for bot in ["googlebot", "bingbot", "slurp"]) and "luuniensuki" not in ua:
                return True, "Prohibited User-Agent spoofing to evade paywall detected"

        # 2. Check provider-level paywall barrier
        if self.is_paywalled:
            auth_token = None
            if headers:
                auth_token = headers.get("Authorization") or headers.get("X-Institutional-Subscription")
            if not auth_token:
                return True, f"Provider '{self.provider_name}' requires institutional license / active subscription"

        return False, "Not paywalled or valid institutional credentials provided"

    def acquire_candidate(
        self,
        candidate: SourceCandidate,
        payload_bytes: Optional[bytes] = None,
        mime_type: Optional[str] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> AcquisitionResult:
        """Execute acquisition with robots and paywall validation."""
        # 1. Check paywall
        target_url = candidate.url or f"{self.base_url}"
        parsed = urlparse(target_url)
        path = parsed.path or "/"

        is_paywalled, pw_reason = self.detect_paywall(target_url, headers)
        if is_paywalled:
            raise PaywallBypassError(
                f"Paywall bypass prohibited for {target_url}: {pw_reason}",
                details={"url": target_url, "provider": self.provider_name, "reason": pw_reason},
            )

        # 2. Check robots.txt
        is_robots_allowed, robots_reason = self.check_robots(path)
        if not is_robots_allowed:
            raise RobotsDisallowedError(
                f"Robots.txt disallowed access to {target_url}: {robots_reason}",
                details={"url": target_url, "path": path, "provider": self.provider_name},
            )

        # Base success with metadata
        return AcquisitionResult(
            candidate_id=candidate.id,
            decision=AcquisitionDecision.ALLOWED_METADATA_ONLY,
            rights_status=candidate.claimed_rights,
            reason=f"Acquired metadata through provider {self.provider_name}",
            public_display_allowed=False,
            derivative_allowed=False,
            is_excerpt_redacted=True,
            quarantine_required=False,
            audit_trail=[
                {
                    "step": "provider_connector",
                    "provider": self.provider_name,
                    "robots_checked": True,
                    "paywall_checked": True,
                }
            ],
        )
