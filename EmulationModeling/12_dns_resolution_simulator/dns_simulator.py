"""DNS resolution simulator with root, TLD, and authoritative servers."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Dict, Optional, Tuple


@dataclass
class DNSRecord:
    domain: str
    address: str
    ttl: int


class AuthoritativeDNSServer:
    """Represents an authoritative server for a specific domain."""

    def __init__(self, domain: str, records: Optional[Dict[str, DNSRecord]] = None):
        self.domain = domain
        self.records: Dict[str, DNSRecord] = records or {}
        self.query_count = 0

    def add_record(self, domain: str, address: str, ttl: int = 60) -> None:
        self.records[domain] = DNSRecord(domain=domain, address=address, ttl=ttl)

    def query(self, domain: str) -> DNSRecord:
        self.query_count += 1
        if domain not in self.records:
            raise KeyError(
                f"{domain} not found on authoritative server for {self.domain}"
            )
        return self.records[domain]


class TLDServer:
    """Represents a Top-Level Domain server (e.g., .com)."""

    def __init__(self, tld: str):
        self.tld = tld
        self.authoritative_servers: Dict[str, AuthoritativeDNSServer] = {}
        self.query_count = 0

    def register_domain(
        self, domain: str, authoritative_server: AuthoritativeDNSServer
    ) -> None:
        self.authoritative_servers[domain] = authoritative_server

    def query(self, domain: str) -> AuthoritativeDNSServer:
        self.query_count += 1
        if domain not in self.authoritative_servers:
            raise KeyError(f"{domain} not managed by {self.tld} TLD server")
        return self.authoritative_servers[domain]


class RootServer:
    """Represents the DNS root server that knows TLD name servers."""

    def __init__(self):
        self.tld_servers: Dict[str, TLDServer] = {}
        self.query_count = 0

    def register_tld(self, tld: str, tld_server: TLDServer) -> None:
        self.tld_servers[tld] = tld_server

    def query(self, tld: str) -> TLDServer:
        self.query_count += 1
        if tld not in self.tld_servers:
            raise KeyError(f"TLD {tld} not found on root server")
        return self.tld_servers[tld]


class DNSResolver:
    """Resolver that walks DNS hierarchy and caches results with TTL."""

    def __init__(
        self, root_server: RootServer, time_provider: Callable[[], float] | None = None
    ):
        self.root_server = root_server
        self.cache: Dict[str, Tuple[str, float]] = {}
        self.time_provider = time_provider or time.time

    def _current_time(self) -> float:
        return self.time_provider()

    def _is_cached(self, domain: str) -> bool:
        if domain not in self.cache:
            return False
        _, expires_at = self.cache[domain]
        return self._current_time() < expires_at

    def resolve(self, domain: str) -> str:
        """Resolve a domain name, using cache when possible."""
        if self._is_cached(domain):
            return self.cache[domain][0]

        labels = domain.split(".")
        if len(labels) < 2:
            raise ValueError("Domain must include a TLD (e.g., example.com)")

        tld = labels[-1]
        root_response = self.root_server.query(tld)
        tld_server = root_response

        authoritative_server = tld_server.query(domain)
        record = authoritative_server.query(domain)

        expires_at = self._current_time() + record.ttl
        self.cache[domain] = (record.address, expires_at)
        return record.address

    def cache_size(self) -> int:
        return len(self.cache)

    def purge_expired(self) -> None:
        now = self._current_time()
        expired_keys = [domain for domain, (_, exp) in self.cache.items() if exp <= now]
        for domain in expired_keys:
            self.cache.pop(domain, None)
