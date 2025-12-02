"""
Radial integration of diffraction TIFF images using a HEXRD instrument model.
"""

import os
import glob
from typing import List, Tuple

import numpy as np
import imageio.v3 as iio
import h5py
from hexrd import instrument


def load_instrument(instr_file: str) -> instrument.HEDMInstrument:
    """Load HEXRD instrument definition from an HDF5 .hexrd file."""
    with h5py.File(instr_file, "r") as h5:
        return instrument.HEDMInstrument(h5)


def compute_tth_map(instr: instrument.HEDMInstrument) -> np.ndarray:
    """
    Compute the 2θ value (in degrees) for each detector pixel.

    pixel_angles() returns (2θ, η) in radians.
    Only 2θ is used for radial integration.
    """
    det_key = list(instr.detectors.keys())[0]
    det = instr.detectors[det_key]
    tth, _ = det.pixel_angles()
    return np.degrees(tth)


def radial_integrate(
    img: np.ndarray,
    tth_map_deg: np.ndarray,
    tth_min: float,
    tth_max: float,
    nbins: int,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Accumulate pixel intensities into 2θ histogram bins (sum per bin).
    """
    img_flat = img.ravel().astype(float)
    tth_flat = tth_map_deg.ravel()

    valid = np.isfinite(tth_flat)
    img_flat = img_flat[valid]
    tth_flat = tth_flat[valid]

    edges = np.linspace(tth_min, tth_max, nbins + 1)
    sum_I, _ = np.histogram(tth_flat, bins=edges, weights=img_flat)
    tth_centers = 0.5 * (edges[:-1] + edges[1:])
    return tth_centers, sum_I


def collect_tiff_files(folder: str, pattern: str = "*.tiff,*.tif") -> List[str]:
    """
    Collect TIFF files in a folder according to a comma-separated pattern string.
    """
    folder = os.path.abspath(folder)
    patterns = [p.strip() for p in pattern.split(",")]
    files: List[str] = []
    for pat in patterns:
        files.extend(glob.glob(os.path.join(folder, pat)))
    return sorted(files)


def integrate_tiff_folder(
    instr_file: str,
    tiff_folder: str,
    tth_min: float = 0.0,
    tth_max: float = 20.0,
    nbins: int = 2000,
    pattern: str = "*.tiff,*.tif",
    output_prefix: str = "pattern",
) -> None:
    """
    Perform independent radial integration for all TIFF files in a folder.

    For each TIFF file, a corresponding text file is generated:
        <output_prefix>_<tiff_basename>.txt

    If output_prefix includes a directory component, that directory
    is created automatically.
    """
    instr_file = os.path.abspath(instr_file)
    tiff_folder = os.path.abspath(tiff_folder)

    print(f"[Diffraxia] Instrument file : {instr_file}")
    print(f"[Diffraxia] TIFF folder     : {tiff_folder}")

    tiff_files = collect_tiff_files(tiff_folder, pattern=pattern)
    if not tiff_files:
        raise RuntimeError("No TIFF files found in the specified directory.")

    print(f"[Diffraxia] Found {len(tiff_files)} TIFF file(s).")

    instr = load_instrument(instr_file)
    tth_map_deg = compute_tth_map(instr)

    test_img = iio.imread(tiff_files[0])
    if test_img.shape != tth_map_deg.shape:
        raise RuntimeError(
            f"Image shape {test_img.shape} does not match detector geometry {tth_map_deg.shape}"
        )

    # Normalize and prepare the output prefix
    # 1) If it has a directory, make it absolute
    # 2) Strip any trailing underscores so we do not get double "__"
    raw_prefix = output_prefix
    if os.path.dirname(raw_prefix):
        raw_prefix = os.path.abspath(raw_prefix)
    prefix = raw_prefix.rstrip("_")

    # Create output directory if needed
    parent_dir = os.path.dirname(prefix)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    for idx, tiff_path in enumerate(tiff_files, start=1):
        base = os.path.splitext(os.path.basename(tiff_path))[0]
        print(f"[Diffraxia] [{idx}/{len(tiff_files)}] Integrating {base} ...")

        img = iio.imread(tiff_path)

        tth, I_sum = radial_integrate(
            img,
            tth_map_deg,
            tth_min,
            tth_max,
            nbins,
        )

        outname = f"{prefix}_{base}.txt"
        np.savetxt(
            outname,
            np.column_stack([tth, I_sum]),
            header="2theta_deg\tIntensity_sum",
        )

    print("[Diffraxia] Integration completed.")
