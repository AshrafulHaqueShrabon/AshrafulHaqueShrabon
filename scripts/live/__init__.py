"""Live data: API fetchers (standard library only) with a last-known-good cache.

Each platform module separates pure parsing (unit-tested against recorded
responses in examples/fixtures/) from fetching, which goes through an
injectable HTTP client so the fallback logic is testable offline.
"""
