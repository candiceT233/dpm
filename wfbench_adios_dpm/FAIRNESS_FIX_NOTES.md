# ADIOS vs Storage Fairness Fix Notes

## Problem

The ADIOS SST consumer currently does **8x more I/O** than the IOR-based Stage 2 in `run_storage.sh`, making the comparison unfair. This explains why ADIOS SST appears 5-8x slower than BeeGFS even at small data sizes.

## Root Cause

| Aspect | IOR Stage 2 (`run_storage.sh`) | ADIOS Consumer (`consumer_task.py`) |
|--------|-------------------------------|-------------------------------------|
| Read volume | `stage2FileSizeBytes` (= stage1 × 0.125) | Full `stage1FileSizeBytes` |
| Write volume | `stage2FileSizeBytes` | Full `stage1FileSizeBytes` |
| Total I/O | 2 × stage2 size | 2 × stage1 size **(8x more)** |

The ADIOS consumer reads ALL steps from the SST producer and writes ALL of them to BP5 output. There is no data reduction. The IOR Stage 2, by contrast, only reads and writes 1/8 of the Stage 1 output.

This also cascades into Stage 3: `aggregate_bp5.py` reads 8x more BP5 data than the `cat` aggregation in `run_storage.sh`, inflating ADIOS Stage 3 time (541-950s vs 109-239s for storage).

## Suggested Fix: `consumer_task.py`

The consumer should write only a reduced subset of the data to match the storage Stage 2 behavior. Write every Nth step where N = reduction ratio (default 8, matching the 0.125 factor).

```python
# Add argument for reduction ratio
parser.add_argument("--reduction-ratio", type=int, default=8,
                    help="Write 1 out of every N steps (default: 8, matching stage2 = stage1 * 0.125)")

# In run_consumer(), change the write logic:
REDUCTION_RATIO = reduction_ratio  # from args

while True:
    status = reader.begin_step(adios2.StepMode.Read, 60.0)
    if status != adios2.StepStatus.OK:
        break

    # ... read step as before ...
    reader.get(var_in, buf)
    reader.end_step()
    steps_read += 1
    bytes_read += buf.nbytes

    # Only write every Nth step to simulate data reduction
    if steps_read % REDUCTION_RATIO == 0:
        writer.begin_step()
        writer.put(var_out, buf)
        writer.end_step()
        bytes_written += buf.nbytes

    if steps_read % 100 == 0:
        elapsed = time.time() - t0
        mb_read = bytes_read / (1024**2)
        print(f"[consumer] step {steps_read}, {mb_read:.0f} MB read, {elapsed:.1f}s")
```

## Suggested Fix: `run_adios_sst.sh`

Pass the reduction ratio to the consumer:

```bash
python3 ${ROOT_DIR}/adios/consumer_task.py \
    --input-name "${RENDEZVOUS_DIR}/sim_out_${i}" \
    --output-path "${BEEGFS_PATH}/analysis_out_${SLURM_JOB_ID}_${i}.bp" \
    --reduction-ratio 8 \
    > "${RESULTS_DIR}/consumer_${i}.log" 2>&1 &
```

## Bug Fix: `consumer_task.py` line 93-98

The `finally` block references an undefined variable `outfile`. This is leftover from an old version that wrote to a raw file. Remove these lines:

```python
# REMOVE these lines from the finally block:
        if outfile is not None:
            try:
                outfile.flush()
                os.fsync(outfile.fileno())
                outfile.close()
            except: pass
```

The consumer only uses ADIOS `writer`, not a raw file handle. The `reader.close()` and `writer.close()` in the finally block are sufficient.

## Fix Applied (2026-04-08)

All suggested fixes implemented:
1. `consumer_task.py`: added `--reduction-ratio` arg (default 8), writes every Nth step only
2. `run_adios_sst.sh`: passes `--reduction-ratio 8` to consumer
3. Removed stale `outfile` references from finally block
4. Time limit increased from 2h to 4h

### Fix history
- **v1** (jobs 639366–639376): had numpy computation, no Stage 3, 2x task allocation → invalidated
- **v2** (jobs 640636–640646): removed computation but wrote ALL data (8x more) → invalidated
- **v3** (jobs 640699–640709): 1/8 reduction ratio, BP5 output, ADIOS aggregation, 4h limit → **current**

## Verification After Fix

After fixing and re-running, verify:
1. Consumer `bytes_written` should be approximately `bytes_read / 8`
2. BP5 output files should be ~1/8 the size of the SST stream
3. Stage 3 aggregation should process ~1/8 the data, running proportionally faster
4. The total ADIOS SST time should decrease significantly

**Status:** v3 jobs running (640699–640709). Results pending.

## What IS Fair (no changes needed)

- Stage 1 data volumes match (both write `stage1FileSizeBytes`)
- Same `TASKS_PER_NODE` from `config.env`
- Same node allocations and Slurm resource requests
- Both include Stage 3 aggregation
- No extra computation in either path
- Total time measurement windows are comparable
