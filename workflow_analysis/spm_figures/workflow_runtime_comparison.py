#!/usr/bin/env python3
"""
Workflow Runtime Comparison Visualization
Compares actual runtime vs SPM-pythonruntime for different workflows
"""

import matplotlib.pyplot as plt
import numpy as np

ddmd_computation_times = {
    "openmm": 106.523076,
    "aggregate": 0.812398,
    "training": 92.242780,
    "inference": 13.141131
}

ddmd_task_runtime_data = {
    "store_conf": [
        "SSD 2n",
        "SSD 4n",
        "BeeGFS 2n",
        "BeeGFS 4n"
    ],
    "openmm": [
        111.854333,
        139.876,
        106.573333,
        108.251333
    ],
    "aggregate": [
        2.639,
        3.150667,
        3.662667,
        4.696333
    ],
    "training": [
        92.762333,
        91.248333,
        105.749,
        105.306333
    ],
    "inference": [
        14.222,
        29.59,
        14.992,
        25.287
    ]
}

pyflextrkr_computation_times = { # BeeGFS4n
    "idfea": 100.369468,
    "single": 79.791476,
    "tracks": 40.295387,
    "stats": 17.144572,
    "idfymcs": 7.665693,
    "matchpf": 15.052777,
    "robustmcs": 4.181825,
    "mapfea": 13.412377,
    "speed": 8.841863,
}

pyflextrkr_task_runtime_data = {
    "store_conf": [
        "SSD 4n",
        "SSD 8n",
        "SSD 16n",
        "TMPFS 4n",
        "TMPFS 8n",
        "TMPFS 16n",
        "BeeGFS 4n",
        "BeeGFS 8n",
        "BeeGFS 16n"
    ],
    "idfea": [
        190.5903,
        204.694,
        186.6143,
        190.847,
        195.586,
        185.6503,
        201.0003,
        192.8427,
        196.224
    ],
    "single": [
        155.742,
        132.1473,
        135.676,
        153.749,
        137.6213,
        126.7127,
        161.9157,
        157.5443,
        132.4283
    ],
    "tracks": [
        83.143,
        81.32433,
        80.23767,
        81.885,
        82.23433,
        81.39933,
        86.167,
        84.54567,
        83.716
    ],
    "stats": [
        34.99533,
        33.24933,
        31.735,
        34.74167,
        33.68767,
        32.96667,
        35.71333,
        35.92967,
        34.32633
    ],
    "idfymcs": [
        15.442,
        13.65733,
        13.22367,
        15.39467,
        14.121,
        13.34433,
        15.866,
        14.105,
        13.591
    ],
    "matchpf": [
        31.07933,
        28.099,
        27.79,
        30.66367,
        28.961,
        28.08367,
        30.619,
        28.18067,
        27.64033
    ],
    "robustmcs": [
        10.59933,
        9.287667,
        9.340667,
        10.57233,
        9.485,
        8.754,
        11.63267,
        9.027667,
        9.934667
    ],
    "mapfea": [
        27.51667,
        25.89433,
        25.14833,
        27.58767,
        26.40533,
        25.27167,
        27.59667,
        19.02167,
        27.746
    ],
    "speed": [
        17.57867,
        15.21633,
        14.56433,
        17.725,
        15.90533,
        14.76433,
        18.285,
        11.90167,
        13.59567
    ]
}

genome_computation_times = {
    "indiv": 25.061781,
    "merge": 13.923060,
    "sift": 1.048064,
    "mutation": 15.301673,
    "frequency": 104.002949,
}

genome_task_runtime_data = {
    "store_conf": [
        "SSD 2n", "SSD 5n", "SSD 10n",
        "TMPFS 2n", "TMPFS 5n", "TMPFS 10n",
        "BeeGFS 2n", "BeeGFS 5n", "BeeGFS 10n"
    ],

    "stage_in": [
        7.333333333, 6.666666667, 4.333333333,
        4.666666667, 6.666666667, 5,
        0, 0, 0
    ],

    "indiv": [
        196.6666667, 124, 106,
        187.3333333, 64.66666667, 67,
        373.3333333, 271.3333333, 294
    ],

    "merge": [
        18.66666667, 22, 18,
        14.66666667, 14.33333333, 14.66666667,
        685, 669.6666667, 419
    ],

    "sift": [
        3.666666667, 3, 3.333333333,
        4, 3, 3,
        11.66666667, 11.66666667, 12
    ],

    "mutation": [
        16.33333333, 16.33333333, 15.33333333,
        16, 15.33333333, 15.33333333,
        29, 32, 27
    ],

    "frequency": [
        132.6666667, 169, 120.3333333,
        113.3333333, 104.3333333, 120.3333333,
        179.3333333, 173.3333333, 113
    ]
}

