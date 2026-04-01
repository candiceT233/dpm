#!/usr/bin/env python3
"""
Calculate task time percentages for breaking down combined runtimes.

This script derives reasonable percentages for:
1. merge vs sifting (when they run together)
2. mutation vs freq (when they run together)

And provides a way to derive sequential task runtimes from parallel execution runtimes.
"""

# Individual task runtimes from workflow_runtime_comparison.py
# All storage configurations: SSD 2n, 5n, 10n, TMPFS 2n, 5n, 10n, BeeGFS 2n, 5n, 10n
individual_task_runtimes_all = {
    "merge": [
        18.66666667, 22, 18,              # SSD 2n, 5n, 10n
        14.66666667, 14.33333333, 14.66666667,  # TMPFS 2n, 5n, 10n
        685, 669.6666667, 419              # BeeGFS 2n, 5n, 10n
    ],
    "sift": [
        3.666666667, 3, 3.333333333,      # SSD 2n, 5n, 10n
        4, 3, 3,                           # TMPFS 2n, 5n, 10n
        11.66666667, 11.66666667, 12      # BeeGFS 2n, 5n, 10n
    ],
    "mutation": [
        16.33333333, 16.33333333, 15.33333333,  # SSD 2n, 5n, 10n
        16, 15.33333333, 15.33333333,     # TMPFS 2n, 5n, 10n
        29, 32, 27                         # BeeGFS 2n, 5n, 10n
    ],
    "freq": [
        132.6666667, 169, 120.3333333,    # SSD 2n, 5n, 10n
        113.3333333, 104.3333333, 120.3333333,  # TMPFS 2n, 5n, 10n
        179.3333333, 173.3333333, 113     # BeeGFS 2n, 5n, 10n
    ]
}

# Calculate averages across all storage configurations
def calculate_average_runtimes():
    """Calculate average runtimes across all storage configurations"""
    avg_runtimes = {}
    for task, times in individual_task_runtimes_all.items():
        avg_runtimes[task] = sum(times) / len(times)
    return avg_runtimes

individual_task_runtimes = calculate_average_runtimes()

# Computation times (CPU-bound, storage-independent)
computation_times = {
    "merge": 13.923060,
    "sift": 1.048064,
    "mutation": 15.301673,
    "freq": 104.002949,
}

def calculate_std_dev(values):
    """Calculate standard deviation"""
    if len(values) == 0:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return variance ** 0.5

