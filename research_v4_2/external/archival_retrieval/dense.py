"""Embed the corpus and training queries using the published BGE CLS pooling recipe."""
import argparse
import hashlib
import json
import tarfile
from pathlib import Path

import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

FILES = {"data.tar.gz":"11c621288d41ac144d29b13b0f8503b3820b7d6e8b1f6ff24dff335c196d76be",
         "bge/model_quantized.onnx":"6c9c6101a956d62dfb5e7190c538226c0c5bb9cb27b651234b6df063ee7dbfe4",
         "bge/tokenizer.json":"d241a60d5e8f04cc1b2b3e9ef7a4921b27bf526d9f6050ab90f9267a1f9e5c66"}

def data(root):
    with tarfile.open(root/"data.tar.gz") as archive:
        def read(name):
            return [json.loads(x) for x in archive.extractfile("data/"+name+".jsonl")]
        return sorted(read("corpus"),key=lambda x:x["doc_id"]), sorted(read("claims_train"),key=lambda x:x["id"])

if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root",type=Path)
    args=parser.parse_args()
    for file, digest in FILES.items():
        assert hashlib.sha256((args.root/file).read_bytes()).hexdigest()==digest
    docs,queries=data(args.root)
    tok=Tokenizer.from_file(str(args.root/"bge/tokenizer.json"))
    tok.enable_truncation(max_length=512)
    config=ort.SessionOptions()
    config.intra_op_num_threads=4
    session=ort.InferenceSession(str(args.root/"bge/model_quantized.onnx"),config,providers=["CPUExecutionProvider"])
    text=[d["title"]+" "+" ".join(d["abstract"]) for d in docs]
    text.extend("Represent this sentence for searching relevant passages: "+q["claim"] for q in queries)
    tokens=tok.encode_batch(text)
    order=np.argsort([len(t.ids) for t in tokens],kind="stable")
    vectors=np.empty((len(order),384),np.float32)
    for start in range(0,len(order),12):
        idx=order[start:start+12]
        rows=[tokens[i].ids for i in idx]
        width=max(map(len,rows))
        ids=np.array([row+[0]*(width-len(row)) for row in rows],np.int64)
        mask=(ids!=0).astype(np.int64)
        batch={"input_ids":ids,"attention_mask":mask,"token_type_ids":np.zeros_like(ids)}
        output=session.run(None,{k.name:batch[k.name] for k in session.get_inputs()})[0][:,0]
        vectors[idx]=output/np.linalg.norm(output,axis=1,keepdims=True)
    np.save(args.root/"bge_vectors.npy",vectors)
