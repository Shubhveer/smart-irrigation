# models/

Trained disease model (included):

- `disease_model.onnx`: MobileNetV3-Large backbone + 38-class head, 17 MB, loaded by `services/disease_service.py`
- `disease_labels.json`: class names in output order
- `disease_model_info.json`: metrics and settings of the training run
- `test_report.txt`, `confusion_matrix.png`: per-class results on the held-out test split

Retrain (CPU is fine, about 10 minutes): `python ml/train_cpu_transfer.py` (see `docs/TRAINING_GUIDE.md`).
If these files are missing the app falls back to a weak colour check.
