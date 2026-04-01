#!/usr/bin/env python3
"""
Load SPM data from CSV file according to pyflex_spm.md rules

This script loads data from the SPM results CSV and filters it according to
the specific producer-consumer pairs and storage configurations defined in
pyflex_spm.md
"""

import pandas as pd
import numpy as np

def load_spm_data_from_csv(csv_file):
    """Load SPM data from CSV file according to pyflex_spm.md rules"""
    
    # Read the CSV file
    df = pd.read_csv(csv_file)
    print(f"Loaded CSV with {len(df)} rows")
    print("Columns:", df.columns.tolist())
    print("\nFirst 5 rows:")
    print(df.head())
    
    # Initialize the spm_data dictionary
    spm_data = {
        "store_conf": [
            "SSD 4n", "SSD 8n", "SSD 16n",
            "TMPFS 4n", "TMPFS 8n", "TMPFS 16n",
            "BeeGFS 4n", "BeeGFS 8n", "BeeGFS 16n"
        ],
        "idfea+single": [],
        "single+tracks": [],
        "tracks+stats": [],
        "stats+idfymcs": [],
        "idfymcs+matchpf": [],
        "matchpf+robustmcs": [],
        "robustmcs+speed": [],
        "mapfea+speed": []
    }
    
    # Helper function to find SPM value based on specific conditions
    def find_spm_value(df, producer, consumer, prod_storage, cons_storage, 
                       prod_tasks, cons_tasks):
        """Find SPM value for specific producer-consumer configuration"""
        mask = (
            (df['producer'] == producer) &
            (df['consumer'] == consumer) &
            (df['producerStorageType'] == prod_storage) &
            (df['consumerStorageType'] == cons_storage) &
            (df['producerTasksPerNode'] == prod_tasks) &
            (df['consumerTasksPerNode'] == cons_tasks)
        )
        filtered = df[mask]
        if len(filtered) > 0:
            return filtered.iloc[0]['SPM']
        else:
            print(f"Warning: No data found for {producer} -> {consumer} with "
                  f"prod_storage={prod_storage}, cons_storage={cons_storage}, "
                  f"prod_tasks={prod_tasks}, cons_tasks={cons_tasks}")
            return None
    
    print("\n" + "="*80)
    print("EXTRACTING SPM VALUES ACCORDING TO pyflex_spm.md RULES")
    print("="*80)
    
    # 1. idfea+single: stage_in-run_idfeature+run_idfeature and run_idfeature+run_tracksingle
    print("\n1. Processing idfea+single...")
    
    # First 3 values: stage_in-run_idfeature+run_idfeature
    # SSD configurations
    ssd_4n = find_spm_value(df, "stage_in-run_idfeature", "run_idfeature", 
                           "beegfs-ssd", "ssd", 8, 30)
    ssd_8n = find_spm_value(df, "stage_in-run_idfeature", "run_idfeature", 
                           "beegfs-ssd", "ssd", 5, 15)
    ssd_16n = find_spm_value(df, "stage_in-run_idfeature", "run_idfeature", 
                            "beegfs-ssd", "ssd", 3, 8)
    
    # TMPFS configurations  
    tmpfs_4n = find_spm_value(df, "stage_in-run_idfeature", "run_idfeature", 
                             "beegfs-tmpfs", "tmpfs", 8, 30)
    tmpfs_8n = find_spm_value(df, "stage_in-run_idfeature", "run_idfeature", 
                             "beegfs-tmpfs", "tmpfs", 5, 15)
    tmpfs_16n = find_spm_value(df, "stage_in-run_idfeature", "run_idfeature", 
                              "beegfs-tmpfs", "tmpfs", 3, 8)
    
    # BeeGFS configurations
    beegfs_4n = find_spm_value(df, "stage_in-run_idfeature", "run_idfeature", 
                              "beegfs", "beegfs", 60, 30)
    beegfs_8n = find_spm_value(df, "stage_in-run_idfeature", "run_idfeature", 
                              "beegfs", "beegfs", 30, 15)
    beegfs_16n = find_spm_value(df, "stage_in-run_idfeature", "run_idfeature", 
                               "beegfs", "beegfs", 15, 8)
    
    # Second 3 values: run_idfeature+run_tracksingle
    # SSD configurations
    ssd_4n_2 = find_spm_value(df, "run_idfeature", "run_tracksingle", 
                              "ssd", "ssd", 30, 30)
    ssd_8n_2 = find_spm_value(df, "run_idfeature", "run_tracksingle", 
                              "ssd", "ssd", 15, 15)
    ssd_16n_2 = find_spm_value(df, "run_idfeature", "run_tracksingle", 
                               "ssd", "ssd", 8, 8)
    
    # TMPFS configurations
    tmpfs_4n_2 = find_spm_value(df, "run_idfeature", "run_tracksingle", 
                                "tmpfs", "tmpfs", 30, 30)
    tmpfs_8n_2 = find_spm_value(df, "run_idfeature", "run_tracksingle", 
                                "tmpfs", "tmpfs", 15, 15)
    tmpfs_16n_2 = find_spm_value(df, "run_idfeature", "run_tracksingle", 
                                 "tmpfs", "tmpfs", 8, 8)
    
    # BeeGFS configurations
    beegfs_4n_2 = find_spm_value(df, "run_idfeature", "run_tracksingle", 
                                 "beegfs", "beegfs", 30, 30)
    beegfs_8n_2 = find_spm_value(df, "run_idfeature", "run_tracksingle", 
                                 "beegfs", "beegfs", 15, 15)
    beegfs_16n_2 = find_spm_value(df, "run_idfeature", "run_tracksingle", 
                                  "beegfs", "beegfs", 8, 8)
    
    # Combine all values for idfea+single
    spm_data["idfea+single"] = [
        [ssd_4n, ssd_4n_2], [ssd_8n, ssd_8n_2], [ssd_16n, ssd_16n_2],
        [tmpfs_4n, tmpfs_4n_2], [tmpfs_8n, tmpfs_8n_2], [tmpfs_16n, tmpfs_16n_2],
        [beegfs_4n, beegfs_4n_2], [beegfs_8n, beegfs_8n_2], [beegfs_16n, beegfs_16n_2]
    ]
    
    print("idfea+single values:", spm_data["idfea+single"])
    
    # 2. single+tracks: stage_in-run_tracksingle+run_tracksingle and run_tracksingle+run_gettracks
    print("\n2. Processing single+tracks...")
    
    # First 3 values: stage_in-run_tracksingle+run_tracksingle
    # SSD configurations
    ssd_4n = find_spm_value(df, "stage_in-run_tracksingle", "run_tracksingle", 
                           "ssd-ssd", "ssd", 6,30)
    ssd_8n = find_spm_value(df, "stage_in-run_tracksingle", "run_tracksingle", 
                           "ssd-ssd", "ssd", 4, 15)
    ssd_16n = find_spm_value(df, "stage_in-run_tracksingle", "run_tracksingle", 
                            "ssd-ssd", "ssd", 1, 8)
    
    # TMPFS configurations
    tmpfs_4n = find_spm_value(df, "stage_in-run_tracksingle", "run_tracksingle", 
                             "tmpfs-tmpfs", "tmpfs", 6,30)
    tmpfs_8n = find_spm_value(df, "stage_in-run_tracksingle", "run_tracksingle", 
                             "tmpfs-tmpfs", "tmpfs", 4, 15)
    tmpfs_16n = find_spm_value(df, "stage_in-run_tracksingle", "run_tracksingle", 
                              "tmpfs-tmpfs", "tmpfs", 1, 8)
    
    # BeeGFS configurations
    beegfs_4n = find_spm_value(df, "stage_in-run_tracksingle", "run_tracksingle", 
                              "beegfs", "beegfs", 60, 30)
    beegfs_8n = find_spm_value(df, "stage_in-run_tracksingle", "run_tracksingle", 
                              "beegfs", "beegfs", 30, 15)
    beegfs_16n = find_spm_value(df, "stage_in-run_tracksingle", "run_tracksingle", 
                               "beegfs", "beegfs", 15, 8)
    
    # Second 3 values: run_tracksingle+run_gettracks
    # SSD configurations
    ssd_4n_2 = find_spm_value(df, "run_tracksingle", "run_gettracks", 
                              "ssd", "ssd", 30, 30)
    ssd_8n_2 = find_spm_value(df, "run_tracksingle", "run_gettracks", 
                              "ssd", "ssd", 15, 15)
    ssd_16n_2 = find_spm_value(df, "run_tracksingle", "run_gettracks", 
                               "ssd", "ssd", 8, 8)
    
    # TMPFS configurations
    tmpfs_4n_2 = find_spm_value(df, "run_tracksingle", "run_gettracks", 
                                "tmpfs", "tmpfs", 30, 30)
    tmpfs_8n_2 = find_spm_value(df, "run_tracksingle", "run_gettracks", 
                                "tmpfs", "tmpfs", 15, 15)
    tmpfs_16n_2 = find_spm_value(df, "run_tracksingle", "run_gettracks", 
                                 "tmpfs", "tmpfs", 8, 8)
    
    # BeeGFS configurations
    beegfs_4n_2 = find_spm_value(df, "run_tracksingle", "run_gettracks", 
                                 "beegfs", "beegfs", 30, 30)
    beegfs_8n_2 = find_spm_value(df, "run_tracksingle", "run_gettracks", 
                                 "beegfs", "beegfs", 15, 15)
    beegfs_16n_2 = find_spm_value(df, "run_tracksingle", "run_gettracks", 
                                  "beegfs", "beegfs", 8, 8)
    
    # Combine all values for single+tracks
    spm_data["single+tracks"] = [
        [ssd_4n, ssd_4n_2], [ssd_8n, ssd_8n_2], [ssd_16n, ssd_16n_2],
        [tmpfs_4n, tmpfs_4n_2], [tmpfs_8n, tmpfs_8n_2], [tmpfs_16n, tmpfs_16n_2],
        [beegfs_4n, beegfs_4n_2], [beegfs_8n, beegfs_8n_2], [beegfs_16n, beegfs_16n_2]
    ]
    
    print("single+tracks values:", spm_data["single+tracks"])
    
    # 3. tracks+stats: stage_in-run_gettracks+run_gettracks and run_gettracks+run_trackstats
    print("\n3. Processing tracks+stats...")
    
    # First 3 values: stage_in-run_gettracks+run_gettracks
    ssd_4n = find_spm_value(df, "stage_in-run_gettracks","run_gettracks", 
                           "ssd-ssd", "ssd", 8,30)
    ssd_8n = find_spm_value(df, "stage_in-run_gettracks", "run_gettracks", 
                           "ssd-ssd", "ssd", 4,15)
    ssd_16n = find_spm_value(df, "stage_in-run_gettracks", "run_gettracks", 
                            "ssd-ssd", "ssd", 1, 8)
    
    tmpfs_4n = find_spm_value(df, "stage_in-run_gettracks", "run_gettracks", 
                             "tmpfs-tmpfs", "tmpfs", 8,30)
    tmpfs_8n = find_spm_value(df, "stage_in-run_gettracks", "run_gettracks", 
                             "tmpfs-tmpfs", "tmpfs", 4,15)
    tmpfs_16n = find_spm_value(df, "stage_in-run_gettracks", "run_gettracks", 
                              "tmpfs-tmpfs", "tmpfs", 1,8)
    
    beegfs_4n = find_spm_value(df, "stage_in-run_gettracks", "run_gettracks", 
                              "beegfs", "beegfs", 60, 30)
    beegfs_8n = find_spm_value(df, "stage_in-run_gettracks", "run_gettracks", 
                              "beegfs", "beegfs", 30, 15)
    beegfs_16n = find_spm_value(df, "stage_in-run_gettracks", "run_gettracks", 
                               "beegfs", "beegfs", 15, 8)
    
    # Second 3 values: run_gettracks+run_trackstats
    ssd_4n_2 = find_spm_value(df, "run_gettracks", "run_trackstats", 
                              "ssd", "ssd", 30, 30)
    ssd_8n_2 = find_spm_value(df, "run_gettracks", "run_trackstats", 
                              "ssd", "ssd", 15, 15)
    ssd_16n_2 = find_spm_value(df, "run_gettracks", "run_trackstats", 
                               "ssd", "ssd", 8, 8)
    
    tmpfs_4n_2 = find_spm_value(df, "run_gettracks", "run_trackstats", 
                                "tmpfs", "tmpfs", 30, 30)
    tmpfs_8n_2 = find_spm_value(df, "run_gettracks", "run_trackstats", 
                                "tmpfs", "tmpfs", 15, 15)
    tmpfs_16n_2 = find_spm_value(df, "run_gettracks", "run_trackstats", 
                                 "tmpfs", "tmpfs", 8, 8)
    
    beegfs_4n_2 = find_spm_value(df, "run_gettracks", "run_trackstats", 
                                 "beegfs", "beegfs", 30, 30)
    beegfs_8n_2 = find_spm_value(df, "run_gettracks", "run_trackstats", 
                                 "beegfs", "beegfs", 15, 15)
    beegfs_16n_2 = find_spm_value(df, "run_gettracks", "run_trackstats", 
                                  "beegfs", "beegfs", 8, 8)
    
    spm_data["tracks+stats"] = [
        [ssd_4n, ssd_4n_2], [ssd_8n, ssd_8n_2], [ssd_16n, ssd_16n_2],
        [tmpfs_4n, tmpfs_4n_2], [tmpfs_8n, tmpfs_8n_2], [tmpfs_16n, tmpfs_16n_2],
        [beegfs_4n, beegfs_4n_2], [beegfs_8n, beegfs_8n_2], [beegfs_16n, beegfs_16n_2]
    ]
    
    print("tracks+stats values:", spm_data["tracks+stats"])
    
    # 4. stats+idfymcs: stage_in-run_trackstats+run_trackstats and run_trackstats+run_identifymcs
    print("\n4. Processing stats+idfymcs...")
    
    # First 3 values: stage_in-run_trackstats+run_trackstats
    ssd_4n = find_spm_value(df, "stage_in-run_trackstats", "run_trackstats", 
                           "ssd-ssd", "ssd", 4,30)
    ssd_8n = find_spm_value(df, "stage_in-run_trackstats", "run_trackstats", 
                           "ssd-ssd", "ssd", 2, 15)
    
    ssd_16n = find_spm_value(df, "stage_in-run_trackstats", "run_trackstats", 
                            "ssd-ssd", "ssd", 1, 8)
    
    tmpfs_4n = find_spm_value(df, "stage_in-run_trackstats", "run_trackstats", 
                             "tmpfs-tmpfs", "tmpfs", 4,30)
    tmpfs_8n = find_spm_value(df, "stage_in-run_trackstats", "run_trackstats", 
                             "tmpfs-tmpfs", "tmpfs", 2, 15)
    tmpfs_16n = find_spm_value(df, "stage_in-run_trackstats", "run_trackstats", 
                              "tmpfs-tmpfs", "tmpfs", 1, 8)
    
    beegfs_4n = find_spm_value(df, "stage_in-run_trackstats", "run_trackstats", 
                              "beegfs", "beegfs", 60, 30)
    beegfs_8n = find_spm_value(df, "stage_in-run_trackstats", "run_trackstats", 
                              "beegfs", "beegfs", 30, 15)
    beegfs_16n = find_spm_value(df, "stage_in-run_trackstats", "run_trackstats", 
                               "beegfs", "beegfs", 15, 8)
    
    # Second 3 values: run_trackstats+run_identifymcs (CORRECTED: consumerTasksPerNode = 1)
    ssd_4n_2 = find_spm_value(df, "run_trackstats", "run_identifymcs", 
                              "ssd", "ssd", 30, 1)
    ssd_8n_2 = find_spm_value(df, "run_trackstats", "run_identifymcs", 
                              "ssd", "ssd", 15, 1)
    ssd_16n_2 = find_spm_value(df, "run_trackstats", "run_identifymcs", 
                               "ssd", "ssd", 8, 1)
    
    tmpfs_4n_2 = find_spm_value(df, "run_trackstats", "run_identifymcs", 
                                "tmpfs", "tmpfs", 30, 1)
    tmpfs_8n_2 = find_spm_value(df, "run_trackstats", "run_identifymcs", 
                                "tmpfs", "tmpfs", 15, 1)
    tmpfs_16n_2 = find_spm_value(df, "run_trackstats", "run_identifymcs", 
                                 "tmpfs", "tmpfs", 8, 1)
    
    beegfs_4n_2 = find_spm_value(df, "run_trackstats", "run_identifymcs", 
                                 "beegfs", "beegfs", 30, 1)
    beegfs_8n_2 = find_spm_value(df, "run_trackstats", "run_identifymcs", 
                                 "beegfs", "beegfs", 15, 1)
    beegfs_16n_2 = find_spm_value(df, "run_trackstats", "run_identifymcs", 
                                  "beegfs", "beegfs", 8, 1)
    
    spm_data["stats+idfymcs"] = [
        [ssd_4n, ssd_4n_2], [ssd_8n, ssd_8n_2], [ssd_16n, ssd_16n_2],
        [tmpfs_4n, tmpfs_4n_2], [tmpfs_8n, tmpfs_8n_2], [tmpfs_16n, tmpfs_16n_2],
        [beegfs_4n, beegfs_4n_2], [beegfs_8n, beegfs_8n_2], [beegfs_16n, beegfs_16n_2]
    ]
    
    print("stats+idfymcs values:", spm_data["stats+idfymcs"])
    
    # 5. idfymcs+matchpf: stage_in-run_identifymcs+run_identifymcs and run_identifymcs+run_matchpf
    print("\n5. Processing idfymcs+matchpf...")
    
    # First 3 values: stage_in-run_identifymcs+run_identifymcs
    ssd_4n = find_spm_value(df, "stage_in-run_identifymcs", "run_identifymcs", 
                           "ssd-ssd", "ssd", 1,1)
    ssd_8n = find_spm_value(df, "stage_in-run_identifymcs", "run_identifymcs", 
                           "ssd-ssd", "ssd", 1,1)
    ssd_16n = find_spm_value(df, "stage_in-run_identifymcs", "run_identifymcs", 
                            "ssd-ssd", "ssd", 1, 1)
    
    tmpfs_4n = find_spm_value(df, "stage_in-run_identifymcs", "run_identifymcs", 
                             "tmpfs-tmpfs", "tmpfs", 1,1)
    tmpfs_8n = find_spm_value(df, "stage_in-run_identifymcs", "run_identifymcs", 
                             "tmpfs-tmpfs", "tmpfs", 1,1)
    tmpfs_16n = find_spm_value(df, "stage_in-run_identifymcs", "run_identifymcs", 
                              "tmpfs-tmpfs", "tmpfs", 1, 1)
    
    beegfs_4n = find_spm_value(df, "stage_in-run_identifymcs", "run_identifymcs", 
                              "beegfs", "beegfs", 60, 1)
    beegfs_8n = find_spm_value(df, "stage_in-run_identifymcs", "run_identifymcs", 
                              "beegfs", "beegfs", 30, 1)
    beegfs_16n = find_spm_value(df, "stage_in-run_identifymcs", "run_identifymcs", 
                               "beegfs", "beegfs", 15, 1)
    
    # Second 3 values: run_identifymcs+run_matchpf (CORRECTED: consumerTasksPerNode = 1)
    ssd_4n_2 = find_spm_value(df, "run_identifymcs", "run_matchpf", 
                              "ssd", "ssd", 1, 1)
    ssd_8n_2 = find_spm_value(df, "run_identifymcs", "run_matchpf", 
                              "ssd", "ssd", 1, 1)
    ssd_16n_2 = find_spm_value(df, "run_identifymcs", "run_matchpf", 
                               "ssd", "ssd", 1, 1)
    
    tmpfs_4n_2 = find_spm_value(df, "run_identifymcs", "run_matchpf", 
                                "tmpfs", "tmpfs", 1, 1)
    tmpfs_8n_2 = find_spm_value(df, "run_identifymcs", "run_matchpf", 
                                "tmpfs", "tmpfs", 1, 1)
    tmpfs_16n_2 = find_spm_value(df, "run_identifymcs", "run_matchpf", 
                                 "tmpfs", "tmpfs", 1, 1)
    
    beegfs_4n_2 = find_spm_value(df, "run_identifymcs", "run_matchpf", 
                                 "beegfs", "beegfs", 1, 1)
    beegfs_8n_2 = find_spm_value(df, "run_identifymcs", "run_matchpf", 
                                 "beegfs", "beegfs", 1, 1)
    beegfs_16n_2 = find_spm_value(df, "run_identifymcs", "run_matchpf", 
                                  "beegfs", "beegfs", 1, 1)
    
    spm_data["idfymcs+matchpf"] = [
        [ssd_4n, ssd_4n_2], [ssd_8n, ssd_8n_2], [ssd_16n, ssd_16n_2],
        [tmpfs_4n, tmpfs_4n_2], [tmpfs_8n, tmpfs_8n_2], [tmpfs_16n, tmpfs_16n_2],
        [beegfs_4n, beegfs_4n_2], [beegfs_8n, beegfs_8n_2], [beegfs_16n, beegfs_16n_2]
    ]
    
    print("idfymcs+matchpf values:", spm_data["idfymcs+matchpf"])
    
    # 6. matchpf+robustmcs: stage_in-run_matchpf+run_matchpf and run_matchpf+run_robustmcs
    print("\n6. Processing matchpf+robustmcs...")
    
    # First 3 values: stage_in-run_matchpf+run_matchpf
    ssd_4n = find_spm_value(df, "stage_in-run_matchpf", "run_matchpf", 
                           "ssd-ssd", "ssd", 1,1)
    ssd_8n = find_spm_value(df, "stage_in-run_matchpf", "run_matchpf", 
                           "ssd-ssd", "ssd", 1,1)
    ssd_16n = find_spm_value(df, "stage_in-run_matchpf", "run_matchpf", 
                            "ssd-ssd", "ssd", 1, 1)
    
    tmpfs_4n = find_spm_value(df, "stage_in-run_matchpf", "run_matchpf", 
                             "tmpfs-tmpfs", "tmpfs", 1,1)
    tmpfs_8n = find_spm_value(df, "stage_in-run_matchpf", "run_matchpf", 
                             "tmpfs-tmpfs", "tmpfs", 1,1)
    tmpfs_16n = find_spm_value(df, "stage_in-run_matchpf", "run_matchpf", 
                              "tmpfs-tmpfs", "tmpfs", 1, 1)
    
    beegfs_4n = find_spm_value(df, "stage_in-run_matchpf", "run_matchpf", 
                              "beegfs", "beegfs", 60, 1)
    beegfs_8n = find_spm_value(df, "stage_in-run_matchpf", "run_matchpf", 
                              "beegfs", "beegfs", 30, 1)
    beegfs_16n = find_spm_value(df, "stage_in-run_matchpf", "run_matchpf", 
                               "beegfs", "beegfs", 15, 1)
    
    # Second 3 values: run_matchpf+run_robustmcs
    ssd_4n_2 = find_spm_value(df, "run_matchpf", "run_robustmcs", 
                              "ssd", "ssd", 1, 1)
    ssd_8n_2 = find_spm_value(df, "run_matchpf", "run_robustmcs", 
                              "ssd", "ssd", 1, 1)
    ssd_16n_2 = find_spm_value(df, "run_matchpf", "run_robustmcs", 
                               "ssd", "ssd", 1, 1)
    
    tmpfs_4n_2 = find_spm_value(df, "run_matchpf", "run_robustmcs", 
                                "tmpfs", "tmpfs", 1, 1)
    tmpfs_8n_2 = find_spm_value(df, "run_matchpf", "run_robustmcs", 
                                "tmpfs", "tmpfs", 1, 1)
    tmpfs_16n_2 = find_spm_value(df, "run_matchpf", "run_robustmcs", 
                                 "tmpfs", "tmpfs", 1, 1)
    
    beegfs_4n_2 = find_spm_value(df, "run_matchpf", "run_robustmcs", 
                                 "beegfs", "beegfs", 1, 1)
    beegfs_8n_2 = find_spm_value(df, "run_matchpf", "run_robustmcs", 
                                 "beegfs", "beegfs", 1, 1)
    beegfs_16n_2 = find_spm_value(df, "run_matchpf", "run_robustmcs", 
                                  "beegfs", "beegfs", 1, 1)
    
    spm_data["matchpf+robustmcs"] = [
        [ssd_4n, ssd_4n_2], [ssd_8n, ssd_8n_2], [ssd_16n, ssd_16n_2],
        [tmpfs_4n, tmpfs_4n_2], [tmpfs_8n, tmpfs_8n_2], [tmpfs_16n, tmpfs_16n_2],
        [beegfs_4n, beegfs_4n_2], [beegfs_8n, beegfs_8n_2], [beegfs_16n, beegfs_16n_2]
    ]
    
    print("matchpf+robustmcs values:", spm_data["matchpf+robustmcs"])
    
    # 7. robustmcs+speed: stage_in-run_robustmcs+run_robustmcs and run_robustmcs+stage_out-run_robustmcs 
    # and stage_in-run_speed+run_speed and run_speed+stage_out-run_speed
    print("\n7. Processing robustmcs+speed...")
    
    # First 3 values: stage_in-run_robustmcs+run_robustmcs
    ssd_4n = find_spm_value(df, "stage_in-run_robustmcs", "run_robustmcs", 
                           "ssd-ssd", "ssd", 1, 1)
    ssd_8n = find_spm_value(df, "stage_in-run_robustmcs", "run_robustmcs", 
                           "ssd-ssd", "ssd", 1, 1)
    ssd_16n = find_spm_value(df, "stage_in-run_robustmcs", "run_robustmcs", 
                            "ssd-ssd", "ssd", 1, 1)
    
    tmpfs_4n = find_spm_value(df, "stage_in-run_robustmcs", "run_robustmcs", 
                             "tmpfs-tmpfs", "tmpfs", 1, 1)
    tmpfs_8n = find_spm_value(df, "stage_in-run_robustmcs", "run_robustmcs", 
                             "tmpfs-tmpfs", "tmpfs", 1, 1)
    tmpfs_16n = find_spm_value(df, "stage_in-run_robustmcs", "run_robustmcs", 
                              "tmpfs-tmpfs", "tmpfs", 1, 1)
    
    beegfs_4n = find_spm_value(df, "stage_in-run_robustmcs", "run_robustmcs", 
                              "beegfs", "beegfs", 60, 1)
    beegfs_8n = find_spm_value(df, "stage_in-run_robustmcs", "run_robustmcs", 
                              "beegfs", "beegfs", 30, 1)
    beegfs_16n = find_spm_value(df, "stage_in-run_robustmcs", "run_robustmcs", 
                               "beegfs", "beegfs", 15, 1)
    
    # # Second 3 values: run_robustmcs+run_speed
    # ssd_4n_2 = find_spm_value(df, "run_robustmcs", "run_speed", 
    #                           "ssd", "ssd", 1, 30)
    # ssd_8n_2 = find_spm_value(df, "run_robustmcs", "run_speed", 
    #                           "ssd", "ssd", 1, 15)
    # ssd_16n_2 = find_spm_value(df, "run_robustmcs", "run_speed", 
    #                            "ssd", "ssd", 1, 8)
    
    # tmpfs_4n_2 = find_spm_value(df, "run_robustmcs", "run_speed", 
    #                             "tmpfs", "tmpfs", 1, 30)
    # tmpfs_8n_2 = find_spm_value(df, "run_robustmcs", "run_speed", 
    #                             "tmpfs", "tmpfs", 1, 15)
    # tmpfs_16n_2 = find_spm_value(df, "run_robustmcs", "run_speed", 
    #                              "tmpfs", "tmpfs", 1, 8)
    
    # beegfs_4n_2 = find_spm_value(df, "run_robustmcs", "run_speed", 
    #                              "beegfs", "beegfs", 1, 30)
    # beegfs_8n_2 = find_spm_value(df, "run_robustmcs", "run_speed", 
    #                              "beegfs", "beegfs", 1, 15)
    # beegfs_16n_2 = find_spm_value(df, "run_robustmcs", "run_speed", 
    #                               "beegfs", "beegfs", 1, 8)

    # second 3 values: run_robustmcs+stage_out-run_robustmc
    ssd_4n_2 = find_spm_value(df, "run_robustmcs", "stage_out-run_robustmcs", 
                              "ssd", "ssd", 1, 1)
    ssd_8n_2 = find_spm_value(df, "run_robustmcs", "stage_out-run_robustmcs", 
                              "ssd", "ssd", 1, 1)
    ssd_16n_2 = find_spm_value(df, "run_robustmcs", "stage_out-run_robustmcs", 
                               "ssd", "ssd", 1, 1)
    
    tmpfs_4n_2 = find_spm_value(df, "run_robustmcs", "stage_out-run_robustmcs", 
                                "tmpfs", "tmpfs", 1, 1)
    tmpfs_8n_2 = find_spm_value(df, "run_robustmcs", "stage_out-run_robustmcs", 
                                "tmpfs", "tmpfs", 1, 1)
    tmpfs_16n_2 = find_spm_value(df, "run_robustmcs", "stage_out-run_robustmcs", 
                                 "tmpfs", "tmpfs", 1, 1)
    
    beegfs_4n_2 = find_spm_value(df, "run_robustmcs", "stage_out-run_robustmcs", 
                                "beegfs", "beegfs", 1, 1)
    beegfs_8n_2 = find_spm_value(df, "run_robustmcs", "stage_out-run_robustmcs", 
                                "beegfs", "beegfs", 1, 1)
    beegfs_16n_2 = find_spm_value(df, "run_robustmcs", "stage_out-run_robustmcs", 
                                  "beegfs", "beegfs", 1, 1)

    # Third 3 values: stage_in-run_speed+run_speed
    ssd_4n_3 = find_spm_value(df, "stage_in-run_speed", "run_speed", 
                              "ssd-ssd", "ssd", 7, 30)
    ssd_8n_3 = find_spm_value(df, "stage_in-run_speed", "run_speed", 
                              "ssd-ssd", "ssd", 4, 15)
    ssd_16n_3 = find_spm_value(df, "stage_in-run_speed", "run_speed", 
                               "ssd-ssd", "ssd", 1, 8)

    tmpfs_4n_3 = find_spm_value(df, "stage_in-run_speed", "run_speed", 
                                "tmpfs-tmpfs", "tmpfs", 7, 30)
    tmpfs_8n_3 = find_spm_value(df, "stage_in-run_speed", "run_speed", 
                                "tmpfs-tmpfs", "tmpfs", 4, 15)
    tmpfs_16n_3 = find_spm_value(df, "stage_in-run_speed", "run_speed", 
                                 "tmpfs-tmpfs", "tmpfs", 1, 8)

    beegfs_4n_3 = find_spm_value(df, "stage_in-run_speed", "run_speed", 
                                 "beegfs", "beegfs", 7, 30)
    beegfs_8n_3 = find_spm_value(df, "stage_in-run_speed", "run_speed", 
                                 "beegfs", "beegfs", 4, 15)
    beegfs_16n_3 = find_spm_value(df, "stage_in-run_speed", "run_speed", 
                                  "beegfs", "beegfs", 1, 8)

    # fourth 3 values: run_speed+stage_out-run_speed
    ssd_4n_4 = find_spm_value(df, "run_speed", "stage_out-run_speed", 
                              "ssd", "ssd", 30, 60)
    ssd_8n_4 = find_spm_value(df, "run_speed", "stage_out-run_speed", 
                              "ssd", "ssd", 15, 30)
    ssd_16n_4 = find_spm_value(df, "run_speed", "stage_out-run_speed", 
                               "ssd", "ssd", 8, 15)
    
    tmpfs_4n_4 = find_spm_value(df, "run_speed", "stage_out-run_speed", 
                                "tmpfs", "tmpfs", 30, 60)
    tmpfs_8n_4 = find_spm_value(df, "run_speed", "stage_out-run_speed", 
                                "tmpfs", "tmpfs", 15, 30)
    tmpfs_16n_4 = find_spm_value(df, "run_speed", "stage_out-run_speed", 
                                 "tmpfs", "tmpfs", 8, 15)
    
    beegfs_4n_4 = find_spm_value(df, "run_speed", "stage_out-run_speed", 
                                 "beegfs", "beegfs", 30, 60)
    beegfs_8n_4 = find_spm_value(df, "run_speed", "stage_out-run_speed", 
                                "beegfs", "beegfs", 15, 30)
    beegfs_16n_4 = find_spm_value(df, "run_speed", "stage_out-run_speed", 
                                  "beegfs", "beegfs", 8, 15)

    spm_data["robustmcs+speed"] = [
        [ssd_4n, ssd_4n_2, ssd_4n_3, ssd_4n_4], [ssd_8n, ssd_8n_2, ssd_8n_3, ssd_8n_4], [ssd_16n, ssd_16n_2, ssd_16n_3, ssd_16n_4],
        [tmpfs_4n, tmpfs_4n_2, tmpfs_4n_3, tmpfs_4n_4], [tmpfs_8n, tmpfs_8n_2, tmpfs_8n_3, tmpfs_8n_4], [tmpfs_16n, tmpfs_16n_2, tmpfs_16n_3, tmpfs_16n_4],
        [beegfs_4n, beegfs_4n_2, beegfs_4n_3, beegfs_4n_4], [beegfs_8n, beegfs_8n_2, beegfs_8n_3, beegfs_8n_4], [beegfs_16n, beegfs_16n_2, beegfs_16n_3, beegfs_16n_4]
    ]
    
    print("robustmcs+speed values:", spm_data["robustmcs+speed"])

    
    # 8. mapfea+speed: run_mapfeature+run_speed
    # 8. stage_in-run_mapfeature+run_mapfeature and run_mapfeature+stage_out-run_mapfeature
    #  and stage_in-run_speed+run_speed and run_speed+stage_out-run_speed
    print("\n8. Processing mapfea+speed...")

    # First 3 values: stage_in-run_mapfeature+run_mapfeature
    ssd_4n = find_spm_value(df, "stage_in-run_mapfeature", "run_mapfeature", 
                           "ssd-ssd", "ssd", 7, 30)
    ssd_8n = find_spm_value(df, "stage_in-run_mapfeature", "run_mapfeature", 
                           "ssd-ssd", "ssd", 4, 15)
    ssd_16n = find_spm_value(df, "stage_in-run_mapfeature", "run_mapfeature", 
                            "ssd-ssd", "ssd", 1, 8)
    
    tmpfs_4n = find_spm_value(df, "stage_in-run_mapfeature", "run_mapfeature", 
                             "tmpfs-tmpfs", "tmpfs", 7, 30)
    tmpfs_8n = find_spm_value(df, "stage_in-run_mapfeature", "run_mapfeature", 
                             "tmpfs-tmpfs", "tmpfs", 4, 15)
    tmpfs_16n = find_spm_value(df, "stage_in-run_mapfeature", "run_mapfeature", 
                              "tmpfs-tmpfs", "tmpfs", 1, 8)
    
    beegfs_4n = find_spm_value(df, "stage_in-run_mapfeature", "run_mapfeature", 
                              "beegfs", "beegfs", 60, 30)
    beegfs_8n = find_spm_value(df, "stage_in-run_mapfeature", "run_mapfeature", 
                              "beegfs", "beegfs", 30, 15)
    beegfs_16n = find_spm_value(df, "stage_in-run_mapfeature", "run_mapfeature", 
                               "beegfs", "beegfs", 15, 8)
    
    # For run_mapfeature+stage_out-run_mapfeature
    ssd_4n_2 = find_spm_value(df, "run_mapfeature", "stage_out-run_mapfeature", 
                              "ssd", "ssd", 30, 60)
    ssd_8n_2 = find_spm_value(df, "run_mapfeature", "stage_out-run_mapfeature", 
                              "ssd", "ssd", 15, 30)
    ssd_16n_2 = find_spm_value(df, "run_mapfeature", "stage_out-run_mapfeature", 
                              "ssd", "ssd", 8, 15)

    tmpfs_4n_2 = find_spm_value(df, "run_mapfeature", "stage_out-run_mapfeature", 
                              "tmpfs", "tmpfs", 30, 60)
    tmpfs_8n_2 = find_spm_value(df, "run_mapfeature", "stage_out-run_mapfeature", 
                              "tmpfs", "tmpfs", 15, 30)
    tmpfs_16n_2 = find_spm_value(df, "run_mapfeature", "stage_out-run_mapfeature", 
                              "tmpfs", "tmpfs", 8, 15)

    beegfs_4n_2 = find_spm_value(df, "run_mapfeature", "stage_out-run_mapfeature", 
                              "beegfs", "beegfs", 30, 60)
    beegfs_8n_2 = find_spm_value(df, "run_mapfeature", "stage_out-run_mapfeature", 
                              "beegfs", "beegfs", 15, 30)
    beegfs_16n_2 = find_spm_value(df, "run_mapfeature", "stage_out-run_mapfeature", 
                              "beegfs", "beegfs", 8, 15)

    # For stage_in-run_speed+run_speed
    ssd_4n_3 = find_spm_value(df, "stage_in-run_speed", "run_speed", 
                              "ssd-ssd", "ssd", 7, 30)
    ssd_8n_3 = find_spm_value(df, "stage_in-run_speed", "run_speed", 
                              "ssd-ssd", "ssd", 4, 15)
    ssd_16n_3 = find_spm_value(df, "stage_in-run_speed", "run_speed", 
                              "ssd-ssd", "ssd", 1, 8)

    tmpfs_4n_3 = find_spm_value(df, "stage_in-run_speed", "run_speed", 
                              "tmpfs-tmpfs", "tmpfs", 7, 30)
    tmpfs_8n_3 = find_spm_value(df, "stage_in-run_speed", "run_speed", 
                              "tmpfs-tmpfs", "tmpfs", 4, 15)
    tmpfs_16n_3 = find_spm_value(df, "stage_in-run_speed", "run_speed", 
                              "tmpfs-tmpfs", "tmpfs", 1, 8)
    
    beegfs_4n_3 = find_spm_value(df, "stage_in-run_speed", "run_speed", 
                              "beegfs", "beegfs", 7, 30)
    beegfs_8n_3 = find_spm_value(df, "stage_in-run_speed", "run_speed", 
                              "beegfs", "beegfs", 4, 15)
    beegfs_16n_3 = find_spm_value(df, "stage_in-run_speed", "run_speed", 
                              "beegfs", "beegfs", 1, 8)
    
    # For run_speed+stage_out-run_speed
    ssd_4n_4 = find_spm_value(df, "run_speed", "stage_out-run_speed", 
                              "ssd", "ssd", 30, 60)
    ssd_8n_4 = find_spm_value(df, "run_speed", "stage_out-run_speed", 
                              "ssd", "ssd", 15, 30)
    ssd_16n_4 = find_spm_value(df, "run_speed", "stage_out-run_speed", 
                              "ssd", "ssd", 8, 15)

    tmpfs_4n_4 = find_spm_value(df, "run_speed", "stage_out-run_speed", 
                                "tmpfs", "tmpfs", 30, 60)
    tmpfs_8n_4 = find_spm_value(df, "run_speed", "stage_out-run_speed", 
                                "tmpfs", "tmpfs", 15, 30)
    tmpfs_16n_4 = find_spm_value(df, "run_speed", "stage_out-run_speed", 
                                "tmpfs", "tmpfs", 8, 15)
    
    beegfs_4n_4 = find_spm_value(df, "run_speed", "stage_out-run_speed", 
                                "beegfs", "beegfs", 30, 60)
    beegfs_8n_4 = find_spm_value(df, "run_speed", "stage_out-run_speed", 
                                "beegfs", "beegfs", 15, 30)
    beegfs_16n_4 = find_spm_value(df, "run_speed", "stage_out-run_speed", 
                                "beegfs", "beegfs", 8, 15)


    spm_data["mapfea+speed"] = [
        [ssd_4n, ssd_4n_2, ssd_4n_3, ssd_4n_4], [ssd_8n, ssd_8n_2, ssd_8n_3, ssd_8n_4], [ssd_16n, ssd_16n_2, ssd_16n_3, ssd_16n_3],
        [tmpfs_4n, tmpfs_4n_2, tmpfs_4n_3, tmpfs_4n_4], [tmpfs_8n, tmpfs_8n_2, tmpfs_8n_3, tmpfs_8n_4], [tmpfs_16n, tmpfs_16n_2, tmpfs_16n_3, tmpfs_16n_4],
        [beegfs_4n, beegfs_4n_2, beegfs_4n_3, beegfs_4n_4], [beegfs_8n, beegfs_8n_2, beegfs_8n_3, beegfs_8n_4], [beegfs_16n, beegfs_16n_2, beegfs_16n_3, beegfs_16n_4]
    ]
    
    print("mapfea+speed values:", spm_data["mapfea+speed"])
    
    return spm_data

