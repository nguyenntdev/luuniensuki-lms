# Lossless edits inside and across cells in a versioned artwork catalogue

A publisher distributing an updated table can send a short edit against the old value of each changed cell. Reusing strings from elsewhere in the same row reduced the June–October 2014 Tate update by **40.67%** against that own-cell codec. The same addition enlarged the January–June update by **24 bytes**. The own-cell codec already captured much of the saving from aligning objects and fields. The cross-column method cleared the 5% development margin against every tested control on **one of two** intervals. Both informed development, so the results provide no held-out estimate.

| Complete update bytes | January–June | June–October |
|---|---:|---:|
| Whole target, zstd -19 | 2,209,789 | 2,225,318 |
| zstd reference patch | 141,196 | 86,810 |
| xdelta3 -9 | 85,418 | 84,298 |
| bsdiff 4.3 | 71,755 | 117,266 |
| HDiffPatch 5.1.3, memory mode and LZMA2 level 9 | 65,637 | 70,840 |
| Row assignments | 186,220 | 83,090 |
| Column assignments | 169,508 | 67,909 |
| Prior column rule patch | 167,887 | 67,722 |
| Own-cell edits, XZ | 48,828 | 55,416 |
| Cross-column edits, XZ | **48,852** | **32,876** |

Each target contains 69,201 artworks. The January–June update includes 126 insertions. Four custom wires were decoded separately by Python and JavaScript, then compared with every target key and field. The binary comparators were decoded with their respective patchers and compared byte for byte. xdelta3 embeds filenames in its application header, so the evaluator fixes these to `base` and `target`. Compressed sizes include the complete header, operation selectors, changes, inserted records and removals. CPU and memory were outside this endpoint. [Design](design.md) · [Core measurements](result.json) · [HDiffPatch replay](hdiff.json) · [Original six-codec analysis](../development.json)

The observed edits suggest a reason for the asymmetry. January–June includes title punctuation changes and shortening of existing URLs. Both preserve substantial parts of their own old string. June–October includes swaps of height and width, where another old field can predict the exact target. The codec also supports reusing text from earlier reconstructed columns. These examples suggest mechanisms. Attributing an exact number of bytes to each transformation would require separate ablations.

## Prior work

DataDiff studies interpretable summaries of transformations. Explain-Da-V studies data transformations that explain dataset changes and evaluates explanation quality. The operational endpoint here is total transmitted bytes for exact reconstruction with a known base. Representing edits using rules or related fields is established prior work. This experiment compared executable patchers and matched implementations. It supplies no direct comparison to either explanation system and establishes no priority for transformation-based deltas. [DataDiff, SIGMOD 2018](https://doi.org/10.1145/3183713.3193564) · [Explain-Da-V, PVLDB](https://doi.org/10.14778/3583140.3583169)

Colin Percival's bsdiff uses suffix sorting and byte differences. HDiffPatch offers several matching and compression modes. We used its in-memory text setting with match score 6, LZMA2 level 9 and a single worker. HDiffPatch produced the smallest general-purpose binary patches among the tested configurations in both intervals. [bsdiff author implementation](https://www.daemonology.net/bsdiff/) · [HDiffPatch release](https://github.com/sisong/HDiffPatch/releases/tag/v5.1.3)

## Reproduction

Use Bash, Python 3.12 with liblzma, Node, xz and zstd. Acquire the three pinned Tate CSVs as `jan.csv`, `jun.csv`, and `oct.csv` using the linked source commands. The Tate release provides collection metadata. The evaluation reproduces a canonical table of strings and stable IDs. Original row order and CSV quoting are outside the endpoint. [Tate commits and acquisition commands](../../catalog_revisions/manuscript.md#reproduction) · [Tate source and terms](https://github.com/tategallery/collection)

From the repository root, set `data` to the directory containing the three CSV files. On Ubuntu 24.04 amd64 the following installs the tools in a temporary directory. Both Python evaluators are single-process. The HDiff command uses a single worker.

```bash
set -euo pipefail
p=$PWD/research_v4_2/external/catalog_sync/relational
tools=$(mktemp -d)
(
  cd "$tools"
  apt-get download bsdiff=4.3-23 xdelta3=3.0.11-dfsg-1.2
  sha256sum -c <<'SUMS'
74359bc075366cd244dfdfa64b2cb1fcef0ecd00da45ff4a699349d09a6970d6  bsdiff_4.3-23_amd64.deb
211bf0fe07f1bb95870dd6da981f56c2e17237286b261f1fe2d77d34ff1f106e  xdelta3_3.0.11-dfsg-1.2_amd64.deb
SUMS
  for pkg in *.deb; do dpkg-deb -x "$pkg" local; done
  curl -fsSL https://github.com/sisong/HDiffPatch/releases/download/v5.1.3/hdiffpatch_v5.1.3_bin_linux64.zip -o hdiff.zip
  echo '628963bf2ee9108a97260fa5eef44acd9ec94369b76090a957c9182b3abbb558  hdiff.zip' | sha256sum -c -
  unzip -q hdiff.zip
  chmod u+x linux64/{hdiffz,hpatchz}
)
inputs=("$data/jan.csv" "$data/jun.csv" "$data/oct.csv")
python "$p/../screen.py" "$tools/local/usr/bin/xdelta3" "${inputs[@]}" "$tools/first.json"
cmp "$tools/first.json" "$p/../development.json"
python "$p/codec.py" "$tools/local/usr/bin" "${inputs[@]}" "$tools/second.json"
cmp "$tools/second.json" "$p/result.json"
python "$p/binary_check.py" "$tools/linux64" "${inputs[@]}" "$tools/hdiff.json"
cmp "$tools/hdiff.json" "$p/hdiff.json"
```
