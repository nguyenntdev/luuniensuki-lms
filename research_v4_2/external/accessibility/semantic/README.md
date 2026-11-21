# P14 external caption coverage

VizWiz-Captions (Gurari et al.) provides independently collected captions for photographs taken by blind people. The authors license the work under CC BY 4.0 and identify Attention on Attention (AoA) as their top baseline. Their caption-generation evaluation excludes pre-canned severe-image-quality responses and rejected captions. The census applies that published exclusion and counts the eligible references per image. [Dataset, evaluation and license](https://vizwiz.org/tasks-and-datasets/image-captioning/) · [AoA baseline code at frozen revision](https://github.com/Yinan-Zhao/AoANet_VizWiz/tree/c5c94198b4c18f49ea20b77320e460e86f2159bb)

The challenge archive supplies caption annotations for training and validation and image metadata alone for test. An image with zero eligible references cannot contribute a reference-based caption score under this rule. These flags describe reference availability. They supply no judgments about the adequacy of existing HTML alternative text in context, educational suitability, or the effect of a description on a reader's task performance. A matched defect-detector comparison would require a labeled outcome for that task. No human labels were added and no AoA predictions were evaluated.

Reproduce from this directory with Python 3. The script checks the archive SHA-256 before reading any labels.

```sh
curl -fLsS https://vizwiz.cs.colorado.edu/VizWiz_final/caption/annotations.zip -o /tmp/p14caption.zip
taskset -c 12-23 python census.py /tmp/p14caption.zip | diff -u result.json -
```
