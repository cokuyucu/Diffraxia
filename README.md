# Diffraxia

Diffraxia is a lightweight, fast, and minimal X-ray diffraction preprocessing toolkit designed for CHESS-style high-energy XRD experiments.  
It provides two core capabilities:

1. **Convert Eiger HDF5 files to TIFF frames** (supports multiple Eiger file layouts)  
2. **Perform per-frame radial integration (I vs 2θ)** using an existing HEXRD instrument file

The goal is to offer a clean, scriptable, dependency-light pipeline before advanced analysis (HEXRD GUI, GSAS-II, MAUD, Rietveld refinement, etc.).

---

## Features

✔ Supports **both Eiger file layouts** commonly found in CHESS beamlines:

- **Stream Layout A**  
  `/entry/data/detector_1/difference/diff_000000`

- **Stream Layout B**  
  `/data/<frame>/difference/<subframe index>`

✔ Fast conversion of structured/unstructured Eiger frames into standard TIFF  
✔ Simple per-frame radial integration (I vs 2θ) via HEXRD instrument geometry  
✔ Clean, minimal CLI: no GUI, no calibration steps  
✔ Ready for integration into automated data-processing pipelines  

---

## Installation

Diffraxia is not yet published on PyPI, but you can install directly from your local clone:

```bash
git clone https://github.com/cokuyucu/Diffraxia.git
cd Diffraxia
pip install -e .
```

This installs the command-line tool:

```
diffraxia
```

---

## Command Line Usage

### 1. Convert Eiger HDF5 to TIFF

```bash
diffraxia eiger2tiff \
  /path/to/eiger_raw.h5 \
  --output-folder tiff_out
```

Diffraxia automatically detects the correct Eiger layout and reads:

```
/entry/data/detector_1/difference/...        (A)
or
/data/<frame>/difference/...                 (B)
```

It writes:

```
tiff_out/frame_00000.tiff
tiff_out/frame_00001.tiff
...
```

---

### 2. Integrate TIFF frames into 1D I(2θ)

```bash
diffraxia integrate \
  --instrument my_instr.hexrd \
  --tiff-folder tiff_out \
  --tth-min 0 \
  --tth-max 20 \
  --nbins 2000 \
  --output-prefix run1_
```

Outputs (one file per TIFF frame):

```
run1_frame_00000.txt
run1_frame_00001.txt
...
```

Each file contains two columns:

```
2theta_deg   intensity
```

---

## End-to-End Example (from the `examples/` folder)

You can run a complete pipeline using the included example dataset:

```bash
./examples/03_full_pipeline.sh
```

This script:

1. Converts `examples/EIG16M_CdTe_ceria.h5` → TIFF frames  
2. Performs radial integration using `examples/beamline_params.hexrd`  
3. Writes output under:

```
examples/text_out/
```

---

## Example File Structure

```
Diffraxia/
│
├── diffraxia/
│   ├── cli.py
│   ├── eiger.py
│   ├── integrate.py
│   └── ...
│
├── examples/
│   ├── EIG16M_CdTe_ceria.h5                # Example Eiger file
│   ├── beamline_params.hexrd               # Calibrated HEXRD instrument file
│   ├── 03_full_pipeline.sh                 # End-to-end demo script
│   ├── tiff_out/                           # Generated TIFFs (created at runtime)
│   └── text_out/                           # Output integrated curves (created at runtime)
│
├── LICENSE
├── README.md
├── pyproject.toml
└── .gitignore
```

---

## Geometry and Calibration Notes

Diffraxia does **not modify or estimate geometry**.  
It relies entirely on the geometry defined in your `.hexrd` instrument file:

- detector distance  
- beam center  
- detector translations  
- detector tilts  
- pixel size, panel shape  

This means:

❗ *If peak positions do not align with expected theoretical values,*  
your HEXRD instrument file is likely not fully calibrated.

We recommend calibrating geometry in **HEXRD GUI** using a standard (CeO₂, LaB₆, etc.) before using Diffraxia for scientific interpretation.

---

## Current Limitations (v0.1)

- No masking or panel-specific dead pixel correction  
- No multi-panel detectors (only first detector in instrument file is used)  
- No peak fitting, phase fraction extraction, or Rietveld refinement  
- No PDF (pair distribution function) support  
- Integration is per-frame only (no summation/averaging)

These will be added in future releases.

---

## Planned Future Improvements

- Peak engine (Gaussian/Lorentzian/Voigt fitting)  
- Phase fraction estimation  
- Multi-detector support  
- Basic PDF computation  
- Parallelized integration  
- Optional geometry overrides from HDF5 metadata  
- Native GSAS-II `.gpx` export  


