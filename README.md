# SPM (Storage Performance Matching) Analysis System

A comprehensive system for analyzing scientific workflow performance and optimizing storage configurations using Storage Performance Matching (SPM).

## 🎯 Overview

This project provides tools and analysis capabilities for understanding and optimizing the performance of scientific workflows across different storage systems. It processes workflow I/O pattern profiles, estimates transfer rates using IOR benchmark data, and calculates Storage Performance Matching (SPM) to recommend optimal storage configurations.

## 🚀 Quick Start

1. **Setup Environment**:
   ```bash
   python3 -m venv spm_env
   source spm_env/bin/activate  # On Linux/macOS
   pip install -r requirements.txt
   ```

2. **Run Analysis**:
   ```bash
   cd workflow_analysis
   # See workflow_analysis/README.md for detailed usage instructions
   python3 workflow_data_loader.py --workflow ddmd_4n_l
   python3 workflow_analyzer.py analysis_data/ddmd_4n_l_workflow_data.csv
   ```

## 📁 Project Structure

```
spm/
├── workflow_analysis/                 # Main analysis system
│   ├── workflow_data_loader.py       # Phase 1: Data loading from JSON to CSV
│   ├── workflow_analyzer.py          # Phase 2: Analysis from CSV
│   ├── modules/                      # Core analysis modules
│   ├── analysis_data/                # Generated data files
│   ├── workflow_spm_results/         # Analysis results
│   └── README.md                     # Detailed usage instructions
├── perf_profiles/                    # Benchmark data and utilities
│   ├── updated_master_ior_df.csv     # IOR benchmark results
│   ├── ior_utils.py                  # IOR data processing utilities
│   └── README.md                     # Benchmark data documentation
└── requirements.txt                  # Python dependencies
```

## 🔧 Key Features

### 📊 4D Interpolation System
- Multi-dimensional analysis based on aggregate file size, nodes, parallelism, and transfer size
- Storage and parallelism optimization recommendations
- Extrapolation support for values outside benchmark range
- Multi-node support with tasksPerNode calculations

### 🎯 SPM (Storage Performance Matching) Calculation
- Producer-consumer analysis for workflow stage transitions
- Storage configuration ranking by performance
- Stage-aware processing for stage_in and stage_out operations
- Detailed intermediate results for analysis and debugging

### 🏗️ Modular Architecture
- **Split Architecture**: Data loading and analysis phases separated for better modularity
- **Input File Preservation**: Original files are never modified, enabling multiple analysis runs
- **Reusable Components**: CSV files can be analyzed multiple times without reloading JSON data
- **Separation of Concerns**: Dedicated modules for different analysis phases
- **Easy Extension**: New workflows or storage types can be easily added

## 💾 Supported Storage Types

- **`localssd`** - Local SSD storage (high bandwidth, low latency)
- **`beegfs`** - BeeGFS/PFS storage (distributed parallel file system)
- **`tmpfs`** - Temporary file system (memory-based, fastest access)
- **`nfs`** - Network File System (network-attached storage)

### Storage Type Transitions
- **`beegfs-ssd`**, **`ssd-beegfs`** - Transitions between BeeGFS and SSD storage
- **`beegfs-tmpfs`**, **`tmpfs-beegfs`** - Transitions between BeeGFS and tmpfs storage
- **`ssd-ssd`**, **`tmpfs-tmpfs`** - Same-storage operations using cp/scp

## 📋 Available Workflows

| Workflow | Description | Data Size | Nodes |
|----------|-------------|-----------|-------|
| `ddmd_4n_l` | DDMD workflow | Large | 4 |
| `1kg` | 1K Genome workflow | Standard | Variable |
| `pyflex_s9_48f` | PyFlex workflow | S9, 48 files | Variable |
| `template_workflow` | Template workflow for testing | Artificial | 4 |

## 📊 Output Files

### Analysis Results
- **`workflow_spm_results/{workflow_name}_filtered_spm_results.csv`** - Filtered SPM results with storage analysis
- **`workflow_spm_results/{workflow_name}_intermediate_estT_results.csv`** - Intermediate results with per-task time estimation
- **`workflow_spm_results/{workflow_name}_WFG.json`** - Complete workflow graph with all nodes and edges

### Data Files
- **`analysis_data/{workflow_name}_original_workflow_data.csv`** - Original data before modifications
- **`analysis_data/{workflow_name}_processed_workflow_data.csv`** - Modified data with staging rows and transfer rates
- **`analysis_data/{workflow_name}_spm_results.json`** - SPM calculation results and best configurations

## 🚧 Development Status

- ✅ **Core Analysis**: Complete and tested
- ✅ **SPM Calculation**: Complete and tested
- ✅ **Transfer Rate Estimation**: Complete and tested
- ✅ **Storage Type Transitions**: Complete and tested (CP/SCP operations)
- ✅ **Split Architecture**: Complete and tested (Data loading + Analysis phases)
- ✅ **Input File Preservation**: Complete and tested (Original files never modified)
- ✅ **Intermediate Results**: Complete and tested (Per-task time estimation CSV)
- 🚧 **Visualization**: Under construction
- ✅ **Template Generation**: Complete and tested
- ✅ **Command-Line Interface**: Complete and tested

## 📚 Documentation

- **Workflow Analysis**: `workflow_analysis/README.md` - Main analysis system documentation and detailed usage instructions
- **Performance Profiles**: `perf_profiles/README.md` - IOR benchmark data documentation and utilities
- **Template Workflow**: `workflow_analysis/template_workflow/README.md` - Template workflow documentation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For questions, issues, or contributions, please:
1. Check the documentation in the respective subfolders
2. Review existing issues in the repository
3. Create a new issue with detailed information about your problem
4. Contact the development team

---

**Note**: This system is designed for analyzing scientific workflow performance and optimizing storage configurations. For production use, ensure all dependencies are properly installed and test with your specific workflow data.


Resume this session with:────────────────────────────────────────────────────────────────────────────────────────────────────────
claude --resume 35b9b70c-9e40-4389-9283-103b7e6df8f0