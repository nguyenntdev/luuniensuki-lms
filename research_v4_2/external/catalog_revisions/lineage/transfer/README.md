# P12 heading relocation across projects

On the Sphinx transfer set, flanking-anchor interpolation recovered 10 of 13 labeled renames across nine files. Nearest-anchor projection also recovered 10 and same ordinal recovered nine. Both body-token overlap and body plus context recovered all 13. The frozen superiority criterion failed. On PEP development data interpolation and nearest-anchor projection each recovered 17 of 21 across 11 files, against 19 for the strongest controls.

Equal file weighting gives interpolation 81.5% on Sphinx and 68.2% on PEPs. Each repository contributes one dependent history. Missing or ambiguous follow-up labels account for 25 Sphinx and 143 PEP censored observations. These have no adjudicated target. The parser recognizes four underline characters and adjacent explicit labels. Its conditional results do not estimate recovery of arbitrary rendered links.

From this directory, obtain complete Git histories and reproduce the saved rows. The protocol pins both Sphinx revisions and the evaluator pins the PEP revisions. Sphinx's project license is BSD-2-Clause with file-specific exceptions. The PEP extractor requires a public-domain declaration in each version.

```sh
taskset -c 0-11 git clone https://github.com/python/peps /tmp/p12-peps-repro
taskset -c 0-11 git clone --branch v8.2.3 https://github.com/sphinx-doc/sphinx /tmp/p12-sphinx-repro
taskset -c 0-11 python evaluate.py /tmp/p12-peps-repro peps > /tmp/repro-peps.json
taskset -c 0-11 python evaluate.py /tmp/p12-sphinx-repro sphinx > /tmp/repro-sphinx.json
cmp peps.json /tmp/repro-peps.json
cmp sphinx.json /tmp/repro-sphinx.json
taskset -c 0-11 python verify.py
```
