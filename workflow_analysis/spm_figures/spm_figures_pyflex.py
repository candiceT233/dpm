#!/usr/bin/env python3
"""
SPM Figures for Pyflex Workflow Analysis
Converted from Jupyter notebook to Python script

This script analyzes SPM (Storage Performance Model) results for Pyflex workflow
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

    runtime_data = {
        "store_conf": [
            "SSD 4n", "SSD 8n", "SSD 16n",
            "TMPFS 4n", "TMPFS 8n", "TMPFS 16n",
            "BeeGFS 4n", "BeeGFS 8n", "BeeGFS 16n"
        ],

        "idfea+single": [
            292.2458431, 287.4203767, 286.732269,
            288.3152814, 283.2829598, 277.3856162,
            248.8221241, 240.8911947, 217.648033
        ],

        "single+tracks": [
            88.17000521, 86.14486045, 85.0342346,
            86.87232527, 87.10344786, 86.30261356,
            88.5063544, 86.82145383, 85.62161539
        ],

        "tracks+stats": [
            37.49840573, 36.0462303, 34.8091286,
            37.1402176, 36.41693986, 36.21407073,
            35.45224169, 35.66574605, 34.07590289
        ],

        "stats+idfymcs": [
            10.39321459, 9.568777842, 9.29094912,
            10.37960805, 9.7208463, 9.454142895,
            8.041726648, 7.185589556, 6.921177248
        ],

        "idfymcs+matchpf": [
            21.48382742, 19.26783775, 18.91059458,
            21.2781235, 19.88184114, 19.10064979,
            21.50030989, 19.53303158, 19.03362237
        ],

        "matchpf+robustmcs": [
            23.68887598, 21.24523054, 21.10198329,
            23.43891196, 21.84594694, 20.925671,
            24.03150145, 21.13977243, 21.36371392
        ],

        "robustmcs+speed": [
            56.48406634, 140.5785885, 327.9867102,
            55.12913012, 142.3366203, 320.8955075,
            23.14037037, 15.66973348, 17.74230712
        ],

        "mapfea+speed": [
            59.16034453, 143.3837209, 330.5772246,
            57.83499856, 145.191245, 323.762716,
            25.40598757, 16.80997873, 20.7551879
        ]
    }
    return runtime_data

def create_spm_data_from_csv(csv_file):
    """Create SPM data dictionary for workflow stages from CSV file"""
    spm_data = {
        "store_conf": [
            "SSD 4n", "SSD 8n", "SSD 16n",
            "TMPFS 4n", "TMPFS 8n", "TMPFS 16n",
            "BeeGFS 4n", "BeeGFS 8n", "BeeGFS 16n"
        ],
    }
    spm_df = pd.read_csv(csv_file)
    print(spm_df.head(5))
    return spm_data

def create_spm_data():
    """Create SPM data dictionary for workflow stages"""
    # spm_data = {
    #     "store_conf": ['SSD 4n', 'SSD 8n', 'SSD 16n', 'TMPFS 4n', 'TMPFS 8n', 'TMPFS 16n', 'BeeGFS 4n', 'BeeGFS 8n', 'BeeGFS 16n'],
    #     "idfea+single": [33.22606054756121, 29.443108574645194, 54.37748185823749, 33.37981051346545, 34.80684917665277, 66.42119683051695, 1.6005172524598799, 1.0478554553719142, 0.9950125728243302],
    #     "single+tracks": [4.328637223351128, 8.575294955139613, 16.82908544657224, 4.350412990546637, 8.671852152488219, 16.907634816352292, 0.3320626446955756, 0.295588637726144, 0.3293212836948363],
    #     "tracks+stats": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    #     "stats+idfymcs": [0.0353489304824732, 0.0217057743673758, 3.682445450919028, 0.0023140099372678, 0.002853326729451, 3.675667210865003, 0.020178460716560098, 0.015568801208716402, 0.0173065111817229],
    #     "idfymcs+matchpf": [2.4158547476979857, 2.4158547476979857, 2.4158547476979857, 2.38454698074245, 2.38454698074245, 2.38454698074245, 0.0510701606518715, 0.0510701606518715, 0.0510701606518715],
    #     "matchpf+robustmcs": [2.7688202788340095, 2.7688202788340095, 2.7688202788340095, 2.729762863543792, 2.729762863543792, 2.729762863543792, 0.0652634773781948, 0.0652634773781948, 0.0652634773781948],
    #     "robustmcs+speed": [153.31480030159548, 303.13831014509725, 602.4745384488474, 154.35083632250578, 303.9173507138337, 602.4157871367917, 0.5055389364499813, 0.44754738215141887, 0.9485911647940561],
    #     "mapfea+speed": [153.7841407099116, 302.37870318259337, 1813.0211022694275, 151.8927095908382, 301.49575083783714, 1211.3626862799733, 2.5776797504137585, 2.2269721839464305, 2.9768951519410125],
    # }
    spm_data = {
        "store_conf": ['SSD 4n', 'SSD 8n', 'SSD 16n', 'TMPFS 4n', 'TMPFS 8n', 'TMPFS 16n', 'BeeGFS 4n', 'BeeGFS 8n', 'BeeGFS 16n'],
        "idfea+single": [17.79760090208529, 14.426537529064634, 4900.04869505691, 19.42587293379506, 22.703589714447908, 363.35935599471253, 2.347234176602055, 0.9754189565866078, 0.8321255572284129],
        "single+tracks": [4.400435682870831, 8.922355017351299, 16.95745669168621, 4.529931834802539, 9.299627239907295, 17.13160673169088, 0.4902956284512696, 0.4208949520012244, 0.4967376261138839],
        "tracks+stats": [4.514421681312409, 9.039738646750724, 17.01499771948783, 4.790648440769337, 9.693166000660494, 17.202930802636438, 0.9197021427706845, 0.788715052310876, 0.9333811490711299],
        "stats+idfymcs": [4.300082291057627, 8.285736280534424, 15.94931094310925, 4.390572331987202, 9.156619140491918, 16.08224075630154, 0.5347588528265654, 0.4725315131003752, 0.5325795679706522],
        "idfymcs+matchpf": [2.576670043956077, 2.576670043956077, 2.576670043956077, 2.5357129170509483, 2.5357129170509483, 2.5357129170509483, 0.283880736521805, 0.283880736521805, 0.283880736521805],
        "matchpf+robustmcs": [2.963858625005101, 2.963858625005101, 2.963858625005101, 2.9184655895540343, 2.9184655895540343, 2.9184655895540343, 0.3640476025953505, 0.3640476025953505, 0.3640476025953505],
        "robustmcs+speed": [153.90267915153478, 302.796137186502, 601.8270186090407, 155.14183565524291, 303.9595437965418, 602.1332762836895, 1.369383849882329, 0.734952534488906, 1.3547010239740769],
        "mapfea+speed": [310.28985788330317, 608.0722774831326, 1810.0131923877443, 307.187837169423, 606.8515273395616, 1210.3762716844963, 3.344408751344272, 1.3684026055312508, 2.3237941971856624],
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
    labels = [
        'idfea\n+single', 'single\n+tracks', 'tracks\n+stats', 'stats\n+idfymcs',
        'idfymcs\n+matchpf', 'matchpf\n+robustmcs', 'robustmcs\n+speed', 'mapfea\n+speed'
    ]
    ranks = ['R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7', 'R8', 'R9']

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
    plt.ylim(0, len(ranks)+1)
    plt.ylabel('SPM Rank Error', fontsize=17)
    plt.xlabel('PyflexTRKR Producer-Consumer Pairs', fontsize=17)
    plt.grid(axis='y', linestyle='--', linewidth=0.5, zorder=0)

    # Legend on top
    plt.legend(title='Rank', title_fontsize=17, fontsize=17, ncol=9, loc='lower center',
               bbox_to_anchor=(0.5, 0.7), columnspacing=0.5)

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
    labels = [
        'idfea\n+single', 'single\n+tracks', 'tracks\n+stats', 'stats\n+idfymcs',
        'idfymcs\n+matchpf', 'matchpf\n+robustmcs', 'robustmcs\n+speed', 'mapfea\n+speed'
    ]
    ranks = ['R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7', 'R8', 'R9']

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
    plt.ylim(0, len(ranks)+1)
    plt.ylabel('SPM Rank Error', fontsize=17)
    plt.xlabel('PyflexTRKR Producer-Consumer Pairs', fontsize=17)
    plt.grid(axis='y', linestyle='--', linewidth=0.5, zorder=0)
    plt.legend(title='Rank', title_fontsize=17, fontsize=17, ncol=9, loc='lower center',
               bbox_to_anchor=(0.5, 0.7), columnspacing=0.5)

    plt.tight_layout()
    plt.savefig("pyflex/pyflex_spm_rank_error.pdf", format='pdf', bbox_inches='tight')
    plt.show()

# def plot_rbo_scores(runtime_rank_dict, spm_rank_dict):
#     """Plot RBO and Kendall's Tau correlation scores"""
#     # Labels (workflows)
#     labels = [
#         'idfea\n+single', 'single\n+tracks', 'tracks\n+stats', 'stats\n+idfymcs',
#         'idfymcs\n+matchpf', 'matchpf\n+robustmcs', 'robustmcs\n+speed', 'mapfea\n+speed'
#     ]

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
#     rbo_values = [rbo_scores[label.replace('\n+', '+').replace('\n', '')] for label in labels]
#     tau_values = [tau_scores[label.replace('\n+', '+').replace('\n', '')] for label in labels]
    
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
#     plt.xlabel('PyflexTRKR Producer-Consumer Pairs', fontsize=17)
#     plt.ylim(-1.1, 1.1)
#     plt.grid(axis='y', linestyle='--', linewidth=0.5, zorder=0)
#     plt.legend(fontsize=12, loc='upper right')
#     plt.axhline(y=0, color='black', linestyle='-', linewidth=0.5)

