# ADIOS SST Failure Analysis

## What is ADIOS SST?

ADIOS2 SST (Sustainable Staging Transport) is an in-memory streaming engine that
couples a producer and consumer application through RDMA or TCP memory buffers.
It is the primary in-situ data transport mechanism for coupled HPC workflows.

Key properties:
- Producer and consumer must run **simultaneously** (same time window)
- Data passes through **memory buffers** (RDMA/TCP), never touching disk
- Rendezvous: consumer connects to producer via a `.sst` rendezvous file
- Backpressure: producer blocks if consumer cannot keep up

## Failure Mode 1: Time Decoupling (Always Present in Batch HPC)

**Scenario**: Stage 1 (sim) submits as Slurm job A; Stage 2 (analysis) submits as job B.

```
Timeline:
  Job A [sim]:      |====runs====| finishes
  Job B [analysis]:                  |====starts====|
  SST rendezvous:   active ------->  CLOSED
  Consumer connect:                  ERROR: cannot connect
```

**Result**: Consumer job fails immediately with `SST connection refused` or hangs
until timeout.

**Why this matters**: In production HPC workflows, it is common to submit stages
as separate batch jobs (dependency chaining with `--dependency=afterok:JOBID`).
The producer job exits — and SST's rendezvous server exits with it — before the
consumer job starts. This is not a configuration error; it is the fundamental
architectural constraint of synchronous in-memory coupling.

**DPM does not have this problem**: Files written to storage persist between job
submissions. Consumer reads files whenever it starts.

## Failure Mode 2: Memory Buffer Overflow (Large Data Config)

**Scenario**: Each producer task writes 300GB of output via SST.

SST internal buffer pipeline:
```
Producer app --> SST write() --> in-memory buffer --> RDMA --> Consumer in-memory buffer --> Consumer app
```

Buffer capacity is bounded by:
- Available node RAM minus OS, MPI library, and application footprint
- Typically 50–70% of total RAM is safely available for SST buffers
- On a 384GB node: ~200–270GB safe buffer

If producer output per node > buffer capacity:
1. SST write() blocks (backpressure) → producer stalls indefinitely
2. OR: OS OOM killer terminates producer → job fails
3. OR: SST internal overflow → data corruption or assert failure

**Threshold** (estimate): SST buffer overflow when intermediate data per node
exceeds ~60% of MEM_PER_NODE_GB.

## Failure Mode 3: Heterogeneous Application Coupling

ADIOS SST requires both applications to be compiled with the same ADIOS2 library
and to call SST-compatible open/read/write/close patterns. For workflows where:
- Producer is a Fortran simulation binary (no ADIOS2 integration)
- Consumer is a Python ML framework

...SST coupling is not possible without modifying both applications.

**DPM does not have this constraint**: Storage-based I/O is language/framework agnostic.

## Comparison Table

| Property                          | ADIOS SST     | DPM (file-based) |
|-----------------------------------|---------------|------------------|
| Requires simultaneous execution   | YES           | No               |
| Data volume limit                 | ~node memory  | Storage capacity |
| Requires ADIOS2 in both apps      | YES           | No               |
| Survives node failure mid-run     | No (data lost)| Yes (files persist)|
| Fault tolerant / restartable      | No            | Yes              |
| Works with batch job scheduling   | No            | Yes              |
| Zero-copy (optimal for small data)| YES           | No               |

## When ADIOS SST is the Right Choice

ADIOS SST is optimal when:
- Data is small enough to fit in memory (~< 50% node RAM per task)
- Producer and consumer can be launched as a single MPI job or coupled job step
- Both applications are ADIOS2-integrated
- Low latency between stages is critical

DPM is the right choice for the complementary regime, which describes the majority
of production HPC scientific workflows where tasks run as independent batch jobs
and intermediate data can be very large.
