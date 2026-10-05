"""
CPU-friendly disease-model training (no GPU, no 2 GB download).

How it stays fast:
  1. Downloads only a stratified subset of PlantVillage straight from GitHub (about 300 MB for 600 images/class)
     using eda/plantvillage/plantvillage_manifest.csv.  Or pass --data-dir to use a folder you already have.
  2. Uses a pretrained MobileNetV3 backbone (ImageNet weights from timm's GitHub release) and runs every image
     through it ONCE to get a feature vector.
  3. Trains a small classifier on those vectors in about a minute, then folds it into the backbone and exports ONE
     ONNX file that the Flask app loads.

Run from the project root:
    pip install -r requirements-ml.txt
    python ml/train_cpu_transfer.py                      # default: 600 images/class
    python ml/train_cpu_transfer.py --per-class 300      # faster / smaller
    python ml/train_cpu_transfer.py --data-dir "D:/plantvillage/color"

Outputs in models/: disease_model.onnx, disease_labels.json, disease_model_info.json,
                    test_report.txt, confusion_matrix.png
"""
import argparse
import hashlib
import json
import sys
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from services.disease_service import preprocess, IMG_SIZE  # same preprocessing as the app  # noqa: E402

RAW = "https://raw.githubusercontent.com/spMohanty/PlantVillage-Dataset/master/raw/color/"
W_BASE = "https://github.com/rwightman/pytorch-image-models/releases/download/v0.1-weights/"
WEIGHT_FILES = {"mobilenetv3_large_100": "mobilenetv3_large_100_ra-f55367f5.pth",
                "mobilenetv3_small_100": "mobilenetv3_small_100_lamb-266a294c.pth"}
EXT = {".jpg", ".jpeg", ".png"}


def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--per-class", type=int, default=600, help="max images per class (default 600)")
    p.add_argument("--backbone", default="mobilenetv3_large_100", choices=list(WEIGHT_FILES))
    p.add_argument("--data-dir", help="local 'color' folder (skips the GitHub download)")
    p.add_argument("--manifest", default=str(ROOT / "eda/plantvillage/plantvillage_manifest.csv"))
    p.add_argument("--cache-dir", default=str(ROOT / "data/plantvillage_subset"))
    p.add_argument("--out-dir", default=str(ROOT / "models"))
    p.add_argument("--threads", type=int, default=0, help="CPU threads (0 = all)")
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


def build_table(a):
    """File list with labels + content hashes, de-duplicated, capped per class."""
    if a.data_dir:
        d = Path(a.data_dir)
        rows = [(c.name, f.name) for c in sorted(d.iterdir()) if c.is_dir()
                for f in c.iterdir() if f.suffix.lower() in EXT]
        df = pd.DataFrame(rows, columns=["label", "filename"])
        print(f"Hashing {len(df):,} local files...")
        df["hash"] = [hashlib.md5((d / l / f).read_bytes()).hexdigest() for l, f in zip(df.label, df.filename)]
        base = d
    else:
        df = pd.read_csv(a.manifest).rename(columns={"git_blob_sha": "hash"})
        base = Path(a.cache_dir) / "images"
    n0 = len(df)
    nlab = df.groupby("hash").label.transform("nunique")
    df = df[nlab == 1].drop_duplicates("hash")                 # drop conflicts and exact duplicates
    print(f"Duplicates/conflicts removed: {n0 - len(df)}")
    df = df.sample(frac=1, random_state=a.seed).groupby("label").head(a.per_class)
    df = df.sort_values(["label", "filename"]).reset_index(drop=True)
    df["path"] = [str(base / l / f) for l, f in zip(df.label, df.filename)]
    return df


def download(df, workers=16):
    import requests
    sess = requests.Session()

    def get(r):
        p = Path(r.path)
        if p.exists() and p.stat().st_size > 0:
            return 1
        p.parent.mkdir(parents=True, exist_ok=True)
        url = RAW + urllib.parse.quote(r.label) + "/" + urllib.parse.quote(r.filename)
        for _ in range(4):
            try:
                x = sess.get(url, timeout=30)
                if x.status_code == 200:
                    p.write_bytes(x.content); return 1
            except Exception:
                time.sleep(1)
        return 0

    todo = [r for r in df.itertuples() if not Path(r.path).exists()]
    if todo:
        print(f"Downloading {len(todo):,} images from GitHub...")
        with ThreadPoolExecutor(workers) as ex:
            ok = sum(ex.map(get, todo))
        if ok < len(todo):
            sys.exit(f"{len(todo) - ok} downloads failed; check your internet connection and re-run (it resumes).")


