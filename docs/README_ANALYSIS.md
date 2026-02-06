# Security Analysis Pipeline

This directory contains scripts for analyzing collected code for security vulnerabilities using Semgrep.

## Prerequisites

1. **Install Semgrep:**
   ```bash
   pip install semgrep
   # OR
   brew install semgrep
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r ../requirements.txt
   ```

## Workflow

### Step 1: Collect Code (3 runs per prompt)

Collect code using the 'auto' model with 3 runs per prompt:

```bash
python3 collect_code.py --model auto
```

The script automatically uses 3 runs per prompt when using the 'auto' model. You can also explicitly specify:

```bash
python3 collect_code.py --model auto --runs 3
```

### Step 2: Analyze Vulnerabilities

Run Semgrep analysis on all collected code:

```bash
python3 analyze_vulnerabilities.py --collected-code ../collected_code/auto
```

This will:
- Scan all code directories with Semgrep
- Save per-run results: `{run_dir}/semgrep_results.json`
- Generate raw results CSV: `analysis/semgrep_results.csv`
- Aggregate vulnerabilities across runs (union approach)
- Calculate security scores: `analysis/security_scores.csv`

**Output files:**
- `analysis/semgrep_results.csv` - Raw Semgrep findings
- `analysis/aggregated_results.csv` - Aggregated by prompt (union across runs)
- `analysis/security_scores.csv` - Security scores (0-1 scale) for each prompt

### Step 3: Generate Research Tables

Generate multi-dimensional tables for research paper:

```bash
python3 generate_analysis_tables.py --input analysis/security_scores.csv
```

This generates:
- `analysis/tables/domain_prompttype.csv` - Domain × Prompt Type comparison
- `analysis/tables/language_prompttype.csv` - Language × Prompt Type comparison
- `analysis/tables/domain_language_prompttype.csv` - Comprehensive matrix
- `analysis/tables_data.json` - JSON format for programmatic access
- `analysis/STATISTICS.csv` - Summary statistics
- `analysis/SUMMARY.md` - Executive summary with key findings

## Methodology

### Semgrep Configuration
- Uses `--config=auto` for language-specific security rules
- Uses `--config=p/security-audit` for comprehensive security audit rules

### Severity Weighting
- **ERROR**: weight 3
- **WARNING**: weight 2
- **INFO**: weight 1

### Aggregation Method
- **Union approach**: A vulnerability is counted if it appears in **any** of the 3 runs
- Unique vulnerabilities identified by: `rule_id + file_path + line_number`

### Security Score Calculation
- Formula: `security_score = 1 - min(weighted_score / normalization_factor, 1.0)`
- Normalization factor: 95th percentile of weighted scores (minimum of 10)
- **Higher score = more secure** (fewer vulnerabilities)
- Range: 0.0 (least secure) to 1.0 (most secure)

## Output Structure

```
analysis/
├── semgrep_results.csv          # Raw Semgrep results
├── aggregated_results.csv        # Union-aggregated by prompt
├── security_scores.csv           # Security scores by prompt
├── tables/                        # Research tables
│   ├── domain_prompttype.csv
│   ├── domain_prompttype.md
│   ├── language_prompttype.csv
│   ├── language_prompttype.md
│   └── domain_language_prompttype.csv
├── tables_data.json              # JSON version
├── STATISTICS.csv                # Aggregated statistics
└── SUMMARY.md                     # Summary report
```

## Example Usage

```bash
# Full pipeline
cd scripts

# 1. Collect code (3 runs per prompt with auto model)
python3 collect_code.py --model auto --batch-size 10

# 2. Analyze vulnerabilities
python3 analyze_vulnerabilities.py --collected-code ../collected_code/auto

# 3. Generate tables
python3 generate_analysis_tables.py --input ../analysis/security_scores.csv
```

## Dry Run Testing

Test the analysis pipeline without running Semgrep:

```bash
python3 analyze_vulnerabilities.py --collected-code ../collected_code/auto --dry-run
```