def calculate_io_time_range(computation_times, task_runtime_data):
    """
    Calculate the I/O operation time range for each task by subtracting computation time from total runtime.
    
    Args:
        computation_times (dict): Dictionary mapping task names to their computation times
        task_runtime_data (dict): Dictionary containing 'store_conf' and task runtime data for different storage configurations
        
    Returns:
        dict: Dictionary with task names as keys and I/O time ranges as values
    """
    io_time_ranges = {}
    
    # Get storage configurations
    storage_configs = task_runtime_data["store_conf"]
    
    for task_name, comp_time in computation_times.items():
        if task_name in task_runtime_data:
            # Get runtime data for this task across all storage configurations
            task_runtimes = task_runtime_data[task_name]
            
            # Calculate I/O time for each storage configuration
            io_times = []
            for i, runtime in enumerate(task_runtimes):
                io_time = runtime - comp_time
                io_times.append(io_time)
            
            # Calculate range (min, max)
            min_io_time = min(io_times)
            max_io_time = max(io_times)
            
            io_time_ranges[task_name] = {
                "min_io_time": min_io_time,
                "max_io_time": max_io_time,
                "io_time_range": max_io_time - min_io_time,
                "computation_time": comp_time,
                "io_times_by_storage": dict(zip(storage_configs, io_times))
            }
    
    return io_time_ranges

def print_io_time_analysis(computation_times, task_runtime_data, workflow_name="Workflow"):
    """
    Print detailed I/O time analysis for a workflow.
    
    Args:
        computation_times (dict): Dictionary mapping task names to their computation times
        task_runtime_data (dict): Dictionary containing 'store_conf' and task runtime data
        workflow_name (str): Name of the workflow for display purposes
    """
    io_ranges = calculate_io_time_range(computation_times, task_runtime_data)
    
    print(f"\n" + "="*80)
    print(f"I/O TIME ANALYSIS FOR {workflow_name.upper()}")
    print("="*80)
    
    for task_name, data in io_ranges.items():
        print(f"\n{task_name.upper()}:")
        print(f"  Computation Time: {data['computation_time']:.3f} seconds")
        print(f"  I/O Time Range: {data['min_io_time']:.3f} - {data['max_io_time']:.3f} seconds")
        print(f"  I/O Time Variation: {data['io_time_range']:.3f} seconds")
        # Calculate I/O percentage of total runtime per storage: io_time / (io_time + comp_time)
        percentages = []
        for io_time in data['io_times_by_storage'].values():
            total_time = io_time + data['computation_time']
            pct = (io_time / total_time * 100) if total_time > 0 else 0.0
            percentages.append(pct)
        print(f"  I/O Time as % of Total: {min(percentages):.1f}% - {max(percentages):.1f}%")
        
        # print(f"  I/O Times by Storage Configuration:")
        # for storage, io_time in data['io_times_by_storage'].items():
        #     print(f"    {storage}: {io_time:.3f} seconds")
    
    # Summary statistics
    print(f"\n" + "-"*50)
    print("SUMMARY STATISTICS:")
    print("-"*50)
    
    all_io_times = []
    for data in io_ranges.values():
        all_io_times.extend(data['io_times_by_storage'].values())
    
    if all_io_times:
        print(f"Overall I/O Time Range: {min(all_io_times):.3f} - {max(all_io_times):.3f} seconds")
        print(f"Average I/O Time: {sum(all_io_times)/len(all_io_times):.3f} seconds")
        print(f"Standard Deviation: {np.std(all_io_times):.3f} seconds")
        
        # Calculate I/O time as percentage of total runtime
        total_comp_time = sum(computation_times.values())
        total_io_time = sum(all_io_times)
        io_percentage = (total_io_time / (total_comp_time + total_io_time)) * 100
        print(f"I/O Time as % of Total Workflow Time: {io_percentage:.1f}%")

