#!/usr/bin/env python3
"""Test script to verify runtime calculations without plotting dependencies"""

# Mock runtime_data structure
runtime_data = {
    "store_conf": [
        "SSD 2n", "SSD 5n", "SSD 10n",
        "TMPFS 2n", "TMPFS 5n", "TMPFS 10n",
        "BeeGFS 2n", "BeeGFS 5n", "BeeGFS 10n"
    ],
    "indiv+merge": [
        264.1850665, 122.3437138, 65.5730081,
        249.8208389, 116.1019967, 63.51818533,
        684.8986654, 669.5675747, 418.9379948  
    ],
    "merge+mutation": [
        5.992466667, 6.008466667, 5.627866667,
        5.8528, 5.610266667, 5.611866667,
        28.94740214, 31.9291954, 26.91863131
    ],
    "merge+freq": [
        73.14913333, 93.1739, 66.35396667,
        62.48306667, 57.52516667, 66.33796667,
        115.2571634, 111.4020991, 72.62299695
    ],
    "sift+mutation": [
        6.819533333, 6.652866667, 6.3748,
        6.7824, 6.291466667, 6.291466667,
        28.84623737, 31.8303015, 26.8568694
    ],
    "sift+freq": [
        73.9762, 93.8183, 67.1009,
        63.41266667, 58.20636667, 67.01756667,
        115.1559987, 111.3032052, 72.56123504
    ]
}

def calculate_dagp_runtime(runtime_data):
    """Calculate total workflow runtime using dagP scheduling configuration (15 nodes BeeGFS)"""
    print("\n" + "="*60)
    print("DAGP RUNTIME CALCULATION (15 nodes BeeGFS)")
    print("="*60)
    
    # 15-node configuration: measured parallel execution times
    # Percentages: merge 82.7%, sifting 17.3% (best storage)
    #              mutation 50.0%, frequency 50.0% (similar times)
    merge_sift_parallel = 2096.0  # seconds
    mut_freq_parallel = 98.0       # seconds
    
    # Derive sequential times from parallel times
    merge_pct = 82.7
    sift_pct = 17.3
    mutation_pct = 50.0
    freq_pct = 50.0
    
    # For merge+sifting: parallel ≈ merge (since merge dominates)
    merge_sift_seq = merge_sift_parallel / (merge_pct / 100.0)
    merge_time = merge_sift_seq * (merge_pct / 100.0)
    sift_time = merge_sift_seq * (sift_pct / 100.0)
    
    # For mutation+frequency: parallel ≈ both (since they're similar)
    mut_freq_seq = mut_freq_parallel * 2
    mutation_time = mut_freq_seq * (mutation_pct / 100.0)
    freq_time = mut_freq_seq * (freq_pct / 100.0)
    
    # Get individuals time from existing data (BeeGFS 10n, index 8)
    # Estimate individuals time from indiv+merge data
    beeGFS_index = runtime_data["store_conf"].index("BeeGFS 10n")
    indiv_merge_time = runtime_data["indiv+merge"][beeGFS_index]
    # Estimate: individuals time ≈ indiv+merge - merge
    # Note: indiv+merge in runtime_data is the combined time, so estimate individuals
    individuals_time = max(indiv_merge_time - merge_time, indiv_merge_time * 0.7)  # Use 70% as fallback
    
    total_time = individuals_time + merge_time + sift_time + mutation_time + freq_time
    
    print("Per-task runtime breakdown:")
    print(f"  individuals: {individuals_time:.2f} seconds")
    print(f"  merge:       {merge_time:.2f} seconds")
    print(f"  sifting:     {sift_time:.2f} seconds")
    print(f"  mutation:    {mutation_time:.2f} seconds")
    print(f"  frequency:   {freq_time:.2f} seconds")
    print(f"\nTotal workflow runtime: {total_time:.2f} seconds")
    
    return total_time

