#!/usr/bin/env python3
"""
analyze_vulnerabilities.py - Run security analysis on collected code using multiple scanners

This script:
1. Scans all collected code with Bandit (Python), cppcheck (C++), ESLint (TypeScript)
2. Parses and stores vulnerability results
3. Aggregates vulnerabilities across runs (union approach)
4. Calculates security scores with severity weighting
5. Generates aggregated results for research analysis

Usage:
    python3 analyze_vulnerabilities.py --collected-code ../collected_code/auto
    python3 analyze_vulnerabilities.py --collected-code ../collected_code/auto --output analysis
"""

import csv
import json
import subprocess
import os
import sys
from pathlib import Path
from datetime import datetime
import argparse
from collections import defaultdict

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from scanner_cwe_mappings import get_cwe_from_rule


class VulnerabilityAnalyzer:
    def __init__(self, collected_code_dir, output_dir, dry_run=False, skip_existing=False):
        self.collected_code_dir = Path(collected_code_dir)
        self.output_dir = Path(output_dir)
        self.dry_run = dry_run
        self.skip_existing = skip_existing
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.run_results_root = self.output_dir / 'vuln_runs'
        self.run_results_root.mkdir(parents=True, exist_ok=True)
        
        # Severity weights
        self.severity_weights = {
            'ERROR': 3,
            'WARNING': 2,
            'INFO': 1
        }
        
        # Statistics
        self.stats = {
            'total_runs_scanned': 0,
            'runs_with_vulnerabilities': 0,
            'total_vulnerabilities': 0,
            'vulnerabilities_by_severity': defaultdict(int)
        }
        
        # Domain processing order
        self.domain_order = ['aiml_ds', 'auth_crypto', 'file_system', 'web_api']
        
        # Load existing results if resuming
        self.existing_results = []
        self.csv_path = self.output_dir / 'vuln_results.csv'
        if self.csv_path.exists() and self.skip_existing:
            with open(self.csv_path, 'r') as f:
                reader = csv.DictReader(f)
                self.existing_results = list(reader)

        # Load CWE-CVSS mapping
        self.cwe_cvss_map = {}
        # Assuming script is in scripts/ and data is in data/
        self.cwe_cvss_path = Path(__file__).resolve().parent.parent / 'data' / 'cwe_cvss_mapping.json'
        
        if self.cwe_cvss_path.exists():
            try:
                with open(self.cwe_cvss_path, 'r') as f:
                    self.cwe_cvss_map = json.load(f)
                print(f"✓ Loaded {len(self.cwe_cvss_map)} CWE-CVSS mappings")
            except Exception as e:
                print(f"⚠ Warning: Could not load CWE-CVSS mapping: {e}")
        else:
            print(f"⚠ Warning: CWE-CVSS mapping file not found at {self.cwe_cvss_path}")

    
    def _get_run_results_path(self, run_dir, ensure_parent=False):
        """Return the analysis-side results.json path for a run"""
        try:
            relative_run_dir = run_dir.relative_to(self.collected_code_dir)
        except ValueError:
            relative_run_dir = Path(run_dir.name)
        target_dir = self.run_results_root / relative_run_dir
        if ensure_parent:
            target_dir.mkdir(parents=True, exist_ok=True)
        return target_dir / 'results.json'
    
    def check_scanners(self):
        """Verify required scanners are available"""
        scanners_available = {}
        
        # Check Bandit (Python)
        try:
            result = subprocess.run(
                ['bandit', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                scanners_available['bandit'] = True
                print(f"✓ Bandit found: {result.stdout.strip()}")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            scanners_available['bandit'] = False
            print("⚠ Bandit not found (Python scans will be skipped)")
        
        # Check cppcheck (C++)
        try:
            result = subprocess.run(
                ['cppcheck', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                scanners_available['cppcheck'] = True
                print(f"✓ cppcheck found: {result.stdout.strip()}")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            scanners_available['cppcheck'] = False
            print("⚠ cppcheck not found (C++ scans will be skipped)")
        
        # Check Semgrep (for TypeScript and other languages)
        try:
            result = subprocess.run(
                ['semgrep', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                scanners_available['semgrep'] = True
                print(f"✓ Semgrep found: {result.stdout.strip()}")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            scanners_available['semgrep'] = False
            print("⚠ Semgrep not found (TypeScript scans will be skipped)")
        
        return scanners_available
    
    def run_bandit(self, code_dir):
        """Run Bandit on a Python code directory"""
        if not code_dir.exists() or not any(code_dir.glob('*.py')):
            return []
        
        if self.dry_run:
            return []
        
        cmd = ['bandit', '-r', '.', '-f', 'json', '-q']
        
        try:
            result = subprocess.run(
                cmd,
                cwd=code_dir,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode in [0, 1]:  # Bandit returns 1 if issues found
                try:
                    data = json.loads(result.stdout)
                    vulnerabilities = []
                    for result_item in data.get('results', []):
                        # Map Bandit severity to our severity levels
                        bandit_severity = result_item.get('issue_severity', 'LOW').upper()
                        if bandit_severity == 'HIGH':
                            severity = 'ERROR'
                        elif bandit_severity == 'MEDIUM':
                            severity = 'WARNING'
                        else:
                            severity = 'INFO'
                        
                        # Get relative file path
                        file_path = result_item.get('filename', '')
                        if file_path:
                            try:
                                # Try to make relative to code_dir
                                abs_path = Path(file_path).resolve()
                                code_abs = code_dir.resolve()
                                if abs_path.is_relative_to(code_abs):
                                    rel_path = abs_path.relative_to(code_abs)
                                else:
                                    rel_path = Path(file_path).name
                            except (ValueError, AttributeError):
                                rel_path = Path(file_path).name
                        else:
                            rel_path = Path('unknown')
                        
                        cwe = get_cwe_from_rule('bandit', result_item.get('test_id'), None)
                        cvss_score = self.cwe_cvss_map.get(cwe) if cwe else None

                        vulnerabilities.append({
                            'scanner': 'bandit',
                            'rule_id': result_item.get('test_id', 'unknown'),
                            'severity': severity,
                            'message': result_item.get('issue_text', ''),
                            'cwe': cwe,
                            'cvss_score': cvss_score,
                            'file_path': str(rel_path),
                            'line_number': result_item.get('line_number', 0),
                            'end_line': result_item.get('line_number', 0)
                        })
                    return vulnerabilities
                except json.JSONDecodeError:
                    return []
            return []
        except subprocess.TimeoutExpired:
            return []
        except Exception:
            return []
    
    def run_cppcheck(self, code_dir):
        """Run cppcheck on a C++ code directory"""
        if not code_dir.exists():
            return []
        
        # Check for C++ files
        cpp_files = list(code_dir.glob('*.cpp')) + list(code_dir.glob('*.cxx')) + \
                    list(code_dir.glob('*.cc')) + list(code_dir.glob('*.h')) + \
                    list(code_dir.glob('*.hpp'))
        if not cpp_files:
            return []
        
        if self.dry_run:
            return []
        
        import xml.etree.ElementTree as ET
        
        # Use security-focused checks: --enable=warning focuses on bugs and security issues
        # Suppress common non-security style issues
        cmd = ['cppcheck', 
               '--enable=warning',  # Focus on bugs/security issues, not style
               '--suppress=missingIncludeSystem',  # Style issue, not security
               '--suppress=unusedFunction',         # Code quality, not security
               '--suppress=functionStatic',        # Code quality, not security
               '--suppress=checkersReport',         # Generic reports, not security
               '--inconclusive', 
               '--xml', 
               '--xml-version=2', 
               '.']
        
        try:
            # cppcheck writes XML to stderr
            result = subprocess.run(
                cmd,
                cwd=code_dir,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # Read XML from stderr (cppcheck writes XML to stderr)
            xml_output = result.stderr
            
            vulnerabilities = []
            if xml_output:
                try:
                    # cppcheck mixes progress messages with XML, extract just the XML part
                    xml_start = xml_output.find('<?xml')
                    if xml_start != -1:
                        xml_output = xml_output[xml_start:]
                    
                    root = ET.fromstring(xml_output)
                    for error in root.findall('.//error'):
                        # Map cppcheck severity
                        cpp_severity = error.get('severity', 'style').upper()
                        if cpp_severity in ['ERROR', 'CRITICAL']:
                            severity = 'ERROR'
                        elif cpp_severity in ['WARNING', 'WARN']:
                            severity = 'WARNING'
                        else:
                            severity = 'INFO'
                        
                        # In cppcheck XML v2, file/line are in <location> child elements, not on <error>
                        # Get the first location (primary location of the error)
                        locations = error.findall('location')
                        file_path = ''
                        line_num = 0
                        
                        if locations:
                            # Use first location as primary
                            first_loc = locations[0]
                            file_path = first_loc.get('file', '')
                            try:
                                line_num = int(first_loc.get('line', 0))
                            except (ValueError, TypeError):
                                line_num = 0
                        
                        # If no location, try file0 attribute (some errors have this)
                        if not file_path:
                            file_path = error.get('file0', '')
                        
                        # Process file path
                        if file_path:
                            try:
                                # Try to make relative to code_dir
                                abs_path = Path(file_path).resolve()
                                code_abs = code_dir.resolve()
                                if abs_path.is_relative_to(code_abs):
                                    rel_path = abs_path.relative_to(code_abs)
                                else:
                                    rel_path = Path(file_path).name
                            except (ValueError, AttributeError):
                                rel_path = Path(file_path).name
                        else:
                            # Skip errors without file information (like normalCheckLevelMaxBranches)
                            # These are informational messages, not file-specific vulnerabilities
                            continue
                        
                        msg = error.get('msg', '')
                        id_val = error.get('id', 'unknown')
                        
                        id_val = error.get('id', 'unknown')
                        raw_cwe = error.get('cwe')
                        cwe = get_cwe_from_rule('cppcheck', id_val, raw_cwe)
                        cvss_score = self.cwe_cvss_map.get(cwe) if cwe else None
                        
                        vulnerabilities.append({
                            'scanner': 'cppcheck',
                            'rule_id': id_val,
                            'severity': severity,
                            'message': msg,
                            'cwe': cwe, 
                            'cvss_score': cvss_score,
                            'file_path': str(rel_path),
                            'line_number': line_num,
                            'end_line': line_num
                        })
                except ET.ParseError as e:
                    # If XML parsing fails, might be due to progress messages
                    pass
            
            return vulnerabilities
        except subprocess.TimeoutExpired:
            return []
        except Exception:
            return []
    
    def run_semgrep_js_ts(self, code_dir):
        """Run Semgrep on a JavaScript/TypeScript code directory"""
        if not code_dir.exists():
            return {"results": [], "errors": []}
        
        # Check for JavaScript/TypeScript files
        js_ts_files = list(code_dir.glob('*.js')) + list(code_dir.glob('*.jsx')) + \
                     list(code_dir.glob('*.ts')) + list(code_dir.glob('*.tsx'))
        if not js_ts_files:
            return {"results": [], "errors": []}
        
        if self.dry_run:
            return {"results": [], "errors": []}
        
        # Use Semgrep with security rules (works for TypeScript/JavaScript)
        # Run from within the directory like Bandit/cppcheck do
        # --config=auto auto-detects TypeScript and applies language-specific rules
        # --no-git-ignore: scan all files, not just git-tracked ones
        cmd = [
            'semgrep',
            '--config=auto',              # Auto-detect language (TypeScript)
            '--config=p/security-audit',  # Security audit rules (includes TS/JS)
            '--no-git-ignore',            # Scan all files, not just git-tracked
            '--json',
            '--quiet',
            '.'  # Scan current directory
        ]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=code_dir,  # Run from within the code directory like Bandit/cppcheck
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # Semgrep returns 0 on success, 1 if findings found, 2 on error
            if result.returncode in [0, 1]:
                try:
                    output = json.loads(result.stdout)
                    # Ensure we always return a dict
                    if isinstance(output, list):
                        return {"results": output, "errors": []}
                    elif isinstance(output, dict):
                        # Check if results are in the dict
                        results = output.get('results', [])
                        if results:
                            # Debug: print first few results to see what we're getting
                            pass
                        return output
                    else:
                        return {"results": [], "errors": []}
                except json.JSONDecodeError as e:
                    # If JSON parse fails, check stderr for errors
                    if result.stderr:
                        return {"results": [], "errors": [result.stderr]}
                    return {"results": [], "errors": [f"Failed to parse JSON: {e}"]}
            else:
                # Return code 2 means error - but check if there's still output
                try:
                    # Sometimes Semgrep returns 2 but still has JSON output
                    output = json.loads(result.stdout)
                    if isinstance(output, list):
                        return {"results": output, "errors": []}
                    elif isinstance(output, dict):
                        return output
                except:
                    pass
                # If no valid output, return error
                error_msg = result.stderr if result.stderr else "Semgrep error"
                return {"results": [], "errors": [error_msg]}
        
        except subprocess.TimeoutExpired:
            return {"results": [], "errors": ["Timeout"]}
        except Exception as e:
            return {"results": [], "errors": [str(e)]}
    
    def extract_semgrep_vulnerabilities(self, semgrep_result, code_dir):
        """Extract vulnerability information from Semgrep result"""
        vulnerabilities = []
        
        # Handle both dict and list formats from Semgrep
        if isinstance(semgrep_result, list):
            findings = semgrep_result
        elif isinstance(semgrep_result, dict):
            findings = semgrep_result.get('results', [])
        else:
            return []
        
        for finding in findings:
            # Extract CWE if available
            cwe = None
            if 'metadata' in finding:
                metadata = finding['metadata']
                if 'cwe' in metadata:
                    cwe_list = metadata['cwe']
                    if isinstance(cwe_list, list) and len(cwe_list) > 0:
                        cwe = cwe_list[0]  # Take first CWE
                    elif isinstance(cwe_list, str):
                        cwe = cwe_list
            
            # Get file path and make it relative
            file_path = finding.get('path', '')
            if file_path:
                try:
                    abs_path = Path(file_path).resolve()
                    code_abs = code_dir.resolve()
                    if abs_path.is_relative_to(code_abs):
                        rel_path = abs_path.relative_to(code_abs)
                    else:
                        rel_path = Path(file_path).name
                except (ValueError, AttributeError):
                    rel_path = Path(file_path).name
            else:
                rel_path = Path('unknown')
            
            check_id = finding.get('check_id', 'unknown')
            final_cwe = get_cwe_from_rule('semgrep', check_id, cwe)
            cvss_score = self.cwe_cvss_map.get(final_cwe) if final_cwe else None
            
            vulnerability = {
                'scanner': 'semgrep',
                'rule_id': check_id,
                'severity': finding.get('extra', {}).get('severity', 'INFO').upper(),
                'message': finding.get('message', ''),
                'cwe': final_cwe,
                'cvss_score': cvss_score,
                'file_path': str(rel_path),
                'line_number': finding.get('start', {}).get('line', 0),
                'end_line': finding.get('end', {}).get('line', 0)
            }
            vulnerabilities.append(vulnerability)
        
        return vulnerabilities
    
    def run_semgrep_java(self, code_dir):
        """Run Semgrep on a Java code directory"""
        if not code_dir.exists():
            return {"results": [], "errors": []}
        
        # Check for Java files
        java_files = list(code_dir.glob('*.java'))
        if not java_files:
            return {"results": [], "errors": []}
        
        if self.dry_run:
            return {"results": [], "errors": []}
        
        # Use Semgrep with security rules for Java
        # Run from within the directory like Bandit/cppcheck do
        # --config=auto auto-detects Java
        # --no-git-ignore: scan all files, not just git-tracked ones
        cmd = [
            'semgrep',
            '--config=auto',              # Auto-detect language (Java)
            '--config=p/security-audit',  # Security audit rules (includes Java)
            '--no-git-ignore',            # Scan all files, not just git-tracked
            '--json',
            '--quiet',
            '.'  # Scan current directory
        ]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=code_dir,  # Run from within the code directory like Bandit/cppcheck
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # Semgrep returns 0 on success, 1 if findings found, 2 on error
            if result.returncode in [0, 1]:
                try:
                    output = json.loads(result.stdout)
                    # Ensure we always return a dict
                    if isinstance(output, list):
                        return {"results": output, "errors": []}
                    elif isinstance(output, dict):
                        return output
                    else:
                        return {"results": [], "errors": []}
                except json.JSONDecodeError as e:
                    # If JSON parse fails, check stderr for errors
                    if result.stderr:
                        return {"results": [], "errors": [result.stderr]}
                    return {"results": [], "errors": [f"Failed to parse JSON: {e}"]}
            else:
                # Return code 2 means error - but check if there's still output
                try:
                    # Sometimes Semgrep returns 2 but still has JSON output
                    output = json.loads(result.stdout)
                    if isinstance(output, list):
                        return {"results": output, "errors": []}
                    elif isinstance(output, dict):
                        return output
                except:
                    pass
                # If no valid output, return error
                error_msg = result.stderr if result.stderr else "Semgrep error"
                return {"results": [], "errors": [error_msg]}
        
        except subprocess.TimeoutExpired:
            return {"results": [], "errors": ["Timeout"]}
        except Exception as e:
            return {"results": [], "errors": [str(e)]}
    
    def scan_code_directory(self, code_dir, language, scanners_available):
        """Run appropriate scanners based on language"""
        all_vulnerabilities = []
        
        # Normalize language name
        lang_lower = language.lower()
        
        if lang_lower == 'python' and scanners_available.get('bandit', False):
            vulns = self.run_bandit(code_dir)
            all_vulnerabilities.extend(vulns)
        elif lang_lower in ['cpp', 'c++', 'c'] and scanners_available.get('cppcheck', False):
            vulns = self.run_cppcheck(code_dir)
            all_vulnerabilities.extend(vulns)
        elif lang_lower in ['typescript', 'ts', 'tsx', 'javascript', 'js', 'jsx'] and scanners_available.get('semgrep', False):
            semgrep_output = self.run_semgrep_js_ts(code_dir)
            vulns = self.extract_semgrep_vulnerabilities(semgrep_output, code_dir)
            all_vulnerabilities.extend(vulns)
        elif lang_lower == 'java' and scanners_available.get('semgrep', False):
            semgrep_output = self.run_semgrep_java(code_dir)
            vulns = self.extract_semgrep_vulnerabilities(semgrep_output, code_dir)
            all_vulnerabilities.extend(vulns)
        
        return all_vulnerabilities
    
    def analyze_all_runs(self):
        """Scan all collected code runs"""
        print(f"\n{'='*70}")
        print(f"VULNERABILITY ANALYSIS")
        print(f"{'='*70}\n")
        
        scanners_available = {}
        if not self.dry_run:
            scanners_available = self.check_scanners()
            if not any(scanners_available.values()):
                print("✗ Error: No scanners available. Please install at least one scanner.")
                return False
        
        print(f"Scanning code in: {self.collected_code_dir}")
        print(f"Output directory: {self.output_dir}\n")
        
        all_results = []
        runs_processed = 0
        
        # Detect structure: check if we're at model level or root level
        # If first level contains domain directories (like aiml_ds, web_api), we're at model level
        first_level_dirs = [d for d in self.collected_code_dir.iterdir() if d.is_dir()]
        known_domains = ['aiml_ds', 'web_api', 'auth_crypto', 'file_system']
        is_model_level = any(d.name in known_domains for d in first_level_dirs)
        
        if is_model_level:
            # We're already at model level: collected_code/model/
            model_name = self.collected_code_dir.name
            # Sort domains in specified order
            domain_dirs = []
            for domain_name in self.domain_order:
                for d in first_level_dirs:
                    if d.name == domain_name:
                        domain_dirs.append(d)
                        break
            # Add any domains not in the order list
            for d in first_level_dirs:
                if d.name not in self.domain_order and d.name in known_domains:
                    domain_dirs.append(d)
        else:
            # We're at root level: collected_code/
            # Need to iterate through model directories first
            model_dirs = first_level_dirs
            # Process all model directories
            for model_dir in model_dirs:
                if not model_dir.is_dir():
                    continue
                
                model_name = model_dir.name
                all_domain_dirs = [d for d in model_dir.iterdir() if d.is_dir()]
                
                # Sort domains in specified order
                domain_dirs = []
                for domain_name in self.domain_order:
                    for d in all_domain_dirs:
                        if d.name == domain_name:
                            domain_dirs.append(d)
                            break
                # Add any domains not in the order list
                for d in all_domain_dirs:
                    if d.name not in self.domain_order and d.name in known_domains:
                        domain_dirs.append(d)
                
                # Process domains for this model
                for domain_dir in domain_dirs:
                    if not domain_dir.is_dir():
                        continue
                    
                    domain = domain_dir.name
                    print(f"\n{'='*60}")
                    print(f"Processing domain: {domain}")
                    print(f"{'='*60}\n")
                    
                    for task_dir in sorted(domain_dir.iterdir(), key=lambda x: x.name):
                        if not task_dir.is_dir():
                            continue
                        
                        task_id = task_dir.name
                        
                        for prompt_dir in sorted(task_dir.iterdir(), key=lambda x: x.name):
                            if not prompt_dir.is_dir():
                                continue
                            
                            # Parse language and prompt_type from directory name
                            dir_parts = prompt_dir.name.split('_', 1)
                            if len(dir_parts) != 2:
                                continue
                            
                            language = dir_parts[0]
                            prompt_type = dir_parts[1]
                            
                            # Process each run
                            for run_dir in sorted(prompt_dir.iterdir(), key=lambda x: x.name):
                                if not run_dir.is_dir() or not run_dir.name.startswith('run_'):
                                    continue
                                
                                try:
                                    run_number = int(run_dir.name.split('_')[1])
                                except (ValueError, IndexError):
                                    continue
                                
                                code_dir = run_dir / 'code'
                                
                                if not code_dir.exists():
                                    continue
                                
                                # Check if already scanned (resume functionality)
                                results_file = self._get_run_results_path(run_dir)
                                if self.skip_existing and results_file.exists():
                                    try:
                                        with open(results_file, 'r') as f:
                                            existing_data = json.load(f)
                                            vulnerabilities = existing_data.get('vulnerabilities', [])
                                            # Add to results
                                            for vuln in vulnerabilities:
                                                all_results.append({
                                                    'task_id': task_id,
                                                    'domain': domain,
                                                    'language': language,
                                                    'prompt_type': prompt_type,
                                                    'run_number': run_number,
                                                    'model': model_name,
                                                    **vuln
                                                })
                                            runs_processed += 1
                                            if runs_processed % 10 == 0:
                                                print(f"  Processed {runs_processed} runs... (skipped existing)")
                                            continue
                                    except (json.JSONDecodeError, KeyError):
                                        pass  # Re-scan if file is corrupted
                                
                                print(f"Scanning: {task_id}/{language}/{prompt_type}/run_{run_number}")
                                
                                # Run appropriate scanners
                                vulnerabilities = self.scan_code_directory(code_dir, language, scanners_available)
                                
                                # Save per-run results
                                results_file = self._get_run_results_path(run_dir, ensure_parent=True)
                                with open(results_file, 'w') as f:
                                    json.dump({
                                        'timestamp': datetime.now().isoformat(),
                                        'language': language,
                                        'vulnerabilities': vulnerabilities,
                                        'vulnerability_count': len(vulnerabilities)
                                    }, f, indent=2)
                                
                                # Add to master results
                                for vuln in vulnerabilities:
                                    all_results.append({
                                        'task_id': task_id,
                                        'domain': domain,
                                        'language': language,
                                        'prompt_type': prompt_type,
                                        'run_number': run_number,
                                        'model': model_name,
                                        **vuln
                                    })
                                
                                # Update statistics
                                self.stats['total_runs_scanned'] += 1
                                if len(vulnerabilities) > 0:
                                    self.stats['runs_with_vulnerabilities'] += 1
                                    self.stats['total_vulnerabilities'] += len(vulnerabilities)
                                    for vuln in vulnerabilities:
                                        self.stats['vulnerabilities_by_severity'][vuln['severity']] += 1
                                
                                runs_processed += 1
                                
                                # Save after every run to ensure progress is never lost
                                self._save_results_incremental(all_results, runs_processed)
                                
                                # Progress messages
                                if runs_processed % 10 == 0:
                                    print(f"  Processed {runs_processed} runs... (saved, {len(all_results)} vulnerabilities)")
                                elif runs_processed % 5 == 0:
                                    print(f"  Processed {runs_processed} runs... ({len(all_results)} vulnerabilities)")
                    
                    # Save after each domain
                    if all_results:
                        self._save_results_incremental(all_results, runs_processed)
                        print(f"\n✓ Domain {domain} complete. Progress saved ({len(all_results)} total results).\n")
            
            # If we processed root level, we're done
            if not is_model_level:
                # Save raw results CSV
                if all_results:
                    csv_path = self.output_dir / 'vuln_results.csv'
                    fieldnames = ['task_id', 'domain', 'language', 'prompt_type', 'run_number', 
                                 'model', 'scanner', 'rule_id', 'severity', 'cwe', 'cvss_score', 
                                 'file_path', 'line_number', 'end_line', 'message']
                    
                    with open(csv_path, 'w', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(all_results)
                    
                    print(f"\n✓ Raw results saved: {csv_path}")
                    print(f"  Total vulnerabilities found: {len(all_results)}")
                
                return True
        
        # Walk through collected code directory structure at model level
        # Structure: collected_code/model/domain/task_id/language_prompttype/run_N/code/
        # Domain order is already set in domain_dirs
        for domain_dir in domain_dirs:
            if not domain_dir.is_dir():
                continue
            
            domain = domain_dir.name
            print(f"\n{'='*60}")
            print(f"Processing domain: {domain}")
            print(f"{'='*60}\n")
            
            for task_dir in sorted(domain_dir.iterdir(), key=lambda x: x.name):
                if not task_dir.is_dir():
                    continue
                
                task_id = task_dir.name
                
                for prompt_dir in sorted(task_dir.iterdir(), key=lambda x: x.name):
                    if not prompt_dir.is_dir():
                        continue
                    
                    # Parse language and prompt_type from directory name
                    # Format: language_prompttype (e.g., python_naive)
                    dir_parts = prompt_dir.name.split('_', 1)
                    if len(dir_parts) != 2:
                        continue
                    
                    language = dir_parts[0]
                    prompt_type = dir_parts[1]
                    
                    # Process each run
                    for run_dir in sorted(prompt_dir.iterdir(), key=lambda x: x.name):
                        if not run_dir.is_dir() or not run_dir.name.startswith('run_'):
                            continue
                        
                        try:
                            run_number = int(run_dir.name.split('_')[1])
                        except (ValueError, IndexError):
                            continue
                        
                        code_dir = run_dir / 'code'
                        
                        if not code_dir.exists():
                            continue
                        
                        # Check if already scanned (resume functionality)
                        results_file = self._get_run_results_path(run_dir)
                        if self.skip_existing and results_file.exists():
                            try:
                                with open(results_file, 'r') as f:
                                    existing_data = json.load(f)
                                    vulnerabilities = existing_data.get('vulnerabilities', [])
                                    # Add to results
                                    for vuln in vulnerabilities:
                                        all_results.append({
                                            'task_id': task_id,
                                            'domain': domain,
                                            'language': language,
                                            'prompt_type': prompt_type,
                                            'run_number': run_number,
                                            'model': model_name,
                                            **vuln
                                        })
                                    runs_processed += 1
                                    if runs_processed % 10 == 0:
                                        print(f"  Processed {runs_processed} runs... (skipped existing)")
                                    continue
                            except (json.JSONDecodeError, KeyError):
                                pass  # Re-scan if file is corrupted
                        
                        print(f"Scanning: {task_id}/{language}/{prompt_type}/run_{run_number}")
                        
                        # Run appropriate scanners
                        vulnerabilities = self.scan_code_directory(code_dir, language, scanners_available)
                        
                        # Save per-run results
                        results_file = self._get_run_results_path(run_dir, ensure_parent=True)
                        with open(results_file, 'w') as f:
                            json.dump({
                                'timestamp': datetime.now().isoformat(),
                                'language': language,
                                'vulnerabilities': vulnerabilities,
                                'vulnerability_count': len(vulnerabilities)
                            }, f, indent=2)
                        
                        # Add to master results
                        for vuln in vulnerabilities:
                            all_results.append({
                                'task_id': task_id,
                                'domain': domain,
                                'language': language,
                                'prompt_type': prompt_type,
                                'run_number': run_number,
                                'model': model_name,
                                **vuln
                            })
                        
                        # Update statistics
                        self.stats['total_runs_scanned'] += 1
                        if len(vulnerabilities) > 0:
                            self.stats['runs_with_vulnerabilities'] += 1
                            self.stats['total_vulnerabilities'] += len(vulnerabilities)
                            for vuln in vulnerabilities:
                                self.stats['vulnerabilities_by_severity'][vuln['severity']] += 1
                        
                        runs_processed += 1
                        
                        # Save after every run to ensure progress is never lost
                        self._save_results_incremental(all_results, runs_processed)
                        
                        # Progress messages
                        if runs_processed % 10 == 0:
                            print(f"  Processed {runs_processed} runs... (saved, {len(all_results)} vulnerabilities)")
                        elif runs_processed % 5 == 0:
                            print(f"  Processed {runs_processed} runs... ({len(all_results)} vulnerabilities)")
            
            # Save after each domain
            if all_results:
                self._save_results_incremental(all_results, runs_processed)
                print(f"\n✓ Domain {domain} complete. Progress saved ({len(all_results)} total results).\n")
        
        # Final save (redundant but ensures everything is saved)
        if all_results:
            self._save_results_incremental(all_results, runs_processed)
            csv_path = self.output_dir / 'vuln_results.csv'
            print(f"\n✓ Final results saved: {csv_path}")
            print(f"  Total vulnerabilities found: {len(all_results)}")
        
        return True
    
    def _save_results_incremental(self, all_results, run_count=None):
        """Save results incrementally to CSV - overwrites with all current results"""
        csv_path = self.output_dir / 'vuln_results.csv'
        fieldnames = ['task_id', 'domain', 'language', 'prompt_type', 'run_number', 
                     'model', 'scanner', 'rule_id', 'severity', 'cwe', 'cvss_score', 
                     'file_path', 'line_number', 'end_line', 'message']
        
        try:
            # Always overwrite with all current results (simpler and ensures consistency)
            # Even if empty, create the file so we know the script is running
            temp_path = csv_path.with_suffix('.tmp')
            with open(temp_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                if all_results:
                    writer.writerows(all_results)
                # Force flush to disk
                f.flush()
                os.fsync(f.fileno())
            
            # Atomic rename to avoid partial writes
            temp_path.replace(csv_path)
            
        except Exception as e:
            print(f"  ⚠ Warning: Failed to save results to {csv_path}: {e}")
            import traceback
            traceback.print_exc()
    
    def aggregate_vulnerabilities(self):
        """Aggregate vulnerabilities across runs using union approach"""
        print(f"\n{'='*70}")
        print(f"AGGREGATING VULNERABILITIES")
        print(f"{'='*70}\n")
        
        csv_path = self.output_dir / 'vuln_results.csv'
        if not csv_path.exists():
            print(f"✗ Error: {csv_path} not found. Run analysis first.")
            return False
        
        # Load raw results
        all_vulnerabilities = []
        if csv_path.exists():
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                all_vulnerabilities = list(reader)
        
        # Find all scanned prompts by looking at results.json files
        # This ensures we include prompts with 0 vulnerabilities
        print("Finding all scanned runs...")
        scanned_prompts = set()
        run_counts = defaultdict(int)  # Pre-compute run counts to avoid repeated rglob calls
        
        results_files = list(self.run_results_root.rglob('results.json'))
        print(f"  Found {len(results_files)} result files")
        
        for idx, results_file in enumerate(results_files):
            if idx % 100 == 0 and idx > 0:
                print(f"  Processing {idx}/{len(results_files)} files...")
            try:
                # Extract task info from path
                # Path format mirrors collected_code: .../domain/task_id/language_prompttype/run_N/results.json
                parts = results_file.parts
                # Find domain, task_id, and language_prompttype from path
                for i, part in enumerate(parts):
                    if part in ['aiml_ds', 'web_api', 'auth_crypto', 'file_system']:
                        domain = part
                        if i + 1 < len(parts):
                            task_id = parts[i + 1]
                            if i + 2 < len(parts):
                                lang_prompt = parts[i + 2]
                                if '_' in lang_prompt:
                                    lang, prompt_type = lang_prompt.split('_', 1)
                                    key = (task_id, domain, lang, prompt_type)
                                    scanned_prompts.add(key)
                                    run_counts[key] += 1
                                    break
            except (KeyError, IndexError):
                continue
        
        print(f"  Found {len(scanned_prompts)} unique prompts")
        
        # Group vulnerabilities by prompt (task_id + language + prompt_type)
        prompt_groups = defaultdict(list)
        for vuln in all_vulnerabilities:
            key = (vuln['task_id'], vuln['domain'], vuln['language'], vuln['prompt_type'])
            prompt_groups[key].append(vuln)
        
        aggregated_results = []
        
        # Process all scanned prompts (including those with 0 vulnerabilities)
        print(f"\nAggregating results for {len(scanned_prompts)} prompts...")
        for idx, (task_id, domain, language, prompt_type) in enumerate(sorted(scanned_prompts)):
            if idx % 50 == 0 and idx > 0:
                print(f"  Processed {idx}/{len(scanned_prompts)} prompts...")
            key = (task_id, domain, language, prompt_type)
            vulns = prompt_groups.get(key, [])
            # Create unique identifier for each vulnerability
            # Use rule_id + file_path + line_number to identify unique vulnerabilities
            unique_vulns = {}
            for vuln in vulns:
                unique_key = (
                    vuln['rule_id'],
                    vuln['file_path'],
                    vuln['line_number']
                )
                if unique_key not in unique_vulns:
                    unique_vulns[unique_key] = vuln
            
            # Count vulnerabilities by severity
            severity_counts = defaultdict(int)
            cwe_counts = defaultdict(int)
            rule_counts = defaultdict(int)
            
            for vuln in unique_vulns.values():
                severity = vuln['severity']
                severity_counts[severity] += 1
                rule_counts[vuln['rule_id']] += 1
                if vuln.get('cwe'):
                    cwe_counts[vuln['cwe']] += 1
            
            # Calculate weighted score
            weighted_score = (
                severity_counts.get('ERROR', 0) * self.severity_weights['ERROR'] +
                severity_counts.get('WARNING', 0) * self.severity_weights['WARNING'] +
                severity_counts.get('INFO', 0) * self.severity_weights['INFO']
            )

            # Calculate CVSS metrics
            cvss_scores = []
            for vuln in unique_vulns.values():
                score = vuln.get('cvss_score')
                if score is not None:
                    try:
                        cvss_scores.append(float(score))
                    except (ValueError, TypeError):
                        pass
            
            total_cvss = sum(cvss_scores)
            max_cvss = max(cvss_scores) if cvss_scores else 0.0
            avg_cvss = total_cvss / len(cvss_scores) if cvss_scores else 0.0
            
            # Count runs analyzed (pre-computed)
            runs_analyzed = run_counts.get((task_id, domain, language, prompt_type), 0)
            
            aggregated_results.append({
                'task_id': task_id,
                'domain': domain,
                'language': language,
                'prompt_type': prompt_type,
                'total_vulnerabilities': len(unique_vulns),
                'error_count': severity_counts.get('ERROR', 0),
                'warning_count': severity_counts.get('WARNING', 0),
                'info_count': severity_counts.get('INFO', 0),
                'weighted_score': weighted_score,
                'total_cvss_score': round(total_cvss, 2),
                'max_cvss_score': round(max_cvss, 2),
                'avg_cvss_score': round(avg_cvss, 2),
                'unique_rules': len(rule_counts),
                'cwe_count': len(cwe_counts),
                'runs_analyzed': runs_analyzed if runs_analyzed > 0 else 1
            })
        
        # Save aggregated results
        agg_path = self.output_dir / 'aggregated_results.csv'
        fieldnames = ['task_id', 'domain', 'language', 'prompt_type', 
                      'total_vulnerabilities', 'error_count', 'warning_count', 
                      'info_count', 'weighted_score', 'total_cvss_score', 
                      'max_cvss_score', 'avg_cvss_score', 'unique_rules', 
                      'cwe_count', 'runs_analyzed']
        
        with open(agg_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(aggregated_results)
        
        print(f"✓ Aggregated results saved: {agg_path}")
        print(f"  Total prompts analyzed: {len(aggregated_results)}")
        
        return True
    
    def calculate_security_scores(self):
        """Calculate normalized security scores (0-1 scale)"""
        print(f"\n{'='*70}")
        print(f"CALCULATING SECURITY SCORES")
        print(f"{'='*70}\n")
        
        agg_path = self.output_dir / 'aggregated_results.csv'
        if not agg_path.exists():
            print(f"✗ Error: {agg_path} not found. Run aggregation first.")
            return False
        
        # Load aggregated results
        with open(agg_path, 'r') as f:
            reader = csv.DictReader(f)
            aggregated = list(reader)
        
        if not aggregated:
            print("No aggregated results to score.")
            return True
        
        # Find maximum Total CVSS score for normalization
        max_total_cvss = max((float(row.get('total_cvss_score', 0)) for row in aggregated), default=0)
        
        # Use a reasonable upper bound for normalization
        # NVD max is 10 per vuln. If we have many vulns, it grows.
        if max_total_cvss > 50:
            # Use 95th percentile as normalization factor
            scores = sorted([float(row.get('total_cvss_score', 0)) for row in aggregated])
            normalization_factor = scores[int(len(scores) * 0.95)]
        else:
            normalization_factor = max(max_total_cvss, 10.0)  # Minimum of 10
        
        print(f"Normalization factor (CVSS): {normalization_factor}")
        print(f"Max total CVSS scores: {max_total_cvss}")
        
        # Calculate security scores
        security_scores = []
        for row in aggregated:
            total_cvss = float(row.get('total_cvss_score', 0))
            
            # Security score: 1 - (normalized total CVSS), clamped to [0, 1]
            # Higher score = more secure (fewer/less severe vulnerabilities)
            if normalization_factor > 0:
                normalized_score = min(total_cvss / normalization_factor, 1.0)
            else:
                normalized_score = 0.0
                
            security_score = 1.0 - normalized_score

            
            security_scores.append({
                'task_id': row['task_id'],
                'domain': row['domain'],
                'language': row['language'],
                'prompt_type': row['prompt_type'],
                'total_vulnerabilities': row['total_vulnerabilities'],
                'error_count': row['error_count'],
                'warning_count': row['warning_count'],
                'info_count': row['info_count'],
                'weighted_score': row['weighted_score'],
                'total_cvss_score': total_cvss,
                'max_cvss_score': float(row.get('max_cvss_score', 0)),
                'avg_cvss_score': float(row.get('avg_cvss_score', 0)),
                'security_score': round(security_score, 4),
                'unique_rules': row['unique_rules'],
                'cwe_count': row['cwe_count'],
                'runs_analyzed': row['runs_analyzed']
            })
        
        # Save security scores
        scores_path = self.output_dir / 'security_scores.csv'
        fieldnames = ['task_id', 'domain', 'language', 'prompt_type',
                     'total_vulnerabilities', 'error_count', 'warning_count',
                     'info_count', 'weighted_score', 'total_cvss_score', 
                     'max_cvss_score', 'avg_cvss_score', 'security_score',
                     'unique_rules', 'cwe_count', 'runs_analyzed']
        
        with open(scores_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(security_scores)
        
        print(f"✓ Security scores saved: {scores_path}")
        print(f"  Security score range: {min(s['security_score'] for s in security_scores):.4f} - {max(s['security_score'] for s in security_scores):.4f}")
        
        return True
    
    def print_summary(self):
        """Print analysis summary"""
        print(f"\n{'='*70}")
        print(f"ANALYSIS SUMMARY")
        print(f"{'='*70}\n")
        
        print(f"Statistics:")
        print(f"  Total runs scanned: {self.stats['total_runs_scanned']}")
        print(f"  Runs with vulnerabilities: {self.stats['runs_with_vulnerabilities']}")
        print(f"  Total vulnerabilities found: {self.stats['total_vulnerabilities']}")
        print(f"\nVulnerabilities by severity:")
        for severity, count in sorted(self.stats['vulnerabilities_by_severity'].items()):
            print(f"  {severity}: {count}")
        
        print(f"\nOutput directory: {self.output_dir}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description='Analyze vulnerabilities in collected code using Bandit, cppcheck, and ESLint',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze all collected code
  python3 analyze_vulnerabilities.py --collected-code ../collected_code/auto
  
  # Specify output directory
  python3 analyze_vulnerabilities.py --collected-code ../collected_code/auto --output analysis
  
  # Dry run (test without running scanners)
  python3 analyze_vulnerabilities.py --collected-code ../collected_code/auto --dry-run
        """
    )
    
    parser.add_argument('--collected-code',
                        default='../collected_code/auto',
                        help='Directory containing collected code (default: ../collected_code/auto)')
    
    parser.add_argument('--output',
                        default='analysis',
                        help='Output directory for analysis results (default: analysis)')
    
    parser.add_argument('--dry-run',
                        action='store_true',
                        help='Test without actually running Semgrep')
    
    parser.add_argument('--skip-existing',
                        action='store_true',
                        help='Skip runs that already have results.json (resume mode)')
    
    args = parser.parse_args()
    
    # Resolve paths relative to script location
    script_dir = Path(__file__).parent
    collected_path = (script_dir / args.collected_code).resolve()
    output_path = (script_dir / args.output).resolve()
    
    analyzer = VulnerabilityAnalyzer(
        collected_code_dir=collected_path,
        output_dir=output_path,
        dry_run=args.dry_run,
        skip_existing=args.skip_existing
    )
    
    # Run analysis pipeline
    success = True
    success = success and analyzer.analyze_all_runs()
    success = success and analyzer.aggregate_vulnerabilities()
    success = success and analyzer.calculate_security_scores()
    
    analyzer.print_summary()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

