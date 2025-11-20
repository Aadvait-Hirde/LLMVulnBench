#!/usr/bin/env python3
"""
collect_code.py - Run prompts through Cursor CLI and collect generated code

This script automates code collection for the LLMVulnBench project by:
1. Reading prompts from the generated CSV
2. Running each prompt through cursor-agent CLI
3. Collecting generated code files
4. Tracking metadata for analysis

Usage:
    # Collect code for one model (default: 1 run per prompt)
    python3 collect_code.py --model gpt-5
    
    # Process in batches (10 prompts per batch)
    python3 collect_code.py --model gpt-5 --batch-size 10
    
    # Test with dry run
    python3 collect_code.py --dry-run
    
    # Collect for specific domain only
    python3 collect_code.py --model claude-sonnet-4 --domain web_api
    
    # Resume from specific task
    python3 collect_code.py --model gpt-5 --resume-from WEB_025
"""

import csv
import json
import subprocess
import os
import sys
import shutil
from pathlib import Path
from datetime import datetime
import time
import argparse


class CodeCollector:
    def __init__(self, prompts_csv, output_dir, model, runs_per_prompt=1, 
                 domain_filter=None, resume_from=None, dry_run=False, batch_size=None, limit=None):
        self.prompts_csv = Path(prompts_csv)
        self.output_dir = Path(output_dir)
        self.model = model
        self.runs_per_prompt = runs_per_prompt
        self.domain_filter = domain_filter
        self.resume_from = resume_from
        self.dry_run = dry_run
        self.batch_size = batch_size  # Number of prompts to process per batch
        self.limit = limit  # Limit total number of prompts to process (for testing)
        self.metadata_rows = []
        
        # Statistics
        self.stats = {
            'total_runs': 0,
            'successful_runs': 0,
            'failed_runs': 0,
            'files_created': 0,
            'total_duration': 0
        }
        
    def check_cursor_cli(self):
        """Verify cursor-agent CLI is available"""
        try:
            result = subprocess.run(
                ['cursor-agent', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print(f"✓ Cursor CLI found: {result.stdout.strip()}")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        print("✗ Error: cursor-agent CLI not found")
        print("\nPlease install Cursor CLI:")
        print("  curl https://cursor.com/install -fsS | bash")
        return False
    
    def run_cursor_agent(self, prompt, working_dir):
        """Run cursor-agent CLI and capture output"""
        
        if self.dry_run:
            return {
                "stdout": '{"type":"result","result":"DRY RUN - No actual execution"}',
                "stderr": "",
                "returncode": 0,
                "success": True
            }
        
        cmd = [
            "cursor-agent",
            "-p",  # Print mode (non-interactive)
            "--force",  # Allow file writes without confirmation
            "--output-format", "stream-json",  # Structured output
            "--model", self.model,
            prompt
        ]
        
        try:
            # Run in the working directory where code should be generated
            result = subprocess.run(
                cmd,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0
            }
        
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": "Timeout after 5 minutes",
                "returncode": -1,
                "success": False
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": str(e),
                "returncode": -1,
                "success": False
            }
    
    def parse_stream_json(self, output):
        """Parse NDJSON output from cursor-agent"""
        events = []
        for line in output.strip().split('\n'):
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return events
    
    def extract_generated_files(self, events, code_dir):
        """Extract list of files created by the agent"""
        created_files = []
        
        for event in events:
            if event.get('type') == 'tool_call' and \
               event.get('subtype') == 'completed':
                
                tool_call = event.get('tool_call', {})
                write_call = tool_call.get('writeToolCall', {})
                result = write_call.get('result', {})
                
                if 'success' in result:
                    path = result['success'].get('path')
                    if path:
                        # Make path relative to code_dir
                        try:
                            rel_path = Path(path).relative_to(code_dir)
                            created_files.append(str(rel_path))
                        except ValueError:
                            # If path is not relative to code_dir, just use basename
                            created_files.append(Path(path).name)
        
        return created_files
    
    def get_final_result(self, events):
        """Extract final result message from events"""
        for event in reversed(events):
            if event.get('type') == 'result':
                return event.get('result', '')
        return ""
    
    def is_already_collected(self, task_id, domain, language, prompt_type, run_number):
        """Check if this run has already been successfully collected"""
        run_dir = self.output_dir / self.model / domain / task_id / \
                  f"{language}_{prompt_type}" / f"run_{run_number}"
        metadata_file = run_dir / "metadata.json"
        
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    # If metadata exists and indicates success, skip
                    if metadata.get('success', False):
                        return True
            except (json.JSONDecodeError, KeyError):
                # If metadata is corrupted, re-run
                pass
        
        return False
    
    def collect_one_run(self, task_id, domain, language, prompt_type, 
                        prompt_text, complexity, risk_tags, run_number):
        """Collect code for one run of one prompt"""
        
        # Create directory structure
        run_dir = self.output_dir / self.model / domain / task_id / \
                  f"{language}_{prompt_type}" / f"run_{run_number}"
        
        run_dir.mkdir(parents=True, exist_ok=True)
        code_dir = run_dir / "code"
        code_dir.mkdir(exist_ok=True)
        
        # Check if already collected
        if self.is_already_collected(task_id, domain, language, prompt_type, run_number):
            print(f"  Run {run_number}: {task_id}/{language}/{prompt_type}... SKIPPED (already collected)", flush=True)
            # Load existing metadata to include in stats
            metadata_file = run_dir / "metadata.json"
            try:
                with open(metadata_file, 'r') as f:
                    existing_metadata = json.load(f)
                    self.metadata_rows.append({
                        **existing_metadata,
                        "run_dir": str(run_dir.relative_to(self.output_dir))
                    })
                    self.stats['total_runs'] += 1
                    self.stats['successful_runs'] += 1
                    if existing_metadata.get('files_created'):
                        self.stats['files_created'] += len(existing_metadata['files_created'])
            except:
                pass
            return True
        
        print(f"  Run {run_number}: {task_id}/{language}/{prompt_type}...", end='', flush=True)
        
        # Run cursor-agent
        start_time = time.time()
        result = self.run_cursor_agent(prompt_text, code_dir)
        duration = time.time() - start_time
        
        # Parse output
        events = []
        created_files = []
        final_result = ""
        
        if result['success']:
            events = self.parse_stream_json(result['stdout'])
            created_files = self.extract_generated_files(events, code_dir)
            final_result = self.get_final_result(events)
        
        # Save full output
        output_file = run_dir / "output.json"
        with open(output_file, 'w') as f:
            json.dump(events, f, indent=2)
        
        # Save stderr if present
        if result['stderr']:
            stderr_file = run_dir / "stderr.txt"
            with open(stderr_file, 'w') as f:
                f.write(result['stderr'])
        
        # Save metadata
        metadata = {
            "task_id": task_id,
            "domain": domain,
            "language": language,
            "prompt_type": prompt_type,
            "complexity_level": complexity,
            "risk_tags": risk_tags,
            "model": self.model,
            "run_number": run_number,
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": round(duration, 2),
            "success": result['success'],
            "files_created": created_files,
            "file_count": len(created_files),
            "return_code": result['returncode'],
            "final_result": final_result,
            "has_stderr": bool(result['stderr'])
        }
        
        metadata_file = run_dir / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Track for master CSV
        self.metadata_rows.append({
            **metadata,
            "run_dir": str(run_dir.relative_to(self.output_dir))
        })
        
        # Update statistics
        self.stats['total_runs'] += 1
        if result['success']:
            self.stats['successful_runs'] += 1
        else:
            self.stats['failed_runs'] += 1
        self.stats['files_created'] += len(created_files)
        self.stats['total_duration'] += duration
        
        # Print result
        if result['success']:
            print(f" ✓ ({len(created_files)} files, {duration:.1f}s)")
        else:
            print(f" ✗ FAILED ({duration:.1f}s)")
        
        return result['success']
    
    def should_skip_prompt(self, task_id):
        """Check if we should skip this prompt (for resume functionality)"""
        if not self.resume_from:
            return False
        
        # Extract numeric part of task_id for comparison
        try:
            current_num = int(task_id.split('_')[1])
            resume_num = int(self.resume_from.split('_')[1])
            return current_num < resume_num
        except (IndexError, ValueError):
            return False
    
    def collect_all(self):
        """Main collection loop"""
        
        if not self.dry_run and not self.check_cursor_cli():
            return False
        
        print(f"\n{'='*70}")
        print(f"CODE COLLECTION - {self.model.upper()}")
        print(f"{'='*70}\n")
        
        # Load prompts
        print(f"Loading prompts from {self.prompts_csv}...")
        
        if not self.prompts_csv.exists():
            print(f"✗ Error: {self.prompts_csv} not found")
            return False
        
        with open(self.prompts_csv, 'r') as f:
            reader = csv.DictReader(f)
            all_prompts = list(reader)
        
        # Filter by domain if specified
        if self.domain_filter:
            prompts = [p for p in all_prompts 
                      if p['domain'].replace('/', '_') == self.domain_filter]
            print(f"  Filtered to domain: {self.domain_filter}")
        else:
            prompts = all_prompts
        
        # Filter for resume
        if self.resume_from:
            original_count = len(prompts)
            prompts = [p for p in prompts if not self.should_skip_prompt(p['task_id'])]
            skipped = original_count - len(prompts)
            if skipped > 0:
                print(f"  Skipped {skipped} prompts (resuming from {self.resume_from})")
        
        # Limit number of prompts for testing
        if self.limit and self.limit > 0:
            original_count = len(prompts)
            prompts = prompts[:self.limit]
            if len(prompts) < original_count:
                print(f"  Limited to first {self.limit} prompts (for testing)")
        
        total_runs = len(prompts) * self.runs_per_prompt
        
        # Check how many prompts are already collected
        already_collected = 0
        for prompt_row in prompts:
            task_id = prompt_row['task_id']
            domain = prompt_row['domain'].replace('/', '_')
            language = prompt_row['language']
            prompt_type = prompt_row['prompt_type']
            if self.is_already_collected(task_id, domain, language, prompt_type, 1):
                already_collected += 1
        
        remaining = len(prompts) - already_collected
        
        print(f"\nCollection plan:")
        print(f"  Total prompts: {len(prompts)}")
        print(f"  Already collected: {already_collected}")
        print(f"  Remaining: {remaining}")
        print(f"  Runs per prompt: {self.runs_per_prompt}")
        print(f"  Model: {self.model}")
        print(f"  Total runs: {total_runs}")
        print(f"  Output: {self.output_dir}")
        if self.batch_size:
            total_batches = (remaining + self.batch_size - 1) // self.batch_size if remaining > 0 else 0
            print(f"  Batch processing: {self.batch_size} prompts per batch ({total_batches} batches)")
        if self.dry_run:
            print(f"  Mode: DRY RUN (no actual execution)")
        print()
        
        # Process prompts
        start_time = time.time()
        
        if self.batch_size:
            # Process in batches
            total_batches = (len(prompts) + self.batch_size - 1) // self.batch_size
            
            for batch_num in range(total_batches):
                batch_start = batch_num * self.batch_size
                batch_end = min(batch_start + self.batch_size, len(prompts))
                batch_prompts = prompts[batch_start:batch_end]
                
                print(f"\n{'='*70}")
                print(f"BATCH {batch_num + 1}/{total_batches} (Prompts {batch_start + 1}-{batch_end} of {len(prompts)})")
                print(f"{'='*70}\n")
                
                # Process batch
                for i, prompt_row in enumerate(batch_prompts, batch_start + 1):
                    task_id = prompt_row['task_id']
                    domain = prompt_row['domain'].replace('/', '_')
                    language = prompt_row['language']
                    prompt_type = prompt_row['prompt_type']
                    prompt_text = prompt_row['prompt_text']
                    complexity = prompt_row.get('complexity_level', '')
                    risk_tags = prompt_row.get('risk_tags', '')
                    
                    print(f"\n[{i}/{len(prompts)}] {task_id} - {language} - {prompt_type}")
                    
                    for run in range(1, self.runs_per_prompt + 1):
                        self.collect_one_run(
                            task_id, domain, language, prompt_type,
                            prompt_text, complexity, risk_tags, run
                        )
                
                # Save progress after each batch
                self.save_master_csv()
                print(f"\n✓ Batch {batch_num + 1} complete. Progress saved.")
        else:
            # Process all prompts at once
            for i, prompt_row in enumerate(prompts, 1):
                task_id = prompt_row['task_id']
                domain = prompt_row['domain'].replace('/', '_')
                language = prompt_row['language']
                prompt_type = prompt_row['prompt_type']
                prompt_text = prompt_row['prompt_text']
                complexity = prompt_row.get('complexity_level', '')
                risk_tags = prompt_row.get('risk_tags', '')
                
                print(f"\n[{i}/{len(prompts)}] {task_id} - {language} - {prompt_type}")
                
                for run in range(1, self.runs_per_prompt + 1):
                    self.collect_one_run(
                        task_id, domain, language, prompt_type,
                        prompt_text, complexity, risk_tags, run
                    )
        
        # Calculate final statistics
        total_time = time.time() - start_time
        
        # Save master metadata CSV
        self.save_master_csv()
        
        # Print summary
        self.print_summary(total_time)
        
        return True
    
    def save_master_csv(self):
        """Save master tracking CSV"""
        csv_path = self.output_dir / f"{self.model}_metadata.csv"
        
        if not self.metadata_rows:
            return
        
        fieldnames = self.metadata_rows[0].keys()
        
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.metadata_rows)
        
        print(f"\n📊 Metadata saved: {csv_path}")
    
    def print_summary(self, total_time):
        """Print collection summary"""
        print(f"\n{'='*70}")
        print(f"COLLECTION COMPLETE")
        print(f"{'='*70}\n")
        
        print(f"Statistics:")
        print(f"  Total runs: {self.stats['total_runs']}")
        print(f"  Successful: {self.stats['successful_runs']}")
        print(f"  Failed: {self.stats['failed_runs']}")
        print(f"  Files created: {self.stats['files_created']}")
        print(f"  Total time: {total_time/60:.1f} minutes")
        print(f"  Avg time per run: {total_time/max(self.stats['total_runs'],1):.1f}s")
        
        if self.stats['successful_runs'] > 0:
            success_rate = (self.stats['successful_runs'] / self.stats['total_runs']) * 100
            print(f"  Success rate: {success_rate:.1f}%")
        
        print(f"\nOutput directory: {self.output_dir}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description='Collect code from Cursor CLI for LLMVulnBench',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Collect for GPT-5 (default: 1 run per prompt)
  python3 collect_code.py --model gpt-5
  
  # Process in batches (10 prompts per batch)
  python3 collect_code.py --model gpt-5 --batch-size 10
  
  # Test without actual execution
  python3 collect_code.py --dry-run
  
  # Collect for specific domain only
  python3 collect_code.py --model claude-sonnet-4 --domain web_api
  
  # Resume from specific task
  python3 collect_code.py --model gpt-5 --resume-from WEB_025
        """
    )
    
    parser.add_argument('--prompts', 
                        default='../generated/prompts_index.csv',
                        help='Path to prompts CSV (default: ../generated/prompts_index.csv)')
    
    parser.add_argument('--output', 
                        default='../collected_code',
                        help='Output directory (default: ../collected_code)')
    
    parser.add_argument('--model', 
                        default='gpt-5',
                        help='Model to use (gpt-5, claude-sonnet-4, gemini-2.5-pro, deepseek, llama)')
    
    parser.add_argument('--runs', 
                        type=int, 
                        default=1,
                        help='Number of runs per prompt (default: 1)')
    
    parser.add_argument('--batch-size',
                        type=int,
                        metavar='N',
                        help='Process N prompts per batch (saves progress after each batch)')
    
    parser.add_argument('--domain',
                        choices=['web_api', 'auth_crypto', 'file_system', 'aiml_ds'],
                        help='Filter to specific domain')
    
    parser.add_argument('--resume-from',
                        metavar='TASK_ID',
                        help='Resume from specific task ID (e.g., WEB_025)')
    
    parser.add_argument('--dry-run', 
                        action='store_true',
                        help='Test without actually running cursor-agent')
    
    parser.add_argument('--limit',
                        type=int,
                        metavar='N',
                        help='Limit to first N prompts (for testing)')
    
    args = parser.parse_args()
    
    # Resolve paths relative to script location
    script_dir = Path(__file__).parent
    prompts_path = (script_dir / args.prompts).resolve()
    output_path = (script_dir / args.output).resolve()
    
    collector = CodeCollector(
        prompts_csv=prompts_path,
        output_dir=output_path,
        model=args.model,
        runs_per_prompt=args.runs,
        domain_filter=args.domain,
        resume_from=args.resume_from,
        dry_run=args.dry_run,
        batch_size=args.batch_size,
        limit=args.limit
    )
    
    success = collector.collect_all()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

