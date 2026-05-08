import pandas as pd
from modules.workflow_data_staging import insert_data_staging_rows

def make_sample_wf_df():
    data = {
        'operation': [1, 1, 0, 1, 0],
        'randomOffset': [0, 0, 1, 1, 1],
        'transferSize': [8192, 8192, 4096, 4096, 4096],
        'aggregateFilesizeMB': [0.1, 0.2, 2.0, 2.1, 2.2],
        'aggregateFilesizeMBtask': [0.1, 0.2, 2.0, 2.1, 2.2],
        'numTasks': [2, 2, 1, 1, 1],
        'parallelism': [2, 2, 1, 1, 1],
        'totalTime': [0.0, 0.0, 10.0, 20.0, 30.0],
        'numNodesList': ['[2, 4]', '[2, 4]', '[2, 4]', '[2, 4]', '[2, 4]'],
        'numNodes': [2, 2, 2, 2, 2],
        'tasksPerNode': [1, 1, 1, 1, 1],
        'trMiB': [100, 100, 200, 200, 200],
        'storageType': ['beegfs', 'beegfs', 'beegfs', 'beegfs', 'beegfs'],
        'opCount': [2, 2, 1, 1, 1],
        'taskName': ['A', 'A', 'B', 'B', 'C'],
        'taskPID': ['p1', 'p2', 'p3', 'p4', 'p5'],
        'fileName': ['f1', 'f2', 'f3', 'f4', 'f5'],
        'stageOrder': [0, 0, 1, 1, 2],
        'prevTask': ['', '', 'A', 'A', 'B']
    }
    return pd.DataFrame(data)

def main():
    print("Testing insert_data_staging_rows with debug output...")
    wf_df = make_sample_wf_df()
    print("Original DataFrame:")
    print(wf_df)
    staged_df = insert_data_staging_rows(wf_df, debug=True)
    print("\nDataFrame after inserting data staging rows:")
    print(staged_df)

if __name__ == "__main__":
    main() 