#!/usr/bin/env python3
"""
ADIOS2 SST producer task for the WfBench ADIOS vs DPM experiment.

This simulates Stage 1 (sim) of the synthetic workflow, writing
output data via ADIOS2's SST engine (in-memory streaming).

Usage:
    mpirun -np <TASKS_PER_NODE> python producer_task.py \
        --output-name sim_out_0 \
        --data-size-gb <STAGE1_FILE_SIZE_GB> \
        --transfer-size-mb 1 \
        --adios-config ../adios/adios2.xml

Environment variables:
    ADIOS2_CONFIG_FILE — path to adios2.xml (overrides --adios-config)
    OUTPUT_DIR         — directory to write rendezvous .sst files
"""

import adios2
import argparse
import numpy as np
import os
import sys
import time

def run_producer(output_name: str, data_size_bytes: int, transfer_size_bytes: int,
                 adios_config: str):
    print(f"[producer] output={output_name}, data={data_size_bytes/(1024**3):.2f} GB, "
          f"transfer_size={transfer_size_bytes/(1024**2):.1f} MB")

    adios = adios2.ADIOS(adios_config)
    io = adios.DeclareIO("SST_writer")

    # Allocate one transfer-size buffer
    buf = np.zeros(transfer_size_bytes // 8, dtype=np.float64)
    n_steps = data_size_bytes // transfer_size_bytes

    var = io.DefineVariable(
        "data",
        buf,
        [n_steps * buf.shape[0]],
        [0],
        buf.shape
    )

    t0 = time.time()
    try:
        with io.Open(output_name, adios2.Mode.Write) as writer:
            for step in range(n_steps):
                buf[:] = step  # simulate computation result
                writer.BeginStep()
                writer.Put(var, buf)
                writer.EndStep()

                if step % 10 == 0:
                    elapsed = time.time() - t0
                    pct = 100.0 * step / n_steps
                    mb_written = (step + 1) * transfer_size_bytes / (1024**2)
                    print(f"[producer] step {step}/{n_steps} ({pct:.1f}%), "
                          f"{mb_written:.0f} MB written, {elapsed:.1f}s elapsed")

    except Exception as e:
        print(f"[producer] ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    elapsed = time.time() - t0
    gb_written = data_size_bytes / (1024**3)
    bw = gb_written / elapsed
    print(f"[producer] DONE: {gb_written:.2f} GB in {elapsed:.1f}s ({bw:.2f} GB/s)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-name",      required=True)
    parser.add_argument("--data-size-gb",     type=float, required=True)
    parser.add_argument("--transfer-size-mb", type=float, default=1.0)
    parser.add_argument("--adios-config",     default=os.environ.get("ADIOS2_CONFIG_FILE", "adios2.xml"))
    args = parser.parse_args()

    run_producer(
        output_name=args.output_name,
        data_size_bytes=int(args.data_size_gb * 1024**3),
        transfer_size_bytes=int(args.transfer_size_mb * 1024**2),
        adios_config=args.adios_config,
    )


if __name__ == "__main__":
    main()