def calculate_merge_sift_percentages():
    """
    Calculate percentage breakdown for merge vs sifting.
    
    Calculates:
    1. Best storage option (minimum runtime)
    2. Average across all storage options with std dev
    
    Returns percentages for merge and sift based on sequential execution.
    """
    # Calculate statistics across all storage configs
    merge_times_all = individual_task_runtimes_all["merge"]
    sift_times_all = individual_task_runtimes_all["sift"]
    
    # Best storage option (minimum runtime = fastest)
    merge_best = min(merge_times_all)
    sift_best = min(sift_times_all)
    
    # Average and std dev
    merge_avg = sum(merge_times_all) / len(merge_times_all)
    sift_avg = sum(sift_times_all) / len(sift_times_all)
    merge_std = calculate_std_dev(merge_times_all)
    sift_std = calculate_std_dev(sift_times_all)
    
    merge_min, merge_max = min(merge_times_all), max(merge_times_all)
    sift_min, sift_max = min(sift_times_all), max(sift_times_all)
    
    print("="*70)
    print("MERGE vs SIFTING BREAKDOWN")
    print("="*70)
    print(f"\nIndividual task runtimes:")
    print(f"  merge:  avg={merge_avg:.2f}s, std={merge_std:.2f}s, range=[{merge_min:.2f}, {merge_max:.2f}]")
    print(f"  sift:   avg={sift_avg:.2f}s, std={sift_std:.2f}s, range=[{sift_min:.2f}, {sift_max:.2f}]")
    
    # 1. Best storage option percentages
    sequential_time_best = merge_best + sift_best
    merge_pct_best = (merge_best / sequential_time_best) * 100
    sift_pct_best = (sift_best / sequential_time_best) * 100
    
    print(f"\n--- 1. BEST STORAGE OPTION (minimum runtime) ---")
    print(f"  merge:  {merge_best:.2f} seconds")
    print(f"  sift:   {sift_best:.2f} seconds")
    print(f"  Sequential time: {sequential_time_best:.2f} seconds")
    print(f"  PERCENTAGE BREAKDOWN:")
    print(f"    merge:  {merge_pct_best:.1f}%")
    print(f"    sift:   {sift_pct_best:.1f}%")
    
    # 2. Average across all storage options
    sequential_time_avg = merge_avg + sift_avg
    merge_pct_avg = (merge_avg / sequential_time_avg) * 100
    sift_pct_avg = (sift_avg / sequential_time_avg) * 100
    
    # Calculate std dev for percentages (using propagation of uncertainty approximation)
    # For percentage = (task_time / total_time) * 100
    # We approximate std dev of percentage
    merge_pct_std = (merge_std / sequential_time_avg) * 100
    sift_pct_std = (sift_std / sequential_time_avg) * 100
    
    print(f"\n--- 2. AVERAGE ACROSS ALL STORAGE OPTIONS ---")
    print(f"  merge:  {merge_avg:.2f} seconds (std={merge_std:.2f})")
    print(f"  sift:   {sift_avg:.2f} seconds (std={sift_std:.2f})")
    print(f"  Sequential time: {sequential_time_avg:.2f} seconds")
    print(f"  PERCENTAGE BREAKDOWN:")
    print(f"    merge:  {merge_pct_avg:.1f}% (std={merge_pct_std:.1f}%)")
    print(f"    sift:   {sift_pct_avg:.1f}% (std={sift_pct_std:.1f}%)")
    
    print(f"\n--- RECOMMENDATION ---")
    print(f"  Use BEST storage percentages for optimistic estimates:")
    print(f"    merge: {merge_pct_best:.1f}%, sift: {sift_pct_best:.1f}%")
    print(f"  Use AVERAGE storage percentages for typical estimates:")
    print(f"    merge: {merge_pct_avg:.1f}%, sift: {sift_pct_avg:.1f}%")
    
    return {
        'best': (merge_pct_best, sift_pct_best),
        'avg': (merge_pct_avg, sift_pct_avg),
        'avg_std': (merge_pct_std, sift_pct_std)
    }

