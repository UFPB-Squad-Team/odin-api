"""Read-only HTTP capacity scenario; run outside the constrained API container."""

import argparse
import asyncio
import json
import math
import time
from collections import Counter, defaultdict

import httpx

from scripts.seed_performance import STATES


async def run(args):
    samples = defaultdict(list)
    errors = Counter()
    stop = time.monotonic() + args.duration

    async def request(client, path, category):
        started = time.monotonic()
        try:
            result = await client.get(path)
            result.raise_for_status()
            if category == "pdf":
                if not result.content.startswith(b"%PDF-"):
                    raise ValueError("Invalid PDF")
            else:
                result.json()  # A successful status must contain complete JSON.
        except Exception as exc:
            errors[
                f"{category}:{type(exc).__name__}:{getattr(getattr(exc, 'response', None), 'status_code', '')}"
            ] += 1
        finally:
            samples[category].append(time.monotonic() - started)

    async def user(index):
        async with httpx.AsyncClient(base_url=args.base_url, timeout=150) as client:
            iteration = 0
            while time.monotonic() < stop:
                uf, capital, _ = STATES[(index + iteration) % len(STATES)]
                for path, category in [
                    ("/health", "light"),
                    (f"/api/v1/schools?estado_sigla={uf}&page_size=100", "light"),
                    (f"/api/v1/aggregations/cities?sg_uf={uf}", "geo"),
                    (
                        f"/api/v1/aggregations/cities?sg_uf={uf}&include_geometria=true",
                        "geo",
                    ),
                    (f"/api/v1/escolas/geojson/paraiba?municipio_id={capital}", "geo"),
                    (
                        f"/api/v1/aggregations/neighborhoods?municipio_id={capital}&include_geometria=true",
                        "geo",
                    ),
                    (
                        f"/api/v1/aggregations/neighborhoods?municipio_id={int(capital)+1}",
                        "geo",
                    ),
                ]:
                    await request(client, path, category)
                if iteration % 5 == 0:
                    # Full legacy map with all nine states, including the heavier BA fixture.
                    await request(client, "/api/v1/escolas/geojson/paraiba", "geo")
                if index == 0 and iteration % 10 == 0:
                    await request(client, f"/api/v1/estados/{uf}/dossie", "pdf")
                iteration += 1
                await asyncio.sleep(args.think_time)

    await asyncio.gather(*(user(i) for i in range(args.users)))
    summary = {}
    for category, values in samples.items():
        values.sort()
        summary[category] = {
            "requests": len(values),
            "p95_seconds": values[math.ceil(0.95 * len(values)) - 1],
            "max_seconds": values[-1],
        }
    print(
        json.dumps(
            {
                "users": args.users,
                "seconds": args.duration,
                "latency": summary,
                "errors": dict(errors),
            },
            indent=2,
        )
    )
    return 1 if errors else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--users", type=int, default=5)
    parser.add_argument("--duration", type=int, default=1800)
    parser.add_argument("--think-time", type=float, default=1)
    raise SystemExit(asyncio.run(run(parser.parse_args())))
