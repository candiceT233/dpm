#!/usr/bin/env python3
"""
ADIOS2 SST consumer task for the WfBench ADIOS vs DPM experiment.

This simulates Stage 2 (analysis) of the synthetic workflow, reading
producer output via ADIOS2's SST engine and writing reduced output to a file.

Usage:
    python consumer_task.py \
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

    adios_obj = adios2.Adios(adios_config)
    io_in  = adios_obj.declare_io("SST_reader")
    io_out = adios_obj.declare_io("BP5_writer")

    t0 = time.time()
    steps_read = 0
    bytes_read = 0
    bytes_written = 0

    reader = None
    writer = None
    try:
        reader = io_in.open(input_name, adios2.Mode.Read)
        writer = io_out.open(output_path, adios2.Mode.Write)

        var_in = None
        var_out = None
        buf = None

        while True:
            status = reader.begin_step(adios2.StepMode.Read, 60.0)
            if status != adios2.StepStatus.OK:
                break

            if var_in is None:
                var_in = io_in.inquire_variable("data")
                step_count = var_in.count()
                buf = np.zeros(step_count, dtype=np.float64)
                if var_out is None:
                    var_out = io_out.define_variable(
                        "data", buf, list(buf.shape), [0], list(buf.shape)
                    )

            reader.get(var_in, buf)
            reader.end_step()

            # Write received data to BP5 output (ADIOS native, no computation)
            writer.begin_step()
            writer.put(var_out, buf)
            writer.end_step()
            bytes_written += buf.nbytes

            steps_read += 1
            bytes_read += buf.nbytes

            if steps_read % 100 == 0:
                elapsed = time.time() - t0
                mb_read = bytes_read / (1024**2)
                print(f"[consumer] step {steps_read}, {mb_read:.0f} MB read, {elapsed:.1f}s")

    except MemoryError as e:
        print(f"[consumer] MEMORY ERROR: {e}", file=sys.stderr)
        print(f"[consumer] Data too large for SST in-memory buffering", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"[consumer] ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if reader is not None:
            try: reader.close()
            except: pass
        if writer is not None:
            try: writer.close()
            except: pass
        if outfile is not None:
            try:
                outfile.flush()
                os.fsync(outfile.fileno())
                outfile.close()
            except: pass

    elapsed = time.time() - t0
    gb_read = bytes_read / (1024**3)
    gb_written = bytes_written / (1024**3)
    bw = gb_read / elapsed if elapsed > 0 else 0
    print(f"[consumer] DONE: {steps_read} steps, {gb_read:.2f} GB read, "
          f"{gb_written:.2f} GB written in {elapsed:.1f}s ({bw:.2f} GB/s)")


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
