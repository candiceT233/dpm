import pandas as pd
import numpy as np
from collections import defaultdict
from .workflow_data_utils import standardize_operation


def insert_data_staging_rows(wf_df: pd.DataFrame, debug: bool = False) -> pd.DataFrame:
    """
    Insert data staging (I/O) rows into the workflow DataFrame to simulate data stage_in and stage_out.
    Rules:
    - Initial data movement from beegfs to ssd/tmpfs for stageOrder==1 tasks with operation=='read' (after normalization)
    - Intermediate data movement for each unique taskName with stageOrder >=1, for all combinations of [beegfs-ssd, beegfs-tmpfs, ssd-ssd, tmpfs-tmpfs]
    - Final data movement from tmpfs/ssd to beegfs for the last stage
    - Handles splitting by max parallelism of 60 files per row
    - Debug print statements can be toggled with the debug flag
    """
    # Copy to avoid modifying original
    wf_df = wf_df.copy()
    staging_rows = []
    fsblocksize = 4096  # Default block size for transferSize
    max_parallelism = 60

    # Helper: get unique files and their sizes for a set of rows
    def get_file_groups(rows):
        file_groups = []
        # Use the correct column name that exists in the DataFrame
        files = rows[['taskPID', 'fileName', 'aggregateFilesizeMB']].drop_duplicates()
        files = files.reset_index(drop=True)
        for i in range(0, len(files), max_parallelism):
            group = files.iloc[i:i+max_parallelism]
            # Extract individual file names from potentially comma-separated fileName fields
            all_file_names = []
            for fileName in group['fileName'].tolist():
                if ',' in fileName:
                    # Split by comma and strip whitespace
                    individual_files = [f.strip() for f in fileName.split(',')]
                    all_file_names.extend(individual_files)
                else:
                    all_file_names.append(fileName)
            
            # Remove duplicates while preserving order
            unique_file_names = []
            seen = set()
            for fname in all_file_names:
                if fname not in seen:
                    unique_file_names.append(fname)
                    seen.add(fname)
            
            # For each file_name, get the largest aggregateFilesizeMB from the original DataFrame
            max_sizes = []
            for fname in unique_file_names:
                # Find all rows in the original DataFrame with this fileName
                matches = wf_df[wf_df['fileName'] == fname]
                if not matches.empty:
                    # get minimum of aggregateFilesizeMB for each file_name
                    max_size = matches['aggregateFilesizeMB'].min()
                else:
                    max_size = 0
                max_sizes.append(max_size)
            agg_size = sum(max_sizes)
            parallelism = len(unique_file_names)
            file_groups.append((unique_file_names, agg_size, parallelism, group))
        return file_groups
    

    # 1. Initial data movement (first stage with read operations)
    # Find the first stage with read operations (stage 1 after normalization)
    all_read_ops = wf_df[wf_df['operation'].apply(lambda x: standardize_operation(x) == 'read')]
    if len(all_read_ops) > 0:
        first_stage_with_read = all_read_ops['stageOrder'].min()
        initial_rows = wf_df[(wf_df['stageOrder'] == first_stage_with_read) & (wf_df['operation'].apply(lambda x: standardize_operation(x) == 'read'))]
        if debug:
            print(f"Initial data movement: {len(initial_rows)} rows found in stage {first_stage_with_read}.")
        if not initial_rows.empty:
            file_groups = get_file_groups(initial_rows)
            numNodesList = initial_rows['numNodesList'].iloc[0] if 'numNodesList' in initial_rows.columns else [1]
            if isinstance(numNodesList, str):
                try:
                    numNodesList = eval(numNodesList)
                except Exception:
                    numNodesList = [int(numNodesList)]
            
            actual_task_names = set()
            for _, row in initial_rows.iterrows():
                actual_task_names.add(row['taskName'])
            
            # Add actual data movement rows
            for taskName in actual_task_names:
                for storageType in ['beegfs-tmpfs', 'beegfs-ssd', 'beegfs', 'ssd-beegfs', 'tmpfs-beegfs', 'ssd-ssd', 'tmpfs-tmpfs']:
                    for file_names, agg_size, parallelism, group in file_groups:
                        for numNodes in numNodesList:
                            if storageType == 'beegfs':
                                row = {
                                    'operation': 'none',  # No operation for stage_in pattern
                                    'randomOffset': 0,
                                    'transferSize': fsblocksize,
                                    'aggregateFilesizeMB': agg_size,  # Use actual data size
                                    'numTasks': parallelism,
                                    'parallelism': parallelism,
                                    'totalTime': 0,  # No time (virtual)
                                    'numNodesList': numNodesList,
                                    'numNodes': numNodes,
                                    'tasksPerNode': int(np.ceil(parallelism / numNodes)),
                                    'trMiB': 1.0,  # Dummy transfer rate to avoid division by zero
                                    'storageType': 'beegfs',  # Virtual producer storage type
                                    'opCount': parallelism,
                                    'taskName': f'stage_in-{taskName}',  # Virtual producer task name matching expected pattern
                                    'taskPID': '',
                                    'fileName': ','.join(file_names),
                                    'stageOrder': 0.5,  # Initial stage-in operations
                                    'prevTask': ''
                                }
                            else:
                                row = {
                                    'operation': 'cp',
                                    'randomOffset': 0,
                                    'transferSize': fsblocksize,
                                    'aggregateFilesizeMB': agg_size,
                                    'numTasks': parallelism,
                                    'parallelism': parallelism,
                                    'totalTime': '',
                                    'numNodesList': numNodesList,
                                    'numNodes': numNodes,
                                    'tasksPerNode': int(np.ceil(parallelism / numNodes)),
                                    'trMiB': '',
                                    'storageType': storageType,
                                    'opCount': parallelism,
                                    'taskName': f'stage_in-{taskName}',
                                    'taskPID': '',
                                    'fileName': ','.join(file_names),
                                    'stageOrder': 0.5,  # Initial stage-in operations
                                    'prevTask': ''
                                }
                            staging_rows.append(row)
                            if debug:
                                print(f"Added initial data movement row: {row}")

    # 1b. Add "none" operations for ALL tasks (virtual producers for every task)
    # This ensures every task has a stage_in-{taskName} with operation "none"
    for taskName, group in wf_df.groupby('taskName'):
        # Skip if taskName already contains 'stage_out' or 'stage_in'
        if 'stage_out' in taskName or 'stage_in' in taskName:
            continue
        
        stageOrder = group['stageOrder'].iloc[0]
        file_groups = get_file_groups(group)
        numNodesList = group['numNodesList'].iloc[0] if 'numNodesList' in group.columns else [1]
        if isinstance(numNodesList, str):
            try:
                numNodesList = eval(numNodesList)
            except Exception:
                numNodesList = [int(numNodesList)]
        
        # Add virtual "none" operation for every task
        for file_names, agg_size, parallelism, file_group in file_groups:
            for numNodes in numNodesList:
                row = {
                    'operation': 'none',  # Virtual operation for all tasks
                    'randomOffset': 0,
                    'transferSize': fsblocksize,
                    'aggregateFilesizeMB': agg_size,  # Use actual data size
                    'numTasks': parallelism,
                    'parallelism': parallelism,
                    'totalTime': 0,  # No time (virtual)
                    'numNodesList': numNodesList,
                    'numNodes': numNodes,
                    'tasksPerNode': int(np.ceil(parallelism / numNodes)),
                    'trMiB': 1.0,  # Dummy transfer rate to avoid division by zero
                    'storageType': 'beegfs',  # Virtual producer storage type
                    'opCount': parallelism,
                    'taskName': f'stage_in-{taskName}',  # Virtual producer task name matching expected pattern
                    'taskPID': '',
                    'fileName': ','.join(file_names),
                    'stageOrder': stageOrder - 0.5,  # Stage-in operations before the actual task
                    'prevTask': ''
                }
                staging_rows.append(row)
                if debug:
                    print(f"Added virtual 'none' operation for task {taskName}: {row}")

    # 1c. Add "none" operations for ALL stage_out tasks (virtual consumers for every task)
    # This ensures every task has a {taskName}-stage_out with operation "none"
    for taskName, group in wf_df.groupby('taskName'):
        # Skip if taskName already contains 'stage_out' or 'stage_in'
        if 'stage_out' in taskName or 'stage_in' in taskName:
            continue
        
        stageOrder = group['stageOrder'].iloc[0]
        file_groups = get_file_groups(group)
        numNodesList = group['numNodesList'].iloc[0] if 'numNodesList' in group.columns else [1]
        if isinstance(numNodesList, str):
            try:
                numNodesList = eval(numNodesList)
            except Exception:
                numNodesList = [int(numNodesList)]
        
        # Add virtual "none" operation for every stage_out task
        for file_names, agg_size, parallelism, file_group in file_groups:
            for numNodes in numNodesList:
                row = {
                    'operation': 'none',  # Virtual operation for all stage_out tasks
                    'randomOffset': 0,
                    'transferSize': fsblocksize,
                    'aggregateFilesizeMB': agg_size,  # Use actual data size
                    'numTasks': parallelism,
                    'parallelism': parallelism,
                    'totalTime': 0,  # No time (virtual)
                    'numNodesList': numNodesList,
                    'numNodes': numNodes,
                    'tasksPerNode': int(np.ceil(parallelism / numNodes)),
                    'trMiB': 1.0,  # Dummy transfer rate to avoid division by zero
                    'storageType': 'beegfs',  # Virtual consumer storage type
                    'opCount': parallelism,
                    'taskName': f'{taskName}-stage_out',  # Virtual consumer task name matching expected pattern
                    'taskPID': '',
                    'fileName': ','.join(file_names),
                    'stageOrder': stageOrder + 0.5,  # Stage-out operations after the actual task
                    'prevTask': taskName
                }
                staging_rows.append(row)
                if debug:
                    print(f"Added virtual 'none' operation for stage_out {taskName}: {row}")

    # 2. Intermediate data movement (stageOrder >= 1)
    for taskName, group in wf_df[wf_df['stageOrder'] >= 1].groupby('taskName'):
        # Skip if taskName already contains 'stage_out' or 'stage_in'
        if 'stage_out' in taskName or 'stage_in' in taskName:
            continue
        stageOrder = group['stageOrder'].iloc[0]
        prevTask = group['prevTask'].iloc[0] if 'prevTask' in group.columns else ''
        file_groups = get_file_groups(group)
        numNodesList = group['numNodesList'].iloc[0] if 'numNodesList' in group.columns else [1]
        if isinstance(numNodesList, str):
            try:
                numNodesList = eval(numNodesList)
            except Exception:
                numNodesList = [int(numNodesList)]
        for storageType in ['beegfs-ssd', 'beegfs-tmpfs', 'ssd-ssd', 'tmpfs-tmpfs', 'ssd-beegfs', 'tmpfs-beegfs']:
            # stage_in
            for file_names, agg_size, parallelism, file_group in file_groups:
                for numNodes in numNodesList:
                    op = 'scp' if storageType in ['ssd-ssd', 'tmpfs-tmpfs'] else 'cp'
                    row = {
                        'operation': op,
                        'randomOffset': 0,
                        'transferSize': fsblocksize,
                        'aggregateFilesizeMB': agg_size,
                        'numTasks': parallelism,
                        'parallelism': parallelism,
                        'totalTime': '',
                        'numNodesList': numNodesList,
                        'numNodes': numNodes,
                        'tasksPerNode': int(np.ceil(parallelism / numNodes)),
                        'trMiB': '',
                        'storageType': storageType,
                        'opCount': parallelism,
                        'taskName': f'stage_in-{taskName}',
                        'taskPID': '',
                        'fileName': ','.join(file_names),
                        'stageOrder': stageOrder - 0.5,
                        'prevTask': prevTask
                    }
                    staging_rows.append(row)
                    if debug:
                        print(f"Added intermediate stage_in row: {row}")
            # stage_out
            for file_names, agg_size, parallelism, file_group in file_groups:
                for numNodes in numNodesList:
                    op = 'scp' if storageType in ['ssd-ssd', 'tmpfs-tmpfs'] else 'cp'
                    row = {
                        'operation': op,
                        'randomOffset': 0,
                        'transferSize': fsblocksize,
                        'aggregateFilesizeMB': agg_size,
                        'numTasks': parallelism,
                        'parallelism': parallelism,
                        'totalTime': '',
                        'numNodesList': numNodesList,
                        'numNodes': numNodes,
                        'tasksPerNode': int(np.ceil(parallelism / numNodes)),
                        'trMiB': '',
                        'storageType': storageType,
                        'opCount': parallelism,
                        'taskName': f'{taskName}-stage_out',
                        'taskPID': '',
                        'fileName': ','.join(file_names),
                        'stageOrder': stageOrder + 0.5,
                        'prevTask': taskName
                    }
                    staging_rows.append(row)
                    if debug:
                        print(f"Added intermediate stage_out row: {row}")

    # 2b. Insert stage-out for all tasks with write operations (operation == 'write')
    write_rows = wf_df[wf_df['operation'].apply(lambda x: standardize_operation(x) == 'write')]
    for taskName, group in write_rows.groupby('taskName'):
        # Skip if taskName already contains 'stage_out' or 'stage_in'
        if 'stage_out' in taskName or 'stage_in' in taskName:
            continue
        stageOrder = group['stageOrder'].iloc[0]
        file_groups = get_file_groups(group)
        numNodesList = group['numNodesList'].iloc[0] if 'numNodesList' in group.columns else [1]
        if isinstance(numNodesList, str):
            try:
                numNodesList = eval(numNodesList)
            except Exception:
                numNodesList = [int(numNodesList)]
        for storageType in ['beegfs-ssd', 'beegfs-tmpfs', 'ssd-ssd', 'tmpfs-tmpfs', 'beegfs', 'ssd-beegfs', 'tmpfs-beegfs']:
            for file_names, agg_size, parallelism, file_group in file_groups:
                for numNodes in numNodesList:
                    if storageType == 'beegfs':
                        row = {
                            'operation': 'none',  # No operation for virtual stage_out
                            'randomOffset': 0,
                            'transferSize': fsblocksize,
                            'aggregateFilesizeMB': agg_size,
                            'numTasks': parallelism,
                            'parallelism': parallelism,
                            'totalTime': 0,  # No time (virtual)
                            'numNodesList': numNodesList,
                            'numNodes': numNodes,
                            'tasksPerNode': int(np.ceil(parallelism / numNodes)),
                            'trMiB': 1.0,  # Dummy transfer rate to avoid division by zero
                            'storageType': 'beegfs',
                            'opCount': parallelism,
                            'taskName': f'{taskName}-stage_out',
                            'taskPID': '',
                            'fileName': ','.join(file_names),
                            'stageOrder': stageOrder + 0.5,
                            'prevTask': taskName
                        }
                    else:
                        op = 'scp' if storageType in ['ssd-ssd', 'tmpfs-tmpfs'] else 'cp'
                        row = {
                            'operation': op,
                            'randomOffset': 0,
                            'transferSize': fsblocksize,
                            'aggregateFilesizeMB': agg_size,
                            'numTasks': parallelism,
                            'parallelism': parallelism,
                            'totalTime': '',
                            'numNodesList': numNodesList,
                            'numNodes': numNodes,
                            'tasksPerNode': int(np.ceil(parallelism / numNodes)),
                            'trMiB': '',
                            'storageType': storageType,
                            'opCount': parallelism,
                            'taskName': f'{taskName}-stage_out',
                            'taskPID': '',
                            'fileName': ','.join(file_names),
                            'stageOrder': stageOrder + 0.5,
                            'prevTask': taskName
                        }
                    staging_rows.append(row)
                    if debug:
                        print(f"Added stage_out row for write op: {row}")

    # 3. Final data movement (last stage)
    max_stage = wf_df['stageOrder'].max()
    last_rows = wf_df[wf_df['stageOrder'] == max_stage]
    if debug:
        print(f"Final data movement: {len(last_rows)} rows found for stageOrder {max_stage}.")
    if not last_rows.empty:
        # Iterate per task to avoid leaking taskName/stageOrder from outer scopes
        for last_taskName, last_task_group in last_rows.groupby('taskName'):
            # Skip rows that already represent staging tasks
            if 'stage_out' in last_taskName or 'stage_in' in last_taskName:
                continue

            file_groups = get_file_groups(last_task_group)
            numNodesList = (
                last_task_group['numNodesList'].iloc[0]
                if 'numNodesList' in last_task_group.columns else [1]
            )
            if isinstance(numNodesList, str):
                try:
                    numNodesList = eval(numNodesList)
                except Exception:
                    numNodesList = [int(numNodesList)]

            for storageType in ['tmpfs-beegfs', 'ssd-beegfs', 'beegfs']:
                for file_names, agg_size, parallelism, group in file_groups:
                    for numNodes in numNodesList:
                        if storageType == 'beegfs':
                            row = {
                                'operation': 'none',  # No operation for virtual stage_out
                                'randomOffset': 0,
                                'transferSize': fsblocksize,
                                'aggregateFilesizeMB': agg_size,
                                'numTasks': parallelism,
                                'parallelism': parallelism,
                                'totalTime': 0,  # No time (virtual)
                                'numNodesList': numNodesList,
                                'numNodes': numNodes,
                                'tasksPerNode': int(np.ceil(parallelism / numNodes)),
                                'trMiB': 1.0,  # Dummy transfer rate to avoid division by zero
                                'storageType': 'beegfs',
                                'opCount': parallelism,
                                'taskName': f'{last_taskName}-stage_out',
                                'taskPID': '',
                                'fileName': ','.join(file_names),
                                'stageOrder': max_stage + 0.5,
                                'prevTask': last_taskName,
                            }
                        else:
                            row = {
                                'operation': 'cp',
                                'randomOffset': 0,
                                'transferSize': fsblocksize,
                                'aggregateFilesizeMB': agg_size,
                                'numTasks': parallelism,
                                'parallelism': parallelism,
                                'totalTime': '',
                                'numNodesList': numNodesList,
                                'numNodes': numNodes,
                                'tasksPerNode': int(np.ceil(parallelism / numNodes)),
                                'trMiB': '',
                                'storageType': storageType,
                                'opCount': parallelism,
                                'taskName': f'{last_taskName}-stage_out',
                                'taskPID': '',
                                'fileName': ','.join(file_names),
                                'stageOrder': max_stage + 0.5,
                                'prevTask': last_taskName,
                            }
                        staging_rows.append(row)
                        if debug:
                            print(f"Added final data movement row: {row}")

    # Combine and sort
    staging_df = pd.DataFrame(staging_rows)

    combined = pd.concat([wf_df, staging_df], ignore_index=True, sort=False)
    combined = combined.sort_values(['stageOrder', 'taskName']).reset_index(drop=True)
    if debug:
        print(f"Total rows after staging: {len(combined)}")
        
        # Save the dataframe output when debug=True
        import os
        os.makedirs("./analysis_data", exist_ok=True)
        debug_output_path = f'./analysis_data/debug_staging_output.csv'
        combined.to_csv(debug_output_path, index=False)
        print(f"Debug: Saved staging output dataframe to: {debug_output_path}")
        print(f"Debug: Original rows: {len(wf_df)}, Staging rows added: {len(staging_df)}, Total: {len(combined)}")
    
    return combined 