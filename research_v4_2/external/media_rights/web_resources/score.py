"""Compare frozen Metis declarations to a separately retrieved public RDF record."""
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

base = Path(__file__).parent
rdf = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}"
edm = "{http://www.europeana.eu/schemas/edm/}"
records = json.loads((base / "sample.json").read_text())
source = next(r for r in records if r["url"].endswith("/europeana_record_rdf_tier_for_overwrite.xml"))
direct = {f["id"]: f["rights"] for f in source["files"]}
propagated = {resource: a["rights"] for a in source["aggregations"] for resource in a["resources"]}
target = json.loads((base / "labels.json").read_text())
labels = target["resources"]
if len(sys.argv) > 1:
    source_bytes = Path(sys.argv[1]).read_bytes()
    assert hashlib.sha256(source_bytes).hexdigest() == target["sha256"]
    observed = {node.get(rdf + "about"): [r.get(rdf + "resource") for r in node.findall(edm + "rights")]
                for node in ET.fromstring(source_bytes).iter(edm + "WebResource")}
    assert observed == labels
for uri, declarations in labels.items():
    print(json.dumps(dict(uri=uri, direct=direct.get(uri, []), propagated=propagated.get(uri, []),
                          published=declarations)))
