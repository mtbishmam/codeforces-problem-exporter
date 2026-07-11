import asyncio
import os
import re
import base64
from urllib.parse import urljoin

from playwright.async_api import async_playwright


async def scrape_and_save_pdfs():
    # url = "https://codeforces.com/problemset?tags=1700-1700"
    url = "https://codeforces.com/problemset/page/2?tags=1600-1600"

    base_url = "https://codeforces.com"
    output_dir = "cf_problem_pdfs"
    os.makedirs(output_dir, exist_ok=True)

    async with async_playwright() as p:
        print("Launching browser...")

        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ]
        )

        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1440, "height": 900},
            device_scale_factor=2,
            is_mobile=False,
            has_touch=False
        )

        page = await context.new_page()

        await page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        print(f"Opening problemset: {url}")

        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)

            print("Waiting 5 seconds for Cloudflare...")
            await page.wait_for_timeout(5000)

        except Exception as e:
            print(f"Failed to load problemset: {e}")
            await browser.close()
            return

        links = await page.locator(
            'table.problems a[href*="/problemset/problem/"]'
        ).all()

        problem_urls = set()

        for link in links:
            href = await link.get_attribute("href")
            if href:
                problem_urls.add(urljoin(base_url, href))

        problem_urls = sorted(problem_urls)

        print(f"Found {len(problem_urls)} problems.\n")

        for idx, problem_url in enumerate(problem_urls, start=1):

            match = re.search(
                r"/problem/(\d+)/([A-Za-z0-9]+)",
                problem_url
            )

            if match:
                filename = f"{match.group(1)}{match.group(2)}.pdf"
            else:
                filename = f"problem_{idx}.pdf"

            pdf_path = os.path.join(output_dir, filename)

            print(f"[{idx}/{len(problem_urls)}] {problem_url}")

            try:
                await page.goto(
                    problem_url,
                    wait_until="load",
                    timeout=30000
                )

                if (
                    "Just a moment..." in await page.title()
                    or await page.locator(
                        "text=Verify you are human"
                    ).count() > 0
                ):
                    print("    Verification page detected...")
                    await page.wait_for_timeout(6000)

                await page.wait_for_timeout(2000)

                # Remove clutter and keep only the statement
                await page.evaluate("""
                () => {
                    const statement =
                        document.querySelector('.problem-statement');

                    if (!statement) return;

                    document.body.innerHTML = '';
                    document.body.appendChild(statement);

                    document.body.style.margin = '20px';
                    document.body.style.background = 'white';
                }
                """)

                # Print styling
                await page.add_style_tag(content="""
                    @page {
                        size: A4;
                        margin: 12mm;
                    }

                    body {
                        font-family: serif;
                        font-size: 12pt;
                    }

                    img {
                        max-width: 100%;
                    }

                    pre {
                        white-space: pre-wrap;
                        word-wrap: break-word;
                    }
                """)

                await page.emulate_media(media="print")

                # Chrome DevTools PDF generation
                client = await context.new_cdp_session(page)

                pdf_data = await client.send(
                    "Page.printToPDF",
                    {
                        "printBackground": True,
                        "paperWidth": 8.27,   # A4
                        "paperHeight": 11.69,
                        "marginTop": 0.4,
                        "marginBottom": 0.4,
                        "marginLeft": 0.4,
                        "marginRight": 0.4,
                        "preferCSSPageSize": True,
                    }
                )

                with open(pdf_path, "wb") as f:
                    f.write(base64.b64decode(pdf_data["data"]))

                print(f"    Saved: {filename}")

            except Exception as e:
                print(f"    Failed: {e}")

            await page.wait_for_timeout(2000)

        await browser.close()

    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(scrape_and_save_pdfs())