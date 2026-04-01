"""
Script to create workflow runtime comparison plot.
Recreates the exact same plot as workflow_runtime_comparison.pdf
"""

import matplotlib.pyplot as plt
import numpy as np
import os

# Data extracted from the PDF
workflows = ['1000 Genome', 'PyFLRXTRKR', 'DDMD']
methods = ['DPM', 'dagP', 'DFMan', 'FaasFlow']

# Runtime data in seconds (from PDF text extraction)
runtime_data = {
    '1000 Genome': {
        'DPM': 211,
        'dagP': 617,
        'DFMan': 445,
        'FaasFlow': 589
    },
    'PyFLRXTRKR': {
        'DPM': 236,
        'dagP': 474,
        'DFMan': 460,
        'FaasFlow': 543
    },
    'DDMD': {
        'DPM': 424,
        'dagP': 445,
        'DFMan': 494,
        'FaasFlow': 445
    }
}

# Speedup annotations (from PDF)
speedup_annotations = {
    '1000 Genome': {
        'dagP': '2.9x faster than dagP',
        'DFMan': '1.1x faster than DFMan',
        'FaasFlow': '2.0x faster than FaasFlow'
    },
    'PyFLRXTRKR': {
        'dagP': '1.1x faster than dagP',
        'DFMan': '1.2x faster than DFMan',
        'FaasFlow': '1.4x faster than FaasFlow'
    },
    'DDMD': {
        'dagP': '1.0x faster than dagP',
        'DFMan': '1.2x faster than DFMan',
        'FaasFlow': '1.0x faster than FaasFlow'
    }
}

def create_workflow_runtime_comparison():
    """Create the workflow runtime comparison bar chart."""
    
    # Use non-interactive backend to avoid display issues
    import matplotlib
    matplotlib.use('Agg')
    
    # Set up the figure (flatter and smaller)
    fig, ax = plt.subplots(figsize=(8, 4))
    
    # Set up bar positions
    x = np.arange(len(workflows))
    width = 0.2  # Width of bars
    spacing = 0.05  # Spacing between groups
    
    # Define colors for each method
    colors = {
        'DPM': '#1f77b4',      # Blue
        'dagP': '#ff7f0e',      # Orange
        'DFMan': '#2ca02c',     # Green
        'FaasFlow': '#d62728'   # Red
    }
    
    # Plot bars for each method
    for i, method in enumerate(methods):
        values = [runtime_data[wf][method] for wf in workflows]
        offset = (i - len(methods) / 2 + 0.5) * (width + spacing)
        bars = ax.bar(x + offset, values, width, label=method, color=colors[method])
        
        # Add value labels on top of bars
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(value)}',
                   ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # Set labels and title
    ax.set_xlabel('Workflow', fontsize=12, fontweight='bold')
    ax.set_ylabel('Runtime (seconds)', fontsize=12, fontweight='bold')
    ax.set_title('Workflow Runtime Comparison', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(workflows)
    ax.legend(loc='upper left', frameon=True)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    # Set y-axis limits
    max_runtime = max([max(runtime_data[wf].values()) for wf in workflows])
    ax.set_ylim(0, max_runtime * 1.15)
    
    # Add speedup annotations (simplified - just text above DPM bars)
    for i, wf in enumerate(workflows):
        dpm_runtime = runtime_data[wf]['DPM']
        dpm_offset = (methods.index('DPM') - len(methods) / 2 + 0.5) * (width + spacing)
        dpm_x = x[i] + dpm_offset
        
        # Collect all speedup annotations for this workflow
        annotations = []
        for method in ['dagP', 'DFMan', 'FaasFlow']:
            method_runtime = runtime_data[wf][method]
            if method_runtime > dpm_runtime:
                speedup = method_runtime / dpm_runtime
                annotations.append(f'{speedup:.1f}x faster than {method}')
        
        # Add combined annotation text above DPM bar
        if annotations:
            annotation_text = '\n'.join(annotations)
            ax.text(dpm_x, dpm_runtime + max_runtime * 0.05,
                   annotation_text,
                   ha='center', va='bottom',
                   fontsize=8,
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))
    
    plt.tight_layout()
    
    # Save the plot
    output_dir = 'spm_figures'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'workflow_runtime_comparison_updated.pdf')
    plt.savefig(output_path, format='pdf', bbox_inches='tight', dpi=300)
    plt.close()  # Close the figure to free memory
    print(f"Plot saved to: {output_path}")
    
    return fig, ax


if __name__ == "__main__":
    create_workflow_runtime_comparison()
    print("Workflow runtime comparison plot created successfully!")
