# Code Collection Pipeline - Implementation Complete

## What's Built

### 1. Code Collection Script (`scripts/collect_code.py`)

**Features:**
- Reads prompts from CSV
- Runs each through `cursor-agent` CLI
- Captures generated code
- Structured output storage
- Metadata tracking
- Statistics and progress reporting
- Error handling and resume functionality
- Dry-run mode for testing
- Domain filtering
- Configurable runs per prompt (default: 5)

**Usage:**
```bash
# Basic collection
python3 collect_code.py --model gpt-5 --runs 5

# Test mode
python3 collect_code.py --dry-run

# Domain-specific
python3 collect_code.py --model claude-sonnet-4 --domain web_api

# Resume interrupted collection
python3 collect_code.py --model gpt-5 --resume-from WEB_025
```

### 2. Output Structure

```
/collected_code
├── {model}_metadata.csv           # Master tracking CSV
│
├── {model}/                        # e.g., gpt-5, claude-sonnet-4
│   ├── {domain}/                   # e.g., web_api, auth_crypto
│   │   ├── {task_id}/             # e.g., WEB_001
│   │   │   ├── {lang}_{prompt}/   # e.g., python_naive
│   │   │   │   ├── run_1/
│   │   │   │   │   ├── code/      # All generated files
│   │   │   │   │   ├── output.json     # CLI output
│   │   │   │   │   ├── metadata.json   # Run metadata
│   │   │   │   │   └── stderr.txt      # Errors (if any)
│   │   │   │   ├── run_2/
│   │   │   │   ├── run_3/
│   │   │   │   ├── run_4/
│   │   │   │   └── run_5/
```

### 3. Metadata Tracking

**Per-Run Metadata (`metadata.json`):**
- Task information (ID, domain, language, prompt type)
- Model used
- Run number
- Execution duration
- Success/failure status
- List of files created
- Final result message
- Timestamps

**Master CSV (`{model}_metadata.csv`):**
- All run metadata in tabular format
- Easy to filter and analyze
- Compatible with pandas/R/Excel

### 4. Updated Project Scope

**Revised from 6 domains → 4 domains:**
- Web/API (50 tasks)
- Auth/Crypto (50 tasks)
- File System (50 tasks)
- AI/ML-DS (50 tasks)

**Total:** 200 tasks (down from 240)

### 5. Documentation

- `README_COLLECTION.md` - Complete usage guide
- Updated `README.md` - Project status
- Updated `QUICKSTART.md` - New task counts
- Updated `TASK_CREATION_GUIDE.md` - 4 domains, 200 tasks
- CWE reference data integrated (`cwe-swe.csv`)

---

## Expected Scale

### Prompts
```
200 tasks × ~4 languages × 4 prompt types = ~3,200 prompts
```

### Code Collection Runs
```
3,200 prompts × 5 runs = 16,000 runs per model
16,000 runs × 5 models = 80,000 total runs
```

### Storage
```
Per run: ~5-50 KB
Total: ~400 MB - 4 GB
```

### Time Estimates
```
Per run: ~30-60 seconds
Per model: ~27-53 hours (sequential)
All models: ~5-11 days (sequential)
```

**Recommendation:** Run models in parallel across machines.

---

## Key Features

### Robust Error Handling
- Timeout protection (5 minutes per run)
- Resume functionality for interrupted collections
- Error logging to stderr files
- Success/failure tracking

### Flexibility
- Domain filtering
- Model selection
- Configurable runs per prompt
- Dry-run testing mode

### Scalability
- Handles 80,000+ runs
- Organized directory structure
- Master CSV for analysis
- Parallel execution ready

### Reproducibility
- Timestamp tracking
- Complete metadata capture
- Deterministic file organization
- Version-controlled prompts

---

## Testing the Pipeline

### Before Full Run

1. **Install Cursor CLI:**
```bash
curl https://cursor.com/install -fsS | bash
cursor-agent login
```

2. **Test with dry run:**
```bash
cd scripts
python3 collect_code.py --dry-run
```

3. **Small pilot (3 current tasks):**
```bash
python3 collect_code.py --model gpt-5 --runs 2
```

4. **Verify output:**
```bash
ls -R ../collected_code/gpt-5/
cat ../collected_code/gpt-5_metadata.csv
```