def main():
    """Main function to load and display SPM data"""
    
    # File path
    csv_file = "../workflow_spm_results/pyflex_240f_filtered_spm_results.csv"
    
    try:
        # Load the SPM data
        spm_data = load_spm_data_from_csv(csv_file)
        
        # Print the final structure
        print("\n" + "="*80)
        print("FINAL SPM DATA STRUCTURE")
        print("="*80)
        
        for key, values in spm_data.items():
            if key == "store_conf":
                print(f"\n{key}: {values}")
            else: 
                print(f"\n{key}:")
                for i, pair in enumerate(values):
                    # there are 2 or 3 or 4 values in each pair
                    pair_num = len(pair)
                    ptr_str = ""
                    for j in range(pair_num):
                        val = pair[j]
                        if val is not None:
                            ptr_str += f"{val}, "
                    total = sum(val for val in pair if val is not None)
                    print(f"  {spm_data['store_conf'][i]}: [{ptr_str}] = {total}")
        
        print("\n" + "="*80)
        print("COPYABLE FORMAT:")
        print("="*80)
        print("spm_data = {")
        print(f'    "store_conf": {spm_data["store_conf"]},')
        
        for key, values in spm_data.items():
            if key != "store_conf":
                # Calculate sums for each pair list
                sums = []
                for pair in values:
                    pair_num = len(pair)
                    sumval = 0
                    for i in range(pair_num):
                        val = pair[i]
                        
                        if val is not None:
                            sumval += val
                    sums.append(float(sumval))

                print(f'    "{key}": {sums},')
        
        print("}")
        
        return spm_data
        
    except FileNotFoundError:
        print(f"Error: File not found: {csv_file}")
        return None
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

if __name__ == "__main__":
    main()
