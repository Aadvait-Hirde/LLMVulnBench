#!/usr/bin/env python3
"""
Generate Domain × Language Vulnerability Prevalence Heatmap

Usage:
    python3 generate_heatmap.py
    
    Requires: matplotlib, numpy
    Install: pip install matplotlib numpy
"""

import csv
import sys
from pathlib import Path

try:
    import matplotlib.pyplot as plt
    import numpy as np
except ImportError:
    print("Error: matplotlib and numpy are required.")
    print("Install with: pip install matplotlib numpy")
    sys.exit(1)


def generate_heatmap():
    """Generate Domain × Language prevalence heatmap"""
    
    # Paths
    script_dir = Path(__file__).parent
    base = script_dir.parent
    sec_path = base / 'analysis' / 'security_scores.csv'
    output_path = base / 'analysis' / 'heatmap_domain_language.png'
    
    if not sec_path.exists():
        print(f"Error: {sec_path} not found")
        sys.exit(1)
    
    # Load data
    print(f"Loading data from {sec_path}...")
    with sec_path.open() as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # Build domain x language matrix
    domains = sorted(set(r['domain'] for r in rows))
    languages = sorted(set(r['language'] for r in rows))
    
    print(f"Domains: {domains}")
    print(f"Languages: {languages}")
    
    # Calculate prevalence for each (domain, language)
    matrix = []
    domain_labels = []
    for domain in domains:
        row_data = []
        for lang in languages:
            group = [r for r in rows if r['domain'] == domain and r['language'] == lang]
            if group:
                total = len(group)
                with_v = sum(int(r['total_vulnerabilities']) > 0 for r in group)
                prevalence = (with_v / total) * 100 if total > 0 else 0.0
                row_data.append(prevalence)
            else:
                row_data.append(np.nan)
        if not all(np.isnan(x) for x in row_data):
            matrix.append(row_data)
            domain_labels.append(domain)
    
    matrix = np.array(matrix)
    
    # Create heatmap with enhanced styling
    print("Generating heatmap...")
    plt.style.use('default')
    fig, ax = plt.subplots(figsize=(12, 7))
    fig.patch.set_facecolor('white')
    
    # Use a more professional colormap (RdYlGn_r: red=high, green=low)
    # Create custom colormap with better contrast
    from matplotlib.colors import LinearSegmentedColormap
    colors = ['#2ecc71', '#f1c40f', '#e67e22', '#e74c3c']  # Green to Red gradient
    n_bins = 256
    cmap = LinearSegmentedColormap.from_list('custom', colors, N=n_bins)
    
    im = ax.imshow(matrix, cmap=cmap, aspect='auto', vmin=0, vmax=100, 
                   interpolation='nearest')
    
    # Add grid lines
    ax.set_xticks(np.arange(len(languages) + 1) - 0.5, minor=True)
    ax.set_yticks(np.arange(len(domain_labels) + 1) - 0.5, minor=True)
    ax.grid(which='minor', color='white', linestyle='-', linewidth=2)
    ax.tick_params(which='minor', size=0)
    
    # Add colorbar with better styling
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('Prevalence (%)', fontsize=13, fontweight='bold', labelpad=15)
    cbar.ax.tick_params(labelsize=11)
    
    # Set ticks and labels with better formatting
    ax.set_xticks(np.arange(len(languages)))
    ax.set_yticks(np.arange(len(domain_labels)))
    
    # Format language labels (capitalize)
    lang_labels = [lang.upper() if lang != 'cpp' else 'C++' for lang in languages]
    ax.set_xticklabels(lang_labels, fontsize=12, fontweight='bold')
    
    # Format domain labels (title case, replace underscores)
    domain_labels_formatted = [d.replace('_', ' ').title() for d in domain_labels]
    ax.set_yticklabels(domain_labels_formatted, fontsize=12, fontweight='bold')
    
    # Add text annotations with better styling
    for i in range(len(domain_labels)):
        for j in range(len(languages)):
            if not np.isnan(matrix[i, j]):
                # Use white text for dark cells, dark text for light cells
                text_color = 'white' if matrix[i, j] > 40 else '#2c3e50'
                ax.text(j, i, f'{matrix[i, j]:.1f}%',
                       ha="center", va="center", color=text_color, 
                       fontweight='bold', fontsize=13)
    
    # Labels and title with better styling
    ax.set_xlabel('Language', fontsize=14, fontweight='bold', labelpad=15)
    ax.set_ylabel('Domain', fontsize=14, fontweight='bold', labelpad=15)
    ax.set_title('Domain × Language Vulnerability Prevalence Heatmap', 
                fontsize=16, fontweight='bold', pad=25, color='#2c3e50')
    
    # Remove top and right spines for cleaner look
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(True)
    ax.spines['left'].set_visible(True)
    ax.spines['bottom'].set_color('#bdc3c7')
    ax.spines['left'].set_color('#bdc3c7')
    
    plt.tight_layout()
    
    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Heatmap saved: {output_path}")
    
    # Print data table for reference
    print("\n" + "="*70)
    print("Prevalence Matrix (%):")
    print("="*70)
    print(f"{'Domain/Language':<20}", end="")
    for lang in languages:
        print(f"{lang:>12}", end="")
    print()
    print("-" * 70)
    for i, domain in enumerate(domain_labels):
        print(f"{domain:<20}", end="")
        for j, lang in enumerate(languages):
            if not np.isnan(matrix[i, j]):
                print(f"{matrix[i, j]:>11.1f}%", end="")
            else:
                print(f"{'N/A':>12}", end="")
        print()
    print("="*70)


if __name__ == "__main__":
    generate_heatmap()


