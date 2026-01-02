# EPEXSPOT - Data Scrapering assessment

## Overview
This assessmrent is a QA-focused automation script that extracts specific and exports validated data to a CSV file. The solution is implemented using **Python, Playwright, and Pytest**.

---

## What It Does
- Builds the EPEX SPOT market results URL dynamically to take yesterday's date.
- Launches a Chromium browser using Playwright
- Handles popup window
- Waits for the market results table to load
- Extracts valid rows (`Low`, `High`, `Last`, `Weight Avg`)
- Skips empty rows
- Writes the cleaned output to `epex_data.csv`
- Fails the test if no valid data is found

---

## Tech Stack
- Python 3.9+
- Playwright (sync API)
- Pytest

---

## Setup & Run

```bash
pip install -r requirements.txt
playwright install chromium
pytest test_scrape.py -v
