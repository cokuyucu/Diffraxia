# Example 1: Convert Eiger HDF5 to TIFF

This example demonstrates how to convert the example Eiger16M HDF5 data
into a folder of TIFF frames.

## Command

From the repository root:

    diffraxia eiger2tiff \
        examples/EIG16M_CdTe_ceria.h5 \
        --output-folder examples/tiff_out

## Input structure expected

The HDF5 file is expected to contain difference images under:

    /entry/data/detector_1/difference/diff_000000
    /entry/data/detector_1/difference/diff_000001
    ...

## Output

TIFF files will be written as:

    examples/tiff_out/frame_000000.tiff
    examples/tiff_out/frame_000001.tiff
    ...

Each frame corresponds to one diffraction image from the original HDF5 file.

