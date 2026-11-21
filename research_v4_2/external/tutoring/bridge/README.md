# Bridge teacher-response preference replay

Macina et al. release 8,136 training pairs and 482 Bridge test pairs in the pedagogical reward model archive under CC BY 4.0. The test compares an expert improvement with an original novice teacher response. MRBench and MathDial contribute training pairs. The binary preference is derived from the source roles. Record-level scoring uses each response's text, excluding the field name and role from all blind features. The expert-source ceiling uses role as its sole input. [Paper](https://aclanthology.org/2025.emnlp-main.11/) · [Data release](https://huggingface.co/datasets/dmacjam/pedagogical-rewardmodel-data/tree/d9dc0c40bf26f417e5eb1ab87d997d48364d1f78) · [Author scoring code](https://github.com/eth-lre/mathtutorbench/tree/6faed173ec2bef55cb899b2a3e0f93982f9cb176/reward_model)

Run from the project root. The scorer verifies fixed source hashes. The verifier also compares IndoML histories to both official V3 releases and checks all saved paired point estimates. The original and secondary protocol hashes can be verified from the bridge directory. The recorded Python environment used pandas 3.0.2, PyArrow 24.0.0, NumPy 2.4.4, SciPy 1.17.1 and scikit-learn 1.8.0. The verifier requires Node.

```bash
set -eu
e=research_v4_2/external/tutoring/bridge
r=private_data/raw/mrbench
v=d9dc0c40bf26f417e5eb1ab87d997d48364d1f78
u=https://raw.githubusercontent.com/kaushal0494/UnifyingAITutorEvaluation/bbef521ddb875f2cc8a5ee798f4066965a7cfd8a
mkdir -p "$r/bridgepairs" "$r/indoml"
for n in train test; do
  curl -fsSL "https://huggingface.co/datasets/dmacjam/pedagogical-rewardmodel-data/resolve/$v/data/$n-00000-of-00001.parquet" -o "$r/bridgepairs/$n.parquet"
done
for n in trainset dev_testset testset; do
  curl -fsSL "$u/IndoML_Datathon/data/$n.json" -o "$r/indoml/$n.json"
done
for n in devset testset; do
  curl -fsSL "$u/BEA_Shared_Task_2025_Datasets/mrbench_v3_$n.json" -o "$r/mrbench_v3_$n.json"
done
work=$(mktemp -d)
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
python "$e/evaluate.py" "$r/bridgepairs" "$r/mrbench_v3_devset.json" "$work/run"
python "$e/evaluate.py" "$r/bridgepairs" "$r/mrbench_v3_devset.json" "$work/topic_run" --by-topic
for mode in run topic_run; do
  node "$e/verify.mjs" "$work/$mode" "$r/indoml" "$r/mrbench_v3_devset.json" "$r/mrbench_v3_testset.json"
  diff -r "$work/$mode" "$e/$mode"
done
```
