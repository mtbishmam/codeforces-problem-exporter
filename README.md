# Codeforces Problem Exporter

Export Codeforces problem statements as clean A4 PDFs using Playwright.

The maintained exporter supports:

- one individual Codeforces problem URL;
- multiple problem URLs from a text file;
- every problem listed on a Codeforces problemset page;
- side-by-side sample input and output blocks;
- removal of Codeforces `Copy` controls from samples;
- combining downloaded PDFs in the order listed in `input/links.txt`.

> [!NOTE]
> This is an unofficial project and is not affiliated with Codeforces. Problem statements remain the property of Codeforces and their respective authors.

## Project Structure

```text
codeforces-problem-exporter/
├── src/
│   ├── pdf_exporter.py
│   └── combine_pdfs.py
├── legacy/
│   ├── screenshot_exporter.py
│   ├── multi_link_pdf_exporter.py
│   └── single_link_pdf_exporter.py
├── input/
│   └── links.txt
├── pdfs/
├── exports/
├── venv/
├── .gitignore
├── README.md
├── TODO.md
├── requirements.txt
└── LICENSE
```

The scripts determine the repository root using their own locations. Therefore, generated files go to the correct root-level directories even though the maintained scripts are stored inside `src/`.

The following local directories and files are excluded from Git:

```text
venv/
input/links.txt
pdfs/
screenshots/
exports/
```

## Quick Start — Already Installed

If the virtual environment and dependencies are already installed:

```bash
cd ~/code/codeforces-problem-exporter
source venv/bin/activate
```

Then choose one of the exporter modes below.

### Export one problem

```bash
python3 src/pdf_exporter.py problem \
  https://codeforces.com/problemset/problem/1915/F
```

### Export the URLs in `input/links.txt`

```bash
python3 src/pdf_exporter.py file
```

### Export URLs from another text file

```bash
python3 src/pdf_exporter.py file ~/Downloads/links_1600.txt
```

### Export all problems on a problemset page

Keep the URL inside quotes because a problemset URL may contain shell-special characters such as `&`.

```bash
python3 src/pdf_exporter.py problemset \
  "https://codeforces.com/problemset/page/2?tags=1600-1600"
```

Individual PDFs are saved automatically inside:

```text
pdfs/
```

### Combine PDFs

The combiner follows the exact URL order in `input/links.txt`, finds the corresponding files inside `pdfs/`, and skips missing PDFs with a warning.

```bash
python3 src/combine_pdfs.py
```

The combined document is saved as:

```text
exports/combined_problems.pdf
```

When finished:

```bash
deactivate
```

Deactivating does not uninstall anything. Everything inside `venv/` remains available for the next session.

## Input File Format

Create `input/links.txt` and put one Codeforces problem URL on each line:

```text
https://codeforces.com/problemset/problem/1915/F
https://codeforces.com/problemset/problem/1891/C
https://codeforces.com/problemset/problem/1881/E
```

Use links only—no numbering, problem titles, or Markdown formatting.

Blank lines are ignored. Duplicate URLs are downloaded only once while preserving the order of their first appearance.

## Complete Setup on a Blank Ubuntu System

### 1. Install Git, Python, pip, and virtual-environment support

```bash
sudo apt update
sudo apt install git python3 python3-pip python3-venv
```

If Ubuntu cannot create the virtual environment correctly, install the complete Python distribution as well:

```bash
sudo apt install python3-full
```

### 2. Clone the repository

Using HTTPS:

```bash
mkdir -p ~/code
cd ~/code
git clone https://github.com/mtbishmam/codeforces-problem-exporter.git
cd codeforces-problem-exporter
```

Or, if GitHub SSH is already configured:

```bash
git clone git@github.com:mtbishmam/codeforces-problem-exporter.git
cd codeforces-problem-exporter
```

### 3. Create the virtual environment

```bash
python3 -m venv venv
```

### 4. Activate it

```bash
source venv/bin/activate
```

The terminal prompt should now begin with `(venv)`.