def calculate_dfman_runtime(runtime_data):
    """Calculate total workflow runtime using DFMan scheduling configuration (15 nodes)"""
    print("\n" + "="*60)
    print("DFMAN RUNTIME CALCULATION (15 nodes)")
    print("="*60)
    
    # 15-node configuration: measured parallel execution times
    # Percentages: merge 82.7%, sifting 17.3% (best storage)
    #              mutation 50.0%, frequency 50.0% (similar times)
    merge_sift_parallel = 1055.5  # seconds
    mut_freq_parallel = 98.0       # seconds
    
    # Derive sequential times from parallel times
    merge_pct = 82.7
    sift_pct = 17.3
    mutation_pct = 50.0
    freq_pct = 50.0
    
    # For merge+sifting: parallel ≈ merge (since merge dominates)
    merge_sift_seq = merge_sift_parallel / (merge_pct / 100.0)
    merge_time = merge_sift_seq * (merge_pct / 100.0)
    sift_time = merge_sift_seq * (sift_pct / 100.0)
    
    # For mutation+frequency: parallel ≈ both (since they're similar)
    mut_freq_seq = mut_freq_parallel * 2
    mutation_time = mut_freq_seq * (mutation_pct / 100.0)
    freq_time = mut_freq_seq * (freq_pct / 100.0)
    
    # Get individuals time from existing data (SSD 10n for DFMan stage 1-2, index 2)
    dfman_1to2_index = runtime_data["store_conf"].index("SSD 10n")
    indiv_merge_time = runtime_data["indiv+merge"][dfman_1to2_index]
    # Estimate: individuals time ≈ indiv+merge - merge
    individuals_time = max(indiv_merge_time - merge_time, indiv_merge_time * 0.7)  # Use 70% as fallback
    
    total_time = individuals_time + merge_time + sift_time + mutation_time + freq_time
    
    print("Per-task runtime breakdown:")
    print(f"  individuals: {individuals_time:.2f} seconds")
    print(f"  merge:       {merge_time:.2f} seconds")
    print(f"  sifting:     {sift_time:.2f} seconds")
    print(f"  mutation:    {mutation_time:.2f} seconds")
    print(f"  frequency:   {freq_time:.2f} seconds")
    print(f"\nTotal workflow runtime: {total_time:.2f} seconds")
    
    return total_time

def calculate_dpm_runtime(runtime_data):
    """Calculate total workflow runtime using DPM scheduling configuration (10 nodes SHM/TMPFS)"""
    print("\n" + "="*60)
    print("DPM RUNTIME CALCULATION (10 nodes SHM/TMPFS)")
    print("="*60)
    
    # DPM uses 10 nodes SHM (TMPFS 10n) for all tasks
    tmpfs_10n_config = "TMPFS 10n"
    tmpfs_10n_index = runtime_data["store_conf"].index(tmpfs_10n_config)
    
    # Get combined stage times from runtime_data
    indiv_merge_time = runtime_data["indiv+merge"][tmpfs_10n_index]
    merge_mutation_time = runtime_data["merge+mutation"][tmpfs_10n_index]
    merge_freq_time = runtime_data["merge+freq"][tmpfs_10n_index]
    sift_mutation_time = runtime_data["sift+mutation"][tmpfs_10n_index]
    sift_freq_time = runtime_data["sift+freq"][tmpfs_10n_index]
    
    # For per-task breakdown, split using percentages
    merge_pct = 82.7
    sift_pct = 17.3
    mutation_pct = 50.0
    freq_pct = 50.0
    
    # Estimate merge time (from merge+mutation and merge+freq, these are parallel times)
    # merge+mutation parallel ≈ merge (since merge runs before mutation)
    # merge+freq parallel ≈ merge (since merge runs before freq)
    avg_merge_parallel = (merge_mutation_time + merge_freq_time) / 2
    merge_time = avg_merge_parallel  # This is already the merge sequential time estimate
    
    # Estimate sifting time (from sift+mutation and sift+freq)
    avg_sift_parallel = (sift_mutation_time + sift_freq_time) / 2
    sift_time = avg_sift_parallel  # This is already the sift sequential time estimate
    
    # Estimate individuals time (indiv+merge contains both, subtract merge)
    individuals_time = indiv_merge_time - merge_time if indiv_merge_time > merge_time else indiv_merge_time * 0.8
    
    # mutation and frequency (50/50 split from parallel times)
    mutation_time = (merge_mutation_time + sift_mutation_time) / 2
    freq_time = (merge_freq_time + sift_freq_time) / 2
    
    # Total workflow time: sequential stages + parallel stages (max of parallel tasks)
    total_time = individuals_time + max(merge_time, sift_time) + max(mutation_time, freq_time)
    
    print(f"Using {tmpfs_10n_config} for all stages:")
    print("Per-task runtime breakdown:")
    print(f"  individuals: {individuals_time:.2f} seconds")
    print(f"  merge:       {merge_time:.2f} seconds")
    print(f"  sifting:     {sift_time:.2f} seconds")
    print(f"  mutation:    {mutation_time:.2f} seconds")
    print(f"  frequency:   {freq_time:.2f} seconds")
    print(f"\nTotal workflow runtime: {total_time:.2f} seconds")
    
    return total_time

if __name__ == "__main__":
    print("Testing Runtime Calculation Functions")
    print("="*60)
    
    dagp_runtime = calculate_dagp_runtime(runtime_data)
    dfman_runtime = calculate_dfman_runtime(runtime_data)
    dpm_runtime = calculate_dpm_runtime(runtime_data)
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"dagP (15 nodes BeeGFS):  {dagp_runtime:.2f} seconds")
    print(f"DFMan (15 nodes):        {dfman_runtime:.2f} seconds")
    print(f"DPM (10 nodes TMPFS):   {dpm_runtime:.2f} seconds")
