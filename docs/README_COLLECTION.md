# Code Collection Pipeline

This directory contains scripts for collecting LLM-generated code using Cursor CLI.

## Prerequisites

1. **Install Cursor CLI:**
```bash
curl https://cursor.com/install -fsS | bash
```

2. **Authenticate:**
```bash
# Using browser authentication (recommended)
cursor-agent login

# OR using API key
export CURSOR_API_KEY=your_api_key_here
```

3. **Generate prompts first:**
```bash
python3 generate_prompts.py
```

## Usage

### Basic Collection

Collect code for one model with 5 runs per prompt:

```bash
python3 collect_code.py --model gpt-5 --runs 5
```

### Test Mode

Test the pipeline without actually running cursor-agent:

```bash
python3 collect_code.py --dry-run
```

### Domain-Specific Collection

Collect for a specific domain only:

```bash
python3 collect_code.py --model claude-sonnet-4 --domain web_api
```

### Resume Collection

Resume from a specific task if interrupted:

```bash
python3 collect_code.py --model gpt-5 --resume-from WEB_025
```

## Full Pipeline Example

```bash
# 1. Generate prompts
python3 generate_prompts.py

# 2. Collect code for multiple models
python3 collect_code.py --model gpt-5 --runs 5
python3 collect_code.py --model claude-sonnet-4 --runs 5
python3 collect_code.py --model gemini-2.5-pro --runs 5
python3 collect_code.py --model deepseek --runs 5
python3 collect_code.py --model llama --runs 5
```

## Output Structure

```
/collected_code
├── gpt-5_metadata.csv              # Metadata for all GPT-5 runs
├── claude-sonnet-4_metadata.csv    # Metadata for all Claude runs
│
├── gpt-5/                           # Model folder
│   ├── web_api/                    # Domain folder
│   │   ├── WEB_001/               # Task folder
│   │   │   ├── python_naive/      # Language + prompt type
│   │   │   │   ├── run_1/
│   │   │   │   │   ├── code/      # Generated code files
│   │   │   │   │   ├── output.json   # CLI output
│   │   │   │   │   └── metadata.json # Run metadata
│   │   │   │   ├── run_2/
│   │   │   │   └── run_3/
│   │   │   ├── python_security_aware/
│   │   │   └── typescript_naive/
│   │   ├── WEB_002/
│   │   └── ...
│   ├── auth_crypto/
│   ├── file_system/
│   └── aiml_ds/
│
└── claude-sonnet-4/
    └── ...
```

## Metadata Files

### Per-Run Metadata (`metadata.json`)

Each run produces a metadata file with:
- Task information (ID, domain, language, prompt type)
- Model used
- Execution duration
- Success/failure status
- List of files created
- Timestamps

### Master Metadata CSV

Each model produces a master CSV (`{model}_metadata.csv`) containing:
- All run metadata in tabular format
- Easy to load for analysis
- Filterable by domain, language, prompt type, etc.

## Statistics Tracking

The script tracks:
- Total runs executed
- Success/failure counts
- Files created
- Total execution time
- Average time per run
- Success rate

## Error Handling

- **Timeout**: Runs timeout after 5 minutes
- **Resume**: Use `--resume-from` to continue interrupted collections
- **Dry run**: Test without execution using `--dry-run`
- **Logs**: Check `stderr.txt` in run directories for errors

## Expected Runtime

For 200 tasks with 5 runs each across 5 models:
- **Total prompts**: 200 tasks × ~4 languages × 4 prompt types = ~3,200 prompts
- **Total runs**: 3,200 prompts × 5 runs = 16,000 runs
- **Per model**: 16,000 runs / 5 models = 3,200 runs
- **Estimated time**: ~30-60 seconds per run = 27-53 hours per model
- **All models**: ~5-11 days if run sequentially

**Recommendation**: Run models in parallel on different machines or use batch processing.

## Cost Estimation

Costs will vary by model and prompt complexity. Monitor usage through:
- Cursor dashboard
- API usage logs
- Model-specific pricing pages

Expected tokens per prompt:
- Input: ~200-500 tokens (prompt + context)
- Output: ~500-2000 tokens (generated code)

For accurate estimates, run a small pilot (10-20 prompts) and calculate costs.

## Troubleshooting

### "cursor-agent: command not found"
Install Cursor CLI:
```bash
curl https://cursor.com/install -fsS | bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### "Not authenticated"
```bash
cursor-agent login
# OR
export CURSOR_API_KEY=your_api_key
```

### Runs timing out
Increase timeout in `collect_code.py`:
```python
timeout=300  # Change to 600 for 10 minutes
```

### Out of disk space
Each run creates ~5-50KB. For 16,000 runs:
- Estimated: 80MB - 800MB total
- Ensure at least 2GB free space

## Next Steps

After code collection:
1. Run static analysis (Semgrep, Cppcheck)
2. Map vulnerabilities to CWE categories
3. Aggregate results across models/prompts
4. Statistical analysis and visualization

