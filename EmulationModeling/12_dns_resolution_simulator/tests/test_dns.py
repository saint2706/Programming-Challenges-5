import pytest
from dns_simulator import (
    AuthoritativeDNSServer,
    DNSResolver,
    RootServer,
    TLDServer,
)


class FakeTime:
    def __init__(self, start: float = 0.0):
        self.now = start

    def advance(self, seconds: float) -> None:
        self.now += seconds

    def __call__(self) -> float:
        return self.now


def build_resolver_with_fake_time(fake_time: FakeTime) -> DNSResolver:
    example_auth = AuthoritativeDNSServer("example.com")
    example_auth.add_record("example.com", "93.184.216.34", ttl=10)

    com_tld = TLDServer("com")
    com_tld.register_domain("example.com", example_auth)

    root = RootServer()
    root.register_tld("com", com_tld)

    return DNSResolver(root, time_provider=fake_time)


def test_resolution_walks_hierarchy_and_caches():
    fake_time = FakeTime()
    resolver = build_resolver_with_fake_time(fake_time)
    root_server = resolver.root_server
    com_tld = root_server.tld_servers["com"]
    auth_server = com_tld.authoritative_servers["example.com"]

    first_ip = resolver.resolve("example.com")

    assert first_ip == "93.184.216.34"
    assert root_server.query_count == 1
    assert com_tld.query_count == 1
    assert auth_server.query_count == 1
    assert resolver.cache_size() == 1

    # Second resolution uses cache, so counts do not increase
    second_ip = resolver.resolve("example.com")
    assert second_ip == first_ip
    assert root_server.query_count == 1
    assert com_tld.query_count == 1
    assert auth_server.query_count == 1


def test_cache_expires_after_ttl():
    fake_time = FakeTime()
    resolver = build_resolver_with_fake_time(fake_time)
    root_server = resolver.root_server
    com_tld = root_server.tld_servers["com"]
    auth_server = com_tld.authoritative_servers["example.com"]

    resolver.resolve("example.com")
    assert root_server.query_count == 1

    fake_time.advance(11)
    resolver.purge_expired()
    resolver.resolve("example.com")

    # Cache expired so new queries are performed
    assert root_server.query_count == 2
    assert com_tld.query_count == 2
    assert auth_server.query_count == 2


if __name__ == "__main__":
    pytest.main(["-q"])
