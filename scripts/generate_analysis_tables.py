#!/usr/bin/env python3
"""
generate_analysis_tables.py - Generate research tables from security analysis results

This script generates multi-dimensional tables for research paper presentation:
- Domain × Prompt Type comparison
- Language × Prompt Type comparison
- Domain × Language × Prompt Type comprehensive matrix
- Summary statistics and comparisons

Usage:
    python3 generate_analysis_tables.py --input analysis/security_scores.csv
    python3 generate_analysis_tables.py --input analysis/security_scores.csv --output analysis/tables
"""

import csv
import json
import sys
from pathlib import Path
from collections import defaultdict
import argparse


class TableGenerator:
    def __init__(self, input_csv, output_dir):
        self.input_csv = Path(input_csv)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load data
        self.data = []
        with open(self.input_csv, 'r') as f:
            reader = csv.DictReader(f)
            self.data = list(reader)
        
        if not self.data:
            raise ValueError(f"No data found in {input_csv}")
    
    def calculate_aggregate_metrics(self, group_key_func):
        """Calculate aggregate metrics for a grouping"""
        groups = defaultdict(list)
        
        for row in self.data:
            key = group_key_func(row)
            groups[key].append(row)
        
        results = []
        for key, rows in groups.items():
            total_vulns = sum(int(r['total_vulnerabilities']) for r in rows)
            error_count = sum(int(r['error_count']) for r in rows)
            warning_count = sum(int(r['warning_count']) for r in rows)
            info_count = sum(int(r['info_count']) for r in rows)
            weighted_score = sum(float(r['weighted_score']) for r in rows)
            security_scores = [float(r['security_score']) for r in rows]
            avg_security_score = sum(security_scores) / len(security_scores) if security_scores else 0
            count = len(rows)
            prompts_with_vuln = sum(int(r['total_vulnerabilities']) > 0 for r in rows)
            prevalence = (prompts_with_vuln / count) if count else 0.0
            avg_weighted_score = (weighted_score / count) if count else 0.0
            
            results.append({
                'key': key,
                'count': count,
                'prompts_with_vuln': prompts_with_vuln,
                'prevalence': round(prevalence, 4),
                'total_vulnerabilities': total_vulns,
                'error_count': error_count,
                'warning_count': warning_count,
                'info_count': info_count,
                'weighted_score': round(weighted_score, 2),
                'avg_weighted_score': round(avg_weighted_score, 4),
                'avg_security_score': round(avg_security_score, 4),
                'min_security_score': round(min(security_scores), 4) if security_scores else 0,
                'max_security_score': round(max(security_scores), 4) if security_scores else 0
            })
        
        return results
    
    def generate_domain_prompttype_table(self):
        """Generate Domain × Prompt Type comparison table"""
        print("Generating Domain × Prompt Type table...")
        
        def key_func(row):
            return (row['domain'], row['prompt_type'])
        
        results = self.calculate_aggregate_metrics(key_func)
        
        # Organize as matrix
        domains = sorted(set(row['domain'] for row in self.data))
        prompt_types = sorted(set(row['prompt_type'] for row in self.data))
        
        # Create matrix
        matrix = {}
        for result in results:
            domain, prompt_type = result['key']
            matrix[(domain, prompt_type)] = result
        
        # Generate CSV
        csv_path = self.output_dir / 'domain_prompttype.csv'
        with open(csv_path, 'w', newline='') as f:
            fieldnames = ['domain', 'prompt_type', 'count',
                         'prompts_with_vuln', 'prevalence',
                         'total_vulnerabilities',
                         'error_count', 'warning_count', 'info_count',
                         'weighted_score', 'avg_weighted_score',
                         'avg_security_score',
                         'min_security_score', 'max_security_score']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for domain in domains:
                for prompt_type in prompt_types:
                    key = (domain, prompt_type)
                    if key in matrix:
                        row = matrix[key]
                        writer.writerow({
                            'domain': domain,
                            'prompt_type': prompt_type,
                            'count': row['count'],
                            'prompts_with_vuln': row['prompts_with_vuln'],
                            'prevalence': row['prevalence'],
                            'total_vulnerabilities': row['total_vulnerabilities'],
                            'error_count': row['error_count'],
                            'warning_count': row['warning_count'],
                            'info_count': row['info_count'],
                            'weighted_score': row['weighted_score'],
                            'avg_weighted_score': row['avg_weighted_score'],
                            'avg_security_score': row['avg_security_score'],
                            'min_security_score': row['min_security_score'],
                            'max_security_score': row['max_security_score']
                        })
        
        print(f"  ✓ Saved: {csv_path}")
        
        # Generate Markdown table
        md_path = self.output_dir / 'domain_prompttype.md'
        with open(md_path, 'w') as f:
            f.write("# Domain × Prompt Type Security Scores\n\n")
            f.write("| Domain | Prompt Type | Count | Prompts ≥1 Vuln | Prevalence | Total Vulns | Errors | Warnings | Info | Avg Weighted | Avg Security |\n")
            f.write("|--------|-------------|-------|-----------------|-----------|-------------|--------|----------|------|--------------|--------------|\n")
            
            for domain in domains:
                for prompt_type in prompt_types:
                    key = (domain, prompt_type)
                    if key in matrix:
                        row = matrix[key]
                        f.write(
                            f"| {domain} | {prompt_type} | {row['count']} | "
                            f"{row['prompts_with_vuln']} | {row['prevalence']:.3f} | "
                            f"{row['total_vulnerabilities']} | {row['error_count']} | "
                            f"{row['warning_count']} | {row['info_count']} | "
                            f"{row['avg_weighted_score']:.4f} | {row['avg_security_score']:.4f} |\n"
                        )
        
        print(f"  ✓ Saved: {md_path}")
        
        return matrix
    
    def generate_language_prompttype_table(self):
        """Generate Language × Prompt Type comparison table"""
        print("Generating Language × Prompt Type table...")
        
        def key_func(row):
            return (row['language'], row['prompt_type'])
        
        results = self.calculate_aggregate_metrics(key_func)
        
        # Organize as matrix
        languages = sorted(set(row['language'] for row in self.data))
        prompt_types = sorted(set(row['prompt_type'] for row in self.data))
        
        # Create matrix
        matrix = {}
        for result in results:
            language, prompt_type = result['key']
            matrix[(language, prompt_type)] = result
        
        # Generate CSV
        csv_path = self.output_dir / 'language_prompttype.csv'
        with open(csv_path, 'w', newline='') as f:
            fieldnames = ['language', 'prompt_type', 'count',
                         'prompts_with_vuln', 'prevalence',
                         'total_vulnerabilities',
                         'error_count', 'warning_count', 'info_count',
                         'weighted_score', 'avg_weighted_score',
                         'avg_security_score',
                         'min_security_score', 'max_security_score']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for language in languages:
                for prompt_type in prompt_types:
                    key = (language, prompt_type)
                    if key in matrix:
                        row = matrix[key]
                        writer.writerow({
                            'language': language,
                            'prompt_type': prompt_type,
                            'count': row['count'],
                            'prompts_with_vuln': row['prompts_with_vuln'],
                            'prevalence': row['prevalence'],
                            'total_vulnerabilities': row['total_vulnerabilities'],
                            'error_count': row['error_count'],
                            'warning_count': row['warning_count'],
                            'info_count': row['info_count'],
                            'weighted_score': row['weighted_score'],
                            'avg_weighted_score': row['avg_weighted_score'],
                            'avg_security_score': row['avg_security_score'],
                            'min_security_score': row['min_security_score'],
                            'max_security_score': row['max_security_score']
                        })
        
        print(f"  ✓ Saved: {csv_path}")
        
        # Generate Markdown table
        md_path = self.output_dir / 'language_prompttype.md'
        with open(md_path, 'w') as f:
            f.write("# Language × Prompt Type Security Scores\n\n")
            f.write("| Language | Prompt Type | Count | Prompts ≥1 Vuln | Prevalence | Total Vulns | Errors | Warnings | Info | Avg Weighted | Avg Security |\n")
            f.write("|----------|-------------|-------|-----------------|-----------|-------------|--------|----------|------|--------------|--------------|\n")
            
            for language in languages:
                for prompt_type in prompt_types:
                    key = (language, prompt_type)
                    if key in matrix:
                        row = matrix[key]
                        f.write(
                            f"| {language} | {prompt_type} | {row['count']} | "
                            f"{row['prompts_with_vuln']} | {row['prevalence']:.3f} | "
                            f"{row['total_vulnerabilities']} | {row['error_count']} | "
                            f"{row['warning_count']} | {row['info_count']} | "
                            f"{row['avg_weighted_score']:.4f} | {row['avg_security_score']:.4f} |\n"
                        )
        
        print(f"  ✓ Saved: {md_path}")
        
        return matrix
    
    def generate_domain_language_prompttype_table(self):
        """Generate comprehensive Domain × Language × Prompt Type matrix"""
        print("Generating Domain × Language × Prompt Type matrix...")
        
        def key_func(row):
            return (row['domain'], row['language'], row['prompt_type'])
        
        results = self.calculate_aggregate_metrics(key_func)
        
        # Organize as nested structure
        domains = sorted(set(row['domain'] for row in self.data))
        languages = sorted(set(row['language'] for row in self.data))
        prompt_types = sorted(set(row['prompt_type'] for row in self.data))
        
        # Create nested matrix
        matrix = {}
        for result in results:
            domain, language, prompt_type = result['key']
            matrix[(domain, language, prompt_type)] = result
        
        # Generate CSV (flat structure)
        csv_path = self.output_dir / 'domain_language_prompttype.csv'
        with open(csv_path, 'w', newline='') as f:
            fieldnames = ['domain', 'language', 'prompt_type', 'count',
                         'prompts_with_vuln', 'prevalence',
                         'total_vulnerabilities',
                         'error_count', 'warning_count', 'info_count',
                         'weighted_score', 'avg_weighted_score',
                         'avg_security_score',
                         'min_security_score', 'max_security_score']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for domain in domains:
                for language in languages:
                    for prompt_type in prompt_types:
                        key = (domain, language, prompt_type)
                        if key in matrix:
                            row = matrix[key]
                            writer.writerow({
                                'domain': domain,
                                'language': language,
                                'prompt_type': prompt_type,
                                'count': row['count'],
                                'prompts_with_vuln': row['prompts_with_vuln'],
                                'prevalence': row['prevalence'],
                                'total_vulnerabilities': row['total_vulnerabilities'],
                                'error_count': row['error_count'],
                                'warning_count': row['warning_count'],
                                'info_count': row['info_count'],
                                'weighted_score': row['weighted_score'],
                                'avg_weighted_score': row['avg_weighted_score'],
                                'avg_security_score': row['avg_security_score'],
                                'min_security_score': row['min_security_score'],
                                'max_security_score': row['max_security_score']
                            })
        
        print(f"  ✓ Saved: {csv_path}")
        
        # Generate JSON for programmatic access
        json_data = {}
        for domain in domains:
            json_data[domain] = {}
            for language in languages:
                json_data[domain][language] = {}
                for prompt_type in prompt_types:
                    key = (domain, language, prompt_type)
                    if key in matrix:
                        row = matrix[key]
                        json_data[domain][language][prompt_type] = {
                            'count': row['count'],
                            'prompts_with_vuln': row['prompts_with_vuln'],
                            'prevalence': row['prevalence'],
                            'total_vulnerabilities': row['total_vulnerabilities'],
                            'error_count': row['error_count'],
                            'warning_count': row['warning_count'],
                            'info_count': row['info_count'],
                            'weighted_score': row['weighted_score'],
                            'avg_weighted_score': row['avg_weighted_score'],
                            'avg_security_score': row['avg_security_score'],
                            'min_security_score': row['min_security_score'],
                            'max_security_score': row['max_security_score']
                        }
        
        json_path = self.output_dir.parent / 'tables_data.json'
        with open(json_path, 'w') as f:
            json.dump(json_data, f, indent=2)
        
        print(f"  ✓ Saved: {json_path}")
        
        return matrix
    
    def generate_summary_statistics(self):
        """Generate summary statistics and comparisons"""
        print("Generating summary statistics...")
        
        # Overall statistics
        total_prompts = len(self.data)
        total_vulns = sum(int(r['total_vulnerabilities']) for r in self.data)
        prompts_with_vuln = sum(int(r['total_vulnerabilities']) > 0 for r in self.data)
        total_errors = sum(int(r['error_count']) for r in self.data)
        total_warnings = sum(int(r['warning_count']) for r in self.data)
        total_info = sum(int(r['info_count']) for r in self.data)
        avg_security_score = sum(float(r['security_score']) for r in self.data) / total_prompts
        avg_weighted_score = sum(float(r['weighted_score']) for r in self.data) / total_prompts
        overall_prevalence = prompts_with_vuln / total_prompts if total_prompts else 0.0
        
        # By prompt type
        prompt_type_stats = {}
        for prompt_type in set(r['prompt_type'] for r in self.data):
            type_data = [r for r in self.data if r['prompt_type'] == prompt_type]
            type_prompts_with_vuln = sum(int(r['total_vulnerabilities']) > 0 for r in type_data)
            type_prevalence = type_prompts_with_vuln / len(type_data) if type_data else 0.0
            prompt_type_stats[prompt_type] = {
                'count': len(type_data),
                'prompts_with_vuln': type_prompts_with_vuln,
                'prevalence': type_prevalence,
                'total_vulnerabilities': sum(int(r['total_vulnerabilities']) for r in type_data),
                'error_count': sum(int(r['error_count']) for r in type_data),
                'warning_count': sum(int(r['warning_count']) for r in type_data),
                'info_count': sum(int(r['info_count']) for r in type_data),
                'avg_weighted_score': sum(float(r['weighted_score']) for r in type_data) / len(type_data) if type_data else 0.0,
                'avg_security_score': sum(float(r['security_score']) for r in type_data) / len(type_data),
                'min_security_score': min(float(r['security_score']) for r in type_data),
                'max_security_score': max(float(r['security_score']) for r in type_data)
            }
        
        # By domain
        domain_stats = {}
        for domain in set(r['domain'] for r in self.data):
            domain_data = [r for r in self.data if r['domain'] == domain]
            domain_prompts_with_vuln = sum(int(r['total_vulnerabilities']) > 0 for r in domain_data)
            domain_prevalence = domain_prompts_with_vuln / len(domain_data) if domain_data else 0.0
            domain_stats[domain] = {
                'count': len(domain_data),
                'prompts_with_vuln': domain_prompts_with_vuln,
                'prevalence': domain_prevalence,
                'total_vulnerabilities': sum(int(r['total_vulnerabilities']) for r in domain_data),
                'error_count': sum(int(r['error_count']) for r in domain_data),
                'warning_count': sum(int(r['warning_count']) for r in domain_data),
                'info_count': sum(int(r['info_count']) for r in domain_data),
                'avg_weighted_score': sum(float(r['weighted_score']) for r in domain_data) / len(domain_data) if domain_data else 0.0,
                'avg_security_score': sum(float(r['security_score']) for r in domain_data) / len(domain_data),
                'min_security_score': min(float(r['security_score']) for r in domain_data),
                'max_security_score': max(float(r['security_score']) for r in domain_data)
            }
        
        # By language
        language_stats = {}
        for language in set(r['language'] for r in self.data):
            lang_data = [r for r in self.data if r['language'] == language]
            lang_prompts_with_vuln = sum(int(r['total_vulnerabilities']) > 0 for r in lang_data)
            lang_prevalence = lang_prompts_with_vuln / len(lang_data) if lang_data else 0.0
            language_stats[language] = {
                'count': len(lang_data),
                'prompts_with_vuln': lang_prompts_with_vuln,
                'prevalence': lang_prevalence,
                'total_vulnerabilities': sum(int(r['total_vulnerabilities']) for r in lang_data),
                'error_count': sum(int(r['error_count']) for r in lang_data),
                'warning_count': sum(int(r['warning_count']) for r in lang_data),
                'info_count': sum(int(r['info_count']) for r in lang_data),
                'avg_weighted_score': sum(float(r['weighted_score']) for r in lang_data) / len(lang_data) if lang_data else 0.0,
                'avg_security_score': sum(float(r['security_score']) for r in lang_data) / len(lang_data),
                'min_security_score': min(float(r['security_score']) for r in lang_data),
                'max_security_score': max(float(r['security_score']) for r in lang_data)
            }
        
        # Find best/worst performing combinations
        best_prompt = max(self.data, key=lambda r: float(r['security_score']))
        worst_prompt = min(self.data, key=lambda r: float(r['security_score']))
        
        # Compare security_aware vs naive
        security_aware_data = [r for r in self.data if r['prompt_type'] == 'security_aware']
        naive_data = [r for r in self.data if r['prompt_type'] == 'naive']
        
        security_aware_avg = sum(float(r['security_score']) for r in security_aware_data) / len(security_aware_data) if security_aware_data else 0
        naive_avg = sum(float(r['security_score']) for r in naive_data) / len(naive_data) if naive_data else 0
        improvement = security_aware_avg - naive_avg
        
        # Save statistics CSV
        stats_path = self.output_dir.parent / 'STATISTICS.csv'
        with open(stats_path, 'w', newline='') as f:
            fieldnames = ['category', 'value', 'count',
                         'prompts_with_vuln', 'prevalence',
                         'total_vulnerabilities',
                         'error_count', 'warning_count', 'info_count',
                         'avg_weighted_score',
                         'avg_security_score', 'min_security_score', 'max_security_score']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            # Overall
            writer.writerow({
                'category': 'OVERALL',
                'value': 'all',
                'count': total_prompts,
                'prompts_with_vuln': prompts_with_vuln,
                'prevalence': round(overall_prevalence, 4),
                'total_vulnerabilities': total_vulns,
                'error_count': total_errors,
                'warning_count': total_warnings,
                'info_count': total_info,
                'avg_weighted_score': round(avg_weighted_score, 4),
                'avg_security_score': round(avg_security_score, 4),
                'min_security_score': min(float(r['security_score']) for r in self.data),
                'max_security_score': max(float(r['security_score']) for r in self.data)
            })
            
            # By prompt type
            for prompt_type, stats in prompt_type_stats.items():
                writer.writerow({
                    'category': 'PROMPT_TYPE',
                    'value': prompt_type,
                    **{k: round(v, 4) if isinstance(v, float) else v for k, v in stats.items()}
                })
            
            # By domain
            for domain, stats in domain_stats.items():
                writer.writerow({
                    'category': 'DOMAIN',
                    'value': domain,
                    **{k: round(v, 4) if isinstance(v, float) else v for k, v in stats.items()}
                })
            
            # By language
            for language, stats in language_stats.items():
                writer.writerow({
                    'category': 'LANGUAGE',
                    'value': language,
                    **{k: round(v, 4) if isinstance(v, float) else v for k, v in stats.items()}
                })
        
        print(f"  ✓ Saved: {stats_path}")
        
        # Generate summary markdown report
        summary_path = self.output_dir.parent / 'SUMMARY.md'
        with open(summary_path, 'w') as f:
            f.write("# Security Analysis Summary\n\n")
            f.write("## Overall Statistics\n\n")
            f.write(f"- **Total Prompts Analyzed**: {total_prompts}\n")
            f.write(f"- **Total Vulnerabilities Found**: {total_vulns}\n")
            f.write(f"  - Errors: {total_errors}\n")
            f.write(f"  - Warnings: {total_warnings}\n")
            f.write(f"  - Info: {total_info}\n")
            f.write(f"- **Prompts with ≥1 Vulnerability**: {prompts_with_vuln} ({overall_prevalence:.3f})\n")
            f.write(f"- **Average Weighted Severity per Prompt**: {avg_weighted_score:.4f}\n")
            f.write(f"- **Average Security Score**: {avg_security_score:.4f}\n")
            f.write(f"- **Security Score Range**: {min(float(r['security_score']) for r in self.data):.4f} - {max(float(r['security_score']) for r in self.data):.4f}\n\n")
            
            f.write("## By Prompt Type\n\n")
            f.write("| Prompt Type | Count | Prompts ≥1 Vuln | Prevalence | Total Vulns | Errors | Warnings | Info | Avg Weighted | Avg Security |\n")
            f.write("|-------------|-------|-----------------|-----------|------------|--------|----------|------|-------------|--------------|\n")
            for prompt_type, stats in sorted(prompt_type_stats.items()):
                f.write(
                    f"| {prompt_type} | {stats['count']} | {stats['prompts_with_vuln']} | "
                    f"{stats['prevalence']:.3f} | {stats['total_vulnerabilities']} | "
                    f"{stats['error_count']} | {stats['warning_count']} | {stats['info_count']} | "
                    f"{stats['avg_weighted_score']:.4f} | {stats['avg_security_score']:.4f} |\n"
                )
            
            f.write("\n## By Domain\n\n")
            f.write("| Domain | Count | Prompts ≥1 Vuln | Prevalence | Total Vulns | Errors | Warnings | Info | Avg Weighted | Avg Security |\n")
            f.write("|--------|-------|-----------------|-----------|------------|--------|----------|------|-------------|--------------|\n")
            for domain, stats in sorted(domain_stats.items()):
                f.write(
                    f"| {domain} | {stats['count']} | {stats['prompts_with_vuln']} | "
                    f"{stats['prevalence']:.3f} | {stats['total_vulnerabilities']} | "
                    f"{stats['error_count']} | {stats['warning_count']} | {stats['info_count']} | "
                    f"{stats['avg_weighted_score']:.4f} | {stats['avg_security_score']:.4f} |\n"
                )
            
            f.write("\n## By Language\n\n")
            f.write("| Language | Count | Prompts ≥1 Vuln | Prevalence | Total Vulns | Errors | Warnings | Info | Avg Weighted | Avg Security |\n")
            f.write("|----------|-------|-----------------|-----------|------------|--------|----------|------|-------------|--------------|\n")
            for language, stats in sorted(language_stats.items()):
                f.write(
                    f"| {language} | {stats['count']} | {stats['prompts_with_vuln']} | "
                    f"{stats['prevalence']:.3f} | {stats['total_vulnerabilities']} | "
                    f"{stats['error_count']} | {stats['warning_count']} | {stats['info_count']} | "
                    f"{stats['avg_weighted_score']:.4f} | {stats['avg_security_score']:.4f} |\n"
                )
            
            f.write("\n## Key Findings\n\n")
            f.write(f"### Security-Aware vs Naive Prompts\n\n")
            f.write(f"- **Security-Aware Average Score**: {security_aware_avg:.4f}\n")
            f.write(f"- **Naive Average Score**: {naive_avg:.4f}\n")
            f.write(f"- **Improvement**: {improvement:+.4f} ({improvement/naive_avg*100:+.2f}%)\n\n")
            
            f.write(f"### Best Performing Prompt\n\n")
            f.write(f"- **Task**: {best_prompt['task_id']}\n")
            f.write(f"- **Domain**: {best_prompt['domain']}\n")
            f.write(f"- **Language**: {best_prompt['language']}\n")
            f.write(f"- **Prompt Type**: {best_prompt['prompt_type']}\n")
            f.write(f"- **Security Score**: {best_prompt['security_score']}\n")
            f.write(f"- **Vulnerabilities**: {best_prompt['total_vulnerabilities']}\n\n")
            
            f.write(f"### Worst Performing Prompt\n\n")
            f.write(f"- **Task**: {worst_prompt['task_id']}\n")
            f.write(f"- **Domain**: {worst_prompt['domain']}\n")
            f.write(f"- **Language**: {worst_prompt['language']}\n")
            f.write(f"- **Prompt Type**: {worst_prompt['prompt_type']}\n")
            f.write(f"- **Security Score**: {worst_prompt['security_score']}\n")
            f.write(f"- **Vulnerabilities**: {worst_prompt['total_vulnerabilities']}\n\n")
            
            f.write("## Methodology\n\n")
            f.write("### Semgrep Configuration\n")
            f.write("- Used `--config=auto` for language-specific security rules\n")
            f.write("- Used `--config=p/security-audit` for comprehensive security audit rules\n\n")
            f.write("### Severity Weighting\n")
            f.write("- ERROR: weight 3\n")
            f.write("- WARNING: weight 2\n")
            f.write("- INFO: weight 1\n\n")
            f.write("### Aggregation Method\n")
            f.write("- Union approach: vulnerabilities counted if they appear in any of the 3 runs\n")
            f.write("- Unique vulnerabilities identified by: rule_id + file_path + line_number\n\n")
            f.write("### Security Score Calculation\n")
            f.write("- Formula: `security_score = 1 - min(weighted_score / normalization_factor, 1.0)`\n")
            f.write("- Normalization factor: 95th percentile of weighted scores (or minimum of 10)\n")
            f.write("- Higher score = more secure (fewer vulnerabilities)\n")
            f.write("- Range: 0.0 (least secure) to 1.0 (most secure)\n")
        
        print(f"  ✓ Saved: {summary_path}")
        
        return {
            'overall': {
                'total_prompts': total_prompts,
                'total_vulnerabilities': total_vulns,
                'avg_security_score': avg_security_score
            },
            'prompt_type_stats': prompt_type_stats,
            'domain_stats': domain_stats,
            'language_stats': language_stats,
            'security_aware_vs_naive': {
                'security_aware_avg': security_aware_avg,
                'naive_avg': naive_avg,
                'improvement': improvement
            }
        }


