# -*- coding: utf-8 -*-
"""Provider Registry and Domain Policies — V5 Wave W07 Slot A04.

Spec references:
- AIR-012: Build provider allowlists and usage policies
- AIR-013: Official/museum/research metadata connectors
- P02-A03: Authority verifier (detect spoofed museum blogs)
- P02-A08: Malware/document sanitizer
- Strictly blocks forbidden pirated domains, paywall evasion, unauthorized scrapers.
"""
from __future__ import annotations

import re
from typing import Any, Optional
from urllib.parse import urlparse

from ..contracts import (
    AuthorityImpersonationError,
    ForbiddenDomainError,
    LegalRightsStatus,
    MaliciousPayloadError,
    PaywallBypassError,
    RobotsDisallowedError,
    UnapprovedSourceQuarantinedError,
)
from .base import BaseProviderConnector


# --------------------------------------------------------------------------- #
# Known Domain Lists
# --------------------------------------------------------------------------- #
APPROVED_DOMAINS: set[str] = {
    # Official heritage and archives
    "unesco.org",
    "mowcap.org",
    "dsvh.gov.vn",
    "nomfoundation.org",
    "hannom.org.vn",
    "archives.org.vn",
    "baotanglichsu.vn",
    "hueworldheritage.org.vn",
    # Open scholarly resolvers
    "crossref.org",
    "doi.org",
    "openalex.org",
    "archive.org",
}

FORBIDDEN_PIRATE_DOMAINS: set[str] = {
    "sci-hub.se",
    "sci-hub.st",
    "sci-hub.ru",
    "sci-hub.ren",
    "sci-hub.tw",
    "libgen.is",
    "libgen.rs",
    "libgen.li",
    "libgen.st",
    "b-ok.org",
    "z-lib.org",
    "pirated-scans.org",
    "leaked-archives.net",
    "darkweb-heritage.onion",
    "bypass-paywall.io",
}

COMMERCIAL_PAYWALLED_DOMAINS: set[str] = {
    "jstor.org",
    "sciencedirect.com",
    "springer.com",
    "tandfonline.com",
    "wiley.com",
    "cambridge.org",
}

# Authority domain mappings to detect spoofing / impersonation
CANONICAL_AUTHORITY_DOMAINS: dict[str, set[str]] = {
    "bảo tàng lịch sử quốc gia": {"baotanglichsu.vn"},
    "trung tâm bảo tồn di tích cố đô huế": {"hueworldheritage.org.vn"},
    "cục di sản văn hóa": {"dsvh.gov.vn"},
    "viện nghiên cứu hán nôm": {"hannom.org.vn"},
    "unesco": {"unesco.org", "mowcap.org"},
    "hội bảo tồn di sản chữ nôm": {"nomfoundation.org"},
}

SUSPICIOUS_BLOG_PLATFORMS: set[str] = {
    "wordpress.com",
    "blogspot.com",
    "blogger.com",
    "medium.com",
    "wixsite.com",
    "weebly.com",
    "sites.google.com",
}


