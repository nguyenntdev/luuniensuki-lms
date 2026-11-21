"""Project one pinned MBTA service day into the specified rail event graph."""
import argparse
import csv
import hashlib
import io
import json
import random
import zipfile
from collections import defaultdict
from pathlib import Path

PIN = "04cd2571fed0494c0c0dd2e30fa770140fd87ad7b6eb3c40265426c3c43d0772"
DATE = "20261120"


def seconds(s):
    h, m, sec = map(int, s.split(":"))
    return 3600*h + 60*m + sec


def rank(prefix, value):
    return hashlib.sha256((prefix+value).encode()).digest(), value


def prepare(path, output):
    with path.open("rb") as f:
        assert hashlib.file_digest(f, "sha256").hexdigest() == PIN
    with zipfile.ZipFile(path) as archive:
        def table(name):
            with archive.open(name+".txt") as raw, io.TextIOWrapper(raw, encoding="utf-8-sig", newline="") as f:
                yield from csv.DictReader(f)
        services = {r["service_id"] for r in table("calendar") if r["friday"]=="1" and r["start_date"]<=DATE<=r["end_date"]}
        for r in table("calendar_dates"):
            if r["date"] == DATE:
                (services.add if r["exception_type"]=="1" else services.discard)(r["service_id"])
        routes = {r["route_id"] for r in table("routes") if r["route_type"] in ("0","1")}
        trips = {r["trip_id"] for r in table("trips") if r["service_id"] in services and r["route_id"] in routes}
        stops = {r["stop_id"]:r["parent_station"] or r["stop_id"] for r in table("stops")}
        seq = defaultdict(list)
        for r in table("stop_times"):
            if r["trip_id"] in trips:
                seq[r["trip_id"]].append((int(r["stop_sequence"]), stops[r["stop_id"]], seconds(r["arrival_time"]),seconds(r["departure_time"])))
    legs = []
    for trip, items in sorted(seq.items()):
        ordered = sorted(items)
        for (_,a,_,dep), (_,b,arr,_) in zip(ordered,ordered[1:]):
            if 7*3600 <= dep < arr <= 9*3600 and a != b:
                legs.append((dep,a,arr,b,trip))
    stations = sorted({x for _,a,_,b,_ in legs for x in (a,b)})
    trips = sorted({trip for *_,trip in legs})
    station_id = {s:i for i,s in enumerate(stations)}
    trip_id = {s:i for i,s in enumerate(trips)}
    rows = [(dep,station_id[a],arr,station_id[b],trip_id[t]) for dep,a,arr,b,t in sorted(legs)]
    targets = [station_id[s] for s in sorted(stations,key=lambda s:rank("target:",s))[:4]]
    rng = random.Random(4202)
    queries = [(rng.choice([s for s in range(len(stations)) if s!=d]),rng.randrange(7*3600,9*3600),d) for d in targets for _ in range(128)]
    cancels = [trip_id[t] for t in sorted(trips,key=lambda t:rank("trip:",t))[:48]]
    with output.open("w") as f:
        print(len(stations),len(trips),len(rows),len(queries),len(cancels),file=f)
        for row in rows+queries: print(*row,file=f)
        print(*cancels,file=f)
    print(json.dumps(dict(source=PIN,date=DATE,routes=sorted(routes),stations=len(stations),trips=len(trips),legs=len(rows),
                          target_ids=[stations[d] for d in targets],queries=len(queries),scenarios=len(cancels),
                          projection_sha256=hashlib.sha256(output.read_bytes()).hexdigest()),indent=2))


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source",type=Path)
    parser.add_argument("output",type=Path)
    args=parser.parse_args()
    prepare(args.source,args.output)