def calculate_mutation_freq_percentages():
    """
    Calculate percentage breakdown for mutation vs freq.
    
    Calculates:
    1. Best storage option (minimum runtime)
    2. Average across all storage options with std dev
    3. Similar time assumption (50/50 split)
    
    Returns percentages for mutation and freq.
    """
    # Calculate statistics across all storage configs
    mutation_times_all = individual_task_runtimes_all["mutation"]
    freq_times_all = individual_task_runtimes_all["freq"]
    
    # Best storage option (minimum runtime = fastest)
    mutation_best = min(mutation_times_all)
    freq_best = min(freq_times_all)
    
    # Average and std dev
    mutation_avg = sum(mutation_times_all) / len(mutation_times_all)
    freq_avg = sum(freq_times_all) / len(freq_times_all)
    mutation_std = calculate_std_dev(mutation_times_all)
    freq_std = calculate_std_dev(freq_times_all)
    
    mutation_min, mutation_max = min(mutation_times_all), max(mutation_times_all)
    freq_min, freq_max = min(freq_times_all), max(freq_times_all)
    
    print("\n" + "="*70)
    print("MUTATION vs FREQ BREAKDOWN")
    print("="*70)
    print(f"\nIndividual task runtimes:")
    print(f"  mutation: avg={mutation_avg:.2f}s, std={mutation_std:.2f}s, range=[{mutation_min:.2f}, {mutation_max:.2f}]")
    print(f"  freq:     avg={freq_avg:.2f}s, std={freq_std:.2f}s, range=[{freq_min:.2f}, {freq_max:.2f}]")
    
    # 1. Best storage option percentages
    sequential_time_best = mutation_best + freq_best
    mutation_pct_best = (mutation_best / sequential_time_best) * 100
    freq_pct_best = (freq_best / sequential_time_best) * 100
    
    print(f"\n--- 1. BEST STORAGE OPTION (minimum runtime) ---")
    print(f"  mutation: {mutation_best:.2f} seconds")
    print(f"  freq:     {freq_best:.2f} seconds")
    print(f"  Sequential time: {sequential_time_best:.2f} seconds")
    print(f"  PERCENTAGE BREAKDOWN:")
    print(f"    mutation: {mutation_pct_best:.1f}%")
    print(f"    freq:     {freq_pct_best:.1f}%")
    
    # 2. Average across all storage options
    sequential_time_avg = mutation_avg + freq_avg
    mutation_pct_avg = (mutation_avg / sequential_time_avg) * 100
    freq_pct_avg = (freq_avg / sequential_time_avg) * 100
    
    # Calculate std dev for percentages
    mutation_pct_std = (mutation_std / sequential_time_avg) * 100
    freq_pct_std = (freq_std / sequential_time_avg) * 100
    
    print(f"\n--- 2. AVERAGE ACROSS ALL STORAGE OPTIONS ---")
    print(f"  mutation: {mutation_avg:.2f} seconds (std={mutation_std:.2f})")
    print(f"  freq:     {freq_avg:.2f} seconds (std={freq_std:.2f})")
    print(f"  Sequential time: {sequential_time_avg:.2f} seconds")
    print(f"  PERCENTAGE BREAKDOWN:")
    print(f"    mutation: {mutation_pct_avg:.1f}% (std={mutation_pct_std:.1f}%)")
    print(f"    freq:     {freq_pct_avg:.1f}% (std={freq_pct_std:.1f}%)")
    
    # 3. Similar time assumption (50/50 split)
    similar_time = (mutation_avg + freq_avg) / 2
    mutation_pct_similar = 50.0
    freq_pct_similar = 50.0
    
    print(f"\n--- 3. SIMILAR TIME ASSUMPTION (as you stated) ---")
    print(f"  If mutation and freq have similar task times:")
    print(f"  Average task time: {similar_time:.2f} seconds")
    print(f"  Sequential time: {similar_time * 2:.2f} seconds")
    print(f"  PERCENTAGE BREAKDOWN:")
    print(f"    mutation: {mutation_pct_similar:.1f}%")
    print(f"    freq:     {freq_pct_similar:.1f}%")
    
    print(f"\n--- RECOMMENDATION ---")
    print(f"  Option A (best storage): mutation {mutation_pct_best:.1f}%, freq {freq_pct_best:.1f}%")
    print(f"  Option B (average storage): mutation {mutation_pct_avg:.1f}%, freq {freq_pct_avg:.1f}%")
    print(f"  Option C (similar times): mutation {mutation_pct_similar:.1f}%, freq {freq_pct_similar:.1f}%")
    print(f"  → Use Option C (50/50) if your measurements show similar parallel execution times")
    
    return {
        'best': (mutation_pct_best, freq_pct_best),
        'avg': (mutation_pct_avg, freq_pct_avg),
        'avg_std': (mutation_pct_std, freq_pct_std),
        'similar': (mutation_pct_similar, freq_pct_similar)
    }

def derive_sequential_from_parallel(parallel_time, task1_pct, task2_pct):
    """
    Derive sequential task runtimes from parallel execution time.
    
    Args:
        parallel_time: Measured parallel execution time
        task1_pct: Percentage of task1 in sequential execution
        task2_pct: Percentage of task2 in sequential execution
    
    Returns:
        task1_time, task2_time, sequential_time
    """
    # If tasks run in parallel, parallel_time ≈ max(task1_time, task2_time)
    # For sequential, we need: sequential_time = task1_time + task2_time
    # And: task1_time / sequential_time = task1_pct / 100
    
    # Estimate sequential time from parallel time
    # If one task dominates (e.g., merge >> sift), parallel ≈ dominant task
    # Sequential ≈ parallel + smaller task
    # Or: sequential ≈ parallel * (1 + smaller_pct/dominant_pct)
    
    if task1_pct > task2_pct:
        # task1 dominates
        dominant_pct = task1_pct
        smaller_pct = task2_pct
    else:
        # task2 dominates
        dominant_pct = task2_pct
        smaller_pct = task1_pct
    
    # Sequential time estimation
    # If parallel ≈ dominant task, then sequential ≈ parallel * (100 / dominant_pct)
    sequential_time = parallel_time * (100.0 / dominant_pct)
    
    task1_time = sequential_time * (task1_pct / 100.0)
    task2_time = sequential_time * (task2_pct / 100.0)
    
    return task1_time, task2_time, sequential_time

