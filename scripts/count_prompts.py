import json
import glob
from pathlib import Path

total_prompts = 0
language_counts = {}
domain_counts = {}

print("Domain | Task Count | Languages Supported per Task (avg) | Total Prompts")
print("-" * 70)

for file in glob.glob("tasks/*.json"):
    with open(file, 'r') as f:
        data = json.load(f)
        domain = data['domain']
        tasks = data['tasks']
        
        domain_prompts = 0
        
        for task in tasks:
            langs = task.get('supported_languages', [])
            num_langs = len(langs)
            prompts_for_task = num_langs * 4
            domain_prompts += prompts_for_task
            total_prompts += prompts_for_task
            
            for lang in langs:
                language_counts[lang] = language_counts.get(lang, 0) + 4 # 4 prompt types per language
        
        print(f"{domain:<15} | {len(tasks):<10} | {domain_prompts/(len(tasks)*4):<30.2f} | {domain_prompts}")

print("\nTotal Prompts: ", total_prompts)
print("\nBreakdown by Language (Prompts):")
for lang, count in language_counts.items():
    print(f"{lang}: {count}")
