#!/usr/bin/env python3
"""
SPM Figures for 1000 Genomes Workflow Analysis
Converted from Jupyter notebook to Python script

This script analyzes SPM (Storage Performance Model) results for 1000 Genomes workflow
and generates visualizations for rank errors and time deviations.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import json
import os

# Color palette for consistent visualization
colors = [
    '#1f77b4',  # blue
    '#ff7f0e',  # orange
    '#2ca02c',  # green
    '#d62728',  # red
    '#9467bd',  # purple
    '#8c564b',  # brown
    '#e377c2',  # pink
    '#7f7f7f',  # gray
    '#bcbd22',  # yellow-green
    '#17becf'   # cyan
]

def create_runtime_data():
    """Create runtime data dictionary for workflow stages"""
    # runtime_data = {
    #     "store_conf": [
    #         "SSD 2n", "SSD 5n", "SSD 10n", 
    #         "TMPFS 2n", "TMPFS 5n", "TMPFS 10n", 
    #         "BeeGFS 2n", "BeeGFS 5n", "BeeGFS 10n"
    #     ],
    #     "indiv+merge": [
    #         264.1850665, 122.3437138, 65.5730081,
    #         249.8208389, 116.1019967, 63.51818533,
    #         684.8986654, 669.5675747, 418.9379948  
    #     ],
    #     "merge+mutation": [
    #         5.992466667, 6.008466667, 5.627866667,
    #         5.8528, 5.610266667, 5.611866667,
    #         28.94740214, 31.9291954, 26.91863131
    #     ],
    #     "merge+freq": [
    #         73.14913333, 93.1739, 66.35396667,
    #         62.48306667, 57.52516667, 66.33796667,
    #         115.2571634, 111.4020991, 72.62299695
    #     ],
    #     "sift+mutation": [
    #         6.819533333, 6.652866667, 6.3748,
    #         6.7824, 6.291466667, 6.291466667,
    #         28.84623737, 31.8303015, 26.8568694
    #     ],
    #     "sift+freq": [
    #         73.9762, 93.8183, 67.1009,
    #         63.41266667, 58.20636667, 67.01756667,
    #         115.1559987, 111.3032052, 72.56123504
    #     ]
    # }
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

    # runtime_data = {
    #     "store_conf": [
    #         "SSD 2n", "SSD 5n", "SSD 10n",
    #         "TMPFS 2n", "TMPFS 5n", "TMPFS 10n",
    #         "BeeGFS 2n", "BeeGFS 5n", "BeeGFS 10n"
    #     ],
    #     "indiv+merge": [
    #         143.7223674, 102.8425105, 85.74558695,
    #         131.4838243, 59.66937233, 59.7322081,
    #         905.3550568, 828.9928454, 593.1077072
    #     ],
    #     "merge+mutation": [
    #         5.992466667, 6.008466667, 5.627866667,
    #         5.8528, 5.610266667, 5.611866667,
    #         28.94740214, 31.9291954, 26.91863131
    #     ],
    #     "merge+freq": [
    #         73.14913333, 93.1739, 66.35396667,
    #         62.48306667, 57.52516667, 66.33796667,
    #         115.2571634, 111.4020991, 72.62299695
    #     ],
    #     "sift+mutation": [
    #         6.819533333, 6.652866667, 6.3748,
    #         6.7824, 6.291466667, 6.291466667,
    #         28.84623737, 31.8303015, 26.8568694
    #     ],
    #     "sift+freq": [
    #         73.9762, 93.8183, 67.1009,
    #         63.41266667, 58.20636667, 67.01756667,
    #         115.1559987, 111.3032052, 72.56123504
    #     ]
    # }
    return runtime_data

def create_spm_data():
    """Create SPM data dictionary for workflow stages"""
    spm_data = {
        "store_conf": ['SSD 2n', 'SSD 5n', 'SSD 10n', 'TMPFS 2n', 'TMPFS 5n', 'TMPFS 10n', 'BeeGFS 2n', 'BeeGFS 5n', 'BeeGFS 10n'],
        "indiv+merge": [101.43620993347376, 16.903608521715448, 14.528247796583583, 41.213463307627066, 18.36111297603876, 15.834521761208178, 1416.964875293468, 170.93783022213117, 131.556947746123],
        "merge+mutation": [0.6115639165310842, 0.3057154249599653, 0.2120703161813482, 0.183468942679617, 0.16626525188779961, 0.1367144361990299, 0.9245363759231143, 0.7379455223278388, 0.4806928715724974],
        "merge+freq": [2.2894578714861984, 1.0762081931007046, 0.6960834215996251, 0.339874166523306, 0.33605165809386806, 0.3296170398411517, 1.3277820941015264, 1.000268799328383, 0.6321511292812876],
        "sift+mutation": [0.5955432330186794, 0.2982537940969912, 0.2066213523895422, 0.1822367149687355, 0.16529141624071692, 0.1358222516023764, 0.9199312505445156, 0.7349159126144158, 0.47872455587121254],
        "sift+freq": [2.2734371879737933, 1.0687465622377306, 0.690634457807819, 0.33864193881242444, 0.3350778224467854, 0.3287248552444981, 1.3231769687229278, 0.9972391896149599, 0.6301828135800027],
    }
    
    return spm_data

def create_runtime_rank_dict(runtime_data):
    """Create runtime ranking dictionary"""
    df = pd.DataFrame(runtime_data)
    runtime_rank_dict = {}
    
    for col in df.columns[1:]:  # exclude 'store_conf'
        sorted_df = df[['store_conf', col]].sort_values(by=col)
        rankings = {row['store_conf']: rank + 1 for rank, row in enumerate(sorted_df.to_dict('records'))}
        runtime_rank_dict[col] = [
            {
                "store_conf": row['store_conf'],
                "runtime": row[col],
                "rank": rankings[row['store_conf']]
            }
            for _, row in df.iterrows()
        ]
    
    return runtime_rank_dict

def create_spm_rank_dict(spm_data):
    """Create SPM ranking dictionary"""
    df = pd.DataFrame(spm_data)
    
    # Helper to extract number of nodes
    def extract_nodes(conf):
        return int(conf.split()[1][:-1])
    
    # Construct dictionary
    spm_rank_dict = {}
    for column in df.columns[1:]:
        # Rank using value ascending, then node count descending
        sorted_df = df.sort_values(
            by=[column, "store_conf"],
            key=lambda col: (
                col if col.name != "store_conf" else col.map(lambda x: -extract_nodes(x))
            ),
            ascending=[True, True]
        ).reset_index()

        # Build a lookup table for ranks
        rank_lookup = {
            df.loc[i, "store_conf"]: rank + 1 for rank, i in enumerate(sorted_df["index"])
        }

        # Store spm_rank_dict per column
        spm_rank_dict[column] = [
            {
                "store_conf": row["store_conf"],
                "runtime": row[column],
                "rank": rank_lookup[row["store_conf"]]
            }
            for _, row in df.iterrows()
        ]
    
    return spm_rank_dict

def compute_rank_error(runtime_rank_dict, spm_rank_dict):
    """Compute rank error between runtime and SPM predictions"""
    stages = list(runtime_rank_dict.keys())
    num_ranks = len(runtime_rank_dict[stages[0]])  # Typically 9
    rank_error_table = []

    for rank_idx in range(num_ranks):  # R1 to R9
        rank_row = []
        for stage in stages:
            # Find store_conf predicted by SPM at current rank
            spm_entry = next((entry for entry in spm_rank_dict[stage] if entry["rank"] == rank_idx + 1), None)
            if not spm_entry:
                rank_row.append(None)
                continue
            predicted_conf = spm_entry["store_conf"]

            # Find actual rank of the predicted store_conf
            actual_entry = next((entry for entry in runtime_rank_dict[stage] if entry["store_conf"] == predicted_conf), None)
            if not actual_entry:
                rank_row.append(None)
                continue
            actual_rank = actual_entry["rank"]

            # Calculate absolute difference
            rank_error = abs((rank_idx + 1) - actual_rank)
            rank_row.append(rank_error)
        rank_error_table.append(rank_row)

    # Format as DataFrame
    rank_labels = [f"R{i+1}" for i in range(num_ranks)]
    df_rank_error = pd.DataFrame(rank_error_table, columns=stages, index=rank_labels)
    return df_rank_error

def compute_local_rank_deviation(runtime_rank_dict, spm_rank_dict):
    """Compute local rank deviation between runtime and SPM predictions"""
    stages = list(runtime_rank_dict.keys())
    num_ranks = len(runtime_rank_dict[stages[0]])  # Typically 9 ranks
    penalty_table = []

    for rank_idx in range(num_ranks):  # R1 to R9
        rank_row = []
        for stage in stages:
            # Get the actual store_conf at this rank
            actual_entry = next((entry for entry in runtime_rank_dict[stage] if entry["rank"] == rank_idx + 1), None)
            if not actual_entry:
                rank_row.append(None)
                continue
            actual_conf = actual_entry["store_conf"]
            actual_runtime = actual_entry["runtime"]

            # Get the SPM-predicted rank for that same store_conf
            spm_entry = next((entry for entry in spm_rank_dict[stage] if entry["rank"] == rank_idx + 1), None)
            
            if not spm_entry:
                rank_row.append(None)
                continue
            spm_conf = spm_entry["store_conf"]
            spm_actual_entry = next((entry for entry in runtime_rank_dict[stage] if entry["store_conf"] == spm_conf), None)
            spm_runtime = spm_actual_entry["runtime"]

            # Compute penalty: can be negative or positive
            penalty_percent = 100 * (spm_runtime - actual_runtime) / actual_runtime
            rank_row.append(penalty_percent)
        penalty_table.append(rank_row)

    # Format as DataFrame
    rank_labels = [f"R{i+1}" for i in range(num_ranks)]
    df_penalty = pd.DataFrame(penalty_table, columns=stages, index=rank_labels)
    return df_penalty

def compute_global_rank_deviation(runtime_rank_dict, spm_rank_dict):
    """Compute global rank deviation between runtime and SPM predictions"""
    stages = list(runtime_rank_dict.keys())
    num_ranks = len(runtime_rank_dict[stages[0]])  # Typically 9 ranks
    penalty_table = []

    for rank_idx in range(num_ranks):  # R1 to R9
        rank_row = []
        for stage in stages:
            # Get the actual store_conf at this rank
            actual_entry = next((entry for entry in runtime_rank_dict[stage] if entry["rank"] == rank_idx + 1), None)
            if not actual_entry:
                rank_row.append(None)
                continue
            actual_conf = actual_entry["store_conf"]
            actual_runtime = actual_entry["runtime"]

            # Get the SPM-predicted rank actual runtime of workflow with the same rank storages
            rank_runtime = 0
            for st in stages:
                entry = next((entry for entry in runtime_rank_dict[st] if entry["rank"] == rank_idx + 1), None)
                rank_runtime += entry["runtime"]
            
            # Get the SPM-predicted rank actual runtime for that same store_conf
            spm_entry = next((entry for entry in spm_rank_dict[stage] if entry["rank"] == rank_idx + 1), None)
            
            if not spm_entry:
                rank_row.append(None)
                continue
            spm_conf = spm_entry["store_conf"]
            spm_actual_entry = next((entry for entry in runtime_rank_dict[stage] if entry["store_conf"] == spm_conf), None)
            spm_runtime = spm_actual_entry["runtime"]

            # Compute penalty: can be negative or positive
            penalty_percent = 100 * (spm_runtime - actual_runtime) / rank_runtime
            rank_row.append(penalty_percent)
        penalty_table.append(rank_row)

    # Format as DataFrame
    rank_labels = [f"R{i+1}" for i in range(num_ranks)]
    df_penalty = pd.DataFrame(penalty_table, columns=stages, index=rank_labels)
    return df_penalty

def plot_rank_error_old(rank_error_table):
    """Plot SPM rank error visualization (old version - no PDF save)"""
    # Labels (workflows) and Ranks
    labels = ['indiv \n+ merge', 'merge \n+ mutation', 'merge \n+ freq', 'sift \n+ mutation', 'sift \n+ freq']
    ranks = ['R 1', 'R 2', 'R 3', 'R 4', 'R 5', 'R 6', 'R 7', 'R 8', 'R 9']

    # Convert DataFrame to list of lists (row-wise values only)
    rank_error = rank_error_table.values.tolist()

    # Optional: Display the result
    for i, row in enumerate(rank_error, start=1):
        print(f"R{i}: {row}")

    # Bar plot config
    x = np.arange(len(labels))
    bar_width = 0.09

    plt.figure(figsize=(12, 4))
    for i in range(len(ranks)):
        plt.bar(x + i * bar_width, rank_error[i], width=bar_width, color=colors[i], label=ranks[i], zorder=3)

    # Add tick for 0 bars
    for i in range(len(ranks)):
        for j, val in enumerate(rank_error[i]):
            xpos = x[j] + i * bar_width
            plt.plot(xpos, 0, marker='|', color='black', markersize=10, zorder=4)

    # Axis and legend
    plt.xticks(x + (len(ranks) - 1) * bar_width / 2, labels, fontsize=17)
    plt.yticks(np.arange(0, 10, 1), fontsize=17)
    plt.ylim(0, len(ranks)+3)
    plt.ylabel('SPM Rank Error', fontsize=17)
    plt.xlabel('1000 Genome Producer-Consumer Pairs', fontsize=17)
    plt.grid(axis='y', linestyle='--', linewidth=0.5, zorder=0)

    # Legend on top
    plt.legend(title='Rank', title_fontsize=16, fontsize=17, ncol=9, loc='lower center',
               bbox_to_anchor=(0.5, 0.63), columnspacing=0.5)

    plt.tight_layout()
    # No PDF save - just show the plot
    plt.show()

def calculate_rbo(runtime_rank_dict, spm_rank_dict, p=0.9, top_k=5):
    """Calculate Rank-Biased Overlap (RBO) score between runtime and SPM rankings for top-k ranks"""
    rbo_scores = {}
    
    for stage in runtime_rank_dict.keys():
        # Get runtime ranking (list of store_conf in rank order)
        runtime_ranking = []
        for entry in sorted(runtime_rank_dict[stage], key=lambda x: x['rank']):
            runtime_ranking.append(entry['store_conf'])
        
        # Get SPM ranking (list of store_conf in rank order)
        spm_ranking = []
        for entry in sorted(spm_rank_dict[stage], key=lambda x: x['rank']):
            spm_ranking.append(entry['store_conf'])
        
        # Limit to top-k rankings
        runtime_top_k = runtime_ranking[:top_k]
        spm_top_k = spm_ranking[:top_k]
        
        # Calculate RBO for top-k only
        rbo_score = 0
        for d in range(1, min(len(runtime_top_k), len(spm_top_k)) + 1):
            # Get top-d elements from both rankings
            runtime_top_d = set(runtime_top_k[:d])
            spm_top_d = set(spm_top_k[:d])
            
            # Calculate overlap
            overlap = len(runtime_top_d.intersection(spm_top_d))
            rbo_score += (p ** (d - 1)) * (overlap / d)
        
        rbo_scores[stage] = rbo_score * (1 - p)
    
    return rbo_scores

def calculate_kendall_tau(runtime_rank_dict, spm_rank_dict, top_k=5):
    """Calculate Kendall's Tau rank-order correlation for top-k ranks"""
    from scipy.stats import kendalltau
    
    tau_scores = {}
    
    for stage in runtime_rank_dict.keys():
        # Get runtime ranking (list of store_conf in rank order)
        runtime_ranking = []
        for entry in sorted(runtime_rank_dict[stage], key=lambda x: x['rank']):
            runtime_ranking.append(entry['store_conf'])
        
        # Get SPM ranking (list of store_conf in rank order)
        spm_ranking = []
        for entry in sorted(spm_rank_dict[stage], key=lambda x: x['rank']):
            spm_ranking.append(entry['store_conf'])
        
        # Limit to top-k rankings
        runtime_top_k = runtime_ranking[:top_k]
        spm_top_k = spm_ranking[:top_k]
        
        # Create rank mappings for common elements
        common_elements = set(runtime_top_k).intersection(set(spm_top_k))
        
        if len(common_elements) < 2:
            tau_scores[stage] = 0.0
            continue
        
        # Get ranks for common elements
        runtime_ranks = []
        spm_ranks = []
        
        for element in common_elements:
            runtime_ranks.append(runtime_top_k.index(element) + 1)  # 1-based ranking
            spm_ranks.append(spm_top_k.index(element) + 1)  # 1-based ranking
        
        # Calculate Kendall's Tau
        tau, _ = kendalltau(runtime_ranks, spm_ranks)
        tau_scores[stage] = tau if not np.isnan(tau) else 0.0
    
    return tau_scores

