#!/usr/bin/env python3
"""
LLMVulnBench Prompt Generator

This script generates prompts from task definitions and prompt templates.
For each task, it iterates over supported languages and prompt types,
validates required variables, and generates final prompts.

Usage:
    python generate_prompts.py

Output:
    - Individual prompt files in ../generated/
    - CSV index in ../generated/prompts_index.csv
"""

import json
import os
import csv
from pathlib import Path
from typing import Dict, List, Any


class PromptGenerator:
    def __init__(self, tasks_dir: str, templates_file: str, output_dir: str, generate_files: bool = True):
        self.tasks_dir = Path(tasks_dir)
        self.templates_file = Path(templates_file)
        self.output_dir = Path(output_dir)
        self.generate_files = generate_files
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Storage
        self.tasks = []
        self.templates = {}
        self.generated_prompts = []
        
    def load_tasks(self):
        """Load all task JSON files from tasks directory.
        
        Each JSON file represents a domain and contains an array of tasks.
        """
        print(f"Loading tasks from {self.tasks_dir}...")
        
        domain_files = sorted(self.tasks_dir.glob("*.json"))
        
        for domain_file in domain_files:
            with open(domain_file, 'r') as f:
                domain_data = json.load(f)
                domain_name = domain_data['domain']
                tasks_in_domain = domain_data['tasks']
                
                print(f"  ✓ Loaded domain: {domain_name} ({len(tasks_in_domain)} tasks)")
                
                # Add domain to each task for reference
                for task in tasks_in_domain:
                    task['domain'] = domain_name
                    self.tasks.append(task)
        
        print(f"\nTotal tasks loaded: {len(self.tasks)}\n")
    
    def load_templates(self):
        """Load prompt templates."""
        print(f"Loading templates from {self.templates_file}...")
        
        with open(self.templates_file, 'r') as f:
            self.templates = json.load(f)
        
        for template_name in self.templates:
            print(f"Loaded template: {template_name}")
        
        print(f"\nTotal templates loaded: {len(self.templates)}\n")
    
    def validate_variables(self, task_id: str, language: str, 
                          template_name: str, variables: Dict[str, str]) -> bool:
        """Check if all required variables are present."""
        template = self.templates[template_name]
        required_vars = template['required_vars']
        
        missing_vars = [var for var in required_vars if var not in variables]
        
        if missing_vars:
            print(f"WARNING: {task_id}/{language}/{template_name} missing vars: {missing_vars}")
            return False
        
        return True
    
    def render_prompt(self, template_name: str, variables: Dict[str, str]) -> str:
        """Render a prompt template with variables."""
        template = self.templates[template_name]
        template_string = template['template']
        
        # Use .format() to replace {variable} placeholders
        rendered = template_string.format(**variables)
        
        return rendered
    
    def generate_all_prompts(self):
        """Main generation loop: iterate over tasks, languages, and prompt types."""
        print("=" * 80)
        print("GENERATING PROMPTS")
        print("=" * 80 + "\n")
        
        total_generated = 0
        total_skipped = 0
        
        for task in self.tasks:
            task_id = task['task_id']
            domain = task['domain']
            description = task['description']
            complexity = task['complexity_level']
            risk_tags = task['risk_tags']
            
            print(f"Processing {task_id} ({domain})...")
            
            for language in task['supported_languages']:
                # Get language-specific variables
                lang_vars = task['variables'][language]
                
                for template_name in self.templates.keys():
                    # Merge variables: language, description, + all lang_vars
                    variables = {
                        'language': language,
                        'description': description,
                        **lang_vars
                    }
                    
                    # Validate required variables
                    if not self.validate_variables(task_id, language, template_name, variables):
                        total_skipped += 1
                        continue
                    
                    # Render prompt
                    prompt_text = self.render_prompt(template_name, variables)
                    
                    # Create organized file path: domain/task_id/language_prompttype.txt
                    # Convert domain name to folder-safe format (e.g., "web/api" -> "web_api")
                    domain_folder = domain.replace('/', '_')
                    task_folder = self.output_dir / domain_folder / task_id
                    filename = f"{language}_{template_name}.txt"
                    relative_path = f"{domain_folder}/{task_id}/{filename}"
                    
                    # Save to file if enabled
                    if self.generate_files:
                        task_folder.mkdir(parents=True, exist_ok=True)
                        filepath = task_folder / filename
                        with open(filepath, 'w') as f:
                            f.write(prompt_text)
                    
                    # Store metadata for CSV
                    self.generated_prompts.append({
                        'task_id': task_id,
                        'domain': domain,
                        'language': language,
                        'prompt_type': template_name,
                        'complexity_level': complexity,
                        'risk_tags': ', '.join(risk_tags),
                        'prompt_text': prompt_text,
                        'file_path': relative_path
                    })
                    
                    total_generated += 1
                    print(f"  ✓ {language}/{template_name}")
            
            print()
        
        print("=" * 80)
        print(f"GENERATION COMPLETE")
        print(f"  Total prompts generated: {total_generated}")
        print(f"  Total prompts skipped: {total_skipped}")
        if self.generate_files:
            print(f"  Files saved to organized folders")
        else:
            print(f"  File generation skipped (CSV only)")
        print("=" * 80 + "\n")
    
    def save_csv_index(self):
        """Save all generated prompts to a CSV index."""
        csv_path = self.output_dir / "prompts_index.csv"
        
        print(f"Saving CSV index to {csv_path}...")
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            if self.generated_prompts:
                fieldnames = self.generated_prompts[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                writer.writeheader()
                writer.writerows(self.generated_prompts)
        
        print(f"  ✓ CSV index saved with {len(self.generated_prompts)} entries\n")
    
    def print_summary(self):
        """Print generation summary statistics."""
        if not self.generated_prompts:
            print("No prompts generated.")
            return
        
        # Count by domain
        domains = {}
        languages = {}
        prompt_types = {}
        
        for prompt in self.generated_prompts:
            domain = prompt['domain']
            lang = prompt['language']
            ptype = prompt['prompt_type']
            
            domains[domain] = domains.get(domain, 0) + 1
            languages[lang] = languages.get(lang, 0) + 1
            prompt_types[ptype] = prompt_types.get(ptype, 0) + 1
        
        print("=" * 80)
        print("SUMMARY STATISTICS")
        print("=" * 80)
        print(f"\nTotal Prompts: {len(self.generated_prompts)}\n")
        
        print("By Domain:")
        for domain, count in sorted(domains.items()):
            print(f"  {domain}: {count}")
        
        print("\nBy Language:")
        for lang, count in sorted(languages.items()):
            print(f"  {lang}: {count}")
        
        print("\nBy Prompt Type:")
        for ptype, count in sorted(prompt_types.items()):
            print(f"  {ptype}: {count}")
        
        print("\n" + "=" * 80 + "\n")
    
    def run(self):
        """Run the full generation pipeline."""
        self.load_tasks()
        self.load_templates()
        self.generate_all_prompts()
        self.save_csv_index()
        self.print_summary()


def main():
    import sys
    
    # Define paths relative to script location
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    tasks_dir = project_root / "tasks"
    templates_file = project_root / "prompts" / "templates.json"
    output_dir = project_root / "generated"
    
    # Check for command-line flag to disable file generation
    generate_files = True
    if len(sys.argv) > 1 and sys.argv[1] == "--csv-only":
        generate_files = False
        print("Running in CSV-only mode (no individual files will be generated)\n")
    
    # Create and run generator
    generator = PromptGenerator(
        tasks_dir=str(tasks_dir),
        templates_file=str(templates_file),
        output_dir=str(output_dir),
        generate_files=generate_files
    )
    
    generator.run()


if __name__ == "__main__":
    main()