def load_backbone(name, cache_dir):
    import timm, torch
    wdir = Path(cache_dir) / "weights"; wdir.mkdir(parents=True, exist_ok=True)
    wf = wdir / WEIGHT_FILES[name]
    if not wf.exists():
        import requests
        print("Downloading pretrained ImageNet weights...")
        r = requests.get(W_BASE + WEIGHT_FILES[name], timeout=120); r.raise_for_status()
        wf.write_bytes(r.content)
    m = timm.create_model(name, pretrained=False, num_classes=0)
    sd = {k: v for k, v in torch.load(wf, map_location="cpu").items() if not k.startswith("classifier")}
    missing = m.load_state_dict(sd, strict=False)
    assert not missing.missing_keys, missing
    return m.eval()


def extract(backbone, paths, tag, cache_dir, gray=False, chunk=1000, batch=64):
    """Feature vectors for `paths`, cached in chunks so an interrupted run resumes."""
    import torch
    fdir = Path(cache_dir) / "features" / tag; fdir.mkdir(parents=True, exist_ok=True)
    parts = []
    for ci, start in enumerate(range(0, len(paths), chunk)):
        f = fdir / f"chunk_{ci:04d}.npy"
        if f.exists():
            parts.append(np.load(f)); continue
        out = []
        sub = paths[start:start + chunk]
        for b in range(0, len(sub), batch):
            xs = []
            for p in sub[b:b + batch]:
                if gray:
                    from PIL import Image
                    import io
                    buf = io.BytesIO(); Image.open(p).convert("L").convert("RGB").save(buf, "JPEG", quality=95); buf.seek(0)
                    xs.append(preprocess(buf))
                else:
                    xs.append(preprocess(p))
            with torch.no_grad():
                out.append(backbone(torch.from_numpy(np.concatenate(xs))).numpy())
        arr = np.concatenate(out).astype(np.float32); np.save(f, arr); parts.append(arr)
        print(f"  features {min(start + chunk, len(paths)):,}/{len(paths):,}", flush=True)
    return np.concatenate(parts)


