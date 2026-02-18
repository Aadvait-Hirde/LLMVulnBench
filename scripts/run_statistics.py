
import pandas as pd
import numpy as np
import scipy.stats as stats
from pathlib import Path
import argparse
import sys
import itertools

def main():
    parser = argparse.ArgumentParser(description='Perform statistical analysis on security scores')
    parser.add_argument('--input', default='analysis/security_scores.csv', help='Input CSV file')
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: {input_path} not found")
        sys.exit(1)

    print(f"Loading data from {input_path}...")
    df = pd.read_csv(input_path)

    # ---------------------------------------------------------
    # 1. Descriptive Statistics
    # ---------------------------------------------------------
    print("\n" + "="*60)
    print("DESCRIPTIVE STATISTICS")
    print("="*60)
    print(df['security_score'].describe())

    # ---------------------------------------------------------
    # 2. ANOVA / T-Tests (Security Scores by Prompt Type)
    # ---------------------------------------------------------
    print("\n" + "="*60)
    print("STATISTICAL TESTS: PROMPT TYPES")
    print("="*60)

    prompt_types = df['prompt_type'].unique()
    groups = [df[df['prompt_type'] == p]['security_score'] for p in prompt_types]

    # Check for variance homogeneity (Levene's Test)
    stat, p_levene = stats.levene(*groups)
    print(f"Levene's Test for Equal Variances: p={p_levene:.4f}")

    if p_levene > 0.05:
        print(" -> Variances are equal (Assumption met for ANOVA).")
        # One-way ANOVA
        f_val, p_val = stats.f_oneway(*groups)
        print(f"One-way ANOVA: F={f_val:.4f}, p={p_val:.4e}")
    else:
        print(" -> Variances are NOT equal (Using Welch's ANOVA / Kruskal-Wallis).")
        # Kruskal-Wallis H-test (Non-parametric alternative to ANOVA)
        stat, p_val = stats.kruskal(*groups)
        print(f"Kruskal-Wallis H-test: H={stat:.4f}, p={p_val:.4e}")

    # Post-hoc Pairwise Comparisons (T-tests with Bonferroni correction)
    print("\nPairwise Comparisons (T-tests with Bonferroni correction):")
    pairs = list(itertools.combinations(prompt_types, 2))
    alpha = 0.05
    adjusted_alpha = alpha / len(pairs)
    
    print(f"Adjusted Alpha (Bonferroni): {adjusted_alpha:.4f}")
    
    for p1, p2 in pairs:
        g1 = df[df['prompt_type'] == p1]['security_score']
        g2 = df[df['prompt_type'] == p2]['security_score']
        
        # Welch's t-test (does not assume equal variance)
        t_stat, p_val = stats.ttest_ind(g1, g2, equal_var=False)
        
        sig = "*" if p_val < adjusted_alpha else " "
        
        # Calculate Cohen's d
        n1, n2 = len(g1), len(g2)
        s1, s2 = np.var(g1, ddof=1), np.var(g2, ddof=1)
        s_pooled = np.sqrt(((n1 - 1) * s1 + (n2 - 1) * s2) / (n1 + n2 - 2))
        cohens_d = (np.mean(g1) - np.mean(g2)) / s_pooled
        
        print(f"{sig} {p1:<15} vs {p2:<15} | t={t_stat:>6.2f} | p={p_val:.2e} | d={cohens_d:>5.2f}")

    # ---------------------------------------------------------
    # 3. Chi-Square Tests (Vulnerability Prevalence)
    # ---------------------------------------------------------
    print("\n" + "="*60)
    print("CATEGORICAL TESTS: VULNERABILITY PREVALENCE")
    print("="*60)

    # Create binary column: Is Vulnerable? (Total Vulnerabilities > 0)
    df['is_vulnerable'] = df['total_vulnerabilities'] > 0

    factors = ['domain', 'language', 'prompt_type']
    
    for factor in factors:
        print(f"\nFactor: {factor.upper()}")
        contingency_table = pd.crosstab(df[factor], df['is_vulnerable'])
        print(contingency_table)
        
        chi2, p, dof, expected = stats.chi2_contingency(contingency_table)
        print(f"Chi-square Test: chi2={chi2:.4f}, p={p:.4e}")
        
        if p < 0.05:
            print(" -> Significant association found.")
        else:
            print(" -> No significant association.")

if __name__ == "__main__":
    main()