def main():
    parser = argparse.ArgumentParser(
        description='Generate research tables from security analysis results',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate all tables from security scores
  python3 generate_analysis_tables.py --input analysis/security_scores.csv
  
  # Specify output directory
  python3 generate_analysis_tables.py --input analysis/security_scores.csv --output analysis/tables
        """
    )
    
    parser.add_argument('--input',
                        default='analysis/security_scores.csv',
                        help='Input CSV file with security scores (default: analysis/security_scores.csv)')
    
    parser.add_argument('--output',
                        default='analysis/tables',
                        help='Output directory for tables (default: analysis/tables)')
    
    args = parser.parse_args()
    
    # Resolve paths relative to script location
    script_dir = Path(__file__).parent
    input_path = (script_dir / args.input).resolve()
    output_path = (script_dir / args.output).resolve()
    
    if not input_path.exists():
        print(f"✗ Error: {input_path} not found")
        sys.exit(1)
    
    print(f"\n{'='*70}")
    print(f"GENERATING RESEARCH TABLES")
    print(f"{'='*70}\n")
    print(f"Input: {input_path}")
    print(f"Output: {output_path}\n")
    
    generator = TableGenerator(input_path, output_path)
    
    generator.generate_domain_prompttype_table()
    generator.generate_language_prompttype_table()
    generator.generate_domain_language_prompttype_table()
    generator.generate_summary_statistics()
    
    print(f"\n✓ All tables generated successfully!")
    print(f"  Output directory: {output_path}")
    print()


if __name__ == "__main__":
    main()