def plot_workflow_runtime_comparison():
    """Plot comparison between actual and SPM-predicted workflow runtimes"""
    # ddmd data from excel
    # Data
    spm_runtime = {
        "workflow_name": ["1000 Genome", "PyFLRXTRKR", "DDMD"],
        "runtime_sec": [211.03, 423.16, 445.19]
    }
    

    dfman_runtime = {
        "workflow_name": ["1000 Genome", "PyFLRXTRKR", "DDMD"],
        "runtime_sec": [236.97, 494.64, 543.62]
    }
    
    
    dagp_runtime = {
        "workflow_name": ["1000 Genome", "PyFLRXTRKR", "DDMD"],
        "runtime_sec": [617.90, 474.90, 460.04]
    }
    
    faasflow_runtime = {
        "workflow_name": ["1000 Genome", "PyFLRXTRKR", "DDMD"],
        "runtime_sec": [424.12, 589.12, 445.19]
    }

    # Set up the plot
    fig, ax = plt.subplots(figsize=(10, 4))
    
    # Create bar positions
    x = np.arange(len(dfman_runtime["workflow_name"]))
    width = 0.2
    
    # Create bars - SPM first, then dagP, DFMan, FaasFlow
    bars1 = ax.bar(x - width*1.5, spm_runtime["runtime_sec"], width,
                   label='DPM', color='#ff7f0e', alpha=0.8)

    bars2 = ax.bar(x - width*0.5, dagp_runtime["runtime_sec"], width,
                   label='dagP', color='#2ca02c', alpha=0.8)
    
    bars3 = ax.bar(x + width*0.5, dfman_runtime["runtime_sec"], width, 
                   label='DFMan', color='#1f77b4', alpha=0.8)
    bars4 = ax.bar(x + width*1.5, faasflow_runtime["runtime_sec"], width,
                   label='FaasFlow', color='#d62728', alpha=0.8)
    
    # Add value labels on bars
    def add_value_labels(bars):
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{int(height)}',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3),  # 3 points vertical offset
                       textcoords="offset points",
                       ha='center', va='bottom',
                       fontsize=14, fontweight='bold')
    
    add_value_labels(bars1)
    add_value_labels(bars2)
    add_value_labels(bars3)
    add_value_labels(bars4)
    
    # Customize the plot
    ax.set_xlabel('Workflow', fontsize=18, fontweight='bold')
    ax.set_ylabel('Runtime (seconds)        ', fontsize=18, fontweight='bold')
    # ax.set_title('Workflow Time: DFMan vs SPM-Predicted vs dagP', 
    #              fontsize=20, fontweight='bold', pad=30)
    ax.set_xticks(x)
    ax.set_xticklabels(dfman_runtime["workflow_name"], fontsize=16)
    # ax.legend(fontsize=16)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    # set legend location to lower center
    ax.legend(loc='lower center', bbox_to_anchor=(0.5, 0.82), ncol=4,
              fontsize=16)

    # Set y-axis to start from 0
    # ax.set_ylim(0, max(max(dfman_runtime["runtime_sec"]), max(spm_runtime["runtime_sec"]), max(dagp_runtime["runtime_sec"])) * 1.2)
    # set y limit to 1000
    ax.set_ylim(0, 800)

    # Add speedup annotations
    # for i, (actual, spm, dagP, faasflow) in enumerate(zip(dfman_runtime["runtime_sec"], spm_runtime["runtime_sec"], dagp_runtime["runtime_sec"], faasflow_runtime["runtime_sec"])):

    for i, (spm, dagP, actual, faasflow) in enumerate(zip(spm_runtime["runtime_sec"], dagp_runtime["runtime_sec"], dfman_runtime["runtime_sec"], faasflow_runtime["runtime_sec"])):
        speedup_vs_dagP = dagP / spm
        speedup_vs_dfman = actual / spm
        speedup_vs_faasflow = faasflow / spm
        # Position at bottom of the bars
        annotate_str = ""
        if speedup_vs_dagP < 1:
            continue
        else:
            annotate_str += f'{speedup_vs_dagP:.1f}x faster than dagP\n'
        if speedup_vs_dfman < 1:
            continue
        else:
            annotate_str += f'{speedup_vs_dfman:.1f}x faster than DFMan\n'
        if speedup_vs_faasflow < 1:
            continue
        else:
            annotate_str += f'{speedup_vs_faasflow:.1f}x faster than FaasFlow'
        if annotate_str != "":
          ax.annotate(annotate_str,
                    xy=(i, 0),
                    xytext=(2, 2),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=12, fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.2", facecolor='#ffcc99', alpha=0.7))
    
    # Adjust layout and save
    plt.tight_layout()
    
    plt.savefig("workflow_runtime_comparison.pdf", format='pdf', bbox_inches='tight', dpi=300)
    # plt.savefig("workflow_runtime_comparison.png", format='png', bbox_inches='tight', dpi=300)
    plt.show()
    
    # Print summary statistics
    print("\n" + "="*60)
    print("WORKFLOW RUNTIME COMPARISON SUMMARY")
    print("="*60)
    
    total_dfman = sum(dfman_runtime["runtime_sec"])
    total_spm = sum(spm_runtime["runtime_sec"])
    total_improvement = ((total_dfman - total_spm) / total_dfman) * 100
    
    print(f"Total DFMan Runtime: {total_dfman:.2f} seconds")
    print(f"Total SPM-Predicted Runtime: {total_spm:.2f} seconds")
    print(f"Total Improvement: {total_improvement:.1f}% faster")
    print()
    
    for i, workflow in enumerate(dfman_runtime["workflow_name"]):
        actual = dfman_runtime["runtime_sec"][i]
        spm = spm_runtime["runtime_sec"][i]
        improvement = ((actual - spm) / actual) * 100
        print(f"{workflow}:")
        print(f"  DFMan: {actual:.2f} seconds")
        print(f"  SPM: {spm:.2f} seconds")
        print(f"  Improvement: {improvement:.1f}% faster")
        print()
    
    # Print SPM prediction error rates
    print("\n" + "="*60)
    print("SPM PREDICTION ERROR RATES")
    print("="*60)
    
    # Error rate data for each workflow
    error_rates = {
        "1000 Genome": {
            "total_entries": 45,
            "global_10": 0,
            "local_10": 12,
            "global_5": 2,
            "local_5": 25
        },
        "PyFLRXTRKR": {
            "total_entries": 72,
            "global_10": 0,
            "local_10": 15,
            "global_5": 0,
            "local_5": 22
        },
        "DDMD": {
            "total_entries": 12,
            "global_10": 1,
            "local_10": 4,
            "global_5": 4,
            "local_5": 6
        }
    }
    
    # Print individual workflow error rates
    for workflow, rates in error_rates.items():
        print(f"{workflow.upper()}:")
        print(f"  Error rate over 10% global margin of error: {rates['global_10']}/{rates['total_entries']}")
        print(f"  Error rate over 10% local margin of error: {rates['local_10']}/{rates['total_entries']}")
        print(f"  Error rate over 5% global margin of error: {rates['global_5']}/{rates['total_entries']}")
        print(f"  Error rate over 5% local margin of error: {rates['local_5']}/{rates['total_entries']}")
        print()
    
    # Calculate and print total error rates across all workflows
    total_entries = sum(rates['total_entries'] for rates in error_rates.values())
    total_global_10 = sum(rates['global_10'] for rates in error_rates.values())
    total_local_10 = sum(rates['local_10'] for rates in error_rates.values())
    total_global_5 = sum(rates['global_5'] for rates in error_rates.values())
    total_local_5 = sum(rates['local_5'] for rates in error_rates.values())
    
    print("TOTAL ACROSS ALL WORKFLOWS:")
    print(f"  Total entries: {total_entries}")
    print(f"  Error rate over 10% global margin of error: {total_global_10}/{total_entries} ({total_global_10/total_entries*100:.1f}%)")
    print(f"  Error rate over 10% local margin of error: {total_local_10}/{total_entries} ({total_local_10/total_entries*100:.1f}%)")
    print(f"  Error rate over 5% global margin of error: {total_global_5}/{total_entries} ({total_global_5/total_entries*100:.1f}%)")
    print(f"  Error rate over 5% local margin of error: {total_local_5}/{total_entries} ({total_local_5/total_entries*100:.1f}%)")
    print()
    
    # Calculate and print correct rates
    print("CORRECT RATES (within margin of error):")
    print(f"  Correct rate within 10% global margin: {(total_entries-total_global_10)/total_entries*100:.1f}%")
    print(f"  Correct rate within 10% local margin: {(total_entries-total_local_10)/total_entries*100:.1f}%")
    print(f"  Correct rate within 5% global margin: {(total_entries-total_global_5)/total_entries*100:.1f}%")
    print(f"  Correct rate within 5% local margin: {(total_entries-total_local_5)/total_entries*100:.1f}%")
    print()

def calculate_dagP_performance_improvement():
    """Calculate and print performance improvement compared to dagP runtime"""
    # DDMD value from excel
    # Data
    dfman_runtime = {
        "workflow_name": ["1000 Genome", "PyFLRXTRKR", "DDMD"],
        "runtime_sec": [236.97, 494.64, 543.62]
    }
    
    spm_runtime = {
        "workflow_name": ["1000 Genome", "PyFLRXTRKR", "DDMD"],
        "runtime_sec": [211.03, 423.16, 445.19]
    }
    
    dagp_runtime = {
        "workflow_name": ["1000 Genome", "PyFLRXTRKR", "DDMD"],
        "runtime_sec": [617.90, 474.90, 460.04]
    }
    
    faasflow_runtime = {
        "workflow_name": ["1000 Genome", "PyFLRXTRKR", "DDMD"],
        "runtime_sec": [424.12, 589.12, 445.19]
    }
    
    print("\n" + "="*60)
    print("PERFORMANCE IMPROVEMENT vs BASELINE RUNTIME")
    print("="*60)
    
    # Calculate total improvements
    total_dfman = sum(dfman_runtime["runtime_sec"])
    total_spm = sum(spm_runtime["runtime_sec"])
    total_dagP = sum(dagp_runtime["runtime_sec"])
    total_faasflow = sum(faasflow_runtime["runtime_sec"])
    
    dfman_improvement = ((total_dagP - total_dfman) / total_dagP) * 100
    spm_improvement = ((total_dagP - total_spm) / total_dagP) * 100
    faasflow_improvement = ((total_dagP - total_faasflow) / total_dagP) * 100
    
    print(f"Total dagP Runtime: {total_dagP:.2f} seconds")
    print(f"Total DFMan Runtime: {total_dfman:.2f} seconds")
    print(f"Total SPM-Predicted Runtime: {total_spm:.2f} seconds")
    print(f"Total FaasFlow Runtime: {total_faasflow:.2f} seconds")
    print()
    print(f"DFMan vs dagP: {dfman_improvement:.1f}% improvement ({total_dagP/total_dfman:.1f}x faster)")
    print(f"SPM vs dagP: {spm_improvement:.1f}% improvement ({total_dagP/total_spm:.1f}x faster)")
    print(f"FaasFlow vs dagP: {faasflow_improvement:.1f}% improvement ({total_dagP/total_faasflow:.1f}x faster)")
    print()
    
    # Calculate individual workflow improvements
    for i, workflow in enumerate(dfman_runtime["workflow_name"]):
        actual = dfman_runtime["runtime_sec"][i]
        spm = spm_runtime["runtime_sec"][i]
        dagP = dagp_runtime["runtime_sec"][i]
        faasflow = faasflow_runtime["runtime_sec"][i]
        
        dfman_improvement = ((dagP - actual) / dagP) * 100
        spm_improvement = ((dagP - spm) / dagP) * 100
        faasflow_improvement = ((dagP - faasflow) / dagP) * 100
        
        print(f"{workflow.upper()}:")
        print(f"  dagP: {dagP:.2f} seconds")
        print(f"  DFMan: {actual:.2f} seconds ({dfman_improvement:.1f}% improvement, {dagP/actual:.1f}x faster)")
        print(f"  SPM: {spm:.2f} seconds ({spm_improvement:.1f}% improvement, {dagP/spm:.1f}x faster)")
        print(f"  FaasFlow: {faasflow:.2f} seconds ({faasflow_improvement:.1f}% improvement, {dagP/faasflow:.1f}x faster)")
        print()

def main():
    """Main function to run the workflow runtime comparison"""
    print("Generating workflow runtime comparison plot...")
    plot_workflow_runtime_comparison()
    print("Plot saved as 'workflow_runtime_comparison.pdf' and 'workflow_runtime_comparison.png'")
    
    # Calculate and print dagP performance improvements
    calculate_dagP_performance_improvement()
    
    # Demonstrate I/O time analysis for 1000 Genomes workflow
    print("\n" + "="*80)
    print("I/O TIME ANALYSIS DEMONSTRATION")
    print("="*80)
    print_io_time_analysis(genome_computation_times, genome_task_runtime_data , "1000 Genomes")

    print_io_time_analysis(pyflextrkr_computation_times, pyflextrkr_task_runtime_data , "Pyflextrkr")
    print_io_time_analysis(ddmd_computation_times, ddmd_task_runtime_data , "DDMD")
    
    # Example of how to use with other workflows
    print("\n" + "="*80)
    print("USAGE EXAMPLE FOR OTHER WORKFLOWS")
    print("="*80)
    print("To use with other workflows, call:")
    print("  io_ranges = calculate_io_time_range(computation_times, task_runtime_data)")
    print("  print_io_time_analysis(computation_times, task_runtime_data, 'Workflow Name')")
    print("\nWhere:")
    print("  - computation_times: dict with task names as keys and computation times as values")
    print("  - task_runtime_data: dict with 'store_conf' and task runtime data for different storage configs")
    print("  - 'Workflow Name': string name for display purposes")

if __name__ == "__main__":
    main()