def calculate_overlap_coefficient(runtime_rank_dict, spm_rank_dict, top_k=9):
    """Calculate Overlap Coefficient for top-k ranks"""
    overlap_scores = {}
    
    for stage in runtime_rank_dict.keys():
        # Get runtime ranking (list of store_conf in rank order)
        runtime_ranking = []
        for entry in sorted(runtime_rank_dict[stage], key=lambda x: x['rank']):
            runtime_ranking.append(entry['store_conf'])
        
        # Get SPM ranking (list of store_conf in rank order)
        spm_ranking = []
        for entry in sorted(spm_rank_dict[stage], key=lambda x: x['rank']):
            spm_ranking.append(entry['store_conf'])
        
        # Limit to top-k rankings
        runtime_top_k = set(runtime_ranking[:top_k])
        spm_top_k = set(spm_ranking[:top_k])
        
        # Calculate Overlap Coefficient
        # Overlap Coefficient = |A ∩ B| / min(|A|, |B|)
        intersection = len(runtime_top_k.intersection(spm_top_k))
        min_size = min(len(runtime_top_k), len(spm_top_k))
        
        if min_size == 0:
            overlap_scores[stage] = 0.0
        else:
            overlap_scores[stage] = intersection / min_size
    
    return overlap_scores

def plot_rank_error(rank_error_table):
    """Plot SPM rank error visualization"""
    # Labels (workflows) and Ranks
    labels = ['indiv \n+ merge', 'merge \n+ mutation', 'merge \n+ freq', 'sift \n+ mutation', 'sift \n+ freq']
    ranks = ['R 1', 'R 2', 'R 3', 'R 4', 'R 5', 'R 6', 'R 7', 'R 8', 'R 9']

    # Convert DataFrame to list of lists (row-wise values only)
    rank_error = rank_error_table.values.tolist()

    # Bar plot config
    x = np.arange(len(labels))
    bar_width = 0.09

    plt.figure(figsize=(12, 4))
    
    # Plot rank errors
    for i in range(len(ranks)):
        plt.bar(x + i * bar_width, rank_error[i], width=bar_width, color=colors[i], label=ranks[i], zorder=3)

    # Add tick for 0 bars
    for i in range(len(ranks)):
        for j, val in enumerate(rank_error[i]):
            xpos = x[j] + i * bar_width
            plt.plot(xpos, 0, marker='|', color='black', markersize=10, zorder=4)

    # Axis and legend
    plt.xticks(x + (len(ranks) - 1) * bar_width / 2, labels, fontsize=17)
    plt.yticks(np.arange(0, 10, 1))
    plt.tick_params(axis='y', labelsize=16)
    plt.ylim(0, len(ranks)+3)
    plt.ylabel('SPM Rank Error', fontsize=17)
    plt.xlabel('1000 Genomes Producer-Consumer Pairs', fontsize=17)
    plt.grid(axis='y', linestyle='--', linewidth=0.5, zorder=0)
    plt.legend(title='Rank', title_fontsize=16, fontsize=17, ncol=9, loc='lower center',
               bbox_to_anchor=(0.5, 0.7), columnspacing=0.5)

    plt.tight_layout()
    plt.savefig("1kg/1kg_spm_rank_error.pdf", format='pdf', bbox_inches='tight')
    plt.show()

