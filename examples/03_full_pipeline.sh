#!/bin/bash

# Example: Full pipeline from Eiger HDF5 → TIFF → 1D integration

# Paths are relative to the repository root.
INPUT_H5="examples/EIG16M_CdTe_ceria.h5"
INSTR="examples/beamline_params.hexrd"
TIFF_OUT="examples/tiff_out"
mkdir -p examples/text_out
PREFIX="examples/text_out/hexrd_experiment_"

echo "Step 1: Converting HDF5 to TIFF..."
diffraxia eiger2tiff \
    "$INPUT_H5" \
    --output-folder "$TIFF_OUT"

echo "Step 2: Performing radial integration..."
diffraxia integrate \
    --instrument "$INSTR" \
    --tiff-folder "$TIFF_OUT" \
    --tth-min 0 \
    --tth-max 20 \
    --nbins 2000 \
    --output-prefix "$PREFIX"

echo "Done. Output TXT files should be under: $PREFIX*.txt"

