# DNS Resolution Simulator

A small Python simulator that walks through DNS resolution: Root → TLD → Authoritative servers with a resolver cache honoring TTLs.

## 📋 Features

- Root server that maps TLDs to their TLD name servers.
- TLD servers that delegate domains to authoritative servers.
- Authoritative servers that return DNS records with TTLs.
- Resolver that caches responses and expires them based on TTL.

## 🚀 Running the Demo

```bash
cd EmulationModeling/12_dns_resolution_simulator
python main.py
```

You should see the resolver walk the hierarchy, then reuse cached entries, and finally re-query once a TTL expires.

## 🧪 Tests

```bash
python -m pytest tests/EmulationModeling/test_12_dns_resolution_simulator.py
```
