#!/usr/bin/env python3
"""Create a smaller RMSX trajectory test fixture.

Run this inside the Flipbook Galaxy runtime container, where MDAnalysis is
available. The script keeps all atoms from the input topology and writes a
uniformly sampled subset of trajectory frames to a new trajectory file.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import MDAnalysis as mda
import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topology", required=True, help="Input topology/structure file.")
    parser.add_argument("--trajectory", required=True, help="Input trajectory file.")
    parser.add_argument("--output", required=True, help="Output reduced trajectory file.")
    parser.add_argument("--frames", type=int, default=30, help="Number of frames to keep.")
    parser.add_argument(
        "--xtc-precision",
        type=int,
        default=3,
        help="Coordinate precision passed to MDAnalysis when writing XTC outputs.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.frames < 1:
        raise SystemExit("--frames must be at least 1")

    topology = Path(args.topology)
    trajectory = Path(args.trajectory)
    output = Path(args.output)

    universe = mda.Universe(str(topology), str(trajectory))
    total_frames = len(universe.trajectory)
    if total_frames < 1:
        raise SystemExit(f"No frames found in {trajectory}")

    frame_count = min(args.frames, total_frames)
    frame_indices = np.linspace(0, total_frames - 1, frame_count, dtype=int)
    frame_indices = np.unique(frame_indices)

    output.parent.mkdir(parents=True, exist_ok=True)
    writer_kwargs = {"n_atoms": universe.atoms.n_atoms}
    if output.suffix.lower() == ".xtc":
        writer_kwargs["precision"] = args.xtc_precision

    with mda.Writer(str(output), **writer_kwargs) as writer:
        for frame_index in frame_indices:
            universe.trajectory[int(frame_index)]
            writer.write(universe.atoms)

    size = output.stat().st_size
    print(
        f"Wrote {output} with {len(frame_indices)} frame(s), "
        f"{universe.atoms.n_atoms} atom(s), {size} byte(s)."
    )


if __name__ == "__main__":
    main()
