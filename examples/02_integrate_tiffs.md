# Example 2: Radial Integration of TIFF Frames

This example shows how to integrate the TIFF frames produced in Example 1
using a calibrated HEXRD instrument file.

## Command

From the repository root:

    diffraxia integrate \
        --instrument examples/beamline_params.hexrd \
        --tiff-folder examples/tiff_out \
        --tth-min 0 \
        --tth-max 20 \
        --nbins 2000 \
        --output-prefix examples/text_out/hexrd_experiment_

## Output

Each input TIFF frame produces one txt file, for example:

    examples/text_out/hexrd_experiment_frame_000000.txt
    examples/text_out/hexrd_experiment_frame_000001.txt
    ...

Each TXT file contains two columns:

    2theta_deg,Intensity_sum

This corresponds to a simple 1D I(2θ) pattern obtained by radial integration
of the 2D diffraction image.
