# TODO - Workflow Analysis Fixes and Improvements

This document tracks the current issues and planned improvements for the workflow analysis system.

## New TODOs

### 0. Improve workflow graph generation performance (current bottleneck)
- [ ] Optimize the workflow graph generation algorithm used by SPM
- [ ] Profile hot spots and reduce complexity and memory churn
- [ ] Add benchmarks and a flag to enable a fast path

### 1. Add Plotting for Producer-Consumer Tasks for Paper
- [ ] Add plotting functions that directly create publication-quality plots for producer-consumer task pairs, suitable for inclusion in papers.
- [ ] Integrate with workflow_spm_calculator and workflow_visualization modules.

### 2. Add Custom Filter Code for Workflow Storage Selection Plan
- [ ] Implement custom filter logic for each workflow to select the optimal storage selection plan.
- [ ] Allow per-workflow customization in storage selection and filtering.

### 3. Fix `workflow_analysis_main.py` to ensure SPM ranking and output matches the notebook (add ranking step after SPM calculation)
- [ ] Implement the fix
- [ ] Verify the fix resolves the issue
- [ ] Add regression tests to prevent future issues
- [ ] Update documentation

### 4. Fix the API to add template workflows (enable adding template workflows via the main analysis interface)
- [ ] Implement the fix
- [ ] Verify the fix resolves the issue
- [ ] Add regression tests to prevent future issues
- [ ] Update documentation

---

## Testing Strategy

For each fix:
1. Create test cases to reproduce the issue
2. Implement the fix
3. Verify the fix resolves the issue
4. Add regression tests to prevent future issues
5. Update documentation

## Notes

- All fixes should maintain backward compatibility
- Add configuration options to enable/disable new features
- Update test scripts to cover new functionality
- Ensure performance impact is minimal
- Add appropriate error handling and logging

---

## Completed Issues (Previously in Priority Order)

### A. Montage data loading and labeling fixes (2025-10-30) ✅
- [x] Correct PID extraction from blk-trace filenames
- [x] Match blk-trace files with and without ".local"
- [x] Read new blk-trace schema fields (task_name) and set `taskName`
- [x] Fill `taskName` from datalife JSON top-level key when blk-trace lacks it
- [x] Avoid overwriting non-empty `taskName` during PID mapping
- [x] Make multi-node expansion robust:
  - Skip expansion for `num_nodes_list == [1]` and `parallelism == 1`
  - Fill missing `parallelism` with 1 and compute sensible defaults

### 1. Make "Calculate Aggregate File Size per Node" Optional ✅
- [x] The aggregate file size calculation is now optional via a configuration flag.

### 2. Step 4 Transfer Rate Estimation - Zero Values Issue ✅
- [x] Fixed data alignment and zero value issues in transfer rate estimation.

### 3. Add CP/SCP Operations for Storage Type Changes ✅
- [x] System now accounts for cp/scp operations when storage changes between producer and consumer.

### 4. Add Performance Modeling for Entire Workflow Stages ✅
- [x] Added workflow-wide performance modeling, critical path analysis, and end-to-end timing predictions.

