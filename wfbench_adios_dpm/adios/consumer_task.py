#!/usr/bin/env python3
"""
ADIOS2 SST consumer task for the WfBench ADIOS vs DPM experiment.

This simulates Stage 2 (analysis) of the synthetic workflow, reading
producer output via ADIOS2's SST engine and writing reduced output to a file.

Usage:
    mpirun -np <TASKS_PER_NODE> python consumer_task.py \
        --input-name sim_out_0 \
        --output-path /path/to/storage/analysis_out_0.bp \
        --adios-config ../adios/adios2.xml

Failure modes captured:
    - SST OpenTimeoutSecs exceeded: producer not running → exit code 1
    - MemoryError / OOM kill: data too large → logged to results/
"""

import adios2
import argparse
import numpy as np
import os
import sys
import time

def run_consumer(input_name: str, output_path: str, adios_config: str):
    print(f"[consumer] input={input_name}, output={output_path}")

    adios = adios2.ADIOS(adios_config)
    io_in  = adios.DeclareIO("SST_reader")
    io_out = adios.DeclareIO("BP5_writer")

    t0 = time.time()
    steps_read = 0
    bytes_read = 0

    try:
        with io_in.Open(input_name, adios2.Mode.Read) as reader, \
             io_out.Open(output_path, adios2.Mode.Write) as writer:

            var_in = None
            var_out = None

            while True:
                status = reader.BeginStep(adios2.StepMode.Read, timeout_seconds=60.0)
                if status != adios2.StepStatus.OK:
                    break

                if var_in is None:
                    var_in = io_in.InquireVariable("data")
                    shape = var_in.Shape()
                    buf = np.zeros(var_in.Count(), dtype=np.float64)
                    # Output is reduced (1/8th of input steps)
                    out_buf = np.zeros(buf.shape[0] // 8, dtype=np.float64)
                    if var_out is None:
                        var_out = io_out.DefineVariable(
                            "result", out_buf, out_buf.shape, [0], out_buf.shape
                        )

                reader.Get(var_in, buf)
                reader.EndStep()

                # Simulate analysis computation (simple reduction)
                out_buf[:] = buf[:out_buf.shape[0]].mean()

                writer.BeginStep()
                writer.Put(var_out, out_buf)
                writer.EndStep()

                steps_read += 1
                bytes_read += buf.nbytes

                if steps_read % 10 == 0:
                    elapsed = time.time() - t0
                    mb_read = bytes_read / (1024**2)
                    print(f"[consumer] step {steps_read}, {mb_read:.0f} MB read, {elapsed:.1f}s")

    except adios2.error.exception as e:
        print(f"[consumer] ADIOS2 ERROR: {e}", file=sys.stderr)
        print(f"[consumer] This may indicate SST connection timeout (producer not running)", file=sys.stderr)
        sys.exit(1)
    except MemoryError as e:
        print(f"[consumer] MEMORY ERROR: {e}", file=sys.stderr)
        print(f"[consumer] Data too large for SST in-memory buffering", file=sys.stderr)
        sys.exit(2)

    elapsed = time.time() - t0
    gb_read = bytes_read / (1024**3)
    print(f"[consumer] DONE: {steps_read} steps, {gb_read:.2f} GB read in {elapsed:.1f}s "
          f"({gb_read/elapsed:.2f} GB/s)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-name",   required=True)
    parser.add_argument("--output-path",  required=True)
    parser.add_argument("--adios-config", default=os.environ.get("ADIOS2_CONFIG_FILE", "adios2.xml"))
    args = parser.parse_args()

    run_consumer(
        input_name=args.input_name,
        output_path=args.output_path,
        adios_config=args.adios_config,
    )


if __name__ == "__main__":
    main()
