"""
Command-line interface for Diffraxia.
"""

import argparse

from .eiger import eiger_to_tiff
from .integrate import integrate_tiff_folder


def main():
    parser = argparse.ArgumentParser(
        prog="diffraxia",
        description="Diffraxia: diffraction data processing toolkit.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: eiger2tiff
    p_eiger = subparsers.add_parser(
        "eiger2tiff",
        help="Convert Eiger HDF5 file to TIFF frames.",
    )
    p_eiger.add_argument("h5file", help="Path to Eiger .h5 file")
    p_eiger.add_argument(
        "-g",
        "--group",
        default="data",
        help="Top-level HDF5 group containing frames (default: data)",
    )
    p_eiger.add_argument(
        "-o",
        "--output-folder",
        default="tiff_out",
        help="Output folder for TIFF images (default: tiff_out)",
    )
    p_eiger.add_argument(
        "-n",
        "--nframes",
        type=int,
        default=None,
        help="Optional limit on number of frames to convert",
    )

    # Subcommand: integrate
    p_int = subparsers.add_parser(
        "integrate",
        help="Radially integrate TIFF frames to 1D I(2θ).",
    )
    p_int.add_argument(
        "--instrument",
        required=True,
        help="Calibrated .hexrd instrument file",
    )
    p_int.add_argument(
        "--tiff-folder",
        required=True,
        help="Folder containing TIFF images",
    )
    p_int.add_argument(
        "--pattern",
        default="*.tiff,*.tif",
        help="Comma-separated filename patterns (default: *.tiff,*.tif)",
    )
    p_int.add_argument(
        "--tth-min",
        type=float,
        default=0.0,
        help="Lower bound of 2θ range (degrees)",
    )
    p_int.add_argument(
        "--tth-max",
        type=float,
        default=20.0,
        help="Upper bound of 2θ range (degrees)",
    )
    p_int.add_argument(
        "--nbins",
        type=int,
        default=2000,
        help="Number of 2θ bins (default: 2000)",
    )
    p_int.add_argument(
        "--output-prefix",
        required=True,
        help="Prefix for per-file output text files",
    )

    args = parser.parse_args()

    if args.command == "eiger2tiff":
        eiger_to_tiff(
            h5_path=args.h5file,
            group_name=args.group,
            output_folder=args.output_folder,
            nframes=args.nframes,
        )
    elif args.command == "integrate":
        integrate_tiff_folder(
            instr_file=args.instrument,
            tiff_folder=args.tiff_folder,
            tth_min=args.tth_min,
            tth_max=args.tth_max,
            nbins=args.nbins,
            pattern=args.pattern,
            output_prefix=args.output_prefix,
        )
    else:
        parser.print_help()