Verify that the environment is actually active:

```bash
which python3
which pip
```

Both commands should point inside the repository’s `venv/bin/` directory, for example:

```text
/home/yourname/code/codeforces-problem-exporter/venv/bin/python3
/home/yourname/code/codeforces-problem-exporter/venv/bin/pip
```

They should not point to `/usr/bin/python3` or `/usr/bin/pip`.

### 5. Install the Python dependencies

```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

The project currently requires:

- `playwright` for browser automation and PDF generation;
- `pypdf` for combining PDFs.

### 6. Install Playwright Chromium and its system dependencies

```bash
python3 -m playwright install --with-deps chromium
```

This may request the Ubuntu password because some browser dependencies are installed system-wide.

### 7. Create the dynamic input file

`input/links.txt` is intentionally excluded from Git because it changes between runs. Create it locally:

```bash
mkdir -p input
touch input/links.txt
```

Open it in an editor and add one problem URL per line:

```bash
vim input/links.txt
```

### 8. Run the exporter

For the default input file:

```bash
python3 src/pdf_exporter.py file
```

The `pdfs/` directory is created automatically if it does not already exist.

## Command Summary

```bash
# Activate
source venv/bin/activate

# One problem
python3 src/pdf_exporter.py problem PROBLEM_URL

# Default input/links.txt
python3 src/pdf_exporter.py file

# Another links file
python3 src/pdf_exporter.py file PATH_TO_FILE

# Every problem on a problemset page
python3 src/pdf_exporter.py problemset "PROBLEMSET_URL"

# Combine according to input/links.txt
python3 src/combine_pdfs.py

# Deactivate
deactivate
```

## Legacy Code

Older working implementations are retained inside:

```text
legacy/
```

This is the appropriate directory name for functional but outdated code that is kept for reference. The files in `legacy/` are not the maintained interface and may use old paths or formatting.

The maintained PDF implementation is:

```text
src/pdf_exporter.py
```

If screenshot exporting becomes an actively supported feature again, move `screenshot_exporter.py` from `legacy/` back into `src/`, update its paths, and document its command here.

## Troubleshooting

### `ModuleNotFoundError: No module named 'playwright'`

Activate the correct environment and install the requirements:

```bash
source venv/bin/activate
python3 -m pip install -r requirements.txt
```

Confirm the interpreter:

```bash
which python3
```

It should point to `codeforces-problem-exporter/venv/bin/python3`.

### `(venv)` appears, but Python points to `/usr/bin/python3`

The virtual environment is broken. Recreate it safely:

```bash
deactivate
mv venv venv_old
python3 -m venv venv
source venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 -m playwright install --with-deps chromium
```

After confirming that the exporter works:

```bash
rm -rf venv_old
```

### `externally-managed-environment`

This usually means Ubuntu’s system Python is being used instead of the project environment. Do not use `--break-system-packages`.

Run:

```bash
source venv/bin/activate
which python3
which pip
```

If they still point to `/usr/bin`, recreate the environment using the steps above.

### Playwright cannot find Chromium

```bash
source venv/bin/activate
python3 -m playwright install chromium
```

If required system libraries are also missing:

```bash
python3 -m playwright install --with-deps chromium
```

### Cloudflare verification appears

The exporter launches a visible browser. Complete the verification in the browser window when requested; the script waits before continuing.

### Check disk usage

```bash
du -sh venv
du -sh pdfs
du -sh exports
du -sh ~/.cache/ms-playwright
```

Playwright’s Chromium installation is normally stored in `~/.cache/ms-playwright`, separately from `venv/`.

## Development Notes

- `ROOT_DIR = Path(__file__).resolve().parent.parent` keeps paths anchored to the repository root.
- `pdfs/` stores individual generated statements.
- `exports/` stores combined final documents.
- `input/links.txt` is dynamic local input and is not committed.
- `venv/` is persistent local state and must not be committed.
- Run the maintained scripts with Python 3 and include the `.py` extension.
