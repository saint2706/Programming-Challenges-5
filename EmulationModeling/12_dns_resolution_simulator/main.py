"""Run a simple DNS resolution simulation with caching."""

from dns_simulator import (
    AuthoritativeDNSServer,
    DNSResolver,
    RootServer,
    TLDServer,
)


def build_demo_resolver() -> DNSResolver:
    # Create authoritative servers with records
    example_auth = AuthoritativeDNSServer("example.com")
    example_auth.add_record("example.com", "93.184.216.34", ttl=10)

    api_auth = AuthoritativeDNSServer("api.example.com")
    api_auth.add_record("api.example.com", "203.0.113.10", ttl=5)

    # Create TLD servers and register domains
    com_tld = TLDServer("com")
    com_tld.register_domain("example.com", example_auth)
    com_tld.register_domain("api.example.com", api_auth)

    # Root server knows about .com
    root = RootServer()
    root.register_tld("com", com_tld)

    return DNSResolver(root)


def demo():
    resolver = build_demo_resolver()

    domains = ["example.com", "api.example.com", "example.com"]
    for domain in domains:
        ip = resolver.resolve(domain)
        print(f"Resolved {domain} to {ip}")

    print("\nSleeping to let api.example.com cache expire (TTL=5s)...")
    import time

    time.sleep(6)
    resolver.purge_expired()
    ip = resolver.resolve("api.example.com")
    print(f"Re-resolved api.example.com after expiry -> {ip}")


if __name__ == "__main__":
    demo()