def main():
    """Main function to calculate and display percentages"""
    
    # Calculate percentages
    merge_sift_results = calculate_merge_sift_percentages()
    mutation_freq_results = calculate_mutation_freq_percentages()
    
    # Extract values for examples
    merge_pct_best, sift_pct_best = merge_sift_results['best']
    merge_pct_avg, sift_pct_avg = merge_sift_results['avg']
    
    mut_pct_best, freq_pct_best = mutation_freq_results['best']
    mut_pct_avg, freq_pct_avg = mutation_freq_results['avg']
    mut_pct_similar, freq_pct_similar = mutation_freq_results['similar']
    
    # Example: Derive sequential times from parallel times
    print("\n" + "="*70)
    print("EXAMPLE: DERIVING SEQUENTIAL TIMES FROM PARALLEL TIMES")
    print("="*70)
    
    # Example 1: merge+sift parallel time (using average percentages)
    print("\nExample 1: merge+sift (using average percentages)")
    print("-" * 70)
    parallel_merge_sift = 18.0  # Example parallel time
    merge_seq, sift_seq, seq_total = derive_sequential_from_parallel(
        parallel_merge_sift, merge_pct_avg, sift_pct_avg
    )
    print(f"Given parallel time: {parallel_merge_sift:.2f} seconds")
    print(f"Derived sequential times (using average percentages):")
    print(f"  merge: {merge_seq:.2f} seconds ({merge_pct_avg:.1f}%)")
    print(f"  sift:  {sift_seq:.2f} seconds ({sift_pct_avg:.1f}%)")
    print(f"  total:  {seq_total:.2f} seconds")
    
    # Example 2: mutation+freq parallel time (similar assumption)
    print("\nExample 2: mutation+freq (assuming similar times)")
    print("-" * 70)
    parallel_mut_freq = 15.0  # Example parallel time (if similar)
    mut_seq, freq_seq, seq_total = derive_sequential_from_parallel(
        parallel_mut_freq, mut_pct_similar, freq_pct_similar
    )
    print(f"Given parallel time: {parallel_mut_freq:.2f} seconds")
    print(f"Derived sequential times (assuming 50/50 split):")
    print(f"  mutation: {mut_seq:.2f} seconds ({mut_pct_similar:.1f}%)")
    print(f"  freq:     {freq_seq:.2f} seconds ({freq_pct_similar:.1f}%)")
    print(f"  total:    {seq_total:.2f} seconds")
    
    # Summary recommendations
    print("\n" + "="*70)
    print("FINAL RECOMMENDED PERCENTAGES FOR YOUR ANALYSIS")
    print("="*70)
    print("\nFor merge+sifting breakdown:")
    print(f"  Best storage option:  merge {merge_pct_best:.1f}%, sifting {sift_pct_best:.1f}%")
    print(f"  Average (recommended): merge {merge_pct_avg:.1f}%, sifting {sift_pct_avg:.1f}%")
    print(f"  (sifting is faster, as you stated)")
    
    print("\nFor mutation+freq breakdown:")
    print(f"  Best storage option:  mutation {mut_pct_best:.1f}%, freq {freq_pct_best:.1f}%")
    print(f"  Average storage:      mutation {mut_pct_avg:.1f}%, freq {freq_pct_avg:.1f}%")
    print(f"  Similar times (recommended if parallel times are similar):")
    print(f"                       mutation {mut_pct_similar:.1f}%, freq {freq_pct_similar:.1f}%")
    print(f"\n  Recommendation: Use 'Similar times' (50/50) if your measurements")
    print(f"  show similar parallel execution times for mutation and freq.")

if __name__ == "__main__":
    main()
