
import json
import sys
import os
from pathlib import Path

# Add script dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from scanner_cwe_mappings import get_cwe_from_rule

def migrate_run(json_path, cwe_cvss_map):
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        modified = False
        for vuln in data.get('vulnerabilities', []):
            # Update CWE
            scanner = vuln.get('scanner')
            rule_id = vuln.get('rule_id')
            orig_cwe = vuln.get('cwe')
            
            new_cwe = get_cwe_from_rule(scanner, rule_id, orig_cwe)
            
            # Update CVSS
            cvss = cwe_cvss_map.get(new_cwe) if new_cwe else None
            
            # Check if update needed (handle missing keys or different values)
            if vuln.get('cwe') != new_cwe or vuln.get('cvss_score') != cvss:
                vuln['cwe'] = new_cwe
                vuln['cvss_score'] = cvss
                modified = True
                
        if modified:
            with open(json_path, 'w') as f:
                json.dump(data, f, indent=2)
        return modified
    except Exception as e:
        print(f"Error migrating {json_path}: {e}")
        return False

def main():
    # Assume script is run from project root or scripts/
    # We try to align with standard layout
    project_root = Path(__file__).resolve().parent.parent
    
    analysis_dir = project_root / 'analysis'
    vuln_runs_dir = analysis_dir / 'vuln_runs'
    map_path = project_root / 'data' / 'cwe_cvss_mapping.json'
    
    if not vuln_runs_dir.exists():
        print(f"No existing runs found at {vuln_runs_dir}. Nothing to migrate.")
        return

    if not map_path.exists():
        print(f"Mapping file not found at {map_path}")
        return

    print("Loading CWE-CVSS mapping...")
    with open(map_path, 'r') as f:
        cwe_map = json.load(f)

    print(f"Scanning for results.json in {vuln_runs_dir}...")
    files = list(vuln_runs_dir.rglob('results.json'))
    total_files = len(files)
    print(f"Found {total_files} runs.")

    mod_count = 0
    for i, f_path in enumerate(files):
        if migrate_run(f_path, cwe_map):
            mod_count += 1
        
        if (i+1) % 100 == 0:
            print(f"Processed {i+1}/{total_files} files...")

    print(f"Migration complete. Updated {mod_count} files.")

if __name__ == "__main__":
    main()
