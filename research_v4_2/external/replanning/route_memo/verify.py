"""Validate exact arrival times, complete witnesses and paired benchmark tables."""
import argparse
import csv
import gzip
import hashlib
import heapq
import json
import math
from bisect import bisect_left
from collections import defaultdict
from pathlib import Path
from statistics import geometric_mean, median

from workloads import workloads

METHODS = ("indexed_csa", "signature_only", "signature_base_index", "memoized_rides")
INF = 1_000_000_000


def shortest(query, ban, departures):
    origin, start, dest = query
    times = [INF] * len(departures)
    times[origin] = start
    queue = [(start, origin)]
    while queue:
        time, station = heapq.heappop(queue)
        if time != times[station]:
            continue
        if station == dest:
            return time
        for dep, _, arr, to, trip in departures[station]:
            if dep >= time and trip != ban and arr < times[to]:
                times[to] = arr
                heapq.heappush(queue, (arr, to))
    return INF


def witness_stats(network, raw_witnesses, original_witnesses):
    header, *rows = [tuple(map(int, row.split())) for row in network.splitlines()]
    stations, trips, n_legs, n_queries, n_bans = header
    legs = rows[:n_legs]
    queries = rows[n_legs:n_legs + n_queries]
    bans, = rows[n_legs + n_queries:]
    assert len(set(bans)) == len(bans) == n_bans
    departures = [[] for _ in range(stations)]
    station_events = [set() for _ in range(stations)]
    for leg in legs:
        dep, origin, arr, dest, trip = leg
        assert 0 <= trip < trips
        departures[origin].append(leg)
        station_events[origin].add(dep)
        station_events[dest].add(arr)
    station_events = [sorted(events) for events in station_events]
    starts = [(origin, bisect_left(station_events[origin], time), dest)
              for origin, time, dest in queries]
    base = [shortest(q, -1, departures) for q in queries]
    expected = [[shortest(q, ban, departures) for q in queries] for ban in bans]
    with gzip.open(raw_witnesses, "rt", encoding="ascii") as source:
        seen = {}
        for row in source:
            scenario, method, query, arrival, *route = map(int, row.split())
            assert 0 <= scenario < n_bans
            assert 0 <= method < len(METHODS) and 0 <= query < n_queries
            key = (scenario, method, query)
            assert key not in seen
            assert arrival == expected[scenario][query], (key, arrival, expected[scenario][query])
            at, time, dest = queries[query]
            if arrival == INF:
                assert not route
            else:
                for leg in route:
                    assert 0 <= leg < n_legs
                    dep, origin, arr, to, trip = legs[leg]
                    assert at == origin and time <= dep < arr and trip != bans[scenario]
                    at, time = to, arr
                assert (at, time) == (dest, arrival)
            seen[key] = (arrival, tuple(route))
    assert len(seen) == n_bans * len(METHODS) * n_queries
    for s in range(n_bans):
        for q in range(n_queries):
            assert seen[s, 1, q] == seen[s, 2, q] == seen[s, 3, q]
    if original_witnesses is not None:
        with gzip.open(original_witnesses, "rt", encoding="ascii") as source:
            reference = {}
            for row in source:
                s, m, q, arrival, *route = map(int, row.split())
                if m == 8:  # Archived corridor signature-only control.
                    reference[s, q] = (arrival, tuple(route))
        assert len(reference) == n_bans * n_queries
        assert all(reference[s, q] == seen[s, 1, q] for s in range(n_bans) for q in range(n_queries))
    # Worsened arrivals are a lower bound on the number of repairs.
    worsened = [[q for q, arrival in enumerate(row) if arrival > base[q]] for row in expected]
    assert all(arrival >= base[q] for row in expected for q, arrival in enumerate(row))
    return bans, {
        "queries": n_queries,
        "scenarios": n_bans,
        "event_destination_states": sum(map(len, station_events)) * len({q[2] for q in queries}),
        "distinct_query_start_events": len(set(starts)),
        "arrival_worsened": sum(map(len, worsened)),
        "worsened_distinct_start_events_summed_over_batches": sum(
            len({starts[q] for q in changed}) for changed in worsened
        ),
        "unreachable": sum(arrival == INF for row in expected for arrival in row),
        "became_unreachable": sum(
            expected[s][q] == INF for s, changed in enumerate(worsened) for q in changed
        ),
        "verified_witnesses": len(seen),
        "witness_legs": sum(len(route) for _, route in seen.values()),
    }


def read_timings(path, bans):
    times = defaultdict(list)
    keys = set()
    with path.open(newline="") as source:
        for row in csv.DictReader(source):
            method = row["method"]
            repeat, ns = int(row["repeat"]), int(row["ns"])
            assert ns > 0 and method in METHODS
            if bans is None:
                assert 0 <= repeat < 7
                group = method
            else:
                assert 0 <= repeat < 15
                scenario = int(row["scenario"])
                assert 0 <= scenario < len(bans) and int(row["trip"]) == bans[scenario]
                group = (method, scenario)
            key = (group, repeat)
            assert key not in keys
            keys.add(key)
            times[group].append(ns)
    assert len(keys) == len(METHODS) * (7 if bans is None else 15 * len(bans))
    return {group: median(samples) for group, samples in times.items()}


def summarize(values):
    return {
        "p95_us": sorted(values)[math.ceil(len(values) * .95) - 1] / 1000,
        "geometric_us": geometric_mean(values) / 1000,
    }


def evaluate(network, evidence, witnesses, archived):
    bans, counts = witness_stats(network, witnesses / "witnesses.txt.gz", archived)
    setup = read_timings(evidence / "setup.csv", None)
    batch = read_timings(evidence / "latency.csv", bans)
    results = {}
    for method in METHODS:
        times = [batch[method, s] for s in range(len(bans))]
        amortized = summarize([t + setup[method] / len(bans) for t in times])
        results[method] = {
            "setup_ms": setup[method] / 1e6,
            **summarize(times),
            **{f"amortized_{key}": value for key, value in amortized.items()},
        }
    candidate = results[METHODS[-1]]
    gains = {
        method: {key: 1 - candidate[key] / value for key, value in results[method].items()
                 if key != "setup_ms"}
        for method in METHODS[:-1]
    }
    return {
        "projection_sha256": hashlib.sha256(network).hexdigest(),
        **counts,
        "results": results,
        "relative_gains": gains,
        "advance": all(gain >= .10 for control in gains.values() for gain in control.values()),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("network", type=Path)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--witness-evidence", type=Path, help="use a byte-identical existing witness archive")
    args = parser.parse_args()
    witnesses = args.witness_evidence or args.evidence
    archive = Path(__file__).resolve().parents[1] / "corridor" / "witnesses.txt.gz"
    result = {
        name: evaluate(network, args.evidence / name, witnesses / name, archive if name == "original" else None)
        for name, network in workloads(args.network).items()
    }
    print(json.dumps(result, indent=2))
