
import json
from pathlib import Path

# Manual fallback values for when API fetch failed
FALLBACK_SCORES = {
    'CWE-78': 9.8,   # OS Command Injection -> Critical
    'CWE-89': 9.8,   # SQL Injection -> Critical
    'CWE-22': 7.5,   # Path Traversal -> High
    'CWE-200': 5.0,  # Info Exposure -> Medium
    'CWE-119': 9.8,  # Buffer Overflow -> Critical
    'CWE-94': 9.8,   # Code Injection -> Critical
    'CWE-494': 7.8,  # Download of Code Without Integrity Check -> High
    'CWE-215': 5.0,  # Info Exposure (Debug) -> Medium
    'CWE-398': 0.0,  # Indicator of Poor Code Quality -> None/Low
    'CWE-570': 0.0,  # Expression is Always False -> Low
    'CWE-377': 5.5,  # Insecure Temporary File -> Medium
    'CWE-252': 6.5,  # Unchecked Return Value -> Medium
    'CWE-404': 5.0,  # Improper Resource Shutdown -> Medium
}

json_path = Path(__file__).parent.parent / 'data' / 'cwe_cvss_mapping.json'

if json_path.exists():
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    updated_count = 0
    for cwe, score in data.items():
        if score is None:
            if cwe in FALLBACK_SCORES:
                data[cwe] = FALLBACK_SCORES[cwe]
                updated_count += 1
                print(f"Patched {cwe} with {data[cwe]}")
            else:
                print(f"Warning: No fallback for {cwe}")
    
    # Also ensure all fallback keys are present
    for cwe, score in FALLBACK_SCORES.items():
        if cwe not in data or data[cwe] is None:
            data[cwe] = score
            updated_count += 1
            print(f"Added/Patched {cwe} with {score}")

    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Updated {updated_count} mapping entries.")
else:
    print("Mapping file not found.")
