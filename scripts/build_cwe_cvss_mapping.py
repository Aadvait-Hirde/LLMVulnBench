
import csv
import json
import time
import sys
import os
import urllib.request
import urllib.error
import statistics
from pathlib import Path

# Add the script directory to path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from scanner_cwe_mappings import get_cwe_from_rule

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
INPUT_CSV = PROJECT_ROOT / 'analysis' / 'vuln_results.csv'
OUTPUT_JSON = PROJECT_ROOT / 'data' / 'cwe_cvss_mapping.json'
NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
SLEEP_TIME = 6.0  # NVD rate limit for no-key is 5 request / 30 secs -> 1 req / 6 secs.

def get_mean_cvss_for_cwe(cwe_id):
    """
    Fetches CVEs for a given CWE from NVD and calculates the median CVSS V3.1 Base Score.
    """
    print(f"Fetching data for {cwe_id}...")
    
    # NVD API expects "CWE-123" not just "123"
    # But usually checks matching. 
    # cweId param takes the full string e.g. "CWE-79"
    
    params = f"?cweId={cwe_id}&resultsPerPage=20" # Get 20 recent CVEs
    url = f"{NVD_API_URL}{params}"
    
    headers = {
        'User-Agent': 'LLMVulnBench_Analysis_Script/1.0'
    }
    
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        scores = []
        vulnerabilities = data.get('vulnerabilities', [])
        
        for item in vulnerabilities:
            cve = item.get('cve', {})
            metrics = cve.get('metrics', {})
            
            # Try V3.1, then V3.0
            cvss_data = None
            if 'cvssMetricV31' in metrics:
                cvss_data = metrics['cvssMetricV31'][0].get('cvssData', {})
            elif 'cvssMetricV30' in metrics:
                cvss_data = metrics['cvssMetricV30'][0].get('cvssData', {})
            
            if cvss_data and 'baseScore' in cvss_data:
                scores.append(float(cvss_data['baseScore']))
                
        if not scores:
            print(f"  No CVSS V3 scores found for recent CVEs of {cwe_id}")
            return None
            
        median_score = statistics.median(scores)
        print(f"  Found {len(scores)} scores. Median: {median_score}")
        return median_score
        
    except urllib.error.HTTPError as e:
        print(f"  HTTP Error {e.code}: {e.reason}")
        return None
    except Exception as e:
        print(f"  Error: {str(e)}")
        return None

def main():
    if not INPUT_CSV.exists():
        print(f"Error: {INPUT_CSV} not found.")
        return

    # Create data dir if not exists
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)

    # 1. Collect all unique CWEs
    print("Collecting CWEs from analysis results...")
    unique_cwes = set()
    
    with open(INPUT_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            scanner = row.get('scanner')
            rule_id = row.get('rule_id')
            raw_cwe = row.get('cwe')
            
            cwe = get_cwe_from_rule(scanner, rule_id, raw_cwe)
            if cwe:
                unique_cwes.add(cwe)
    
    print(f"Found {len(unique_cwes)} unique CWEs: {', '.join(sorted(unique_cwes))}")

    # 2. Load existing mapping if exists to avoid re-fetching
    mapping = {}
    if OUTPUT_JSON.exists():
        try:
            with open(OUTPUT_JSON, 'r') as f:
                mapping = json.load(f)
            print(f"Loaded existing mapping with {len(mapping)} entries.")
        except json.JSONDecodeError:
            print("Existing mapping file is corrupt, starting fresh.")

    # 3. Fetch missing CWEs
    cwes_to_fetch = [c for c in unique_cwes if c not in mapping]
    
    if not cwes_to_fetch:
        print("All CWEs already mapped.")
    else:
        print(f"Need to fetch scores for {len(cwes_to_fetch)} CWEs.")
        
        for i, cwe in enumerate(cwes_to_fetch):
            print(f"[{i+1}/{len(cwes_to_fetch)}] Processing {cwe}...")
            
            score = get_mean_cvss_for_cwe(cwe)
            
            if score is not None:
                mapping[cwe] = score
            else:
                # Default fallback or manual intervention might be needed later
                # For now, store None? Or skip?
                # Let's map to null so we know we tried.
                mapping[cwe] = None
                
            # Rate limiting
            time.sleep(SLEEP_TIME)
            
            # Save intermediate progress
            with open(OUTPUT_JSON, 'w') as f:
                json.dump(mapping, f, indent=2)

    print(f"Mapping complete. Saved to {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
