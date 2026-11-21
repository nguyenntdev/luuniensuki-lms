"""Audit URLs in historical English Wikipedia source against two pinned Tate snapshots."""
import argparse
import csv
import hashlib
import json
import re
import time
from io import StringIO
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
API = "https://en.wikipedia.org/w/api.php"
CUTOFF = "2014-06-12T00:00:00Z"
TATE = [
    ("b628039a8759f5f27f3edd542d959859a5882039", "f709c2289805615e21395a915119d44f5f139023cc845b979562741a0652baf5"),
    ("e7936a63d954d5b17628c59990531d723d2da010", "3fb68c02725846b540a86fa9629de8b0a6902659378e853af0691bc5ff74f09d"),
]
LINK = re.compile(r"""https?://www\.tate\.org\.uk(/art/artworks/[^\s<>{}\[\]|"'?#]+)""")
LABEL = re.compile(r"\[" + LINK.pattern + r"[ \t]+([^\[\]{}<>\n]+)\]")
HIDDEN = re.compile(r"<!--.*?-->|<nowiki\b[^>]*>.*?</nowiki\s*>", re.I | re.S)


def download(url):
    request = Request(url, headers={"User-Agent": "CatalogueCitationResearch/1.0 (Tate collection metadata research; https://github.com/tategallery/collection)"})
    for attempt in range(5):
        try:
            with urlopen(request, timeout=60) as response:
                return response.read()
        except HTTPError as error:
            if error.code not in {429, 502, 503, 504} or attempt == 4:
                raise
            time.sleep(int(error.headers.get("Retry-After", 2 ** (attempt + 1))))


def pinned_revisions(cache, mapping):
    missing = [(int(page), rev) for page, rev in mapping.items() if rev and
               not (cache / f"{page}-{rev}.json").exists()]
    for offset in range(0, len(missing), 10):
        group = missing[offset:offset + 10]
        params = dict(action="query", prop="revisions", rvslots="main", rvprop="ids|timestamp|content",
                      format="json", formatversion=2, revids="|".join(str(rev) for _, rev in group))
        reply = json.loads(download(API + "?" + urlencode(params)))
        pages = {p["pageid"]: p for p in reply["query"]["pages"]}
        for page_id, rev_id in group:
            page = pages[page_id]
            rev, = page["revisions"]
            assert rev["revid"] == rev_id and "content" in rev["slots"]["main"]
            save(cache / f"{page_id}-{rev_id}.json", {"query": {"pages": [page]}})


def revision(cache, page_id, rev_id=None):
    path = cache / f"{page_id}-{rev_id or 'cutoff'}.json"
    if not path.exists():
        params = dict(action="query", prop="revisions", rvslots="main", rvprop="ids|timestamp|content",
                      format="json", formatversion=2)
        if rev_id:
            params["revids"] = rev_id
        else:
            params.update(pageids=page_id, rvlimit=1, rvstart=CUTOFF)
        raw = download(API + "?" + urlencode(params))
        reply = json.loads(raw)
        if "error" in reply or "pages" not in reply.get("query", {}):
            raise ValueError(f"Wikipedia query failed for {page_id}: {str(reply)[:250]}")
        path.write_bytes(raw)
    page, = json.loads(path.read_bytes())["query"]["pages"]
    assert page["pageid"] == page_id
    revisions = page.get("revisions", [])
    if not revisions:
        return None, []
    rev, = revisions
    assert rev["timestamp"] <= CUTOFF
    if rev_id:
        assert rev["revid"] == rev_id
    body = HIDDEN.sub("", rev["slots"]["main"]["content"])
    labels = {}
    for path, label in LABEL.findall(body):
        digest = hashlib.sha256(label.strip().encode()).hexdigest()
        labels.setdefault(path, set()).add(digest)
    return rev["revid"], [(p, sorted(labels.get(p, ()))) for p in sorted(set(LINK.findall(body)))]


def collect(args):
    page_ids = sorted({r["pageid"] for r in json.loads((HERE / "frame.json").read_bytes())["query"]["exturlusage"]})
    manifest = None if args.discover else json.loads((HERE / "revisions.json").read_bytes())
    if manifest is not None:
        pinned_revisions(args.cache, manifest)
    records, mapping = [], {}
    for page_id in page_ids:
        rev_id = None if manifest is None else manifest[str(page_id)]
        if manifest is not None and rev_id is None:
            continue
        rev_id, paths = revision(args.cache, page_id, rev_id)
        mapping[page_id] = rev_id
        records.extend([page_id, rev_id, path, labels] for path, labels in paths)
    if manifest is None:
        save(args.out / "revisions.json", mapping)
    save(args.out / "paths.json", records)


def save(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def catalog(cache, commit, digest):
    path = cache / f"{commit}.csv"
    if not path.exists():
        path.write_bytes(download(f"https://raw.githubusercontent.com/tategallery/collection/{commit}/artwork_data.csv"))
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == digest
    rows = list(csv.DictReader(StringIO(raw.decode("utf-8-sig"), newline="")))
    by_id = {r["id"]: r for r in rows}
    assert len(rows) == len(by_id)
    return by_id


def evaluate(args):
    old, new = [catalog(args.cache, *version) for version in TATE]
    by_path = {}
    for rid, row in old.items():
        key = urlsplit(row["url"]).path
        by_path.setdefault(key, []).append(rid)
    references = json.loads((args.inputs / "paths.json").read_bytes())
    edges = []
    for page, rev, path, labels in references:
        ids = by_path.get(path, [])
        if len(ids) != 1:
            continue
        rid, = ids
        after = new.get(rid, {})
        changes = [k for k in old[rid] if old[rid][k] != after.get(k)]
        title = old[rid]["title"]
        title_match = bool(title) and hashlib.sha256(title.encode()).hexdigest() in labels
        edges.append(dict(page=page, revision=rev, id=rid, accession=old[rid]["accession_number"],
                          path=path, october_path=urlsplit(after.get("url", "")).path,
                          changed_fields=changes, matched_label=title if title_match else None,
                          october_title=after.get("title") if title_match else None))
    record = sum(bool(e["changed_fields"]) for e in edges)
    drift = sum(e["path"] != e["october_path"] for e in edges)
    labeled = [e for e in edges if e["matched_label"] is not None]
    save(args.out / "edges.json", edges)
    save(args.out / "results.json", dict(source_pairs=len(references), unmatched_pairs=len(references)-len(edges),
         eligible_pairs=len(edges), citing_pages=len({e["page"] for e in edges}), artworks=len({e["id"] for e in edges}),
         file_alerts=len(edges) if TATE[0][1] != TATE[1][1] else 0, record_alerts=record,
         path_alerts=drift, record_alerts_on_unchanged_path=record-drift,
         labeled_pairs=len(labeled), labeled_record_alerts=sum(bool(e["changed_fields"]) for e in labeled),
         labeled_title_alerts=sum(e["matched_label"] != e["october_title"] for e in labeled),
         labeled_path_or_title_alerts=sum(e["matched_label"] != e["october_title"] or
                                         e["path"] != e["october_path"] for e in labeled)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("step", choices=["collect", "evaluate"])
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, default=HERE)
    parser.add_argument("--discover", action="store_true", help="Resolve historical revisions using the cutoff date")
    args = parser.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)
    args.out.mkdir(parents=True, exist_ok=True)
    (collect if args.step == "collect" else evaluate)(args)
