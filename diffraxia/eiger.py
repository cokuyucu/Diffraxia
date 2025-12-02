"""
Helpers for converting Eiger HDF5 files to TIFF.

This module is tailored for CHESS-style Eiger outputs and currently supports
two on-disk layout variants under the top-level ``/data`` group:

1) Multi-channel layout:

   /data/<frame_index>/difference/{data, shape, dtype, elem_size, compression_type}
   /data/<frame_index>/threshold_1/{...}
   /data/<frame_index>/threshold_2/{...}

2) Flattened layout:

   /data/<frame_index>/{data, shape, dtype, elem_size, compression_type}

In both cases, we select a single payload channel (typically the
``difference`` channel) and return it as a 2D NumPy array.

For now we assume a 32-bit unsigned integer (uint32) Eiger bitstream,
which is consistent with typical CHESS EIG16M_CdTe configurations.
"""

from __future__ import annotations

import os
from typing import Iterable, Optional

import h5py
import imageio.v3 as iio
import numpy as np
from dectris.compression import decompress


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_REQUIRED_KEYS = ["data", "shape", "dtype", "elem_size", "compression_type"]


def _has_required_keys(group: h5py.Group) -> bool:
    """
    Return True if the given HDF5 group looks like an Eiger payload group,
    i.e. it contains all required metadata fields.
    """
    return all(key in group for key in _REQUIRED_KEYS)


def _select_payload_group(frame_group: h5py.Group) -> h5py.Group:
    """
    Select the HDF5 group that actually holds the pixel payload
    for a single frame.

    Supported cases:

    1) Multi-channel layout:
       The frame group contains a "difference" subgroup with the
       required keys. In this case we prefer and return that subgroup.

    2) Flattened layout:
       The frame group itself contains the required keys, in which
       case we treat the frame group as the payload.

    If neither structure is detected, a RuntimeError is raised with
    a descriptive message.
    """
    # Case 1: multi-channel layout with a "difference" subgroup
    if "difference" in frame_group and isinstance(frame_group["difference"], h5py.Group):
        diff = frame_group["difference"]
        if _has_required_keys(diff):
            return diff

    # Case 2: flattened layout with the payload directly in the frame group
    if _has_required_keys(frame_group):
        return frame_group

    # Otherwise, we do not know how to interpret this frame
    raise RuntimeError(
        "Eiger frame group does not match any supported layout. "
        "Expected either a 'difference' subgroup with "
        "{data, shape, dtype, elem_size, compression_type}, or those datasets "
        "directly under the frame group. "
        f"Available keys at this level: {list(frame_group.keys())}"
    )


def _read_scalar(dataset) -> object:
    """
    Read a scalar HDF5 dataset and convert it to a plain Python scalar.

    This helper also decodes ASCII-encoded byte strings to str.
    """
    value = dataset[()]
    # Handle bytes / np.bytes_
    if isinstance(value, (bytes, np.bytes_)):
        try:
            return value.decode("ascii", errors="ignore")
        except Exception:
            return value
    # Handle 0-dim NumPy arrays
    if isinstance(value, np.ndarray) and value.shape == ():
        return value.item()
    return value


def _read_shape(shape_ds) -> tuple[int, int]:
    """
    Read the 'shape' dataset as a (ny, nx) tuple of ints.
    """
    arr = shape_ds[()]
    arr = np.atleast_1d(arr)
    return tuple(int(x) for x in arr)


