#!/usr/bin/env python3
"""
Load SPM data from CSV file for 1kgenome workflow

This script loads data from the SPM results CSV and filters it according to
the specific producer-consumer pairs for 1kgenome workflow:
- indiv+merge: stage_in-individuals+individuals and individuals+individuals_merge
- merge+mutation: individuals_merge+mutation_overlap
- merge+freq: individuals_merge+frequency
- sift+mutation: sifting+mutation_overlap
- sift+freq: sifting+frequency
"""

import pandas as pd
import numpy as np

def load_spm_data_from_csv(csv_file):
    """Load SPM data from CSV file for 1kgenome workflow"""
    
    # Read the CSV file
    df = pd.read_csv(csv_file)
    print(f"Loaded CSV with {len(df)} rows")
    print("Columns:", df.columns.tolist())
    print("\nFirst 5 rows:")
    print(df.head())
    
    # Initialize the spm_data dictionary
    spm_data = {
        "store_conf": [
            "SSD 2n", "SSD 5n", "SSD 10n",
            "TMPFS 2n", "TMPFS 5n", "TMPFS 10n",
            "BeeGFS 2n", "BeeGFS 5n", "BeeGFS 10n"
        ],
        "indiv+merge": [],
        "merge+mutation": [],
        "merge+freq": [],
        "sift+mutation": [],
        "sift+freq": []
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
    print("EXTRACTING SPM VALUES FOR 1KGENOME WORKFLOW")
    print("="*80)
    
    # 1. indiv+merge: stage_in-individuals+individuals and individuals+individuals_merge
    print("\n1. Processing indiv+merge...")
    
    # First 3 values: stage_in-individuals+individuals
    # SSD configurations
    ssd_2n = find_spm_value(df, "stage_in-individuals", "individuals", 
                           "ssd", "ssd", 150, 150)
    ssd_5n = find_spm_value(df, "stage_in-individuals", "individuals", 
                           "ssd", "ssd", 60, 60)
    ssd_10n = find_spm_value(df, "stage_in-individuals", "individuals", 
                            "ssd", "ssd", 30, 30)
    
    # TMPFS configurations  
    tmpfs_2n = find_spm_value(df, "stage_in-individuals", "individuals", 
                             "tmpfs", "tmpfs", 150, 150)
    tmpfs_5n = find_spm_value(df, "stage_in-individuals", "individuals", 
                             "tmpfs", "tmpfs", 60, 60)
    tmpfs_10n = find_spm_value(df, "stage_in-individuals", "individuals", 
                              "tmpfs", "tmpfs", 30, 30)
    
    # BeeGFS configurations
    beegfs_2n = find_spm_value(df, "stage_in-individuals", "individuals", 
                              "beegfs", "beegfs", 150, 150)
    beegfs_5n = find_spm_value(df, "stage_in-individuals", "individuals", 
                              "beegfs", "beegfs", 60, 60)
    beegfs_10n = find_spm_value(df, "stage_in-individuals", "individuals", 
                               "beegfs", "beegfs", 30, 30)
    
    # Second 3 values: individuals+individuals_merge
    # SSD configurations
    ssd_2n_2 = find_spm_value(df, "individuals", "individuals_merge", 
                              "ssd", "ssd", 150, 150)
    ssd_5n_2 = find_spm_value(df, "individuals", "individuals_merge", 
                              "ssd", "ssd", 60, 60)
    ssd_10n_2 = find_spm_value(df, "individuals", "individuals_merge", 
                               "ssd", "ssd", 5, 5)
    
    # TMPFS configurations
    tmpfs_2n_2 = find_spm_value(df, "individuals", "individuals_merge", 
                                "tmpfs", "tmpfs", 150, 150)
    tmpfs_5n_2 = find_spm_value(df, "individuals", "individuals_merge", 
                                "tmpfs", "tmpfs", 60, 60)
    tmpfs_10n_2 = find_spm_value(df, "individuals", "individuals_merge", 
                                 "tmpfs", "tmpfs", 5, 5)
    
    # BeeGFS configurations
    beegfs_2n_2 = find_spm_value(df, "individuals", "individuals_merge", 
                                 "beegfs", "beegfs", 150, 150)
    beegfs_5n_2 = find_spm_value(df, "individuals", "individuals_merge", 
                                 "beegfs", "beegfs", 60, 60)
    beegfs_10n_2 = find_spm_value(df, "individuals", "individuals_merge", 
                                  "beegfs", "beegfs", 5, 5)
    
    # Combine all values for indiv+merge
    spm_data["indiv+merge"] = [
        [ssd_2n, ssd_2n_2], [ssd_5n, ssd_5n_2], [ssd_10n, ssd_10n_2],
        [tmpfs_2n, tmpfs_2n_2], [tmpfs_5n, tmpfs_5n_2], [tmpfs_10n, tmpfs_10n_2],
        [beegfs_2n, beegfs_2n_2], [beegfs_5n, beegfs_5n_2], [beegfs_10n, beegfs_10n_2]
    ]
    
    print("indiv+merge values:", spm_data["indiv+merge"])
    
    # 2. merge+mutation: individuals_merge+mutation_overlap and mutation_overlap+stage_out-mutation_overlap
    print("\n2. Processing merge+mutation...")
    
    # First 3 values: individuals_merge+mutation_overlap
    # SSD configurations
    ssd_2n = find_spm_value(df, "individuals_merge", "mutation_overlap", 
                           "ssd", "ssd", 5, 5)
    ssd_5n = find_spm_value(df, "individuals_merge", "mutation_overlap", 
                           "ssd", "ssd", 2, 2)
    ssd_10n = find_spm_value(df, "individuals_merge", "mutation_overlap", 
                            "ssd", "ssd", 1, 1)
    
    # TMPFS configurations
    tmpfs_2n = find_spm_value(df, "individuals_merge", "mutation_overlap", 
                             "tmpfs", "tmpfs", 5, 5)
    tmpfs_5n = find_spm_value(df, "individuals_merge", "mutation_overlap", 
                             "tmpfs", "tmpfs", 2, 2)
    tmpfs_10n = find_spm_value(df, "individuals_merge", "mutation_overlap", 
                              "tmpfs", "tmpfs", 1, 1)
    
    # BeeGFS configurations
    beegfs_2n = find_spm_value(df, "individuals_merge", "mutation_overlap", 
                              "beegfs", "beegfs", 5, 5)
    beegfs_5n = find_spm_value(df, "individuals_merge", "mutation_overlap", 
                              "beegfs", "beegfs", 2, 2)
    beegfs_10n = find_spm_value(df, "individuals_merge", "mutation_overlap", 
                               "beegfs", "beegfs", 1, 1)
    
    # Second 3 values: mutation_overlap+stage_out-mutation_overlap
    ssd_2n_2 = find_spm_value(df, "mutation_overlap", "stage_out-mutation_overlap", 
                              "ssd", "ssd", 5, 5)
    ssd_5n_2 = find_spm_value(df, "mutation_overlap", "stage_out-mutation_overlap", 
                              "ssd", "ssd", 2, 2)
    ssd_10n_2 = find_spm_value(df, "mutation_overlap", "stage_out-mutation_overlap", 
                              "ssd", "ssd", 1, 1)
    
    tmpfs_2n_2 = find_spm_value(df, "mutation_overlap", "stage_out-mutation_overlap", 
                              "tmpfs", "tmpfs", 5, 5)
    tmpfs_5n_2 = find_spm_value(df, "mutation_overlap", "stage_out-mutation_overlap", 
                              "tmpfs", "tmpfs", 2, 2)
    tmpfs_10n_2 = find_spm_value(df, "mutation_overlap", "stage_out-mutation_overlap", 
                              "tmpfs", "tmpfs", 1, 1)
    
    beegfs_2n_2 = find_spm_value(df, "mutation_overlap", "stage_out-mutation_overlap", 
                              "beegfs", "beegfs", 5, 5)
    beegfs_5n_2 = find_spm_value(df, "mutation_overlap", "stage_out-mutation_overlap", 
                              "beegfs", "beegfs", 2, 2)
    beegfs_10n_2 = find_spm_value(df, "mutation_overlap", "stage_out-mutation_overlap", 
                              "beegfs", "beegfs", 1, 1)

    # Combine all values for merge+mutation
    spm_data["merge+mutation"] = [
        [ssd_2n, ssd_2n_2], [ssd_5n, ssd_5n_2], [ssd_10n, ssd_10n_2],
        [tmpfs_2n, tmpfs_2n_2], [tmpfs_5n, tmpfs_5n_2], [tmpfs_10n, tmpfs_10n_2],
        [beegfs_2n, beegfs_2n_2], [beegfs_5n, beegfs_5n_2], [beegfs_10n, beegfs_10n_2]
    ]
    
    print("merge+mutation values:", spm_data["merge+mutation"])
    
    # 3. merge+freq: individuals_merge+frequency and frequency+stage_out-frequency
    print("\n3. Processing merge+freq...")
    
    # First 3 values: individuals_merge+frequency
    # SSD configurations
    ssd_2n = find_spm_value(df, "individuals_merge", "frequency", 
                           "ssd", "ssd", 5, 5)
    ssd_5n = find_spm_value(df, "individuals_merge", "frequency", 
                           "ssd", "ssd", 2, 2)
    ssd_10n = find_spm_value(df, "individuals_merge", "frequency", 
                            "ssd", "ssd", 1, 1)
    
    # TMPFS configurations
    tmpfs_2n = find_spm_value(df, "individuals_merge", "frequency", 
                             "tmpfs", "tmpfs", 5, 5)
    tmpfs_5n = find_spm_value(df, "individuals_merge", "frequency", 
                             "tmpfs", "tmpfs", 2, 2)
    tmpfs_10n = find_spm_value(df, "individuals_merge", "frequency", 
                              "tmpfs", "tmpfs", 1, 1)
    
    # BeeGFS configurations
    beegfs_2n = find_spm_value(df, "individuals_merge", "frequency", 
                              "beegfs", "beegfs", 5, 5)
    beegfs_5n = find_spm_value(df, "individuals_merge", "frequency", 
                              "beegfs", "beegfs", 2, 2)
    beegfs_10n = find_spm_value(df, "individuals_merge", "frequency", 
                               "beegfs", "beegfs", 1, 1)
    
    # Second 3 values: frequency+stage_out-frequency
    ssd_2n_2 = find_spm_value(df, "frequency", "stage_out-frequency", 
                              "ssd", "ssd", 5, 5)
    ssd_5n_2 = find_spm_value(df, "frequency", "stage_out-frequency", 
                              "ssd", "ssd", 2, 2)
    ssd_10n_2 = find_spm_value(df, "frequency", "stage_out-frequency", 
                              "ssd", "ssd", 1, 1)
    
    tmpfs_2n_2 = find_spm_value(df, "frequency", "stage_out-frequency", 
                              "tmpfs", "tmpfs", 5, 5)
    tmpfs_5n_2 = find_spm_value(df, "frequency", "stage_out-frequency", 
                              "tmpfs", "tmpfs", 2, 2)
    tmpfs_10n_2 = find_spm_value(df, "frequency", "stage_out-frequency", 
                              "tmpfs", "tmpfs", 1, 1)
    
    beegfs_2n_2 = find_spm_value(df, "frequency", "stage_out-frequency", 
                              "beegfs", "beegfs", 5, 5)
    beegfs_5n_2 = find_spm_value(df, "frequency", "stage_out-frequency", 
                              "beegfs", "beegfs", 2, 2)
    beegfs_10n_2 = find_spm_value(df, "frequency", "stage_out-frequency", 
                              "beegfs", "beegfs", 1, 1)
    
    # Combine all values for merge+freq
    spm_data["merge+freq"] = [
        [ssd_2n, ssd_2n_2], [ssd_5n, ssd_5n_2], [ssd_10n, ssd_10n_2],
        [tmpfs_2n, tmpfs_2n_2], [tmpfs_5n, tmpfs_5n_2], [tmpfs_10n, tmpfs_10n_2],
        [beegfs_2n, beegfs_2n_2], [beegfs_5n, beegfs_5n_2], [beegfs_10n, beegfs_10n_2]
    ]
    
    print("merge+freq values:", spm_data["merge+freq"])
    
    # 4. sift+mutation: sifting+mutation_overlap and mutation_overlap+stage_out-mutation_overlap
    print("\n4. Processing sift+mutation...")
    
    # First 3 values: sifting+mutation_overlap
    # SSD configurations
    ssd_2n = find_spm_value(df, "sifting", "mutation_overlap", 
                           "ssd", "ssd", 5, 5)
    ssd_5n = find_spm_value(df, "sifting", "mutation_overlap", 
                           "ssd", "ssd", 2, 2)
    ssd_10n = find_spm_value(df, "sifting", "mutation_overlap", 
                            "ssd", "ssd", 1, 1)
    
    # TMPFS configurations
    tmpfs_2n = find_spm_value(df, "sifting", "mutation_overlap", 
                             "tmpfs", "tmpfs", 5, 5)
    tmpfs_5n = find_spm_value(df, "sifting", "mutation_overlap", 
                             "tmpfs", "tmpfs", 2, 2)
    tmpfs_10n = find_spm_value(df, "sifting", "mutation_overlap", 
                              "tmpfs", "tmpfs", 1, 1)
    
    # BeeGFS configurations
    beegfs_2n = find_spm_value(df, "sifting", "mutation_overlap", 
                              "beegfs", "beegfs", 5, 5)
    beegfs_5n = find_spm_value(df, "sifting", "mutation_overlap", 
                              "beegfs", "beegfs", 2, 2)
    beegfs_10n = find_spm_value(df, "sifting", "mutation_overlap", 
                               "beegfs", "beegfs", 1, 1)
    
    # Second 3 values: mutation_overlap+stage_out-mutation_overlap
    ssd_2n_2 = find_spm_value(df, "mutation_overlap", "stage_out-mutation_overlap", 
                              "ssd", "ssd", 5, 5)
    ssd_5n_2 = find_spm_value(df, "mutation_overlap", "stage_out-mutation_overlap", 
                              "ssd", "ssd", 2, 2)
    ssd_10n_2 = find_spm_value(df, "mutation_overlap", "stage_out-mutation_overlap", 
                              "ssd", "ssd", 1, 1)
    
    tmpfs_2n_2 = find_spm_value(df, "mutation_overlap", "stage_out-mutation_overlap", 
                              "tmpfs", "tmpfs", 5, 5)
    tmpfs_5n_2 = find_spm_value(df, "mutation_overlap", "stage_out-mutation_overlap", 
                              "tmpfs", "tmpfs", 2, 2)
    tmpfs_10n_2 = find_spm_value(df, "mutation_overlap", "stage_out-mutation_overlap", 
                              "tmpfs", "tmpfs", 1, 1)
    
    beegfs_2n_2 = find_spm_value(df, "mutation_overlap", "stage_out-mutation_overlap", 
                              "beegfs", "beegfs", 5, 5)
    beegfs_5n_2 = find_spm_value(df, "mutation_overlap", "stage_out-mutation_overlap", 
                              "beegfs", "beegfs", 2, 2)
    beegfs_10n_2 = find_spm_value(df, "mutation_overlap", "stage_out-mutation_overlap", 
                              "beegfs", "beegfs", 1, 1)
    
    # Combine all values for sift+mutation
    spm_data["sift+mutation"] = [
        [ssd_2n, ssd_2n_2], [ssd_5n, ssd_5n_2], [ssd_10n, ssd_10n_2],
        [tmpfs_2n, tmpfs_2n_2], [tmpfs_5n, tmpfs_5n_2], [tmpfs_10n, tmpfs_10n_2],
        [beegfs_2n, beegfs_2n_2], [beegfs_5n, beegfs_5n_2], [beegfs_10n, beegfs_10n_2]
    ]
    
    print("sift+mutation values:", spm_data["sift+mutation"])
    
    # 5. sift+freq: sifting+frequency and frequency+stage_out-frequency
    print("\n5. Processing sift+freq...")
    
    # First 3 values: sifting+frequency, no nodes to nodes data transfer
    # SSD configurations
    ssd_2n = find_spm_value(df, "sifting", "frequency", 
                           "ssd", "ssd", 5, 5)
    ssd_5n = find_spm_value(df, "sifting", "frequency", 
                           "ssd", "ssd", 2, 2)
    ssd_10n = find_spm_value(df, "sifting", "frequency", 
                            "ssd", "ssd", 1, 1)
    
    # TMPFS configurations
    tmpfs_2n = find_spm_value(df, "sifting", "frequency", 
                             "tmpfs", "tmpfs", 5, 5)
    tmpfs_5n = find_spm_value(df, "sifting", "frequency", 
                             "tmpfs", "tmpfs", 2, 2)
    tmpfs_10n = find_spm_value(df, "sifting", "frequency", 
                              "tmpfs", "tmpfs", 1, 1)
    
    # BeeGFS configurations
    beegfs_2n = find_spm_value(df, "sifting", "frequency", 
                              "beegfs", "beegfs", 5, 5)
    beegfs_5n = find_spm_value(df, "sifting", "frequency", 
                              "beegfs", "beegfs", 2, 2)
    beegfs_10n = find_spm_value(df, "sifting", "frequency", 
                               "beegfs", "beegfs", 1, 1)
    
    # Second 3 values: frequency+stage_out-frequency
    ssd_2n_2 = find_spm_value(df, "frequency", "stage_out-frequency", 
                              "ssd", "ssd", 5, 5)
    ssd_5n_2 = find_spm_value(df, "frequency", "stage_out-frequency", 
                              "ssd", "ssd", 2, 2)
    ssd_10n_2 = find_spm_value(df, "frequency", "stage_out-frequency", 
                              "ssd", "ssd", 1, 1)
    
    tmpfs_2n_2 = find_spm_value(df, "frequency", "stage_out-frequency", 
                              "tmpfs", "tmpfs", 5, 5)
    tmpfs_5n_2 = find_spm_value(df, "frequency", "stage_out-frequency", 
                              "tmpfs", "tmpfs", 2, 2)
    tmpfs_10n_2 = find_spm_value(df, "frequency", "stage_out-frequency", 
                              "tmpfs", "tmpfs", 1, 1)
    
    beegfs_2n_2 = find_spm_value(df, "frequency", "stage_out-frequency", 
                              "beegfs", "beegfs", 5, 5)
    beegfs_5n_2 = find_spm_value(df, "frequency", "stage_out-frequency", 
                              "beegfs", "beegfs", 2, 2)
    beegfs_10n_2 = find_spm_value(df, "frequency", "stage_out-frequency", 
                              "beegfs", "beegfs", 1, 1)

    
    # Combine all values for sift+freq
    spm_data["sift+freq"] = [
        [ssd_2n, ssd_2n_2], [ssd_5n, ssd_5n_2], [ssd_10n, ssd_10n_2],
        [tmpfs_2n, tmpfs_2n_2], [tmpfs_5n, tmpfs_5n_2], [tmpfs_10n, tmpfs_10n_2],
        [beegfs_2n, beegfs_2n_2], [beegfs_5n, beegfs_5n_2], [beegfs_10n, beegfs_10n_2]
    ]
    
    print("sift+freq values:", spm_data["sift+freq"])
    
    return spm_data

def main():
    """Main function to load and display SPM data"""
    
    # File path
    csv_file = "../workflow_spm_results/1kg_filtered_spm_results.csv"
    
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
                    # there are 1 or 2 values in each pair
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
