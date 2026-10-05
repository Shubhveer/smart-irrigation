"""
Train the crop-disease classifier on PlantVillage and export it for the Flask app.

Run from the project root (works on Windows, macOS, Linux; GPU optional):

    python ml/train_disease_model.py                      # downloads data via kagglehub, trains 6 epochs
    python ml/train_disease_model.py --data-dir "D:/plantvillage/color"   # use a folder you already have
    python ml/train_disease_model.py --quick              # 2-minute smoke test (tiny subset, 1 epoch)

Outputs (in models/):
    disease_model.onnx       the model the app loads (about 6 MB)
    disease_labels.json      class names in model output order
    disease_model_info.json  test accuracy, macro-F1, settings
    test_report.txt          per-class precision/recall/F1 on the held-out test set
    confusion_matrix.png
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

IMG = 224                      # must match services/disease_service.py
MEAN, STD = [0.485, 0.456, 0.406], [0.229, 0.224, 0.225]
EXT = {".jpg", ".jpeg", ".png"}


def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data-dir", help="folder containing the 38 class folders (the 'color' folder). "
                                      "Default: download with kagglehub")
    p.add_argument("--out-dir", default="models")
    p.add_argument("--epochs", type=int, default=6)
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--workers", type=int, default=0 if sys.platform == "win32" else 2,
                   help="DataLoader workers (0 is safest on Windows)")
    p.add_argument("--max-per-class", type=int, default=0, help="limit images per class (0 = all)")
    p.add_argument("--no-pretrained", action="store_true", help="skip ImageNet weights (not recommended)")
    p.add_argument("--no-dedup", action="store_true", help="skip duplicate removal")
    p.add_argument("--quick", action="store_true", help="smoke test: 20 images/class, 1 epoch")
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


def find_data_dir(arg):
    if arg:
        d = Path(arg)
    else:
        import kagglehub
        root = Path(kagglehub.dataset_download("abdallahalidev/plantvillage-dataset"))
        d = next(p for p in root.rglob("color") if p.is_dir())
    classes = [c for c in d.iterdir() if c.is_dir()]
    if len(classes) < 30:
        sys.exit(f"{d} has {len(classes)} sub-folders; expected the 38 class folders. "
                 "Point --data-dir at the 'color' folder.")
    return d


def list_images(data_dir):
    classes = sorted(c.name for c in data_dir.iterdir() if c.is_dir())
    items = [(str(f), ci) for ci, c in enumerate(classes)
             for f in sorted((data_dir / c).iterdir()) if f.suffix.lower() in EXT]
    return classes, items


def dedup(items, classes):
    """Drop byte-identical copies, and any image that appears under two different labels."""
    hashes = [hashlib.md5(Path(p).read_bytes()).hexdigest() for p, _ in items]
    labels_by_hash = {}
    for h, (_, y) in zip(hashes, items):
        labels_by_hash.setdefault(h, set()).add(y)
    keep, used = [], set()
    for h, it in zip(hashes, items):
        if len(labels_by_hash[h]) > 1 or h in used:
            continue
        used.add(h); keep.append(it)
    print(f"Duplicates removed: {len(items) - len(keep)} (kept {len(keep):,})")
    return keep


def main():
    a = parse_args()
    if a.quick:
        a.epochs, a.max_per_class, a.no_dedup = 1, 20, True

    import torch, torch.nn as nn
    from torch.utils.data import DataLoader, Dataset
    from torchvision import models, transforms
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import classification_report, confusion_matrix, f1_score

    torch.manual_seed(a.seed); np.random.seed(a.seed)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {dev}" + ("" if dev == "cuda" else "   (CPU training is slow; see docs/TRAINING_GUIDE.md)"))

    data_dir = find_data_dir(a.data_dir)
    classes, items = list_images(data_dir)
    print(f"Found {len(items):,} images in {len(classes)} classes at {data_dir}")
    if a.max_per_class:
        rng = np.random.default_rng(a.seed); by = {}
        for it in items: by.setdefault(it[1], []).append(it)
        items = [v[i] for v in by.values() for i in rng.permutation(len(v))[:a.max_per_class]]
    if not a.no_dedup:
        print("Checking for duplicate images (about a minute on the full dataset)...")
        items = dedup(items, classes)

    y_all = np.array([y for _, y in items])
    idx = np.arange(len(items))
    tr_i, tmp_i = train_test_split(idx, test_size=0.2, stratify=y_all, random_state=a.seed)
    va_i, te_i = train_test_split(tmp_i, test_size=0.5, stratify=y_all[tmp_i], random_state=a.seed)
    print(f"Split: train {len(tr_i):,} | val {len(va_i):,} | test {len(te_i):,}")

    train_tf = transforms.Compose([
        transforms.RandomResizedCrop(IMG, scale=(0.5, 1.0)), transforms.RandomHorizontalFlip(),
        transforms.RandomVerticalFlip(), transforms.ColorJitter(0.3, 0.3, 0.3, 0.05),
        transforms.ToTensor(), transforms.Normalize(MEAN, STD)])
    eval_tf = transforms.Compose([transforms.Resize((IMG, IMG)), transforms.ToTensor(),
                                  transforms.Normalize(MEAN, STD)])

    class DS(Dataset):
        def __init__(self, ids, tf): self.ids, self.tf = ids, tf
        def __len__(self): return len(self.ids)
        def __getitem__(self, i):
            path, y = items[self.ids[i]]
            with Image.open(path) as im:
                return self.tf(im.convert("RGB")), y

    mk = lambda ids, tf, sh: DataLoader(DS(ids, tf), batch_size=a.batch_size, shuffle=sh,
                                        num_workers=a.workers, pin_memory=(dev == "cuda"))
    train_dl, val_dl, test_dl = mk(tr_i, train_tf, True), mk(va_i, eval_tf, False), mk(te_i, eval_tf, False)

    weights = None
    if not a.no_pretrained:
        weights = models.MobileNet_V3_Small_Weights.DEFAULT
    try:
        model = models.mobilenet_v3_small(weights=weights)
    except Exception as e:                      # offline / blocked download
        print(f"WARNING: could not load ImageNet weights ({e}). Training from scratch: expect lower accuracy.")
        model = models.mobilenet_v3_small(weights=None)
    model.classifier[-1] = nn.Linear(model.classifier[-1].in_features, len(classes))
    model.to(dev)

    cnt = torch.bincount(torch.tensor(y_all[tr_i]), minlength=len(classes)).float().clamp(min=1)
    loss_fn = nn.CrossEntropyLoss(weight=(cnt.sum() / (len(classes) * cnt)).to(dev))
    opt = torch.optim.AdamW(model.parameters(), lr=a.lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=a.lr, total_steps=a.epochs * len(train_dl))
    use_amp = dev == "cuda"
    scaler = torch.amp.GradScaler("cuda", enabled=use_amp)

    def predict(dl):
        model.eval(); ys, ps = [], []
        with torch.no_grad():
            for x, y in dl:
                ps.append(model(x.to(dev)).argmax(1).cpu().numpy()); ys.append(y.numpy())
        return np.concatenate(ys), np.concatenate(ps)

    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    best, ckpt, history = -1, out / "best.pt", []
    for ep in range(1, a.epochs + 1):
        t0 = time.time(); model.train(); run, n = 0.0, 0
        for bi, (x, y) in enumerate(train_dl, 1):
            x, y = x.to(dev), y.to(dev)
            opt.zero_grad(set_to_none=True)
            with torch.autocast(device_type=dev, enabled=use_amp):
                loss = loss_fn(model(x), y)
            scaler.scale(loss).backward(); scaler.step(opt); scaler.update(); sched.step()
            run += loss.item() * len(y); n += len(y)
            if bi % 50 == 0 or bi == len(train_dl):
                print(f"  epoch {ep}/{a.epochs} batch {bi}/{len(train_dl)} loss {run / n:.4f}", end="\r")
        yv, pv = predict(val_dl)
        acc, f1 = float((yv == pv).mean()), f1_score(yv, pv, average="macro")
        history.append(dict(epoch=ep, train_loss=run / n, val_acc=acc, val_macro_f1=f1))
        print(f"\nepoch {ep}: loss {run / n:.4f} | val acc {acc:.4f} | val macro-F1 {f1:.4f} | {time.time() - t0:.0f}s")
        if f1 > best:
            best = f1; torch.save(model.state_dict(), ckpt)

    model.load_state_dict(torch.load(ckpt, map_location=dev))
    yt, pt = predict(test_dl)
    t_acc, t_f1 = float((yt == pt).mean()), f1_score(yt, pt, average="macro")
    print(f"\nTEST accuracy {t_acc:.4f} | TEST macro-F1 {t_f1:.4f}")
    rep = classification_report(yt, pt, labels=range(len(classes)), target_names=classes, zero_division=0)
    (out / "test_report.txt").write_text(rep); print(rep)

    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        cm = confusion_matrix(yt, pt, labels=range(len(classes)), normalize="true")
        plt.figure(figsize=(12, 10)); plt.imshow(cm, cmap="Blues"); plt.colorbar()
        plt.xticks(range(len(classes)), classes, rotation=90, fontsize=6)
        plt.yticks(range(len(classes)), classes, fontsize=6)
        plt.title("Normalised confusion matrix (test set)"); plt.tight_layout()
        plt.savefig(out / "confusion_matrix.png", dpi=130); plt.close()
    except Exception as e:
        print("Skipped confusion matrix:", e)

    # ---- export to ONNX and verify it matches PyTorch ----
    model.cpu().eval()
    dummy = torch.randn(2, 3, IMG, IMG)
    onnx_path = out / "disease_model.onnx"
    kw = dict(input_names=["input"], output_names=["logits"], dynamic_axes={"input": {0: "batch"}}, opset_version=17)
    try:
        torch.onnx.export(model, dummy, str(onnx_path), dynamo=False, **kw)
    except TypeError:
        torch.onnx.export(model, dummy, str(onnx_path), **kw)
    (out / "disease_labels.json").write_text(json.dumps(classes, indent=2))
    try:
        import onnxruntime as ort
        s = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
        diff = np.abs(s.run(None, {"input": dummy.numpy()})[0] - model(dummy).detach().numpy()).max()
        print(f"ONNX check: max difference vs PyTorch = {diff:.2e}", "(OK)" if diff < 1e-3 else "(PROBLEM)")
    except ImportError:
        print("onnxruntime not installed; skipped the ONNX check (pip install onnxruntime)")
    (out / "disease_model_info.json").write_text(json.dumps(dict(
        test_accuracy=t_acc, test_macro_f1=float(t_f1), epochs=a.epochs, images=len(items),
        pretrained=weights is not None, history=history), indent=2))
    ckpt.unlink(missing_ok=True)
    print(f"\nDone. Files in {out.resolve()}: disease_model.onnx ({onnx_path.stat().st_size / 1e6:.1f} MB), "
          "disease_labels.json")


if __name__ == "__main__":      # required on Windows (multiprocessing)
    main()