def create_filtered_rankings(runtime_data, spm_data):
    """Create rankings for only SSD and BeeGFS configurations (excluding TMPFS)"""
    # Filter storage configurations to only SSD and BeeGFS
    filtered_configs = ['SSD 2n', 'SSD 5n', 'SSD 10n', 'BeeGFS 2n', 'BeeGFS 5n', 'BeeGFS 10n']
    filtered_indices = [0, 1, 2, 6, 7, 8]  # Indices for SSD and BeeGFS in original data
    
    # Create filtered runtime data
    filtered_runtime_data = {
        "store_conf": filtered_configs,
        "indiv+merge": [runtime_data["indiv+merge"][i] for i in filtered_indices],
        "merge+mutation": [runtime_data["merge+mutation"][i] for i in filtered_indices],
        "merge+freq": [runtime_data["merge+freq"][i] for i in filtered_indices],
        "sift+mutation": [runtime_data["sift+mutation"][i] for i in filtered_indices],
        "sift+freq": [runtime_data["sift+freq"][i] for i in filtered_indices]
    }
    
    # Create filtered SPM data
    filtered_spm_data = {
        "store_conf": filtered_configs,
        "indiv+merge": [spm_data["indiv+merge"][i] for i in filtered_indices],
        "merge+mutation": [spm_data["merge+mutation"][i] for i in filtered_indices],
        "merge+freq": [spm_data["merge+freq"][i] for i in filtered_indices],
        "sift+mutation": [spm_data["sift+mutation"][i] for i in filtered_indices],
        "sift+freq": [spm_data["sift+freq"][i] for i in filtered_indices]
    }
    
    # Create rankings for filtered data
    runtime_rank_dict = create_runtime_rank_dict(filtered_runtime_data)
    spm_rank_dict = create_spm_rank_dict(filtered_spm_data)
    
    return runtime_rank_dict, spm_rank_dict

def plot_rank_error_filtered(runtime_data, spm_data):
    """Plot SPM rank error visualization for 6 configurations only (SSD and BeeGFS, no TMPFS)"""
    # Create filtered rankings
    runtime_rank_dict, spm_rank_dict = create_filtered_rankings(runtime_data, spm_data)
    
    # Compute rank error for filtered data
    rank_error_table = compute_rank_error(runtime_rank_dict, spm_rank_dict)
    
    # Labels (workflows) and Ranks (only 6 ranks for 6 configurations)
    labels = ['indiv \n+ merge', 'merge \n+ mutation', 'merge \n+ freq', 'sift \n+ mutation', 'sift \n+ freq']
    ranks = ['R 1', 'R 2', 'R 3', 'R 4', 'R 5', 'R 6']

    # Convert DataFrame to list of lists (row-wise values only)
    rank_error = rank_error_table.values.tolist()

    # Bar plot config
    x = np.arange(len(labels))
    bar_width = 0.12  # Wider bars since fewer ranks

    plt.figure(figsize=(10, 3))
    
    # Plot rank errors
    for i in range(len(ranks)):
        plt.bar(x + i * bar_width, rank_error[i], width=bar_width, color=colors[i], label=ranks[i], zorder=3)

    # Add tick for 0 bars
    for i in range(len(ranks)):
        for j, val in enumerate(rank_error[i]):
            xpos = x[j] + i * bar_width
            plt.plot(xpos, 0, marker='|', color='black', markersize=10, zorder=4)

    # Axis and legend
    plt.xticks(x + (len(ranks) - 1) * bar_width / 2, labels, fontsize=17)
    plt.yticks(np.arange(0, 7, 1))
    plt.tick_params(axis='y', labelsize=16)
    plt.ylim(0, 7)
    plt.ylabel('Rank Error', fontsize=17)
    plt.xlabel('1000 Genomes Producer-Consumer Pairs', fontsize=17)
    plt.grid(axis='y', linestyle='--', linewidth=0.5, zorder=0)
    plt.legend(title='Rank', title_fontsize=16, fontsize=17, ncol=6, loc='lower center',
               bbox_to_anchor=(0.5, 0.5), columnspacing=0.5)

    plt.tight_layout()
    plt.savefig("1kg/1kg_spm_rank_error_filtered.pdf", format='pdf', bbox_inches='tight')
    plt.show()
    
    return rank_error_table

# def plot_rbo_scores(runtime_rank_dict, spm_rank_dict):
#     """Plot RBO and Kendall's Tau correlation scores"""
#     # Labels (workflows)
#     labels = ['indiv \n+ merge', 'merge \n+ mutation', 'merge \n+ freq', 'sift \n+ mutation', 'sift \n+ freq']

#     # Calculate RBO scores for top-9 ranks
#     rbo_scores = calculate_rbo(runtime_rank_dict, spm_rank_dict, top_k=9)
    
#     # Calculate Kendall's Tau scores for top-9 ranks
#     tau_scores = calculate_kendall_tau(runtime_rank_dict, spm_rank_dict, top_k=9)
    
#     # Print scores
#     print("\nRank-Biased Overlap (RBO) Scores (Top-9):")
#     for stage, score in rbo_scores.items():
#         print(f"  {stage}: {score:.4f}")
    
#     print("\nKendall's Tau Scores (Top-9):")
#     for stage, score in tau_scores.items():
#         print(f"  {stage}: {score:.4f}")

#     # Plot RBO and Kendall's Tau scores
#     rbo_values = [rbo_scores[label.replace(' \n+ ', '+').replace(' ', '')] for label in labels]
#     tau_values = [tau_scores[label.replace(' \n+ ', '+').replace(' ', '')] for label in labels]
    
#     x_pos = np.arange(len(labels))
#     width = 0.35
    
#     plt.figure(figsize=(14, 6))
    
#     # Plot both metrics (RBO and Kendall's Tau)
#     bars1 = plt.bar(x_pos - width/2, rbo_values, width, label='RBO (Top-9)', color='steelblue', alpha=0.7)
#     bars2 = plt.bar(x_pos + width/2, tau_values, width, label="Kendall's τ (Top-9)", color='darkorange', alpha=0.7)
    
#     # Add value labels on bars
#     for i, (bar, value) in enumerate(zip(bars1, rbo_values)):
#         plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
#                 f'{value:.3f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
#     for i, (bar, value) in enumerate(zip(bars2, tau_values)):
#         plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
#                 f'{value:.3f}', ha='center', va='bottom', fontsize=10, fontweight='bold')

#     # Axis setup
#     plt.xticks(x_pos, labels, fontsize=17)
#     plt.ylabel('Correlation Score', fontsize=17)
#     plt.xlabel('1000 Genomes Producer-Consumer Pairs', fontsize=17)
#     plt.ylim(-1.1, 1.1)
#     plt.grid(axis='y', linestyle='--', linewidth=0.5, zorder=0)
#     plt.legend(fontsize=12, loc='upper right')
#     plt.axhline(y=0, color='black', linestyle='-', linewidth=0.5)

#     plt.tight_layout()
#     plt.savefig("1kg/1kg_spm_rbo.pdf", format='pdf', bbox_inches='tight')
#     plt.show()

# def calculate_tier_classification_accuracy(runtime_rank_dict, spm_rank_dict):
#     """Calculate tier classification accuracy by grouping storage options into performance tiers"""
#     tier_accuracies = {}
    