def list_frame_keys(group: h5py.Group) -> Iterable[str]:
    """
    Return sorted frame keys under a /data group.

    Eiger typically uses integer-like names ("0", "1", "2", ...),
    so we sort them numerically.
    """
    return sorted(group.keys(), key=lambda k: int(k))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_frame_array(frame_group: h5py.Group) -> np.ndarray:
    """
    Decode a single Eiger frame into a 2D NumPy array.

    The function automatically supports both:
      * multi-channel layout: /data/<i>/difference/...
      * flattened layout:     /data/<i>/{data, shape, dtype, ...}

    Notes
    -----
    * We use a fixed NumPy dtype of uint32 for the decoded array, which
      matches the typical Eiger bitstream (often reported as ``"<u4"``).
    * The 'dtype' and 'elem_size' fields from the file are used only for
      sanity checks and diagnostics, not for choosing the NumPy dtype.
    """
    payload = _select_payload_group(frame_group)

    # Read metadata and compressed data
    raw_data = payload["data"][()]
    shape = _read_shape(payload["shape"])
    dtype_meta = _read_scalar(payload["dtype"])
    elem_size = int(_read_scalar(payload["elem_size"]))
    compression_type = _read_scalar(payload["compression_type"])

    # Use a fixed uint32 representation for the Eiger bitstream.
    dtype_np = np.dtype("uint32")

    # Light sanity check: elem_size should match uint32 size.
    if elem_size != dtype_np.itemsize:
        raise RuntimeError(
            "Inconsistent Eiger frame metadata: elem_size does not match uint32. "
            f"elem_size={elem_size} byte(s), expected={dtype_np.itemsize}. "
            f"Reported dtype in file: {dtype_meta!r}"
        )

    # Decompress the raw data buffer
    buf = decompress(raw_data, compression_type, elem_size=elem_size)

    # Validate decompressed size
    expected_nbytes = int(np.prod(shape)) * dtype_np.itemsize
    if len(buf) != expected_nbytes:
        raise RuntimeError(
            "Decompressed Eiger frame has unexpected size. "
            f"len(buf)={len(buf)}, expected={expected_nbytes} for "
            f"shape={shape} and dtype={dtype_np}."
        )

    # Interpret the buffer as a 2D uint32 array
    arr = np.frombuffer(buf, dtype=dtype_np).reshape(shape)

    return arr


def eiger_to_tiff(
    h5_path: str,
    group_name: str = "data",
    output_folder: str = "tiff_out",
    nframes: Optional[int] = None,
) -> None:
    """
    Convert an Eiger HDF5 file to a sequence of TIFF images.

    Parameters
    ----------
    h5_path : str
        Path to the Eiger .h5 file.
    group_name : str, optional
        Name of the top-level group that holds frame subgroups.
        Typically "data". Default is "data".
    output_folder : str, optional
        Directory where the TIFF files will be written. It will be
        created if it does not exist. Default is "tiff_out".
    nframes : int, optional
        Maximum number of frames to convert. If None, all available
        frames under the given group are converted.
    """
    h5_path = os.path.abspath(h5_path)
    output_folder = os.path.abspath(output_folder)
    os.makedirs(output_folder, exist_ok=True)

    print(f"[Diffraxia] Opening Eiger file: {h5_path}")

    with h5py.File(h5_path, "r") as f:
        if group_name not in f:
            raise RuntimeError(f"Group {group_name!r} not found in file.")

        group = f[group_name]
        keys = list(list_frame_keys(group))

        if nframes is not None:
            keys = keys[:nframes]

        print(f"[Diffraxia] Found {len(keys)} frame(s) in group {group_name!r}.")

        for idx, k in enumerate(keys):
            frame_group = group[k]
            img = get_frame_array(frame_group)

            # Replace saturation sentinel values (max of dtype) with 0.
            # This avoids huge spikes in downstream integration.
            if np.issubdtype(img.dtype, np.integer):
                sentinel = np.iinfo(img.dtype).max
                img = np.where(img == sentinel, 0, img)

            img = np.asarray(img, dtype=np.uint32)

            out_name = os.path.join(output_folder, f"frame_{idx:05d}.tiff")
            iio.imwrite(out_name, img)

            print(f"[Diffraxia] {idx + 1}/{len(keys)} frame(s) → {out_name}")

    print(f"[Diffraxia] Done. TIFF files saved to: {output_folder}")