#     plt.tight_layout()
#     plt.savefig("pyflex/pyflex_spm_rbo.pdf", format='pdf', bbox_inches='tight')
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

def calculate_2_tier_classification_accuracy(runtime_rank_dict, spm_rank_dict):
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

def calculate_3_tier_classification_accuracy(runtime_rank_dict, spm_rank_dict):
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
        tier_size = n_storages // 3
        
        # Runtime tiers (lower runtime = better performance)
        runtime_tiers = {'high': [], 'medium': [], 'low': []}
        for i, (conf, _) in enumerate(runtime_values):
            if i < tier_size:
                runtime_tiers['high'].append(conf)
            elif i < 2 * tier_size:
                runtime_tiers['medium'].append(conf)
            else:
                runtime_tiers['low'].append(conf)
        
        # SPM tiers (lower SPM value = better performance)
        spm_tiers = {'high': [], 'medium': [], 'low': []}
        for i, (conf, _) in enumerate(spm_values):
            if i < tier_size:
                spm_tiers['high'].append(conf)
            elif i < 2 * tier_size:
                spm_tiers['medium'].append(conf)
            else:
                spm_tiers['low'].append(conf)
        
        # Calculate accuracy for each tier
        tier_accuracy = 0
        for tier in ['high', 'medium', 'low']:
            correct = len(set(runtime_tiers[tier]).intersection(set(spm_tiers[tier])))
            total = len(runtime_tiers[tier])
            tier_accuracy += correct / total if total > 0 else 0
        
        tier_accuracies[stage] = tier_accuracy / 3  # Average across all tiers
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
    """Calculate accuracy of storage type (Local vs Shared) prediction per stage across ranks."""
    type_acc = {}
    stages = list(runtime_rank_dict.keys())
    num_ranks = len(next(iter(runtime_rank_dict.values())))
    for stage in stages:
        matches = 0
        total = 0
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
    labels = [
        'idfea\n+single', 'single\n+tracks', 'tracks\n+stats', 'stats\n+idfymcs',
        'idfymcs\n+matchpf', 'matchpf\n+robustmcs', 'robustmcs\n+speed', 'mapfea\n+speed'
    ]
    acc = calculate_storage_type_accuracy(runtime_rank_dict, spm_rank_dict)
    values = [acc[label.replace('\n+', '+').replace('\n', '')] for label in labels]
    x_pos = np.arange(len(labels))
    plt.figure(figsize=(12, 4))
    bars = plt.bar(x_pos, values, color='steelblue', alpha=0.7)
    for bar, val in zip(bars, values):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                 f'{val:.3f}', ha='center', va='bottom', fontsize=17, fontweight='bold')
    plt.xticks(x_pos, labels, fontsize=17)
    plt.ylabel('Storage Type Accuracy (Local vs Shared)', fontsize=17)
    plt.xlabel('PyflexTRKR Producer-Consumer Pairs', fontsize=17)
    plt.ylim(0, 1.1)
    plt.grid(axis='y', linestyle='--', linewidth=0.5, zorder=0)
    plt.tight_layout()
    plt.savefig("pyflex/pyflex_spm_storage_type_class_acc.pdf", format='pdf', bbox_inches='tight')
    plt.show()

