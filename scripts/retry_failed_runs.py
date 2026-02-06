#!/usr/bin/env python3
"""
Retry specific failed runs by re-collecting them.
"""

import json
import csv
import sys
from pathlib import Path
import subprocess
import time
from datetime import datetime

# Import the CodeCollector class
sys.path.insert(0, str(Path(__file__).parent))
from collect_code import CodeCollector

def retry_failed_runs(failed_runs_file='failed_runs.json', model='auto'):
    """Retry failed runs from the failed_runs.json file"""
    
    # Load failed runs
    with open(failed_runs_file, 'r') as f:
        failed_runs = json.load(f)
    
    print(f"\n{'='*70}")
    print(f"RETRYING {len(failed_runs)} FAILED RUNS")
    print(f"{'='*70}\n")
    
    # Load prompts CSV
    prompts_file = Path('prompts/prompts.csv')
    if not prompts_file.exists():
        prompts_file = Path('generated/prompts_index.csv')
    
    if not prompts_file.exists():
        print(f"✗ Error: Could not find prompts CSV file")
        return False
    
    # Load all prompts
    prompts_dict = {}
    with open(prompts_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row['task_id'], row['language'], row['prompt_type'])
            prompts_dict[key] = row
    
    # Create collector instance
    collector = CodeCollector(
        prompts_csv=prompts_file,
        output_dir=Path('collected_code'),
        model=model,
        runs_per_prompt=1,
        dry_run=False
    )
    
    # Retry each failed run
    for i, failed_run in enumerate(failed_runs, 1):
        task_id = failed_run['task_id']
        language = failed_run['language']
        prompt_type = failed_run['prompt_type']
        run_number = failed_run['run_number']
        domain = failed_run['domain']
        
        print(f"\n[{i}/{len(failed_runs)}] Retrying: {task_id} - {language} - {prompt_type} (Run {run_number})")
        
        # Get prompt text
        key = (task_id, language, prompt_type)
        if key not in prompts_dict:
            print(f"  ✗ Error: Prompt not found in CSV")
            continue
        
        prompt_row = prompts_dict[key]
        prompt_text = prompt_row['prompt_text']
        complexity = prompt_row.get('complexity_level', '')
        risk_tags = prompt_row.get('risk_tags', '')
        
        # Re-collect
        collector.collect_one_run(
            task_id, domain, language, prompt_type,
            prompt_text, complexity, risk_tags, run_number
        )
    
    # Save metadata
    collector.save_master_csv()
    
    print(f"\n{'='*70}")
    print(f"✓ Retry complete for {len(failed_runs)} failed runs")
    print(f"{'='*70}\n")
    
    return True

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Retry failed code collection runs')
    parser.add_argument('--failed-runs', 
                        default='failed_runs.json',
                        help='JSON file with failed runs (default: failed_runs.json)')
    parser.add_argument('--model',
                        default='auto',
                        help='Model to use (default: auto)')
    
    args = parser.parse_args()
    
    success = retry_failed_runs(args.failed_runs, args.model)
    sys.exit(0 if success else 1)

