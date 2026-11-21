# Reserved museum catalogue releases for lossless updates

This panel contains four dated snapshots per museum. Sequential pairs from an institution share a publisher, catalogue and intermediate releases. The panel therefore provides nine updates from three publisher clusters. Tate supplies the development releases. An acquisition audit checks individual tables independently and records identifiers and source-file digests. Codec evaluation remains gated on the Tate screen. [Sampling protocol](protocol.md) · [Publisher revisions and file Git hashes](revisions.json) · [Inventories and SHA-256 digests](inventory.json)

| Provider | Published table | Record key | Source and metadata terms |
|---|---|---|---|
| Cleveland Museum of Art | data.csv | id | The museum provides its collection export and links its field documentation. It releases the metadata under CC0, including identifying data for works under copyright. [Publisher documentation](https://github.com/ClevelandMuseumArt/openaccess/blob/5d23322753bbd9ebf2b072207bebba8f4d46a54b/README.md) · [CC0](https://github.com/ClevelandMuseumArt/openaccess/blob/5d23322753bbd9ebf2b072207bebba8f4d46a54b/LICENSE) |
| The Museum of Modern Art | Artworks.csv | ObjectID | MoMA supplies accessioned artwork metadata and distributes the dataset under CC0. The README requests attribution and describes image licensing separately. [Publisher documentation](https://github.com/MuseumofModernArt/collection/blob/e64a37df3107051043c4f0f2a0566792aaa0760b/README.md) · [CC0](https://github.com/MuseumofModernArt/collection/blob/e64a37df3107051043c4f0f2a0566792aaa0760b/LICENSE.md) |
| National Gallery of Art | data/objects.csv | objectid | The gallery publishes a relational catalogue under CC0. The object table and its data dictionary identify the record key. [Data dictionary](https://github.com/NationalGalleryOfArt/opendata/blob/2e432d03965ff688274ad4f83e0a2e3b9d6c5d4b/documentation/Data%20Dictionary.txt) · [Publisher documentation](https://github.com/NationalGalleryOfArt/opendata/blob/2e432d03965ff688274ad4f83e0a2e3b9d6c5d4b/README.md) · [CC0](https://github.com/NationalGalleryOfArt/opendata/blob/2e432d03965ff688274ad4f83e0a2e3b9d6c5d4b/LICENSE) |

## Structural audit

The 12 raw tables occupy 1,132,871,906 bytes. Each passed the row-width and unique-key checks. The four quarterly exports contain 68,077–68,779 Cleveland records, 160,113–160,700 MoMA records, and 143,846–146,099 National Gallery records. Three of nine consecutive intervals change the header. Cleveland changes from 45 to 46 columns and later to 48, while the National Gallery changes from 30 to 31. MoMA retains the same 30 columns throughout. The current Tate formatter requires matching schemas. Its successful Tate replay does not establish support for this full panel. The protocol requires charging schema operations in the wire before any held-out comparison and reporting every interval. No codec ran on these tables.

## Replay

Run in Bash from the repository root with Python 3.12+ and Node. Acquisition uses immutable revision URLs. Reusing the same cache rechecks every raw Git object or LFS pointer and its content. The Python audit validates field counts, header uniqueness and the presence and uniqueness of every publisher key. The separate Node verifier streams the bytes and reconstructs Git hashes and the LFS chain. A numeric identifier is treated as its original string, and the original header order is saved for any subsequent canonicalization. A single-snapshot audit does not establish semantic identity persistence across releases.

```bash
set -euo pipefail
p=research_v4_2/external/catalog_sync/external_sources
r=private_data/raw/catalogue-releases
tmp=$(mktemp -d)
(cd "$p" && sha256sum -c protocol.sha256)
taskset -c 64 python "$p/acquire.py" acquire "$r" > "$tmp/inventory.json"
cmp "$tmp/inventory.json" "$p/inventory.json"
taskset -c 64 node --check "$p/verify.mjs"
UV_THREADPOOL_SIZE=1 taskset -c 64 node --v8-pool-size=1 "$p/verify.mjs" "$r"
```

The calendar query can be reissued with `python "$p/acquire.py" discover`. The saved Git SHAs remain authoritative if an upstream branch later rewrites its history.
