"""
Configuration module for workflow analysis.
Contains constants, test configurations, and parameters used across the analysis.
"""

import os

# Global configuration flags
MULTI_NODES = True  # True: uses tasksPerNodes; False: uses parallelism
NORMALIZE = False
DEBUG = True

# Storage types
STORAGE_LIST = ['ssd', 'beegfs', 'tmpfs'] # 'nfs', 'pfs' , 'tmpfs'

# Data size mappings in KB
DATA_SIZE_KB = {
    '4mb': 4096, '16mb': 16384, '64mb': 65536,
    '256mb': 262144, '512mb': 524288, '1gb': 1048576,
    '5gb': 5242880, '50gb': 52428800, '100gb': 104857600,
    '300gb': 314572800,
}

# Key parameters for workflow analysis
WF_PARAMS = [
    'operation', 'randomOffset', 'transferSize', 
    'aggregateFilesizeMB', 'numTasks', 'parallelism', 'totalTime', 
    'numNodesList', 'numNodes', 'tasksPerNode', 'trMiB', 'storageType',
    'opCount', 'taskName', 'taskPID', 'fileName', 'stageOrder'
]

TARGET_PARAMS = ["bestStorage"]

# Operation dictionary
OP_DICT = {0: "write", 1: "read"}

# Test configurations for different workflows
TEST_CONFIGS = {
    # "ddmd_2n_s": {  # old data, less I/O intensive
    #     "SCRIPT_ORDER": "ddmd_script_order",
    #     "NUM_NODES_LIST": [1, 2, 4],
    #     "ALLOWED_PARALLELISM": [1, 3, 6, 12],
    #     "exp_data_path": "./ddmd",
    #     "test_folders": ['ddmd_2n_pfs_small']
    # },
    "ddmd_4n_l": {  # normalize global # this is for spm paper
        "SCRIPT_ORDER": "ddmd_script_order",
        "NUM_NODES_LIST": [1, 2, 4],
        "exp_data_path": "./ddmd",
        "ALLOWED_PARALLELISM": [1, 3, 6, 12],
        "test_folders": ['ddmd_4n_pfs_large']
    },
    "1kg": {
        "SCRIPT_ORDER": "1kg_script_order",
        "NUM_NODES_LIST": [2, 5, 10],
        "ALLOWED_PARALLELISM": [1, 2, 5, 30, 60, 150], # [2, 4, 5, 10, 30, 60, 150],
        "exp_data_path": "./1kgenome", 
        "test_folders": ['par_6000_10n_nfs_ps300'] 
    },
    # "1kg_2": {
    #     "SCRIPT_ORDER": "1kg_script_order_short",
    #     "NUM_NODES_LIST": [2, 5, 10],
    #     "ALLOWED_PARALLELISM": [1, 2, 5, 30, 60, 150], # [2, 4, 5, 10, 30, 60, 150],
    #     "exp_data_path": "./1kgenome", 
    #     "test_folders": ['par_6000_10n_nfs_ps300'] 
    # },
    "pyflex_240f": {
        "SCRIPT_ORDER": "pyflextrkr_s9p240_script_order",
        "NUM_NODES_LIST": [8, 16, 32],
        "ALLOWED_PARALLELISM": [1, 8, 15, 30],
        "exp_data_path": "./pyflextrkr",
        "test_folders": ['summer_sam_4n96p_pfs_s9']
    },
    "pyflex_s9_48f": {
        "SCRIPT_ORDER": "pyflextrkr_s9_script_order",
        "NUM_NODES_LIST": [2, 4, 8],
        "ALLOWED_PARALLELISM": [1, 12, 24, 48],
        "exp_data_path": "./pyflextrkr",
        "test_folders": ['summer_sam_4n_pfs_s9']
    },
    # "ptychonn": {
    #     "SCRIPT_ORDER": "ptychonn_script_order",
    #     "NUM_NODES_LIST": [1],
    #     "ALLOWED_PARALLELISM": [1],
    #     "exp_data_path": "./ptychonn",
    #     "test_folders": ['ptychonn_212m']  # ['ptychonn_14m', 'ptychonn_212m']
    # },
    # "montage": {
    #     "SCRIPT_ORDER": "montage_script_order",
    #     "NUM_NODES_LIST": [1],
    #     "ALLOWED_PARALLELISM": [1],
    #     "exp_data_path": "./montage",
    #     "test_folders": ['datalife_montage_1']
    # },
    # "seismology": {
    #     "SCRIPT_ORDER": "seismology_script_order",
    #     "NUM_NODES_LIST": [1],
    #     "ALLOWED_PARALLELISM": [1],
    #     "exp_data_path": "./seismology",
    #     "test_folders": ['seis_1n']
    # },
    # "llm_wf": {
    #     "SCRIPT_ORDER": "llm_script_order",
    #     "NUM_NODES_LIST": [1],
    #     "ALLOWED_PARALLELISM": [1],
    #     "exp_data_path": "./llm",
    #     "test_folders": ['llm_wf_2s']
    # },
    "template_workflow": {
        "SCRIPT_ORDER": "template_script_order",
        "NUM_NODES_LIST": [1],
        "ALLOWED_PARALLELISM": [1],
        "exp_data_path": "./template_workflow",
        "test_folders": ['template_t1']
    },
    "montage": {
        "SCRIPT_ORDER": "montage_script_order_v1",
        "NUM_NODES_LIST": [1],
        "ALLOWED_PARALLELISM": [1],
        "exp_data_path": "./montage",
        "test_folders": ['montage_2n_16blue']
    },
}

# Default workflow configuration
DEFAULT_WF = "ddmd_4n_l"

# Target tasks for filtering
TARGET_TASKS = ["python"]  # omit srun from 1kgenome run

# OSCache size in MiB
OSCACHE_SIZE_MB = 25 * 1024  # Convert to MiB 