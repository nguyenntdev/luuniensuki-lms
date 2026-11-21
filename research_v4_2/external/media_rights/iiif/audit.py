"""Audit direct IIIF Presentation 3 declarations on a fixed Wellcome sample."""
import hashlib
import json
from urllib.request import urlopen

for identifier in ("b18659135", "b30598977", "b19871831", "b21053613", "b18035723"):
    url = "https://iiif.wellcomecollection.org/presentation/" + identifier
    with urlopen(url, timeout=60) as response:
        raw = response.read()
    manifest = json.loads(raw)
    assert manifest["type"] == "Manifest"
    canvases = manifest["items"]
    images = [annotation["body"] for canvas in canvases for page in canvas["items"]
              for annotation in page["items"] if annotation["motivation"] == "painting"]
    assert all(image["type"] == "Image" for image in images)
    print(identifier, hashlib.sha256(raw).hexdigest(), manifest.get("rights"),
          len(canvases), sum("rights" in c for c in canvases),
          len(images), sum("rights" in i for i in images))
