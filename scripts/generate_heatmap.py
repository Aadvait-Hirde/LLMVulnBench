#!/usr/bin/env python3
"""
Generate Domain × Language Vulnerability Prevalence Heatmap (Seaborn)
"""

import csv
import sys
from pathlib import Path

try:
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    import seaborn as sns
    from matplotlib.colors import LinearSegmentedColormap
except ImportError:
    print("Error: matplotlib, numpy, pandas, seaborn required.")
    sys.exit(1)


def generate_heatmap():
    script_dir = Path(__file__).parent
    base = script_dir.parent
    sec_path = base / 'analysis' / 'security_scores.csv'
    output_path = base / 'analysis' / 'heatmap_domain_language.png'

    if not sec_path.exists():
        print(f"Error: {sec_path} not found")
        sys.exit(1)

    # Load & filter
    df = pd.read_csv(sec_path)
    df = df[df['language'] != 'javascript']

    # Compute prevalence per (domain, language)
    df['has_vuln'] = (df['total_vulnerabilities'] > 0).astype(int)
    pivot = df.groupby(['domain', 'language'])['has_vuln'].mean().unstack() * 100

    # Pretty labels
    domain_map = {
        'web_api': 'Web API',
        'aiml_ds': 'AI/ML & Data Science',
        'file_system': 'File System',
        'auth_crypto': 'Auth & Cryptography'
    }
    lang_map = {
        'python': 'Python',
        'typescript': 'TypeScript',
        'java': 'Java',
        'cpp': 'C++'
    }

    # Reindex to desired order
    domain_order = ['web_api', 'aiml_ds', 'file_system', 'auth_crypto']
    lang_order = ['python', 'typescript', 'java', 'cpp']

    pivot = pivot.reindex(index=domain_order, columns=lang_order)
    pivot.index = [domain_map[d] for d in pivot.index]
    pivot.columns = [lang_map[l] for l in pivot.columns]

    # Custom diverging colormap: green → yellow → red
    cmap = LinearSegmentedColormap.from_list('vuln_risk', [
        '#1a9850',  # deep green
        '#66bd63',  # green
        '#a6d96a',  # light green
        '#d9ef8b',  # yellow-green
        '#fee08b',  # yellow
        '#fdae61',  # amber
        '#f46d43',  # orange
        '#d73027',  # red
        '#a50026',  # dark red
    ], N=256)

    # ── Plot ──
    sns.set_theme(style='white', font_scale=1.2)
    fig, ax = plt.subplots(figsize=(9, 5.5))

    sns.heatmap(
        pivot,
        annot=True,
        fmt='.1f',
        cmap=cmap,
        vmin=0,
        vmax=100,
        linewidths=2.5,
        linecolor='white',
        square=True,
        cbar_kws={
            'label': 'Vulnerability Prevalence (%)',
            'shrink': 0.8,
            'pad': 0.02,
        },
        annot_kws={'size': 15, 'weight': 'bold'},
        mask=pivot.isna(),
        ax=ax,
    )

    # Style the N/A cells
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            if pd.isna(pivot.iloc[i, j]):
                ax.text(j + 0.5, i + 0.5, '—',
                       ha='center', va='center',
                       fontsize=14, color='#aaaaaa', fontstyle='italic')

    # Fix annotation colors (white on dark, dark on light)
    for text in ax.texts:
        try:
            val = float(text.get_text())
            text.set_text(f'{val:.1f}%')
            text.set_color('white' if val > 40 else '#1a1a2e')
        except ValueError:
            pass

    # Labels
    ax.set_xlabel('')
    ax.set_ylabel('')
    ax.xaxis.set_ticks_position('top')
    ax.xaxis.set_label_position('top')
    ax.tick_params(axis='both', which='both', length=0)
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontweight='600')
    ax.set_xticklabels(ax.get_xticklabels(), fontweight='600')

    # Title
    fig.suptitle('Domain × Language Vulnerability Prevalence',
                fontsize=18, fontweight='bold', color='#1a1a2e',
                x=0.02, ha='left', y=0.98)

    plt.tight_layout(rect=[0, 0, 1, 0.95])

    # Save
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✓ PNG saved: {output_path}")

    pdf_path = output_path.with_suffix('.pdf')
    plt.savefig(pdf_path, bbox_inches='tight', facecolor='white')
    print(f"✓ PDF saved: {pdf_path}")

    # Print table
    print(f"\n{pivot.to_string()}")


if __name__ == "__main__":
    generate_heatmap()
