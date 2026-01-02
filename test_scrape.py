import csv
import pytest
import logging
from datetime import datetime, timedelta
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture(scope="session")
def yesterday_url():

    # NOTE: Jan 1st is often a holiday; fallback added for stability
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    return (
        f"https://www.epexspot.com/en/market-results?market_area=GB&auction=&trading_date=&delivery_date={yesterday}&underlying_year=&modality=Continuous&sub_modality=&technology=&data_mode=table&period=&production_period=&product=30"
    )

def test_scrape_epexspot(yesterday_url):

    headers = ["Low", "High", "Last", "Weight Avg"]
    rows = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )

        context = browser.new_context(
            viewport={"width": 1366, "height": 768},
            locale="en-GB",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )

        page = context.new_page()

        try:
            page.goto(yesterday_url, wait_until="domcontentloaded", timeout=30000)

            # Handle disclaimers/popups FIRST
            popup_selectors = [
                "xpath=//div[@id='popup-buttons']//button[contains(text(), 'Allow all cookies')]",
                "xpath=//button[contains(text(), 'Accept')]",
                "xpath=//button[contains(text(), 'Agree')]",
                ".data-use-acceptation-button",
                "#edit-acceptationbutton"
            ]
            
            for selector in popup_selectors:
                try:
                    page.wait_for_selector(selector, timeout=2000)
                    page.click(selector)
                    print(f"✅ Clicked popup: {selector}")
                    break
                except TimeoutError:
                    continue

            # Human-like pause (prevents false automation heuristics)
            page.wait_for_timeout(2000)

            page.wait_for_selector("div.js-table-values table", timeout=15000)
            logger.info("Table loaded")

            table_rows = page.locator(
                "div.js-table-values tbody tr"
            ).all()

            for idx, row in enumerate(table_rows, 1):
                cells = row.locator("td").all()[:4]
                values = [cell.inner_text().strip() for cell in cells]

                if len(values) == 4 and all(values):
                    rows.append(values)
                else:
                    logger.debug(f"Skipped row {idx}")

            assert rows, "No valid data rows extracted"

        except PlaywrightTimeoutError as e:
            logger.error(f"Timeout error: {e}")
            raise
        finally:
            context.close()
            browser.close()

    output_path = Path("epex_data.csv")
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

    logger.info(f"Exported {len(rows)} rows to {output_path}")
    assert output_path.exists() and output_path.stat().st_size > 100