#     for stage in runtime_rank_dict.keys():
#         # Get runtime values and sort them
#         runtime_values = []
#         for entry in runtime_rank_dict[stage]:
#             runtime_values.append((entry['store_conf'], entry['runtime']))
#         runtime_values.sort(key=lambda x: x[1])  # Sort by runtime (ascending)
        
#         # Get SPM values and sort them
#         spm_values = []
#         for entry in spm_rank_dict[stage]:
#             spm_values.append((entry['store_conf'], entry['runtime']))
#         spm_values.sort(key=lambda x: x[1])  # Sort by SPM value (ascending)
        
#         # Group into tiers (high/medium/low performance)
#         n_storages = len(runtime_values)
#         tier_size = n_storages // 3
        
#         # Runtime tiers (lower runtime = better performance)
#         runtime_tiers = {'high': [], 'medium': [], 'low': []}
#         for i, (conf, _) in enumerate(runtime_values):
#             if i < tier_size:
#                 runtime_tiers['high'].append(conf)
#             elif i < 2 * tier_size:
#                 runtime_tiers['medium'].append(conf)
#             else:
#                 runtime_tiers['low'].append(conf)
        
#         # SPM tiers (lower SPM value = better performance)
#         spm_tiers = {'high': [], 'medium': [], 'low': []}
#         for i, (conf, _) in enumerate(spm_values):
#             if i < tier_size:
#                 spm_tiers['high'].append(conf)
#             elif i < 2 * tier_size:
#                 spm_tiers['medium'].append(conf)
#             else:
#                 spm_tiers['low'].append(conf)
        
#         # Calculate accuracy for each tier
#         tier_accuracy = 0
#         for tier in ['high', 'medium', 'low']:
#             correct = len(set(runtime_tiers[tier]).intersection(set(spm_tiers[tier])))
#             total = len(runtime_tiers[tier])
#             tier_accuracy += correct / total if total > 0 else 0
        
#         tier_accuracies[stage] = tier_accuracy / 3  # Average across all tiers
    
#     return tier_accuracies

def calculate_tier_classification_accuracy(runtime_rank_dict, spm_rank_dict):
    """Calculate tier classification accuracy by grouping storage options into performance tiers"""
    tier_accuracies = {}
    
    for stage in runtime_rank_dict.keys():
        # Get runtime values and sort them
        runtime_values = []
        for entry in runtime_rank_dict[stage]:
            runtime_values.append((entry['store_conf'], entry['runtime']))
        runtime_values.sort(key=lambda x: x[1])  # Sort by runtime (ascending)
        
        # Get SPM values and sort them
        spm_values = []
        for entry in spm_rank_dict[stage]:
            spm_values.append((entry['store_conf'], entry['runtime']))
        spm_values.sort(key=lambda x: x[1])  # Sort by SPM value (ascending)
        
        # Group into tiers (high/low performance)
        n_storages = len(runtime_values)
        tier_size = n_storages // 2
        
        # Runtime tiers (lower runtime = better performance)
        runtime_tiers = {'high': [], 'low': []}
        for i, (conf, _) in enumerate(runtime_values):
            if i < tier_size:
                runtime_tiers['high'].append(conf)
            else:
                runtime_tiers['low'].append(conf)

        
        # SPM tiers (lower SPM value = better performance)
        spm_tiers = {'high': [], 'low': []}
        for i, (conf, _) in enumerate(spm_values):
            if i < tier_size:
                spm_tiers['high'].append(conf)
            else:
                spm_tiers['low'].append(conf)
        
        # Calculate accuracy for each tier
        tier_accuracy = 0
        for tier in ['high', 'low']:
            correct = len(set(runtime_tiers[tier]).intersection(set(spm_tiers[tier])))
            total = len(runtime_tiers[tier])
            tier_accuracy += correct / total if total > 0 else 0
        
        tier_accuracies[stage] = tier_accuracy / 2  # Average across all tiers
    
    return tier_accuracies

def calculate_tier_classification_accuracy_with_details(runtime_rank_dict, spm_rank_dict):
    """Calculate tier classification accuracy with detailed tier breakdown"""
    tier_accuracies = {}
    tier_details = {}
    
    for stage in runtime_rank_dict.keys():
        # Get runtime values and sort them
        runtime_values = []
        for entry in runtime_rank_dict[stage]:
            runtime_values.append((entry['store_conf'], entry['runtime']))
        runtime_values.sort(key=lambda x: x[1])  # Sort by runtime (ascending)
        
        # Get SPM values and sort them
        spm_values = []
        for entry in spm_rank_dict[stage]:
            spm_values.append((entry['store_conf'], entry['runtime']))
        spm_values.sort(key=lambda x: x[1])  # Sort by SPM value (ascending)
        
        # Group into tiers (high/medium/low performance)
        n_storages = len(runtime_values)
        tier_size = n_storages // 2
        
        # Runtime tiers (lower runtime = better performance)
        runtime_tiers = {'high': [], 'low': []}
        for i, (conf, _) in enumerate(runtime_values):
            if i < tier_size:
                runtime_tiers['high'].append(conf)
            else:
                runtime_tiers['low'].append(conf)
        
        # SPM tiers (lower SPM value = better performance)
        spm_tiers = {'high': [], 'low': []}
        for i, (conf, _) in enumerate(spm_values):
            if i < tier_size:
                spm_tiers['high'].append(conf)
            else:
                spm_tiers['low'].append(conf)
        
        # Calculate accuracy for each tier
        tier_accuracy = 0
        for tier in ['high', 'low']:
            correct = len(set(runtime_tiers[tier]).intersection(set(spm_tiers[tier])))
            total = len(runtime_tiers[tier])
            tier_accuracy += correct / total if total > 0 else 0
        
        tier_accuracies[stage] = tier_accuracy / 2  # Average across all tiers
        tier_details[stage] = {
            'runtime_tiers': runtime_tiers,
            'spm_tiers': spm_tiers
        }
    
    return tier_accuracies, tier_details

def calculate_precision_recall_at_k(runtime_rank_dict, spm_rank_dict, k=5):
    """Calculate Precision@K and Recall@K metrics"""
    precision_scores = {}
    recall_scores = {}
    
    for stage in runtime_rank_dict.keys():
        # Get top-k from runtime ranking
        runtime_top_k = []
        for entry in sorted(runtime_rank_dict[stage], key=lambda x: x['rank']):
            if entry['rank'] <= k:
                runtime_top_k.append(entry['store_conf'])
        
        # Get top-k from SPM ranking
        spm_top_k = []
        for entry in sorted(spm_rank_dict[stage], key=lambda x: x['rank']):
            if entry['rank'] <= k:
                spm_top_k.append(entry['store_conf'])
        
        # Calculate Precision@K: fraction of SPM top-k that are in runtime top-k
        intersection = set(runtime_top_k).intersection(set(spm_top_k))
        precision = len(intersection) / len(spm_top_k) if len(spm_top_k) > 0 else 0
        
        # Calculate Recall@K: fraction of runtime top-k that are in SPM top-k
        recall = len(intersection) / len(runtime_top_k) if len(runtime_top_k) > 0 else 0
        
        precision_scores[stage] = precision
        recall_scores[stage] = recall
    
    return precision_scores, recall_scores

def _storage_type_from_conf(conf):
    conf_upper = conf.upper()
    if conf_upper.startswith('SSD') or conf_upper.startswith('TMPFS'):
        return 'Local'
    if conf_upper.startswith('BEEGFS'):
        return 'Shared'
    return 'Unknown'

def calculate_storage_type_accuracy(runtime_rank_dict, spm_rank_dict):
    """Calculate accuracy of storage type (Local vs Shared) prediction per stage across ranks.
    For each rank position, compare type of runtime's storage vs SPM-predicted storage.
    Accuracy = matches / total ranks.
    """
    type_acc = {}
    stages = list(runtime_rank_dict.keys())
    num_ranks = len(next(iter(runtime_rank_dict.values())))
    for stage in stages:
        matches = 0
        total = 0
        # Build quick lookups by rank
        runtime_by_rank = {entry['rank']: entry['store_conf'] for entry in runtime_rank_dict[stage]}
        spm_by_rank = {entry['rank']: entry['store_conf'] for entry in spm_rank_dict[stage]}
        for r in range(1, num_ranks + 1):
            if r in runtime_by_rank and r in spm_by_rank:
                rt_type = _storage_type_from_conf(runtime_by_rank[r])
                spm_type = _storage_type_from_conf(spm_by_rank[r])
                matches += 1 if rt_type == spm_type else 0
                total += 1
        type_acc[stage] = (matches / total) if total > 0 else 0.0
    return type_acc

def plot_storage_type_classification_accuracy(runtime_rank_dict, spm_rank_dict):
    """Plot Local vs Shared storage type classification accuracy per stage."""
    labels = ['indiv \n+ merge', 'merge \n+ mutation', 'merge \n+ freq', 'sift \n+ mutation', 'sift \n+ freq']
    acc = calculate_storage_type_accuracy(runtime_rank_dict, spm_rank_dict)
    values = [acc[label.replace(' \n+ ', '+').replace(' ', '')] for label in labels]
    x_pos = np.arange(len(labels))
    plt.figure(figsize=(12, 4))
    bars = plt.bar(x_pos, values, color='steelblue', alpha=0.7)
    for bar, val in zip(bars, values):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                 f'{val:.3f}', ha='center', va='bottom', fontsize=17, fontweight='bold')
    plt.xticks(x_pos, labels, fontsize=17)
    plt.ylabel('Storage Type Accuracy (Local vs Shared)', fontsize=17)
    plt.xlabel('1000 Genomes Producer-Consumer Pairs', fontsize=17)
    plt.ylim(0, 1.1)
    plt.grid(axis='y', linestyle='--', linewidth=0.5, zorder=0)
    plt.tight_layout()
    plt.savefig("1kg/1kg_spm_storage_type_class_acc.pdf", format='pdf', bbox_inches='tight')
    plt.show()

