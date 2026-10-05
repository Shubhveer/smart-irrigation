# EDA + training in VS Code (Windows steps; macOS/Linux are the same except where noted)

## 1. One-time setup
1. Install **Python 3.10-3.12**, **VS Code**, and the VS Code extensions **Python** and **Jupyter**.
2. In VS Code: *File > Open Folder* > the `smart-irrigation` folder. Open a terminal (**Ctrl+`**).
3. Create and activate a virtual environment:
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
   ```
   If PowerShell blocks it: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then retry.
4. Select it: **Ctrl+Shift+P** > *Python: Select Interpreter* > choose `.venv`.
5. Install packages:
   ```powershell
   pip install -r requirements.txt
   pip install -r requirements-ml.txt
   ```
   NVIDIA GPU? Install PyTorch with the command from https://pytorch.org/get-started/locally/ **before** the line above.
   Check: `python -c "import torch; print(torch.cuda.is_available())"` prints `True` when the GPU is used.

## 2. Get the PlantVillage data (about 1 GB)
**Option A, automatic (kagglehub):** create a Kaggle token (kaggle.com > Settings > API > *Create New Token*), then in the terminal:
```powershell
$env:KAGGLE_USERNAME="your_username"; $env:KAGGLE_KEY="your_key"
```
**Option B, manual:** download the zip from
https://www.kaggle.com/datasets/abdallahalidev/plantvillage-dataset , unzip it, and find the folder named **`color`**
(it contains 38 folders like `Apple___Black_rot`). You will pass that path in the steps below.

## 3. EDA
1. Open `eda/plantvillage/plantvillage_eda.ipynb`. Top right: **Select Kernel** > the `.venv` Python.
2. Using Option B? Before opening VS Code, set the path (or edit the `DATA_DIR` line in the first code cell):
   ```powershell
   $env:PV_COLOR_DIR="D:\data\plantvillage\color"
   code .
   ```
   Option A needs nothing: leave `PV_COLOR_DIR` unset and the notebook downloads the data.
3. **Run All.** It takes a few minutes. The notebook is already saved with outputs from my run; re-running overwrites them with yours.
4. Irrigation EDA: save the Kaggle CSV as `eda/data/smart_agriculture_dataset.csv` (see `eda/data/README.md`), then run `eda/smart_irrigation_eda.ipynb`.

## 4a. No GPU / small disk? Use the CPU method (recommended)
Skip the 2 GB Kaggle download entirely:
```powershell
python ml/train_cpu_transfer.py
```
- Downloads only 20,923 images (about 500 MB cache in `data/plantvillage_subset`, git-ignored) from GitHub and the pretrained weights (10-20 MB).
- Runs each image through a pretrained MobileNetV3 once, then trains the classifier in seconds.
- Measured here on ONE CPU core and 4 GB RAM: 7.3 minutes total, 97.6% test accuracy, macro-F1 0.976.
- Smaller/faster: `--per-class 300`. Already have the Kaggle `color` folder: `--data-dir "D:\data\color"`.
- It is resumable: if it stops, run the same command again.
- It writes the same files to `models/` and checks that the exported ONNX file reproduces the training-time predictions.

Sections 2 and 4 (Kaggle download and GPU fine-tuning with `ml/train_disease_model.py`) are optional if you use this method.

## 4. Train the disease model (GPU fine-tuning, optional)
**Smoke test first (2-3 minutes, poor accuracy on purpose):**
```powershell
python ml/train_disease_model.py --data-dir "D:\data\plantvillage\color" --quick
```
Omit `--data-dir` to use kagglehub. If it finishes with `ONNX check ... (OK)`, the pipeline works.

**Full training:**
```powershell
python ml/train_disease_model.py --data-dir "D:\data\plantvillage\color" --epochs 6
```
- NVIDIA GPU: roughly 10-30 minutes (estimate; depends on the card).
- CPU only: several hours for the full dataset. Use a subset instead:
  `--max-per-class 300 --epochs 5`, or train in Google Colab (free GPU) with the same script.
- Out of memory: add `--batch-size 32`.
- You can also press **F5** and pick a configuration from `.vscode/launch.json`.

**What you get in `models/`:** `disease_model.onnx`, `disease_labels.json`, `disease_model_info.json`,
`test_report.txt` (per-class precision/recall/F1) and `confusion_matrix.png`.

**Reading the result:** look at **macro-F1** and the weakest classes in `test_report.txt`, not just accuracy.
PlantVillage test scores are usually very high but optimistic (see the EDA: background colour alone predicts the class
far above chance). Judge the model on your own real leaf photos too.

## 5. Use it in the app
```powershell
python app.py
```
Open http://127.0.0.1:5000/image-check , choose *Plant*, upload a leaf photo. With the model files present the app
shows the disease name and confidence. Without them it falls back to the weak colour check.

## 6. Put it on GitHub / Render
```powershell
git checkout -b feature/disease-model
git add models/disease_model.onnx models/disease_labels.json models/disease_model_info.json
git commit -m "Add trained disease model"
git push -u origin feature/disease-model
```
The model is about 6 MB, fine for Git. Do **not** commit the dataset or `.pt` files.

## 7. Train the irrigation model on real data
Save the Kaggle CSV as `eda/data/smart_agriculture_dataset.csv`, then `python train_model.py`
(add `--with-moi` if your form collects soil moisture).

## Troubleshooting
| Problem | Fix |
|---|---|
| `RuntimeError ... spawn / multiprocessing` on Windows | Use the provided script as is (it has the required guard and defaults to `--workers 0`) |
| `torch.cuda.is_available()` is False | You installed the CPU build; reinstall PyTorch using the CUDA command from pytorch.org |
| kagglehub 401/403 | Token missing or wrong; or open the dataset page in the browser once while logged in |
| `has N sub-folders; expected the 38 class folders` | `--data-dir` must point at the `color` folder itself |
| Notebook says "Manifest does not match" | Normal for a different copy of the dataset; it scans your folder instead (adds about a minute of hashing) |
| Kernel not found in VS Code | `pip install ipykernel`, then reselect the kernel |
| Out of memory | `--batch-size 32` (or 16) |
