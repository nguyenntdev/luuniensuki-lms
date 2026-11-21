# P07 Wellcome scope feasibility

Four manifests came from the IIIF digital locations in the first ten results of [this catalogue query](https://api.wellcomecollection.org/catalogue/v2/works?availabilities=online&include=items&pageSize=10). A fifth purposively selected pamphlet supplied a contrasting manifest declaration. This convenience sample cannot estimate collection-wide frequencies.

Direct rights properties occurred on 2/5 manifests, 0/503 canvases and 0/503 painting image bodies. The two manifest URIs identify a Public Domain Mark and CC BY-NC 4.0. The pamphlet's metadata includes publication, physical description, contributors, technique, subjects and an attribution and usage note about copying. The general website terms endpoint returned HTTP 202 without usable terms text, leaving collection-wide terms unverified.

IIIF distinguishes the presentation resource carrying a rights property from the underlying object. A canvas represents a presentation space and a painting annotation associates content with it. Copying the manifest value to its images would manufacture the target. Neither item propagation nor a donor matched on object fields has an independently observed image target here. This audit measures field presence only and supplies no legal assessment or performance estimate. [IIIF Presentation 3 specification](https://iiif.io/api/presentation/3.0/#rights)

Run `taskset -c 0-11 python audit.py | diff - results.txt` from this directory. Columns give identifier, response SHA-256, manifest rights URI, canvas count, canvases with rights, image body count and bodies with rights. Raw hashes detect upstream changes.
