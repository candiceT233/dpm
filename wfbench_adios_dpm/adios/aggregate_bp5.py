#!/usr/bin/env python3
"""
ADIOS2 BP5 aggregation — reads multiple consumer BP5 outputs and writes
one aggregated BP5 file. This is the ADIOS-native equivalent of the
file-based Stage 3 `cat` aggregation.

Usage:
    python aggregate_bp5.py --inputs /path/to/analysis_out_*.bp \
                            --output /path/to/aggregate.bp
"""

import adios2
import argparse
import glob
import numpy as np
import os
import sys
import time


def run_aggregate(input_pattern: str, output_path: str):
    input_files = sorted(glob.glob(input_pattern))
    print(f"[aggregate] {len(input_files)} input files, output={output_path}")

    if not input_files:
        print("[aggregate] ERROR: no input files found", file=sys.stderr)
        sys.exit(1)

    t0 = time.time()
    total_bytes = 0
    total_steps = 0

    adios_obj = adios2.Adios()
    io_out = adios_obj.declare_io("BP5_agg_writer")
    writer = io_out.open(output_path, adios2.Mode.Write)
    var_out = None

    for bp_file in input_files:
        io_in = adios_obj.declare_io(f"reader_{os.path.basename(bp_file)}")
        reader = io_in.open(bp_file, adios2.Mode.Read)

        while True:
            status = reader.begin_step(adios2.StepMode.Read, 10.0)
            if status != adios2.StepStatus.OK:
                break

            var_in = io_in.inquire_variable("data")
            if var_in is None:
                reader.end_step()
                continue

            step_count = var_in.count()
            buf = np.zeros(step_count, dtype=np.float64)
            reader.get(var_in, buf)
            reader.end_step()

            if var_out is None:
                var_out = io_out.define_variable(
                    "data", buf, list(buf.shape), [0], list(buf.shape)
                )

            writer.begin_step()
            writer.put(var_out, buf)
            writer.end_step()

            total_bytes += buf.nbytes
            total_steps += 1

        reader.close()
        io_in.remove_all_variables()

    writer.close()

    elapsed = time.time() - t0
    gb = total_bytes / (1024**3)
    bw = gb / elapsed if elapsed > 0 else 0
    print(f"[aggregate] DONE: {total_steps} steps, {gb:.2f} GB aggregated "
          f"in {elapsed:.1f}s ({bw:.2f} GB/s)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", required=True, help="Glob pattern for input BP5 files")
    parser.add_argument("--output", required=True, help="Output aggregated BP5 file")
    args = parser.parse_args()

    run_aggregate(args.inputs, args.output)


if __name__ == "__main__":
    main()