def plot_tier_classification_accuracy(runtime_rank_dict, spm_rank_dict):
    """Plot tier classification accuracy with tier breakdown details"""
    # Labels (workflows)
    labels = ['indiv \n+ merge', 'merge \n+ mutation', 'merge \n+ freq', 'sift \n+ mutation', 'sift \n+ freq']
    
    # Calculate tier classification accuracy and get tier details
    tier_accuracies, tier_details = calculate_tier_classification_accuracy_with_details(runtime_rank_dict, spm_rank_dict)
    
    # Print scores and tier details
    print("\nTier Classification Accuracy:")
    for stage, score in tier_accuracies.items():
        print(f"  {stage}: {score:.4f}")
    
    print("\nTier Classifications:")
    for stage, details in tier_details.items():
        print(f"\n  {stage}:")
        for tier in ['high', 'low']:
            runtime_tier = details['runtime_tiers'][tier]
            spm_tier = details['spm_tiers'][tier]
            correct = len(set(runtime_tier).intersection(set(spm_tier)))
            total = len(runtime_tier)
            print(f"    {tier.upper()} Performance:")
            print(f"      Runtime: {runtime_tier}")
            print(f"      SPM:     {spm_tier}")
            print(f"      Correct: {correct}/{total}")
    
    # Plot tier classification accuracy
    tier_values = [tier_accuracies[label.replace(' \n+ ', '+').replace(' ', '')] for label in labels]
    
    x_pos = np.arange(len(labels))
    
    plt.figure(figsize=(12, 5))
    
    # Plot tier classification accuracy
    bars = plt.bar(x_pos, tier_values, color='steelblue', alpha=0.7)
    
    # Add value labels on bars
    for i, (bar, value) in enumerate(zip(bars, tier_values)):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                f'{value:.3f}', ha='center', va='bottom', fontsize=17, fontweight='bold')
    
    # Axis setup
    plt.xticks(x_pos, labels, fontsize=17)
    plt.ylabel('Tier Classification Accuracy', fontsize=17)
    plt.xlabel('1000 Genomes Producer-Consumer Pairs', fontsize=17)
    plt.ylim(0, 1.1)
    plt.grid(axis='y', linestyle='--', linewidth=0.5, zorder=0)
    # plt.title('SPM Tier Classification Accuracy\n(High/Medium/Low Performance Tiers)', fontsize=17, fontweight='bold')
    
    # Add tier classification details as text below the plot
    # tier_text = "Tier Classifications:\n"
    # for i, label in enumerate(labels):
    #     stage_key = label.replace(' \n+ ', '+').replace(' ', '')
    #     if stage_key in tier_details:
    #         details = tier_details[stage_key]
    #         tier_text += f"\n{label}:\n"
    #         for tier in ['high', 'medium', 'low']:
    #             runtime_tier = details['runtime_tiers'][tier]
    #             spm_tier = details['spm_tiers'][tier]
    #             correct = len(set(runtime_tier).intersection(set(spm_tier)))
    #             total = len(runtime_tier)
    #             tier_text += f"  {tier.upper()}: Runtime={runtime_tier}, SPM={spm_tier} ({correct}/{total})\n"
    
    # Add text box with tier details
    # plt.figtext(0.02, 0.02, tier_text, fontsize=8, verticalalignment='bottom', 
    #             bbox=dict(boxstyle="round,pad=0.3", facecolor='lightgray', alpha=0.8))
    
    plt.tight_layout()
    # plt.subplots_adjust(bottom=0.3)  # Make room for the text box
    plt.savefig("1kg/1kg_spm_tier_class_acc.pdf", format='pdf', bbox_inches='tight')
    plt.show()