class ProviderRegistry:
    """Registry managing provider connectors, domain allowlists, and access policies."""

    def __init__(self) -> None:
        self._connectors: dict[str, BaseProviderConnector] = {}
        self._seed_default_connectors()

    def _seed_default_connectors(self) -> None:
        """Seed built-in authorized connectors."""
        # 1. UNESCO & MOWCAP
        self.register_connector(
            BaseProviderConnector(
                provider_name="UNESCO Heritage Archive",
                domain="unesco.org",
                base_url="https://en.unesco.org",
                is_approved=True,
                is_paywalled=False,
            )
        )
        self.register_connector(
            BaseProviderConnector(
                provider_name="MOWCAP Heritage Register",
                domain="mowcap.org",
                base_url="https://www.mowcap.org",
                is_approved=True,
                is_paywalled=False,
            )
        )
        # 2. National Heritage Department
        self.register_connector(
            BaseProviderConnector(
                provider_name="Vietnam Department of Cultural Heritage",
                domain="dsvh.gov.vn",
                base_url="http://dsvh.gov.vn",
                is_approved=True,
                is_paywalled=False,
            )
        )
        # 3. Nôm Foundation
        self.register_connector(
            BaseProviderConnector(
                provider_name="Vietnamese Nom Preservation Foundation",
                domain="nomfoundation.org",
                base_url="https://www.nomfoundation.org",
                is_approved=True,
                is_paywalled=False,
            )
        )
        # 4. Hue Monuments Conservation Centre
        self.register_connector(
            BaseProviderConnector(
                provider_name="Hue Monuments Conservation Centre",
                domain="hueworldheritage.org.vn",
                base_url="https://hueworldheritage.org.vn",
                is_approved=True,
                is_paywalled=False,
            )
        )
        # 5. National Museum of History
        self.register_connector(
            BaseProviderConnector(
                provider_name="Vietnam National Museum of History",
                domain="baotanglichsu.vn",
                base_url="https://baotanglichsu.vn",
                is_approved=True,
                is_paywalled=False,
            )
        )
        # 6. DOI Open Access Resolver
        self.register_connector(
            BaseProviderConnector(
                provider_name="DOI Foundation Resolver",
                domain="doi.org",
                base_url="https://doi.org",
                is_approved=True,
                is_paywalled=False,
            )
        )
        # 7. Crossref Metadata
        self.register_connector(
            BaseProviderConnector(
                provider_name="Crossref Open Scholarly Metadata",
                domain="crossref.org",
                base_url="https://api.crossref.org",
                is_approved=True,
                is_paywalled=False,
            )
        )
        # 8. JSTOR (Paywalled provider)
        self.register_connector(
            BaseProviderConnector(
                provider_name="JSTOR Academic Repository",
                domain="jstor.org",
                base_url="https://www.jstor.org",
                is_approved=True,
                is_paywalled=True,
                requires_auth=True,
            )
        )

    def register_connector(self, connector: BaseProviderConnector) -> None:
        self._connectors[connector.domain.lower()] = connector

    def get_connector(self, domain_or_url: str) -> Optional[BaseProviderConnector]:
        domain = self.extract_domain(domain_or_url)
        if domain.lower() in self._connectors:
            return self._connectors[domain.lower()]
        for reg_domain, conn in self._connectors.items():
            if domain.lower().endswith(f".{reg_domain}"):
                return conn
        return None

    @staticmethod
    def extract_domain(url_or_domain: str) -> str:
        """Extract clean lowercased domain without port or protocol."""
        if "://" in url_or_domain:
            parsed = urlparse(url_or_domain)
            domain = parsed.hostname or url_or_domain
        else:
            domain = url_or_domain.split("/")[0].split(":")[0]
        return domain.strip().lower()

    def is_domain_forbidden(self, domain: str) -> bool:
        norm = domain.lower()
        if norm in FORBIDDEN_PIRATE_DOMAINS:
            return True
        for forbidden in FORBIDDEN_PIRATE_DOMAINS:
            if norm.endswith(f".{forbidden}"):
                return True
        return False

    def is_domain_paywalled(self, domain: str) -> bool:
        norm = domain.lower()
        if norm in COMMERCIAL_PAYWALLED_DOMAINS:
            return True
        for paywalled in COMMERCIAL_PAYWALLED_DOMAINS:
            if norm.endswith(f".{paywalled}"):
                return True
        return False

    def is_domain_approved(self, domain: str) -> bool:
        norm = domain.lower()
        if norm in APPROVED_DOMAINS:
            return True
        for approved in APPROVED_DOMAINS:
            if norm.endswith(f".{approved}"):
                return True
        return False

    def validate_domain_access(
        self,
        url_or_domain: str,
        headers: Optional[dict[str, str]] = None,
    ) -> BaseProviderConnector:
        """Validate domain access against forbidden lists and paywalls.
        
        Raises ForbiddenDomainError or PaywallBypassError if policy violated.
        """
        domain = self.extract_domain(url_or_domain)

        # 1. Strictly block forbidden pirated/shadow library domains
        if self.is_domain_forbidden(domain):
            raise ForbiddenDomainError(
                f"Access to unauthorized scan repository / pirated domain '{domain}' is strictly blocked",
                details={"domain": domain, "policy": "FORBIDDEN_PIRATE_REPOSITORY"},
            )

        # 2. Check for paywalled domain and bypass attempt
        is_paywalled = self.is_domain_paywalled(domain)
        connector = self.get_connector(domain)

        if connector and connector.is_paywalled:
            is_blocked_pw, reason = connector.detect_paywall(url_or_domain, headers)
            if is_blocked_pw:
                raise PaywallBypassError(
                    f"Paywall bypass prohibited for '{domain}': {reason}",
                    details={"domain": domain, "reason": reason},
                )
        elif is_paywalled:
            # Check bypass headers first
            if headers:
                for k in headers:
                    if "bypass" in k.lower():
                        raise PaywallBypassError(
                            f"Paywall bypass header prohibited for '{domain}': {k}",
                            details={"domain": domain, "header": k},
                        )
            # Domain known to be paywalled but no connector credentials
            raise PaywallBypassError(
                f"Domain '{domain}' is a subscription paywall and lacks institutional credentials",
                details={"domain": domain, "requires_auth": True},
            )

        # 3. Return connector or fallback connector if domain is approved
        if connector:
            return connector

        if self.is_domain_approved(domain):
            new_connector = BaseProviderConnector(
                provider_name=f"Approved Provider ({domain})",
                domain=domain,
                base_url=f"https://{domain}",
                is_approved=True,
            )
            self.register_connector(new_connector)
            return new_connector

        # Untrusted or unapproved domain -> fallback connector with quarantine required
        return BaseProviderConnector(
            provider_name=f"Unapproved Domain ({domain})",
            domain=domain,
            base_url=f"https://{domain}",
            is_approved=False,
        )

    def validate_authority(
        self,
        authority_name: Optional[str],
        domain_or_url: Optional[str],
    ) -> None:
        """P02-A03: Validate institution authenticity.
        
        Detects personal blogs pretending to be national museums or state institutions.
        """
        if not authority_name or not domain_or_url:
            return

        norm_authority = authority_name.strip().lower()
        domain = self.extract_domain(domain_or_url)

        # Check if authority is an official institution
        for official_name, canonical_domains in CANONICAL_AUTHORITY_DOMAINS.items():
            if official_name in norm_authority:
                # Must originate from one of the canonical domains
                matches_canonical = any(
                    domain == c_dom or domain.endswith(f".{c_dom}")
                    for c_dom in canonical_domains
                )
                if not matches_canonical:
                    # Check if hosting on suspicious blog platforms
                    is_suspicious_blog = any(
                        domain == b_dom or domain.endswith(f".{b_dom}")
                        for b_dom in SUSPICIOUS_BLOG_PLATFORMS
                    )
                    raise AuthorityImpersonationError(
                        f"Impersonation detected: Source claims authority '{authority_name}' "
                        f"but originates from untrusted domain '{domain}'",
                        details={
                            "claimed_authority": authority_name,
                            "domain": domain,
                            "expected_domains": list(canonical_domains),
                            "is_blog": is_suspicious_blog,
                        },
                    )

    @staticmethod
    def sanitize_payload(payload_bytes: bytes, declared_mime_type: str) -> None:
        """P02-A08: Inspect payload magic bytes for executable malware masked as PDF/images."""
        if not payload_bytes:
            return

        # Check PE Windows executable (MZ header)
        if payload_bytes.startswith(b"MZ"):
            raise MaliciousPayloadError(
                "Malicious payload detected: Windows executable (PE) disguised as document",
                details={"magic_bytes": "MZ", "declared_mime_type": declared_mime_type},
            )

        # Check Linux ELF executable (\x7fELF)
        if payload_bytes.startswith(b"\x7fELF"):
            raise MaliciousPayloadError(
                "Malicious payload detected: Linux executable (ELF) disguised as document",
                details={"magic_bytes": "\\x7fELF", "declared_mime_type": declared_mime_type},
            )

        # Check Shell script header
        if payload_bytes.startswith(b"#!/bin/") or payload_bytes.startswith(b"#!/usr/bin/"):
            raise MaliciousPayloadError(
                "Malicious payload detected: Shell script disguised as document",
                details={"magic_bytes": "#!", "declared_mime_type": declared_mime_type},
            )

        # If declared as PDF, must have %PDF header within first 1024 bytes
        if declared_mime_type.lower() == "application/pdf":
            if b"%PDF-" not in payload_bytes[:1024]:
                raise MaliciousPayloadError(
                    "Invalid PDF payload: missing standard %PDF- header in document preface",
                    details={"declared_mime_type": declared_mime_type},
                )


# Global singleton instance
provider_registry = ProviderRegistry()
