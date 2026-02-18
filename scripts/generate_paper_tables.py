
import pandas as pd
import numpy as np
from collections import Counter
import json

def analyze_data():
    try:
        # Load Data
        df = pd.read_csv('analysis/security_scores.csv')
        vulns_df = pd.read_csv('analysis/vuln_results.csv')
        
        # -------------------------------------------------------
        # 1. Corpus-Wide Metrics
        # -------------------------------------------------------
        total_prompts = len(df)
        vuln_prompts = df[df['total_vulnerabilities'] > 0].shape[0]
        prevalence = (vuln_prompts / total_prompts) * 100
        mean_score = df['security_score'].mean()
        std_score = df['security_score'].std()
        median_score = df['security_score'].median()
        
        print(f"--- Corpus Metrics ---")
        print(f"Prevalence: {prevalence:.1f}% ({vuln_prompts}/{total_prompts})")
        print(f"Mean Security Score: {mean_score:.3f} (SD={std_score:.3f})")
        print(f"Median Security Score: {median_score:.3f}")
        
        # -------------------------------------------------------
        # 2. Language Distribution Table
        # -------------------------------------------------------
        print(f"\n--- Language Table ---")
        langs = df['language'].unique()
        for lang in langs:
            sub = df[df['language'] == lang]
            prompts = len(sub)
            vuln_runs = sub[sub['total_vulnerabilities'] > 0].shape[0]
            prev = (vuln_runs / prompts) * 100
            avg_score = sub['security_score'].mean()
            
            # Count total findings for this language from raw results
            findings = len(vulns_df[vulns_df['language'] == lang])
            
            print(f"{lang:10} | Prompts: {prompts:4} | Findings: {findings:4} | Vuln Runs: {vuln_runs:3} ({prev:.1f}%) | Avg Score: {avg_score:.3f}")

        # -------------------------------------------------------
        # 3. CWE Analysis (Top 10)
        # -------------------------------------------------------
        print(f"\n--- Top 10 CWEs ---")
        # Filter out 'None' or empty CWEs
        valid_cwes = vulns_df[vulns_df['cwe'].notna() & (vulns_df['cwe'] != 'None')]['cwe']
        cwe_counts = valid_cwes.value_counts().head(10)
        total_findings = len(valid_cwes)
        
        # Load CVSS mapping for reference
        with open('data/cwe_cvss_mapping.json', 'r') as f:
            cwe_map = json.load(f)
            
        for cwe, count in cwe_counts.items():
            pct = (count / total_findings) * 100
            cvss = cwe_map.get(cwe, 'N/A')
            print(f"{cwe:10} | Count: {count:3} | {pct:4.1f}% | CVSS: {cvss}")

        # -------------------------------------------------------
        # 4. Prompt Strategy Efficacy
        # -------------------------------------------------------
        print(f"\n--- Prompt Strategy Comparison ---")
        strategies = df['prompt_type'].unique()
        for strat in strategies:
            sub = df[df['prompt_type'] == strat]
            prev = (sub[sub['total_vulnerabilities'] > 0].shape[0] / len(sub)) * 100
            avg_findings = sub['total_vulnerabilities'].mean()
            avg_total_cvss = sub['total_cvss_score'].mean()
            avg_score = sub['security_score'].mean()
            print(f"{strat:15} | Prev: {prev:.1f}% | Avg Findings: {avg_findings:.2f} | Avg Total CVSS: {avg_total_cvss:.2f} | Avg Score: {avg_score:.3f}")

        # -------------------------------------------------------
        # 5. Domain-Language Matrix (Avg Security Score)
        # -------------------------------------------------------
        print(f"\n--- Domain-Language Matrix (Security Score) ---")
        domains = df['domain'].unique()
        languages = ['python', 'typescript', 'java', 'cpp'] # c++ might be cpp
        
        print(f"{'Domain':25} | {'Python':6} | {'TS':6} | {'Java':6} | {'C++':6}")
        for dom in domains:
            scores = []
            for lang in languages:
                # Handle c++ naming
                l_query = lang
                if lang == 'c++': l_query = ['cpp', 'c++']
                
                if isinstance(l_query, list):
                    cell = df[(df['domain'] == dom) & (df['language'].isin(l_query))]
                else:
                    cell = df[(df['domain'] == dom) & (df['language'] == l_query)]
                
                if len(cell) > 0:
                    mean_val = cell['security_score'].mean()
                    scores.append(f"{mean_val:.3f}")
                else:
                    scores.append("--")
            print(f"{dom:25} | {scores[0]:6} | {scores[1]:6} | {scores[2]:6} | {scores[3]:6}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze_data()