def plot_tier_classification_accuracy(runtime_rank_dict, spm_rank_dict):
    """Plot tier classification accuracy with tier breakdown details"""
    # Labels (workflows)
    labels = [
        'idfea\n+single', 'single\n+tracks', 'tracks\n+stats', 'stats\n+idfymcs',
        'idfymcs\n+matchpf', 'matchpf\n+robustmcs', 'robustmcs\n+speed', 'mapfea\n+speed'
    ]
    
    # Calculate tier classification accuracy and get tier details
    TIER = 2
    if TIER == 2:
        tier_accuracies, tier_details = calculate_2_tier_classification_accuracy(runtime_rank_dict, spm_rank_dict)
    elif TIER == 3:
        tier_accuracies, tier_details = calculate_3_tier_classification_accuracy(runtime_rank_dict, spm_rank_dict)
    else:
        raise ValueError(f"Invalid tier: {TIER}")
    
    # Print scores and tier details
    print("\nTier Classification Accuracy:")
    for stage, score in tier_accuracies.items():
        print(f"  {stage}: {score:.4f}")
    
    print("\nTier Classifications:")
    for stage, details in tier_details.items():
        print(f"\n  {stage}:")
        if TIER == 2:
            for tier in ['high', 'low']:
                runtime_tier = details['runtime_tiers'][tier]
                spm_tier = details['spm_tiers'][tier]
                correct = len(set(runtime_tier).intersection(set(spm_tier)))
                total = len(runtime_tier)
                print(f"    {tier.upper()} Performance:")
                print(f"      Runtime: {runtime_tier}")
                print(f"      SPM:     {spm_tier}")
                print(f"      Correct: {correct}/{total}")
        elif TIER == 3:
            for tier in ['high', 'medium', 'low']:
                runtime_tier = details['runtime_tiers'][tier]
                spm_tier = details['spm_tiers'][tier]
                correct = len(set(runtime_tier).intersection(set(spm_tier)))
                total = len(runtime_tier)
                print(f"    {tier.upper()} Performance:")
                print(f"      Runtime: {runtime_tier}")
                print(f"      SPM:     {spm_tier}")
                print(f"      Correct: {correct}/{total}")
    
    # Plot tier classification accuracy
    tier_values = [tier_accuracies[label.replace('\n+', '+').replace('\n', '')] for label in labels]
    
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
    plt.xlabel('PyflexTRKR Producer-Consumer Pairs', fontsize=17)
    plt.ylim(0, 1.1)
    plt.grid(axis='y', linestyle='--', linewidth=0.5, zorder=0)
    # plt.title('SPM Tier Classification Accuracy (High/Medium/Low Performance Tiers)', fontsize=17, fontweight='bold')
    
    # Add tier classification details as text below the plot
    # tier_text = "Tier Classifications:\n"
    # for i, label in enumerate(labels):
    #     stage_key = label.replace('\n+', '+').replace('\n', '')
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
    plt.savefig("pyflex/pyflex_spm_tier_class_acc.pdf", format='pdf', bbox_inches='tight')
    plt.show()

