"""Construct the two request workloads from the pinned development projection."""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path


def workloads(network):
    inventory = Path(__file__).resolve().parents[1] / "inventory.json"
    source = network.read_bytes()
    if hashlib.sha256(source).hexdigest() != json.loads(inventory.read_text())["projection_sha256"]:
        raise ValueError("expected the pinned MBTA development projection")
    header, *rows = source.decode("ascii").splitlines()
    _, _, leg_count, query_count, _ = map(int, header.split())
    legs = rows[:leg_count]
    queries = rows[leg_count:leg_count + query_count]
    cancellations = rows[leg_count + query_count:]
    seen = defaultdict(int)
    bursts = []
    for query in queries:
        origin, start, destination = map(int, query.split())
        if seen[destination] < 16:
            burst_start = min(start, 9 * 3600 - 8)
            bursts.extend(f"{origin} {second} {destination}"
                          for second in range(burst_start, burst_start + 8))
        seen[destination] += 1
    if len(bursts) != query_count:
        raise ValueError("request count changed in the burst workload")
    burst_network = "\n".join([header, *legs, *bursts, *cancellations]) + "\n"
    return {"original": source, "bursts": burst_network.encode("ascii")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("network", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    for name, data in workloads(args.network).items():
        (args.output / f"{name}.network").write_bytes(data)