def plot_precision_recall_at_k(runtime_rank_dict, spm_rank_dict, k=5):
    """Plot Precision@K and Recall@K metrics"""
    # Labels (workflows)
    labels = ['indiv \n+ merge', 'merge \n+ mutation', 'merge \n+ freq', 'sift \n+ mutation', 'sift \n+ freq']
    
    # Calculate Precision@K and Recall@K
    precision_scores, recall_scores = calculate_precision_recall_at_k(runtime_rank_dict, spm_rank_dict, k)
    
    # Print scores
    print(f"\nPrecision@{k} Scores:")
    for stage, score in precision_scores.items():
        print(f"  {stage}: {score:.4f}")
    
    print(f"\nRecall@{k} Scores:")
    for stage, score in recall_scores.items():
        print(f"  {stage}: {score:.4f}")
    
    # Plot Precision@K and Recall@K
    precision_values = [precision_scores[label.replace(' \n+ ', '+').replace(' ', '')] for label in labels]
    recall_values = [recall_scores[label.replace(' \n+ ', '+').replace(' ', '')] for label in labels]
    
    x_pos = np.arange(len(labels))
    width = 0.35
    
    plt.figure(figsize=(12, 4))
    
    # Plot both metrics
    bars1 = plt.bar(x_pos - width/2, precision_values, width, label=f'Precision@{k}', color='steelblue', alpha=0.7)
    bars2 = plt.bar(x_pos + width/2, recall_values, width, label=f'Recall@{k}', color='darkorange', alpha=0.7)
    
    # Add value labels on bars
    for i, (bar, value) in enumerate(zip(bars1, precision_values)):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                f'{value:.3f}', ha='center', va='bottom', fontsize=17, fontweight='bold')
    
    for i, (bar, value) in enumerate(zip(bars2, recall_values)):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                f'{value:.3f}', ha='center', va='bottom', fontsize=17, fontweight='bold')
    
    # Axis setup
    plt.xticks(x_pos, labels, fontsize=17)
    plt.ylabel('Precision/Recall Score', fontsize=17)
    plt.xlabel('1000 Genomes Producer-Consumer Pairs', fontsize=17)
    plt.ylim(0, 1.1)
    plt.grid(axis='y', linestyle='--', linewidth=0.5, zorder=0)
    plt.legend(fontsize=16, loc='upper right')
    plt.title(f'SPM Precision@{k} and Recall@{k} Metrics', fontsize=17, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig("1kg/1kg_spm_prec_recall_5.pdf", format='pdf', bbox_inches='tight')
    plt.show()

def plot_time_deviation_old(local_deviation_table, global_deviation_table):
    """Plot SPM time deviation visualization (old combined version - no PDF save)"""
    # Labels (workflows) and Ranks
    labels = ['indiv \n+ merge', 'merge \n+ mutation', 'merge \n+ freq', 'sift \n+ mutation', 'sift \n+ freq']
    ranks = ['R 1', 'R 2', 'R 3', 'R 4', 'R 5', 'R 6', 'R 7', 'R 8', 'R 9']

    # Bar and dot plot data
    local_deviation = local_deviation_table.values.tolist()
    global_deviation = global_deviation_table.values.tolist()

    x = np.arange(len(labels))
    bar_width = 0.1
    fig, ax1 = plt.subplots(figsize=(12, 4))

    # Plot bars
    for i in range(len(ranks)):
        for j, val in enumerate(local_deviation[i]):
            xpos = x[j] + i * bar_width
            label = ranks[i] if j == 0 else None  # Only label once per rank
            bar = ax1.bar(xpos, val, width=bar_width, color=colors[i], label=label, zorder=3)

    # Tick marker for 0 bars
    for i in range(len(ranks)):
        for j, val in enumerate(local_deviation[i]):
            xpos = x[j] + i * bar_width
            ax1.plot(xpos, 0, marker='|', color='black', markersize=5, zorder=4)

    # Plot dots with annotations
    for i in range(len(ranks)):
        for j, val in enumerate(global_deviation[i]):
            xpos = x[j] + i * bar_width
            if val != 0:
                ax1.scatter(
                    xpos, val,
                    color=colors[i],
                    marker='o',
                    s=30,
                    edgecolors='black',
                    linewidths=0.8,
                    zorder=6
                )

    # Axes setup
    centered_x = x + ((len(ranks) - 1) * bar_width) / 2
    ax1.set_xticks(centered_x)
    ax1.set_xticklabels(labels, fontsize=17)
    ax1.set_yticks(np.arange(-100, 101, 10))
    ax1.set_ylim(-50, 50)
    ax1.set_ylabel('DPM Deviation Time (%)', fontsize=17)
    ax1.set_xlabel('1000 Genomes Producer-Consumer Pairs', fontsize=17)
    ax1.grid(axis='y', linestyle='--', linewidth=0.5, zorder=0)

    # Legend
    ax1.legend(title='Rank', fontsize=17, ncol=9, loc='upper center', bbox_to_anchor=(0.6, 0.25), columnspacing=1)

    plt.tight_layout()
    # No PDF save - just show the plot
    plt.show()

    # Calculate error rates
    local_errors_10 = sum(1 for row in local_deviation for val in row if abs(val) > 10)
    global_errors_10 = sum(1 for row in global_deviation for val in row if abs(val) > 10)
    local_errors_5 = sum(1 for row in local_deviation for val in row if abs(val) > 5)
    global_errors_5 = sum(1 for row in global_deviation for val in row if abs(val) > 5)
    total_entries = len(local_deviation) * len(labels)
    
    print(f"Error rate over 10% global margin of error: {global_errors_10}/{total_entries}")
    print(f"Error rate over 10% local margin of error: {local_errors_10}/{total_entries}")
    print(f"Error rate over 5% global margin of error: {global_errors_5}/{total_entries}")
    print(f"Error rate over 5% local margin of error: {local_errors_5}/{total_entries}")

def plot_global_time_deviation(global_deviation_table):
    """Plot only global time deviation as bars"""
    # Labels (workflows) and Ranks
    labels = ['indiv \n+ merge', 'merge \n+ mutation', 'merge \n+ freq', 'sift \n+ mutation', 'sift \n+ freq']
    ranks = ['R 1', 'R 2', 'R 3', 'R 4', 'R 5', 'R 6', 'R 7', 'R 8', 'R 9']

    # Global deviation data (clamped to non-negative values)
    raw_global_deviation = global_deviation_table.values.tolist()
    global_deviation = [[max(val, 0) if val is not None else None for val in row] for row in raw_global_deviation]

    x = np.arange(len(labels))
    bar_width = 0.1
    fig, ax1 = plt.subplots(figsize=(12, 4))

    # Plot bars for global deviation
    for i in range(len(ranks)):
        for j, val in enumerate(global_deviation[i]):
            xpos = x[j] + i * bar_width
            label = ranks[i] if j == 0 else None  # Only label once per rank
            bar = ax1.bar(xpos, val, width=bar_width, color=colors[i], label=label, zorder=3)

    # Tick marker for 0 bars
    for i in range(len(ranks)):
        for j, val in enumerate(global_deviation[i]):
            xpos = x[j] + i * bar_width
            ax1.plot(xpos, 0, marker='|', color='black', markersize=5, zorder=4)

    # Axes setup
    centered_x = x + ((len(ranks) - 1) * bar_width) / 2
    ax1.set_xticks(centered_x)
    ax1.set_xticklabels(labels, fontsize=18)
    ax1.set_yticks(np.arange(0, 14, 2))
    ax1.set_yticklabels(np.arange(0, 14, 2), fontsize=18)
    ax1.set_ylim(0, 14)
    ax1.set_ylabel('DPM Deviation Time (%)', fontsize=18)
    ax1.set_xlabel('1000 Genomes Producer-Consumer Pairs', fontsize=20)
    ax1.grid(axis='y', linestyle='--', linewidth=0.5, zorder=0)
    
    # Add baseline at y=0
    ax1.axhline(y=0, color='black', linestyle='-', linewidth=1, zorder=2)

    # Legend
    ax1.legend(title='Rank', title_fontsize=16, prop={'size': 15}, ncol=9,loc='lower center', 
    bbox_to_anchor=(0.5, 0.66),
    columnspacing=1)

    plt.tight_layout()
    plt.savefig("1kg/1kg_spm_time_deviation.pdf", format='pdf', bbox_inches='tight')
    plt.show()

def print_percent_deviation(global_deviation_table):
    """Print percent deviation for each producer+consumer stage"""
    print("\n" + "="*60)
    print("PERCENT DEVIATION BY PRODUCER+CONSUMER STAGE")
    print("="*60)
    
    # Labels (workflows) and Ranks
    labels = ['indiv+merge', 'merge+mutation', 'merge+freq', 'sift+mutation', 'sift+freq']
    ranks = ['R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7', 'R8', 'R9']
    
    # Convert DataFrame to list of lists
    global_deviation = global_deviation_table.values.tolist()
    
    # Print header
    print(f"{'Stage':<15}", end="")
    for rank in ranks:
        print(f"{rank:>8}", end="")
    print()
    print("-" * (15 + 8 * len(ranks)))
    
    # Print each stage's deviations
    for j, stage in enumerate(labels):
        print(f"{stage:<15}", end="")
        for i in range(len(ranks)):
            deviation = global_deviation[i][j]
            if deviation is not None:
                print(f"{deviation:>7.1f}%", end="")
            else:
                print(f"{'N/A':>7}", end="")
        print()
    
    print()
    
    # Calculate and print summary statistics
    print("SUMMARY STATISTICS:")
    print("-" * 30)
    
    # Calculate statistics for each stage
    for j, stage in enumerate(labels):
        deviations = [global_deviation[i][j] for i in range(len(ranks)) if global_deviation[i][j] is not None]
        if deviations:
            mean_dev = np.mean(deviations)
            std_dev = np.std(deviations)
            max_dev = np.max(deviations)
            min_dev = np.min(deviations)
            abs_deviations = [abs(d) for d in deviations]
            mean_abs_dev = np.mean(abs_deviations)
            
            print(f"{stage}:")
            print(f"  Mean deviation: {mean_dev:.2f}%")
            print(f"  Mean absolute deviation: {mean_abs_dev:.2f}%")
            print(f"  Standard deviation: {std_dev:.2f}%")
            print(f"  Range: [{min_dev:.2f}%, {max_dev:.2f}%]")
            print()

def plot_spm_values(spm_data):
    """Plot SPM values for SSD and BeeGFS only"""
    # Filter for SSD and BeeGFS only (indices 0,1,2 for SSD and 6,7,8 for BeeGFS)
    ssd_indices = [0, 1, 2]  # SSD 2n, SSD 5n, SSD 10n
    beegfs_indices = [6, 7, 8]  # BeeGFS 2n, BeeGFS 5n, BeeGFS 10n
    
    # Labels for producer-consumer pairs
    labels = ['indiv \n+ merge', 'merge \n+ mutation', 'merge \n+ freq', 'sift \n+ mutation', 'sift \n+ freq']
    
    # Storage configurations to plot
    storage_configs = ['SSD 2n', 'SSD 5n', 'SSD 10n', 'BeeGFS 2n', 'BeeGFS 5n', 'BeeGFS 10n']
    storage_indices = ssd_indices + beegfs_indices
    
    x = np.arange(len(labels))
    bar_width = 0.13
    
    plt.figure(figsize=(12, 4))
    
    # Plot bars for each storage configuration
    for i, (config, idx) in enumerate(zip(storage_configs, storage_indices)):
        values = []
        for stage in labels:
            # Get the SPM value for this stage and storage configuration
            stage_key = stage.replace(' \n+ ', '+').replace(' ', '')
            if stage_key in spm_data:
                values.append(spm_data[stage_key][idx])
            else:
                values.append(0)
        
        plt.bar(x + i * bar_width, values, width=bar_width, 
                label=config, color=colors[i], alpha=0.8)
    
    # Customize the plot
    plt.xlabel('1000 Genomes Producer-Consumer Pairs', fontsize=17)
    plt.ylabel('Rank Score', fontsize=17)
    plt.title('Rank Score by Storage Configuration (SSD and BeeGFS)', fontsize=17)
    plt.xticks(x + (len(storage_configs) - 1) * bar_width / 2, labels, fontsize=17)
    plt.legend(fontsize=16, ncol=2)
    plt.grid(axis='y', alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    plt.savefig("1kg/1kg_spm_rank.pdf", format='pdf', bbox_inches='tight')
    plt.show()

def plot_spm_values_log(spm_data, show_total=True):
    """Plot SPM values for SSD and BeeGFS only with log scale.
    Optionally add a "Sum" group rendered as bars per storage configuration.
    """
    # Filter for SSD and BeeGFS only (indices 0,1,2 for SSD and 6,7,8 for BeeGFS)
    ssd_indices = [0, 1, 2]  # SSD 2n, SSD 5n, SSD 10n
    beegfs_indices = [6, 7, 8]  # BeeGFS 2n, BeeGFS 5n, BeeGFS 10n
    
    # Labels for producer-consumer pairs
    base_labels = ['indiv \n+ merge', 'merge \n+ mutation', 'merge \n+ freq', 'sift \n+ mutation', 'sift \n+ freq']
    
    # Storage configurations to plot
    storage_configs = ['SSD 2n', 'SSD 5n', 'SSD 10n', 'BeeGFS 2n', 'BeeGFS 5n', 'BeeGFS 10n']
    storage_indices = ssd_indices + beegfs_indices
    
    # Optionally extend x to accommodate an extra "Sum" group
    labels = base_labels + (['Workflow\nSum'] if show_total else [])
    x = np.arange(len(labels))
    bar_width = 0.13
    
    plt.figure(figsize=(10, 4))
    
    max_plotted_val = 0
    totals = []  # keep totals per config for potential future use
    
    # Plot bars for each storage configuration
    for i, (config, idx) in enumerate(zip(storage_configs, storage_indices)):
        values = []
        for stage in base_labels:
            # Get the SPM value for this stage and storage configuration
            stage_key = stage.replace(' \n+ ', '+').replace(' ', '')
            val = spm_data[stage_key][idx] if stage_key in spm_data else 0
            values.append(val)
            if val > max_plotted_val:
                max_plotted_val = val
        
        # Print debug info for SPM values
        print(f"\nSPM Values for {config}:")
        for j, (stage, val) in enumerate(zip(base_labels, values)):
            print(f"  {stage}: {val:.6f}")
        print(f"  Sum: {np.sum(values):.6f}")
        
        # Bars for per-stage values
        plt.bar(x[:len(base_labels)] + i * bar_width, values, width=bar_width,
                label=config, color=colors[i], alpha=0.8)
        
        # Optional: bar for total per configuration at the "Sum" group
        if show_total:
            total_val = float(np.sum(values))
            totals.append(total_val)
            plt.bar(x[len(base_labels)] + i * bar_width, total_val, width=bar_width,
                    color=colors[i], alpha=0.8)
            if total_val > max_plotted_val:
                max_plotted_val = total_val
    
    # Customize the plot with log scale
    plt.xlabel('1000 Genomes Producer-Consumer Pairs', fontsize=17)
    plt.ylabel('Proxy Time (seconds, log)', fontsize=17)
    plt.title('Proxy Time by Storage Configuration (SSD and BeeGFS) - Log Scale', fontsize=17)
    plt.xticks(x + (len(storage_configs) - 1) * bar_width / 2, labels, fontsize=17)
    plt.legend(fontsize=16, ncol=2)
    plt.grid(axis='y', alpha=0.3, linestyle='--')
    plt.yscale('log')  # Set y-axis to log scale
    
    plt.tight_layout()
    plt.savefig("1kg/1kg_spm_rank_log.pdf", format='pdf', bbox_inches='tight')
    plt.show()

def plot_workflow_time(runtime_data):
    """Plot workflow time for SSD and BeeGFS only"""
    # Filter for SSD and BeeGFS only (indices 0,1,2 for SSD and 6,7,8 for BeeGFS)
    ssd_indices = [0, 1, 2]  # SSD 2n, SSD 5n, SSD 10n
    beegfs_indices = [6, 7, 8]  # BeeGFS 2n, BeeGFS 5n, BeeGFS 10n
    
    # Labels for producer-consumer pairs
    labels = ['indiv \n+ merge', 'merge \n+ mutation', 'merge \n+ freq', 'sift \n+ mutation', 'sift \n+ freq']
    
    # Storage configurations to plot
    storage_configs = ['SSD 2n', 'SSD 5n', 'SSD 10n', 'BeeGFS 2n', 'BeeGFS 5n', 'BeeGFS 10n']
    storage_indices = ssd_indices + beegfs_indices
    
    x = np.arange(len(labels))
    bar_width = 0.13
    
    plt.figure(figsize=(12, 4))
    
    # Plot bars for each storage configuration
    for i, (config, idx) in enumerate(zip(storage_configs, storage_indices)):
        values = []
        for stage in labels:
            # Get the runtime value for this stage and storage configuration
            stage_key = stage.replace(' \n+ ', '+').replace(' ', '')
            if stage_key in runtime_data:
                values.append(runtime_data[stage_key][idx])
            else:
                values.append(0)
        
        plt.bar(x + i * bar_width, values, width=bar_width, 
                label=config, color=colors[i], alpha=0.8)
    
    # Customize the plot
    plt.xlabel('1000 Genomes Producer-Consumer Pairs', fontsize=17)
    plt.ylabel('Runtime (seconds)', fontsize=17)
    plt.title('Workflow Time by Storage Configuration (SSD and BeeGFS)', fontsize=17)
    plt.xticks(x + (len(storage_configs) - 1) * bar_width / 2, labels, fontsize=17)
    plt.legend(fontsize=16, ncol=2)
    plt.grid(axis='y', alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    plt.savefig("1kg/1kg_wf_time.pdf", format='pdf', bbox_inches='tight')
    plt.show()

def plot_workflow_time_log(runtime_data, show_total=True):
    """Plot workflow time for SSD and BeeGFS only with log scale.
    Optionally add a "Sum" group rendered as bars per storage configuration.
    """
    # Filter for SSD and BeeGFS only (indices 0,1,2 for SSD and 6,7,8 for BeeGFS)
    ssd_indices = [0, 1, 2]  # SSD 2n, SSD 5n, SSD 10n
    beegfs_indices = [6, 7, 8]  # BeeGFS 2n, BeeGFS 5n, BeeGFS 10n
    
    # Labels for producer-consumer pairs
    base_labels = ['indiv \n+ merge', 'merge \n+ mutation', 'merge \n+ freq', 'sift \n+ mutation', 'sift \n+ freq']
    
    # Storage configurations to plot
    storage_configs = ['SSD 2n', 'SSD 5n', 'SSD 10n', 'BeeGFS 2n', 'BeeGFS 5n', 'BeeGFS 10n']
    storage_indices = ssd_indices + beegfs_indices
    
    # Optionally extend x to accommodate an extra "Sum" group
    labels = base_labels + (['Workflow\nSum'] if show_total else [])
    x = np.arange(len(labels))
    bar_width = 0.13
    
    plt.figure(figsize=(10, 4))
    
    max_plotted_val = 1
    totals = []
    
    # Plot bars for each storage configuration
    for i, (config, idx) in enumerate(zip(storage_configs, storage_indices)):
        values = []
        for stage in base_labels:
            # Get the runtime value for this stage and storage configuration
            stage_key = stage.replace(' \n+ ', '+').replace(' ', '')
            val = runtime_data[stage_key][idx] if stage_key in runtime_data else 0
            values.append(val)
            if val > max_plotted_val:
                max_plotted_val = val
        
        # Print debug info for runtime values
        print(f"\nRuntime Values for {config}:")
        for j, (stage, val) in enumerate(zip(base_labels, values)):
            print(f"  {stage}: {val:.2f}")
        print(f"  Sum: {np.sum(values):.2f}")
        
        plt.bar(x[:len(base_labels)] + i * bar_width, values, width=bar_width,
                label=config, color=colors[i], alpha=0.8)
        
        # Optional: bar for total per configuration at the "Sum" group
        if show_total:
            total_val = float(np.sum(values))
            totals.append(total_val)
            plt.bar(x[len(base_labels)] + i * bar_width, total_val, width=bar_width,
                    color=colors[i], alpha=0.8)
            if total_val > max_plotted_val:
                max_plotted_val = total_val
    
    # Customize the plot with log scale
    plt.xlabel('1000 Genomes Producer-Consumer Pairs', fontsize=17)
    plt.ylabel('Runtime (seconds, log)', fontsize=17)
    plt.title('Workflow Time by Storage Configuration (SSD and BeeGFS) - Log Scale', fontsize=17)
    plt.xticks(x + (len(storage_configs) - 1) * bar_width / 2, labels, fontsize=17)
    plt.legend(fontsize=16, ncol=2)
    plt.grid(axis='y', alpha=0.3, linestyle='--')
    plt.yscale('log')  # Set y-axis to log scale
    plt.ylim(1, 18 * max_plotted_val)
    
    plt.tight_layout()
    plt.savefig("1kg/1kg_wf_time_log.pdf", format='pdf', bbox_inches='tight')
    plt.show()

def calculate_total_workflow_time(runtime_data, spm_rank_dict):
    """Calculate total workflow time using best ranked SPM storage selection"""
    print("\n" + "="*60)
    print("TOTAL WORKFLOW TIME CALCULATION")
    print("="*60)
    
    # Get the best ranked storage configuration for each stage
    best_storages = {}
    total_time = 0
    
    for stage, entries in spm_rank_dict.items():
        # Find the entry with rank 1 (best rank)
        best_entry = next((entry for entry in entries if entry["rank"] == 1), None)
        if best_entry:
            best_storage = best_entry["store_conf"]
            best_storages[stage] = best_storage
            
            # Get the corresponding runtime value
            runtime_value = runtime_data[stage][runtime_data["store_conf"].index(best_storage)]
            total_time += runtime_value
            
            print(f"{stage}: {best_storage} -> {runtime_value:.2f} seconds")
    
    print(f"\nTotal workflow time: {total_time:.2f} seconds")
    print(f"Best storage configuration: {best_storages}")
    
    return total_time, best_storages

def calculate_total_workflow_time_primary_selection(runtime_data, spm_data):
    """Calculate total workflow time using primary storage selection based on largest SPM stage"""
    print("\n" + "="*60)
    print("TOTAL WORKFLOW TIME CALCULATION (PRIMARY SELECTION METHOD)")
    print("="*60)
    
    # Find the stage with the largest SPM value
    max_spm_value = 0
    max_spm_stage = None
    
    for stage in spm_data.keys():
        if stage == "store_conf":
            continue
        for spm_value in spm_data[stage]:
            if spm_value > max_spm_value:
                max_spm_value = spm_value
                max_spm_stage = stage
    
    print(f"Stage with largest SPM: {max_spm_stage}")
    print(f"Largest SPM value: {max_spm_value:.6f}")
    
    # Find the storage configuration with the smallest SPM value for this stage
    min_spm_value = float('inf')
    min_spm_storage = None
    
    for i, spm_value in enumerate(spm_data[max_spm_stage]):
        if spm_value < min_spm_value:
            min_spm_value = spm_value
            min_spm_storage = spm_data["store_conf"][i]
    
    print(f"Smallest SPM value for {max_spm_stage}: {min_spm_value:.6f}")
    print(f"Primary storage selection: {min_spm_storage}")
    
    # Apply the primary storage selection to all stages
    total_time = 0
    primary_storage_index = spm_data["store_conf"].index(min_spm_storage)
    
    print(f"\nApplying {min_spm_storage} to all stages:")
    for stage in runtime_data.keys():
        if stage == "store_conf":
            continue
        runtime_value = runtime_data[stage][primary_storage_index]
        total_time += runtime_value
        print(f"{stage}: {min_spm_storage} -> {runtime_value:.2f} seconds")
    
    print(f"\nTotal workflow time (primary selection): {total_time:.2f} seconds")
    print(f"Primary storage configuration: {min_spm_storage}")
    
    return total_time, min_spm_storage

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
    
    return {
        'method': 'dagP',
        'storage_config': 'BeeGFS 15n',
        'total_runtime': total_time,
        'tasks': {
            'individuals': individuals_time,
            'merge': merge_time,
            'sifting': sift_time,
            'mutation': mutation_time,
            'frequency': freq_time
        }
    }

def calculate_faasflow_runtime(runtime_data):
    """Calculate total workflow runtime using FaasFlow scheduling configuration"""
    print("\n" + "="*60)
    print("FAASFLOW RUNTIME CALCULATION")
    print("="*60)
    
    # This scheduling method prioritizes colocating tasks on the same node and on fast storage
    faasflow_config = "SSD 2n"
    faasflow_index = runtime_data["store_conf"].index(faasflow_config)
    
    # Get combined stage times
    indiv_merge_time = runtime_data["indiv+merge"][faasflow_index]
    merge_mutation_time = runtime_data["merge+mutation"][faasflow_index]
    merge_freq_time = runtime_data["merge+freq"][faasflow_index]
    sift_mutation_time = runtime_data["sift+mutation"][faasflow_index]
    sift_freq_time = runtime_data["sift+freq"][faasflow_index]
    
    # For per-task breakdown, split using percentages
    merge_pct = 82.7
    sift_pct = 17.3
    mutation_pct = 50.0
    freq_pct = 50.0
    
    # Estimate task times
    # merge time from merge+mutation and merge+freq
    avg_merge_parallel = (merge_mutation_time + merge_freq_time) / 2
    merge_time = avg_merge_parallel / (merge_pct / 100.0) * (merge_pct / 100.0)
    
    # sifting time from sift+mutation and sift+freq
    avg_sift_parallel = (sift_mutation_time + sift_freq_time) / 2
    sift_time = avg_sift_parallel / (sift_pct / 100.0) * (sift_pct / 100.0)
    
    # individuals time (indiv+merge - merge estimate)
    individuals_time = indiv_merge_time - merge_time if indiv_merge_time > merge_time else indiv_merge_time
    
    # mutation and frequency (50/50 split)
    mutation_time = (merge_mutation_time + sift_mutation_time) / 2
    freq_time = (merge_freq_time + sift_freq_time) / 2
    
    total_time = individuals_time + max(merge_time, sift_time) + max(mutation_time, freq_time)
    
    print(f"Using {faasflow_config} for all stages:")
    print("Per-task runtime breakdown:")
    print(f"  individuals: {individuals_time:.2f} seconds")
    print(f"  merge:       {merge_time:.2f} seconds")
    print(f"  sifting:     {sift_time:.2f} seconds")
    print(f"  mutation:    {mutation_time:.2f} seconds")
    print(f"  frequency:   {freq_time:.2f} seconds")
    print(f"\nTotal workflow runtime: {total_time:.2f} seconds")
    
    return {
        'method': 'FaasFlow',
        'storage_config': faasflow_config,
        'total_runtime': total_time,
        'tasks': {
            'individuals': individuals_time,
            'merge': merge_time,
            'sifting': sift_time,
            'mutation': mutation_time,
            'frequency': freq_time
        }
    }

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
    
    return {
        'method': 'DFMan',
        'storage_config': 'SSD 15n / BeeGFS 15n',
        'total_runtime': total_time,
        'tasks': {
            'individuals': individuals_time,
            'merge': merge_time,
            'sifting': sift_time,
            'mutation': mutation_time,
            'frequency': freq_time
        }
    }

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
    
    return {
        'method': 'DPM',
        'storage_config': tmpfs_10n_config,
        'total_runtime': total_time,
        'tasks': {
            'individuals': individuals_time,
            'merge': merge_time,
            'sifting': sift_time,
            'mutation': mutation_time,
            'frequency': freq_time
        }
    }

def save_runtime_summary_to_csv(results_list, output_file):
    """Save runtime summary to CSV file"""
    import csv
    
    # Get all unique task names from all results
    all_tasks = set()
    for result in results_list:
        if 'tasks' in result:
            all_tasks.update(result['tasks'].keys())
    all_tasks = sorted(list(all_tasks))
    
    # Create CSV rows
    rows = []
    for result in results_list:
        row = {
            'scheduling_method': result.get('method', ''),
            'storage_config': result.get('storage_config', ''),
            'total_runtime_seconds': f"{result.get('total_runtime', 0):.2f}"
        }
        # Add per-task times
        for task in all_tasks:
            task_time = result.get('tasks', {}).get(task, 0)
            row[f'{task}_seconds'] = f"{task_time:.2f}"
        rows.append(row)
    
    # Write to CSV
    fieldnames = ['scheduling_method', 'storage_config', 'total_runtime_seconds'] + [f'{task}_seconds' for task in all_tasks]
    
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"\nRuntime summary saved to: {output_file}")

def main():
    """Main function to run the SPM analysis"""
    # Create output directory
    output_dir = "1kg"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
    
    print("Creating runtime data...")
    runtime_data = create_runtime_data()
    
    print("Creating SPM data...")
    spm_data = create_spm_data()
    
    print("Computing runtime rankings...")
    runtime_rank_dict = create_runtime_rank_dict(runtime_data)
    
    print("Computing SPM rankings...")
    spm_rank_dict = create_spm_rank_dict(spm_data)
    
    # Display runtime rankings
    print("\nRuntime Rankings:")
    print(json.dumps(runtime_rank_dict, indent=2))
    
    # Display SPM rankings
    print("\nSPM Rankings:")
    print(json.dumps(spm_rank_dict, indent=2))
    
    print("\nComputing rank errors...")
    rank_error_table = compute_rank_error(runtime_rank_dict, spm_rank_dict)
    print(rank_error_table)
    
    print("\nComputing local rank deviations...")
    local_deviation_table = compute_local_rank_deviation(runtime_rank_dict, spm_rank_dict)
    print(local_deviation_table)
    
    print("\nComputing global rank deviations...")
    global_deviation_table = compute_global_rank_deviation(runtime_rank_dict, spm_rank_dict)
    print(global_deviation_table)
    
    print("\nGenerating visualizations...")
    plot_rank_error_old(rank_error_table)
    plot_rank_error(rank_error_table)
    plot_rank_error_filtered(runtime_data, spm_data)
    # plot_rbo_scores(runtime_rank_dict, spm_rank_dict)  # Commented out RBO and Kendall's Tau
    plot_tier_classification_accuracy(runtime_rank_dict, spm_rank_dict)
    plot_storage_type_classification_accuracy(runtime_rank_dict, spm_rank_dict)
    plot_precision_recall_at_k(runtime_rank_dict, spm_rank_dict, k=5)
    plot_time_deviation_old(local_deviation_table, global_deviation_table)
    plot_global_time_deviation(global_deviation_table)
    print_percent_deviation(global_deviation_table)
    
    print("\nGenerating additional plots...")
    plot_spm_values(spm_data)
    plot_spm_values_log(spm_data)
    plot_workflow_time(runtime_data)
    plot_workflow_time_log(runtime_data)
    
    print("\nCalculating total workflow time...")
    total_time, best_storages = calculate_total_workflow_time(runtime_data, spm_rank_dict)
    
    print("\nCalculating total workflow time (primary selection method)...")
    total_time_primary, primary_storage = calculate_total_workflow_time_primary_selection(runtime_data, spm_data)
    
    print("\nCalculating dagP runtime (15 nodes BeeGFS)...")
    dagp_result = calculate_dagp_runtime(runtime_data)

    print("\nCalculating DFMan runtime (15 nodes)...")
    dfman_result = calculate_dfman_runtime(runtime_data)

    print("\nCalculating DPM runtime (10 nodes SHM/TMPFS)...")
    dpm_result = calculate_dpm_runtime(runtime_data)

    print("\nCalculating FaasFlow runtime...")
    faasflow_result = calculate_faasflow_runtime(runtime_data)
    
    # Save runtime summary to CSV
    results_list = [dagp_result, dfman_result, dpm_result, faasflow_result]
    save_runtime_summary_to_csv(results_list, "1kg_runtime_summary.csv")
    
    print("Analysis complete!")

if __name__ == "__main__":
    main()