def plot_precision_recall_at_k(runtime_rank_dict, spm_rank_dict, k=5):
    """Plot Precision@K and Recall@K metrics"""
    # Labels (workflows)
    labels = [
        'idfea\n+single', 'single\n+tracks', 'tracks\n+stats', 'stats\n+idfymcs',
        'idfymcs\n+matchpf', 'matchpf\n+robustmcs', 'robustmcs\n+speed', 'mapfea\n+speed'
    ]
    
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
    precision_values = [precision_scores[label.replace('\n+', '+').replace('\n', '')] for label in labels]
    recall_values = [recall_scores[label.replace('\n+', '+').replace('\n', '')] for label in labels]
    
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
    plt.xlabel('PyflexTRKR Producer-Consumer Pairs', fontsize=17)
    plt.ylim(0, 1.1)
    plt.grid(axis='y', linestyle='--', linewidth=0.5, zorder=0)
    plt.legend(fontsize=17, loc='upper right')
    plt.title(f'SPM Precision@{k} and Recall@{k} Metrics', fontsize=17, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig("pyflex/pyflex_spm_prec_recall_5.pdf", format='pdf', bbox_inches='tight')
    plt.show()

def plot_time_deviation_old(local_deviation_table, global_deviation_table):
    """Plot SPM time deviation visualization (old combined version - no PDF save)"""
    # Labels (workflows) and Ranks
    labels = [
        'idfea\n+single', 'single\n+tracks', 'tracks\n+stats', 'stats\n+idfymcs',
        'idfymcs\n+matchpf', 'matchpf\n+robustmcs', 'robustmcs\n+speed', 'mapfea\n+speed'
    ]
    ranks = ['R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7', 'R8', 'R9']

    # Bar plot data
    local_deviation = local_deviation_table.values.tolist()

    # Line data to be plotted as points
    global_deviation = global_deviation_table.values.tolist()

    x = np.arange(len(labels))
    bar_width = 0.1

    fig, ax1 = plt.subplots(figsize=(12, 4))

    # Plot bars
    for i in range(len(ranks)):
        ax1.bar(x + i * bar_width, local_deviation[i], width=bar_width, color=colors[i], label=ranks[i], zorder=3)

    # Tick marker for 0 bars
    for i in range(len(ranks)):
        for j, val in enumerate(local_deviation[i]):
            xpos = x[j] + i * bar_width
            if val == 0:
                ax1.plot(xpos, 0, marker='|', color='black', markersize=5, zorder=4)

    # Plot global_deviation as scatter points (over bars), using same color
    for i in range(len(ranks)):
        for j in range(len(labels)):
            xpos = x[j] + i * bar_width
            if global_deviation[i][j] != 0:
                ax1.scatter(
                    xpos, global_deviation[i][j],
                    color=colors[i],
                    marker='o',
                    s=30,
                    edgecolors='black',  # Black outline
                    linewidths=0.8,
                    zorder=6
                )

    # Axes setup
    centered_x = x + ((len(ranks) - 1) * bar_width) / 2
    ax1.set_xticks(centered_x)
    ax1.set_xticklabels(labels, fontsize=17)
    ax1.set_yticks(np.arange(-50, 51, 10))
    ax1.set_ylim(-50, 50)
    ax1.set_ylabel('DPM Deviation Time (%)', fontsize=17)
    ax1.set_xlabel('PyflexTRKR Producer-Consumer Pairs', fontsize=17)
    ax1.grid(axis='y', linestyle='--', linewidth=0.5, zorder=0)

    # Legend
    ax1.legend(title='Rank', fontsize=17, ncol=6, loc='upper center', bbox_to_anchor=(0.3, 0.33), columnspacing=1)

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
    labels = [
        'idfea\n+single', 'single\n+tracks', 'tracks\n+stats', 'stats\n+idfymcs',
        'idfymcs\n+matchpf', 'matchpf\n+robustmcs', 'robustmcs\n+speed', 'mapfea\n+speed'
    ]
    ranks = ['R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7', 'R8', 'R9']

    # Global deviation data (clamped to non-negative values)
    raw_global_deviation = global_deviation_table.values.tolist()
    global_deviation = [[max(val, 0) if val is not None else None for val in row] for row in raw_global_deviation]

    x = np.arange(len(labels))
    bar_width = 0.1

    fig, ax1 = plt.subplots(figsize=(12, 3))

    # Plot bars for global deviation
    for i in range(len(ranks)):
        ax1.bar(x + i * bar_width, global_deviation[i], width=bar_width, color=colors[i], label=ranks[i], zorder=3)

    # Tick marker for 0 bars
    for i in range(len(ranks)):
        for j, val in enumerate(global_deviation[i]):
            xpos = x[j] + i * bar_width
            if val == 0:
                ax1.plot(xpos, 0, marker='|', color='black', markersize=5, zorder=4)

    # Axes setup
    centered_x = x + ((len(ranks) - 1) * bar_width) / 2
    ax1.set_xticks(centered_x)
    ax1.set_xticklabels(labels, fontsize=16)
    ax1.set_yticks(np.arange(0, 5, 1))
    ax1.tick_params(axis='y', labelsize=16)
    ax1.set_ylim(0, 4)
    ax1.set_ylabel('DPM Deviation Time %        ', fontsize=16)
    ax1.set_xlabel('PyflexTRKR Producer-Consumer Pairs', fontsize=16)
    ax1.grid(axis='y', linestyle='--', linewidth=0.5, zorder=0)

    # Legend
    ax1.legend(title='Rank', fontsize=16, ncol=9, loc='lower center', 
    bbox_to_anchor=(0.5, 0.5), columnspacing=1)

    plt.tight_layout()
    plt.savefig("pyflex/pyflex_spm_time_deviation.pdf", format='pdf', bbox_inches='tight')
    plt.show()

def print_percent_deviation(global_deviation_table):
    """Print percent deviation for each producer+consumer stage"""
    print("\n" + "="*60)
    print("PERCENT DEVIATION BY PRODUCER+CONSUMER STAGE")
    print("="*60)
    
    # Labels (workflows) and Ranks
    labels = ['idfea+single', 'single+tracks', 'tracks+stats', 'stats+idfymcs', 'idfymcs+matchpf', 'matchpf+robustmcs', 'robustmcs+speed', 'mapfea+speed']
    ranks = ['R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7', 'R8', 'R9']
    
    # Convert DataFrame to list of lists
    global_deviation = global_deviation_table.values.tolist()
    
    # Print header
    print(f"{'Stage':<20}", end="")
    for rank in ranks:
        print(f"{rank:>8}", end="")
    print()
    print("-" * (20 + 8 * len(ranks)))
    
    # Print each stage's deviations
    for j, stage in enumerate(labels):
        print(f"{stage:<20}", end="")
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
    ssd_indices = [0, 1, 2]  # SSD 4n, SSD 8n, SSD 16n
    beegfs_indices = [6, 7, 8]  # BeeGFS 4n, BeeGFS 8n, BeeGFS 16n
    
    # Labels for producer-consumer pairs
    labels = [
        'idfea\n+single', 'single\n+tracks', 'tracks\n+stats', 'stats\n+idfymcs',
        'idfymcs\n+matchpf', 'matchpf\n+robustmcs', 'robustmcs\n+speed', 'mapfea\n+speed'
    ]
    
    # Storage configurations to plot
    storage_configs = ['SSD 4n', 'SSD 8n', 'SSD 16n', 'BeeGFS 4n', 'BeeGFS 8n', 'BeeGFS 16n']
    storage_indices = ssd_indices + beegfs_indices
    
    x = np.arange(len(labels))
    bar_width = 0.13
    
    plt.figure(figsize=(12, 4))
    
    # Plot bars for each storage configuration
    for i, (config, idx) in enumerate(zip(storage_configs, storage_indices)):
        values = []
        for stage in labels:
            # Get the SPM value for this stage and storage configuration
            stage_key = stage.replace('\n+', '+').replace('\n', '')
            if stage_key in spm_data:
                values.append(spm_data[stage_key][idx])
            else:
                values.append(0)
        
        plt.bar(x + i * bar_width, values, width=bar_width, 
                label=config, color=colors[i], alpha=0.8)
    
    # Customize the plot
    plt.xlabel('PyflexTRKR Producer-Consumer Pairs', fontsize=17)
    plt.ylabel('Rank Score', fontsize=17)
    plt.title('Rank Score by Storage Configuration (SSD and BeeGFS)', fontsize=17)
    plt.xticks(x + (len(storage_configs) - 1) * bar_width / 2, labels, fontsize=17)
    plt.legend(fontsize=17, ncol=2)
    plt.grid(axis='y', alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    plt.savefig("pyflex/pyflex_spm_rank.pdf", format='pdf', bbox_inches='tight')
    plt.show()

def plot_spm_values_log(spm_data):
    """Plot SPM values for SSD and BeeGFS only with log scale"""
    # Filter for SSD and BeeGFS only (indices 0,1,2 for SSD and 6,7,8 for BeeGFS)
    ssd_indices = [0, 1, 2]  # SSD 4n, SSD 8n, SSD 16n
    beegfs_indices = [6, 7, 8]  # BeeGFS 4n, BeeGFS 8n, BeeGFS 16n
    
    # Labels for producer-consumer pairs
    labels = [
        'idfea\n+single', 'single\n+tracks', 'tracks\n+stats', 'stats\n+idfymcs',
        'idfymcs\n+matchpf', 'matchpf\n+robustmcs', 'robustmcs\n+speed', 'mapfea\n+speed'
    ]
    
    # Storage configurations to plot
    storage_configs = ['SSD 4n', 'SSD 8n', 'SSD 16n', 'BeeGFS 4n', 'BeeGFS 8n', 'BeeGFS 16n']
    storage_indices = ssd_indices + beegfs_indices
    
    x = np.arange(len(labels))
    bar_width = 0.13
    
    plt.figure(figsize=(12, 4))
    
    # Plot bars for each storage configuration
    for i, (config, idx) in enumerate(zip(storage_configs, storage_indices)):
        values = []
        for stage in labels:
            # Get the SPM value for this stage and storage configuration
            stage_key = stage.replace('\n+', '+').replace('\n', '')
            if stage_key in spm_data:
                values.append(spm_data[stage_key][idx])
            else:
                values.append(0)
        
        plt.bar(x + i * bar_width, values, width=bar_width, 
                label=config, color=colors[i], alpha=0.8)
    
    # Customize the plot with log scale
    plt.xlabel('PyflexTRKR Producer-Consumer Pairs', fontsize=17)
    plt.ylabel('Rank Score (log)', fontsize=17)
    plt.title('Rank Score by Storage Configuration (SSD and BeeGFS) - Log Scale', fontsize=17)
    plt.xticks(x + (len(storage_configs) - 1) * bar_width / 2, labels, fontsize=17)
    plt.legend(fontsize=17, ncol=2)
    plt.grid(axis='y', alpha=0.3, linestyle='--')
    plt.yscale('log')  # Set y-axis to log scale
    
    plt.tight_layout()
    plt.savefig("pyflex/pyflex_spm_rank_log.pdf", format='pdf', bbox_inches='tight')
    plt.show()

def plot_workflow_time(runtime_data):
    """Plot workflow time for SSD and BeeGFS only"""
    # Filter for SSD and BeeGFS only (indices 0,1,2 for SSD and 6,7,8 for BeeGFS)
    ssd_indices = [0, 1, 2]  # SSD 4n, SSD 8n, SSD 16n
    beegfs_indices = [6, 7, 8]  # BeeGFS 4n, BeeGFS 8n, BeeGFS 16n
    
    # Labels for producer-consumer pairs
    labels = [
        'idfea\n+single', 'single\n+tracks', 'tracks\n+stats', 'stats\n+idfymcs',
        'idfymcs\n+matchpf', 'matchpf\n+robustmcs', 'robustmcs\n+speed', 'mapfea\n+speed'
    ]
    
    # Storage configurations to plot
    storage_configs = ['SSD 4n', 'SSD 8n', 'SSD 16n', 'BeeGFS 4n', 'BeeGFS 8n', 'BeeGFS 16n']
    storage_indices = ssd_indices + beegfs_indices
    
    x = np.arange(len(labels))
    bar_width = 0.13
    
    plt.figure(figsize=(12, 4))
    
    # Plot bars for each storage configuration
    for i, (config, idx) in enumerate(zip(storage_configs, storage_indices)):
        values = []
        for stage in labels:
            # Get the runtime value for this stage and storage configuration
            stage_key = stage.replace('\n+', '+').replace('\n', '')
            if stage_key in runtime_data:
                values.append(runtime_data[stage_key][idx])
            else:
                values.append(0)
        
        plt.bar(x + i * bar_width, values, width=bar_width, 
                label=config, color=colors[i], alpha=0.8)
    
    # Customize the plot
    plt.xlabel('PyflexTRKR Producer-Consumer Pairs', fontsize=17)
    plt.ylabel('Runtime (seconds)', fontsize=17)
    plt.title('Workflow Time by Storage Configuration (SSD and BeeGFS)', fontsize=17)
    plt.xticks(x + (len(storage_configs) - 1) * bar_width / 2, labels, fontsize=17)
    plt.legend(fontsize=17, ncol=2)
    plt.grid(axis='y', alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    plt.savefig("pyflex/pyflex_wf_time.pdf", format='pdf', bbox_inches='tight')
    plt.show()

def plot_workflow_time_log(runtime_data):
    """Plot workflow time for SSD and BeeGFS only with log scale"""
    # Filter for SSD and BeeGFS only (indices 0,1,2 for SSD and 6,7,8 for BeeGFS)
    ssd_indices = [0, 1, 2]  # SSD 4n, SSD 8n, SSD 16n
    beegfs_indices = [6, 7, 8]  # BeeGFS 4n, BeeGFS 8n, BeeGFS 16n
    
    # Labels for producer-consumer pairs
    labels = [
        'idfea\n+single', 'single\n+tracks', 'tracks\n+stats', 'stats\n+idfymcs',
        'idfymcs\n+matchpf', 'matchpf\n+robustmcs', 'robustmcs\n+speed', 'mapfea\n+speed'
    ]
    
    # Storage configurations to plot
    storage_configs = ['SSD 4n', 'SSD 8n', 'SSD 16n', 'BeeGFS 4n', 'BeeGFS 8n', 'BeeGFS 16n']
    storage_indices = ssd_indices + beegfs_indices
    
    x = np.arange(len(labels))
    bar_width = 0.13
    
    plt.figure(figsize=(12, 4))
    
    # Plot bars for each storage configuration
    for i, (config, idx) in enumerate(zip(storage_configs, storage_indices)):
        values = []
        for stage in labels:
            # Get the runtime value for this stage and storage configuration
            stage_key = stage.replace('\n+', '+').replace('\n', '')
            if stage_key in runtime_data:
                values.append(runtime_data[stage_key][idx])
            else:
                values.append(0)
        
        plt.bar(x + i * bar_width, values, width=bar_width, 
                label=config, color=colors[i], alpha=0.8)
    
    # Customize the plot with log scale
    plt.xlabel('PyflexTRKR Producer-Consumer Pairs', fontsize=17)
    plt.ylabel('Runtime (seconds, log)', fontsize=17)
    plt.title('Workflow Time by Storage Configuration (SSD and BeeGFS) - Log Scale', fontsize=17)
    plt.xticks(x + (len(storage_configs) - 1) * bar_width / 2, labels, fontsize=17)
    plt.legend(fontsize=17, ncol=2)
    plt.grid(axis='y', alpha=0.3, linestyle='--')
    plt.yscale('log')  # Set y-axis to log scale
    
    plt.tight_layout()
    plt.savefig("pyflex/pyflex_wf_time_log.pdf", format='pdf', bbox_inches='tight')
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
    """Calculate total workflow time using primary storage selection based on largest averaged SPM stage"""
    print("\n" + "="*60)
    print("TOTAL WORKFLOW TIME CALCULATION (PRIMARY SELECTION METHOD)")
    print("="*60)
    
    # Find the stage with the largest averaged SPM value
    max_avg_spm_value = -float('inf')
    max_spm_stage = None
    for stage, values in spm_data.items():
        if stage == "store_conf":
            continue
        avg_val = float(np.mean(values)) if len(values) > 0 else -float('inf')
        if avg_val > max_avg_spm_value:
            max_avg_spm_value = avg_val
            max_spm_stage = stage
    print(f"Stage with largest averaged SPM: {max_spm_stage}")
    print(f"Largest averaged SPM value: {max_avg_spm_value:.6f}")
    
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

def calculate_faasflow_runtime(runtime_data):
    """Calculate total workflow runtime using FaasFlow scheduling configuration"""
    print("\n" + "="*60)
    print("FAASFLOW RUNTIME CALCULATION")
    print("="*60)
    
    # This scheduling method prioritizes colocating tasks on the same node and on fast storage
    faasflow_config = "SSD 4n"
    faasflow_index = runtime_data["store_conf"].index(faasflow_config)
    
    # Get all stage times
    stage_times = {}
    for stage in runtime_data.keys():
        if stage == "store_conf":
            continue
        stage_times[stage] = runtime_data[stage][faasflow_index]
    
    # Estimate per-task times from producer-consumer pairs
    # For sequential pairs, estimate ~60% producer, 40% consumer
    idfea_time = stage_times.get("idfea+single", 0) * 0.6
    single_time = stage_times.get("idfea+single", 0) * 0.4 + stage_times.get("single+tracks", 0) * 0.6
    tracks_time = stage_times.get("single+tracks", 0) * 0.4 + stage_times.get("tracks+stats", 0) * 0.6
    stats_time = stage_times.get("tracks+stats", 0) * 0.4 + stage_times.get("stats+idfymcs", 0) * 0.6
    idfymcs_time = stage_times.get("stats+idfymcs", 0) * 0.4 + stage_times.get("idfymcs+matchpf", 0) * 0.6
    matchpf_time = stage_times.get("idfymcs+matchpf", 0) * 0.4 + stage_times.get("matchpf+robustmcs", 0) * 0.6
    robustmcs_time = stage_times.get("matchpf+robustmcs", 0) * 0.4 + stage_times.get("robustmcs+speed", 0) * 0.6
    speed_time = stage_times.get("robustmcs+speed", 0) * 0.4
    
    total_time = sum(stage_times.values())
    
    print(f"Using {faasflow_config} for all stages:")
    print("Per-task runtime breakdown:")
    if idfea_time > 0:
        print(f"  idfea:      {idfea_time:.2f} seconds")
    if single_time > 0:
        print(f"  single:     {single_time:.2f} seconds")
    if tracks_time > 0:
        print(f"  tracks:     {tracks_time:.2f} seconds")
    if stats_time > 0:
        print(f"  stats:      {stats_time:.2f} seconds")
    if idfymcs_time > 0:
        print(f"  idfymcs:    {idfymcs_time:.2f} seconds")
    if matchpf_time > 0:
        print(f"  matchpf:    {matchpf_time:.2f} seconds")
    if robustmcs_time > 0:
        print(f"  robustmcs:  {robustmcs_time:.2f} seconds")
    if speed_time > 0:
        print(f"  speed:      {speed_time:.2f} seconds")
    print(f"\nTotal workflow runtime: {total_time:.2f} seconds")
    
    tasks_dict = {}
    if idfea_time > 0:
        tasks_dict['idfea'] = idfea_time
    if single_time > 0:
        tasks_dict['single'] = single_time
    if tracks_time > 0:
        tasks_dict['tracks'] = tracks_time
    if stats_time > 0:
        tasks_dict['stats'] = stats_time
    if idfymcs_time > 0:
        tasks_dict['idfymcs'] = idfymcs_time
    if matchpf_time > 0:
        tasks_dict['matchpf'] = matchpf_time
    if robustmcs_time > 0:
        tasks_dict['robustmcs'] = robustmcs_time
    if speed_time > 0:
        tasks_dict['speed'] = speed_time
    
    return {
        'method': 'FaasFlow',
        'storage_config': faasflow_config,
        'total_runtime': total_time,
        'tasks': tasks_dict
    }

def calculate_baseline_runtime(runtime_data):
    """Calculate total workflow runtime using BeeGFS with the most node configuration (dagP)"""
    print("\n" + "="*60)
    print("BEEGFS BASELINE (dagP) RUNTIME CALCULATION")
    print("="*60)

    # dagP would create partitions to minimize edge cuts while respecting the synchronization points. 
    # With strict sequential dependencies between stages and parallel tasks within stages, 
    # it would likely choose 8 nodes to balance between parallelism and avoiding idle resources 
    # and it would use BeeGFS over SSD because the data dependencies.
    # And to prioritizes throughput, 96 parallel tasks would be scheduled on BeeGFS 4n

    beeGFS_baseline = "BeeGFS 4n"
    beeGFS_index = runtime_data["store_conf"].index(beeGFS_baseline)
    
    # Get all stage times
    stage_times = {}
    for stage in runtime_data.keys():
        if stage == "store_conf":
            continue
        stage_times[stage] = runtime_data[stage][beeGFS_index]
    
    # Estimate per-task times from producer-consumer pairs
    idfea_time = stage_times.get("idfea+single", 0) * 0.6
    single_time = stage_times.get("idfea+single", 0) * 0.4 + stage_times.get("single+tracks", 0) * 0.6
    tracks_time = stage_times.get("single+tracks", 0) * 0.4 + stage_times.get("tracks+stats", 0) * 0.6
    stats_time = stage_times.get("tracks+stats", 0) * 0.4 + stage_times.get("stats+idfymcs", 0) * 0.6
    idfymcs_time = stage_times.get("stats+idfymcs", 0) * 0.4 + stage_times.get("idfymcs+matchpf", 0) * 0.6
    matchpf_time = stage_times.get("idfymcs+matchpf", 0) * 0.4 + stage_times.get("matchpf+robustmcs", 0) * 0.6
    robustmcs_time = stage_times.get("matchpf+robustmcs", 0) * 0.4 + stage_times.get("robustmcs+speed", 0) * 0.6
    speed_time = stage_times.get("robustmcs+speed", 0) * 0.4
    
    total_time = sum(stage_times.values())
    
    print(f"Using {beeGFS_baseline} for all stages:")
    print("Per-task runtime breakdown:")
    if idfea_time > 0:
        print(f"  idfea:      {idfea_time:.2f} seconds")
    if single_time > 0:
        print(f"  single:     {single_time:.2f} seconds")
    if tracks_time > 0:
        print(f"  tracks:     {tracks_time:.2f} seconds")
    if stats_time > 0:
        print(f"  stats:      {stats_time:.2f} seconds")
    if idfymcs_time > 0:
        print(f"  idfymcs:    {idfymcs_time:.2f} seconds")
    if matchpf_time > 0:
        print(f"  matchpf:    {matchpf_time:.2f} seconds")
    if robustmcs_time > 0:
        print(f"  robustmcs:  {robustmcs_time:.2f} seconds")
    if speed_time > 0:
        print(f"  speed:      {speed_time:.2f} seconds")
    print(f"\nTotal workflow runtime: {total_time:.2f} seconds")
    
    tasks_dict = {}
    if idfea_time > 0:
        tasks_dict['idfea'] = idfea_time
    if single_time > 0:
        tasks_dict['single'] = single_time
    if tracks_time > 0:
        tasks_dict['tracks'] = tracks_time
    if stats_time > 0:
        tasks_dict['stats'] = stats_time
    if idfymcs_time > 0:
        tasks_dict['idfymcs'] = idfymcs_time
    if matchpf_time > 0:
        tasks_dict['matchpf'] = matchpf_time
    if robustmcs_time > 0:
        tasks_dict['robustmcs'] = robustmcs_time
    if speed_time > 0:
        tasks_dict['speed'] = speed_time
    
    return {
        'method': 'dagP',
        'storage_config': beeGFS_baseline,
        'total_runtime': total_time,
        'tasks': tasks_dict
    }

def calculate_dfmann_runtime(runtime_data):
    """Calculate total workflow runtime using DFMan"""
    print("\n" + "="*60)
    print("DFMAN RUNTIME CALCULATION")
    print("="*60)

    # Stages on Local SSD (single consumers):
    # Stage 1 (idfea): Outputs consumed only by Stage 2 (trksg)
    # Stage 2 (trksg): Outputs consumed only by Stage 3 (gettr)
    # Stage 3 (gettr): Outputs consumed only by Stage 4 (trkst)
    # Stage 4 (trkst): Outputs consumed only by Stage 5 (idmcs)
    # Stage 5 (idmcs): Outputs consumed only by Stage 6 (mtpf)

    # Stages on BeeGFS (multiple consumers or reuse):
    # Stage 6 (mtpf): Outputs (mcs_tracks) consumed by Stage 7 (robmcs) AND potentially reused
    # Stage 7 (robmcs): Outputs (mcs_tracks) consumed by Stage 8 (mapf)
    # Stage 8 (mapf): Outputs (mcstrack) consumed by Stage 9 (speed) and contains multiple data references
    # Stage 9 (speed): Final output, likely BeeGFS for accessibility

    # use mixed SSD and BeeGFS for stages
    # for stage 1-5, use SSD 16n
    dfman_1to5_config = "SSD 16n"
    dfman_1to5_index = runtime_data["store_conf"].index(dfman_1to5_config)
    # for stage 6-9, use BeeGFS 16n
    dfman_6to9_config = "BeeGFS 16n"
    dfman_6to9_index = runtime_data["store_conf"].index(dfman_6to9_config)

    # Get stage times with appropriate storage
    stage_times = {}
    for stage in runtime_data.keys():
        if stage == "store_conf":
            continue
        if stage in ["idfea+single", "single+tracks", "tracks+stats", "stats+idfymcs", "idfymcs+matchpf"]:
            stage_times[stage] = runtime_data[stage][dfman_1to5_index]
        else:
            stage_times[stage] = runtime_data[stage][dfman_6to9_index]
    
    # Estimate per-task times from producer-consumer pairs
    idfea_time = stage_times.get("idfea+single", 0) * 0.6
    single_time = stage_times.get("idfea+single", 0) * 0.4 + stage_times.get("single+tracks", 0) * 0.6
    tracks_time = stage_times.get("single+tracks", 0) * 0.4 + stage_times.get("tracks+stats", 0) * 0.6
    stats_time = stage_times.get("tracks+stats", 0) * 0.4 + stage_times.get("stats+idfymcs", 0) * 0.6
    idfymcs_time = stage_times.get("stats+idfymcs", 0) * 0.4 + stage_times.get("idfymcs+matchpf", 0) * 0.6
    matchpf_time = stage_times.get("idfymcs+matchpf", 0) * 0.4 + stage_times.get("matchpf+robustmcs", 0) * 0.6
    robustmcs_time = stage_times.get("matchpf+robustmcs", 0) * 0.4 + stage_times.get("robustmcs+speed", 0) * 0.6
    speed_time = stage_times.get("robustmcs+speed", 0) * 0.4
    
    total_time = sum(stage_times.values())
    
    print(f"Using {dfman_1to5_config} for stages 1-5:")
    print(f"Using {dfman_6to9_config} for stages 6-9:")
    print("Per-task runtime breakdown:")
    if idfea_time > 0:
        print(f"  idfea:      {idfea_time:.2f} seconds")
    if single_time > 0:
        print(f"  single:     {single_time:.2f} seconds")
    if tracks_time > 0:
        print(f"  tracks:     {tracks_time:.2f} seconds")
    if stats_time > 0:
        print(f"  stats:      {stats_time:.2f} seconds")
    if idfymcs_time > 0:
        print(f"  idfymcs:    {idfymcs_time:.2f} seconds")
    if matchpf_time > 0:
        print(f"  matchpf:    {matchpf_time:.2f} seconds")
    if robustmcs_time > 0:
        print(f"  robustmcs:  {robustmcs_time:.2f} seconds")
    if speed_time > 0:
        print(f"  speed:      {speed_time:.2f} seconds")
    print(f"\nTotal workflow runtime: {total_time:.2f} seconds")
    
    tasks_dict = {}
    if idfea_time > 0:
        tasks_dict['idfea'] = idfea_time
    if single_time > 0:
        tasks_dict['single'] = single_time
    if tracks_time > 0:
        tasks_dict['tracks'] = tracks_time
    if stats_time > 0:
        tasks_dict['stats'] = stats_time
    if idfymcs_time > 0:
        tasks_dict['idfymcs'] = idfymcs_time
    if matchpf_time > 0:
        tasks_dict['matchpf'] = matchpf_time
    if robustmcs_time > 0:
        tasks_dict['robustmcs'] = robustmcs_time
    if speed_time > 0:
        tasks_dict['speed'] = speed_time
    
    return {
        'method': 'DFMan',
        'storage_config': f'{dfman_1to5_config} / {dfman_6to9_config}',
        'total_runtime': total_time,
        'tasks': tasks_dict
    }



    # DFMan would maximize bandwidth by distributing the parallel tasks across 16 nodes during stages 1-2 and 6-7. 
    # It would place frequently accessed data (track.nc, trknum.nc) on multiple nodes to serve parallel consumers. 
    # The large number of random I/O operations would perform better on local SSD than BeeGFS.
    # dfman_config = "SSD 16n"
    # beeGFS_index = runtime_data["store_conf"].index(dfman_config)
    
    # total_time = 0
    # print(f"Using {dfman_config} for all stages:")
    
    # for stage in runtime_data.keys():
    #     if stage == "store_conf":
    #         continue
    #     runtime_value = runtime_data[stage][beeGFS_index]
    #     total_time += runtime_value
    #     print(f"{stage}: {dfman_config} -> {runtime_value:.2f} seconds")
    
    # print(f"\nTotal workflow runtime with {dfman_config}: {total_time:.2f} seconds")
    
    # return total_time

def calculate_dpm_runtime(runtime_data):
    """Calculate total workflow runtime using DPM scheduling configuration (TMPFS)"""
    print("\n" + "="*60)
    print("DPM RUNTIME CALCULATION (TMPFS)")
    print("="*60)
    
    # DPM uses TMPFS for all tasks (use TMPFS 16n as representative)
    tmpfs_config = "TMPFS 16n"
    tmpfs_index = runtime_data["store_conf"].index(tmpfs_config)
    
    # Get all stage times
    stage_times = {}
    for stage in runtime_data.keys():
        if stage == "store_conf":
            continue
        stage_times[stage] = runtime_data[stage][tmpfs_index]
    
    # Estimate per-task times from producer-consumer pairs
    idfea_time = stage_times.get("idfea+single", 0) * 0.6
    single_time = stage_times.get("idfea+single", 0) * 0.4 + stage_times.get("single+tracks", 0) * 0.6
    tracks_time = stage_times.get("single+tracks", 0) * 0.4 + stage_times.get("tracks+stats", 0) * 0.6
    stats_time = stage_times.get("tracks+stats", 0) * 0.4 + stage_times.get("stats+idfymcs", 0) * 0.6
    idfymcs_time = stage_times.get("stats+idfymcs", 0) * 0.4 + stage_times.get("idfymcs+matchpf", 0) * 0.6
    matchpf_time = stage_times.get("idfymcs+matchpf", 0) * 0.4 + stage_times.get("matchpf+robustmcs", 0) * 0.6
    robustmcs_time = stage_times.get("matchpf+robustmcs", 0) * 0.4 + stage_times.get("robustmcs+speed", 0) * 0.6
    speed_time = stage_times.get("robustmcs+speed", 0) * 0.4
    
    total_time = sum(stage_times.values())
    
    print(f"Using {tmpfs_config} for all stages:")
    print("Per-task runtime breakdown:")
    if idfea_time > 0:
        print(f"  idfea:      {idfea_time:.2f} seconds")
    if single_time > 0:
        print(f"  single:     {single_time:.2f} seconds")
    if tracks_time > 0:
        print(f"  tracks:     {tracks_time:.2f} seconds")
    if stats_time > 0:
        print(f"  stats:      {stats_time:.2f} seconds")
    if idfymcs_time > 0:
        print(f"  idfymcs:    {idfymcs_time:.2f} seconds")
    if matchpf_time > 0:
        print(f"  matchpf:    {matchpf_time:.2f} seconds")
    if robustmcs_time > 0:
        print(f"  robustmcs:  {robustmcs_time:.2f} seconds")
    if speed_time > 0:
        print(f"  speed:      {speed_time:.2f} seconds")
    print(f"\nTotal workflow runtime: {total_time:.2f} seconds")
    
    tasks_dict = {}
    if idfea_time > 0:
        tasks_dict['idfea'] = idfea_time
    if single_time > 0:
        tasks_dict['single'] = single_time
    if tracks_time > 0:
        tasks_dict['tracks'] = tracks_time
    if stats_time > 0:
        tasks_dict['stats'] = stats_time
    if idfymcs_time > 0:
        tasks_dict['idfymcs'] = idfymcs_time
    if matchpf_time > 0:
        tasks_dict['matchpf'] = matchpf_time
    if robustmcs_time > 0:
        tasks_dict['robustmcs'] = robustmcs_time
    if speed_time > 0:
        tasks_dict['speed'] = speed_time
    
    return {
        'method': 'DPM',
        'storage_config': tmpfs_config,
        'total_runtime': total_time,
        'tasks': tasks_dict
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
    output_dir = "pyflex"
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
    
    print("\nCalculating BeeGFS most nodes runtime...")
    dagp_result = calculate_baseline_runtime(runtime_data)

    print("\nCalculating DFMan runtime...")
    dfman_result = calculate_dfmann_runtime(runtime_data)

    print("\nCalculating FaasFlow runtime...")
    faasflow_result = calculate_faasflow_runtime(runtime_data)

    print("\nCalculating DPM runtime...")
    dpm_result = calculate_dpm_runtime(runtime_data)
    
    # Save runtime summary to CSV
    results_list = [dagp_result, dfman_result, faasflow_result, dpm_result]
    save_runtime_summary_to_csv(results_list, "pyflextrkr_runtime_summary.csv")
    
    print("Analysis complete!")

if __name__ == "__main__":
    main()
