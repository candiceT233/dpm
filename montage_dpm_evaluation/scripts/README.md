# scripts/ — Montage DPM evaluation scripts

All scripts read `../config.env` from the folder root, so values you set
there flow through automatically. Run them from any working directory —
each resolves its own location.

For a full walkthrough (compile Montage, fill in `config.env`, download
data, run the sweep), see `../SETUP_AGENT.md`. For per-script args and
inputs/outputs, see the "Scripts Reference" section in `../README.md`.

## `MONTAGE_PY` and `mArchiveDownload.py`

`scripts/download_data.sh` calls Montage's `mArchiveDownload.py` to fetch
2MASS FITS images from IRSA. A few things people ask:

- **It is not a standalone download.** `mArchiveDownload.py` ships *inside
  the Montage source tree* at `<Montage_src>/python/MontagePy/mArchiveDownload.py`.
  Once you have run `git clone https://github.com/Caltech-IPAC/Montage.git`
  (SETUP_AGENT.md Step 2), the file is already on disk. No `pip install`,
  no separate fetch.
- **What `MONTAGE_PY` is for.** The script does
  `sys.path.insert(0, '${MONTAGE_PY}')` and then `from mArchiveDownload
  import mArchiveDownload`. So `MONTAGE_PY` must point at the *directory*
  containing `mArchiveDownload.py` — i.e. `<Montage_src>/python/MontagePy`,
  not the file itself and not the Montage root.
- **If the file is missing under `${MONTAGE_PY}`.** Either `MONTAGE_PY` is
  pointing at the wrong directory, or your Montage clone is incomplete —
  re-clone from `https://github.com/Caltech-IPAC/Montage.git`.