def main():
    a = parse_args()
    import torch, torch.nn as nn
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import classification_report, confusion_matrix, f1_score
    from sklearn.model_selection import train_test_split

    if a.threads:
        torch.set_num_threads(a.threads)
    t_start = time.time()
    df = build_table(a)
    classes = sorted(df.label.unique())
    cidx = {c: i for i, c in enumerate(classes)}
    df["y"] = df.label.map(cidx)
    print(f"Using {len(df):,} images, {len(classes)} classes ({a.per_class}/class cap)")

    tr, tmp = train_test_split(df, test_size=0.2, stratify=df.y, random_state=a.seed)
    va, te = train_test_split(tmp, test_size=0.5, stratify=tmp.y, random_state=a.seed)
    print(f"Split: train {len(tr):,} | val {len(va):,} | test {len(te):,}")

    if not a.data_dir:
        download(df)
    backbone = load_backbone(a.backbone, a.cache_dir)
    tag = f"{a.backbone}_{a.per_class}_{a.seed}"

    print("Extracting features (one pass through the pretrained network)...")
    order = pd.concat([tr, va, te]).reset_index(drop=True)
    F = extract(backbone, list(order.path), tag, a.cache_dir)
    ntr, nva = len(tr), len(va)
    Xtr, Xva, Xte = F[:ntr], F[ntr:ntr + nva], F[ntr + nva:]
    ytr, yva, yte = tr.y.values, va.y.values, te.y.values
    print(f"Feature dim: {F.shape[1]}")

    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-6
    z = lambda X: (X - mu) / sd
    best = (-1, None, None)
    for C in (0.05, 0.5, 5.0):
        t0 = time.time()
        clf = LogisticRegression(C=C, class_weight="balanced", max_iter=400, n_jobs=1)
        clf.fit(z(Xtr), ytr)
        f1 = f1_score(yva, clf.predict(z(Xva)), average="macro")
        print(f"  C={C}: val macro-F1 {f1:.4f} ({time.time() - t0:.0f}s)")
        if f1 > best[0]:
            best = (f1, C, clf)
    _, C, clf = best
    print(f"Best C = {C}")

    pte = clf.predict(z(Xte))
    acc, f1 = float((pte == yte).mean()), f1_score(yte, pte, average="macro")
    print(f"\nTEST accuracy {acc:.4f} | TEST macro-F1 {f1:.4f}")
    rep = classification_report(yte, pte, labels=range(len(classes)), target_names=classes, zero_division=0)
    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    (out / "test_report.txt").write_text(rep)

    proba = clf.predict_proba(z(Xte)); conf = proba.max(1)
    thr_rows = []
    for t in (0.5, 0.6, 0.7, 0.8, 0.9):
        m = conf >= t
        thr_rows.append(dict(threshold=t, coverage=float(m.mean()), accuracy_when_answered=float((pte[m] == yte[m]).mean()) if m.any() else None))
    print("Confidence threshold trade-off:", json.dumps(thr_rows))

    # Stress test: remove colour (grayscale). Colour/background shortcuts stop working, lesions/texture remain.
    sub = te.sample(min(600, len(te)), random_state=a.seed)
    Xg = extract(backbone, list(sub.path), tag + "_gray", a.cache_dir, gray=True)
    gray_acc = float((clf.predict(z(Xg)) == sub.y.values).mean())
    colour_acc = float((clf.predict(z(Xte[[te.index.get_loc(i) for i in sub.index]])) == sub.y.values).mean())
    print(f"Stress test on {len(sub)} test images: colour {colour_acc:.4f} -> grayscale {gray_acc:.4f}")

    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        cm = confusion_matrix(yte, pte, labels=range(len(classes)), normalize="true")
        plt.figure(figsize=(12, 10)); plt.imshow(cm, cmap="Blues"); plt.colorbar()
        plt.xticks(range(len(classes)), classes, rotation=90, fontsize=6); plt.yticks(range(len(classes)), classes, fontsize=6)
        plt.title("Normalised confusion matrix (test set)"); plt.tight_layout()
        plt.savefig(out / "confusion_matrix.png", dpi=130); plt.close()
    except Exception as e:
        print("Skipped confusion matrix:", e)

    # ---- fold standardisation into the linear layer and export ONE model ----
    W = clf.coef_.astype(np.float32) / sd.astype(np.float32)
    b = clf.intercept_.astype(np.float32) - (clf.coef_ * (mu / sd)).sum(1).astype(np.float32)
    head = nn.Linear(F.shape[1], len(classes))
    head.weight.data = torch.from_numpy(W); head.bias.data = torch.from_numpy(b)
    model = nn.Sequential(backbone, head).eval()
    dummy = torch.randn(2, 3, IMG_SIZE, IMG_SIZE)
    path = out / "disease_model.onnx"
    kw = dict(input_names=["input"], output_names=["logits"], dynamic_axes={"input": {0: "batch"}}, opset_version=17)
    try:
        torch.onnx.export(model, dummy, str(path), dynamo=False, **kw)
    except TypeError:
        torch.onnx.export(model, dummy, str(path), **kw)
    (out / "disease_labels.json").write_text(json.dumps(classes, indent=2))

    # ---- verify the exported file reproduces the sklearn predictions on real images ----
    import onnxruntime as ort
    sess = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
    chk = te.sample(min(150, len(te)), random_state=1)
    onnx_pred = np.array([sess.run(None, {"input": preprocess(p)})[0].argmax() for p in chk.path])
    sk_pred = pte[[te.index.get_loc(i) for i in chk.index]]
    agree = float((onnx_pred == sk_pred).mean())
    print(f"ONNX vs training-time predictions agree on {agree:.1%} of {len(chk)} test images",
          "(OK)" if agree >= 0.98 else "(PROBLEM)")

    info = dict(backbone=a.backbone, per_class=a.per_class, images_used=int(len(df)), train=int(ntr), val=int(nva),
                test=int(len(te)), test_accuracy=acc, test_macro_f1=float(f1), best_C=C,
                grayscale_stress_accuracy=gray_acc, colour_accuracy_same_images=colour_acc,
                confidence_tradeoff=thr_rows, onnx_agreement=agree, size_mb=round(path.stat().st_size / 1e6, 1),
                train_minutes=round((time.time() - t_start) / 60, 1))
    (out / "disease_model_info.json").write_text(json.dumps(info, indent=2))
    print(f"\nDone in {info['train_minutes']} min. {path} ({info['size_mb']} MB)")


if __name__ == "__main__":
    main()
