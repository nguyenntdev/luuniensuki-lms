# File declaration feasibility audit

The scikit-image 0.25.2 sample image release provides a development source for distinguishing published declaration wording. Each row below joins the documentation of one fetcher to the literal file that fetcher loads. The release applies BSD-3-Clause to the source module containing this metadata under its default file rule. The audit uses the module only. [Source module](https://github.com/scikit-image/scikit-image/blob/v0.25.2/skimage/data/_fetchers.py) · [Release license](https://github.com/scikit-image/scikit-image/blob/v0.25.2/LICENSE.txt)

| Development example | Declaration in fetcher documentation | Line of declaration |
|---|---|---:|
| camera.png | Explicit CC0 by photographer | 351 |
| eagle.png | Explicit CC0 by photographer | 372 |
| astronaut.png | Public-domain release statement | 393 |
| text.png | Public-domain release statement | 581 |

These four illustrative files distinguish two forms of declaration. Both concern public-domain material. They provide no evidence of a restricted-versus-open classification result. The selection was purposive, so its class frequencies cannot estimate the distribution of the release.

## Applicability

Object-status propagation requires a separately published underlying-object status linked to each file. The four fetchers supply no such field. A majority control could count the example declarations (a 2–2 tie), but that count depends on example selection and supplies no independent evaluation. A matched control would need labeled donor files matched on independent provider and object metadata. All four examples are PNG files and their documentary provenance occurs alongside their declarations. Matching the license-bearing text or using file identity would reveal the answer. This source supplies neither a paired multi-provider evaluation nor independent object-status labels for the proposed comparison. No model was trained, no baseline accuracy was estimated, and the declarations were used solely to audit label availability. The study supports no legal permission or superiority claim.

## Reproduction

From the repository root, inspect the pinned module and its file bindings.

```bash
src=$(mktemp)
curl -fsSL https://raw.githubusercontent.com/scikit-image/scikit-image/v0.25.2/skimage/data/_fetchers.py -o "$src"
echo "7f429eaa2284e18df7b170b19f675488347ff90dfee2eb101fbced2c072f4bde  $src" | sha256sum -c -
sed -n '339,401p;573,589p' "$src"
rm "$src"
```
