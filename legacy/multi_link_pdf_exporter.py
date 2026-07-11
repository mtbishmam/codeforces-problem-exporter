import asyncio
import os
import re
import base64

from playwright.async_api import async_playwright


async def scrape_and_save_pdfs():
    links_file = "links.txt"
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
            """
            Object.defineProperty(
                navigator,
                'webdriver',
                {get: () => undefined}
            )
            """
        )

        # Read problem links from links.txt
        try:
            with open(links_file, "r", encoding="utf-8") as file:
                problem_urls = [
                    line.strip()
                    for line in file
                    if line.strip()
                ]

        except FileNotFoundError:
            print(f"Could not find {links_file}")
            await browser.close()
            return

        if not problem_urls:
            print(f"No links found inside {links_file}")
            await browser.close()
            return

        print(f"Found {len(problem_urls)} problems.\n")

        for idx, problem_url in enumerate(
            problem_urls,
            start=1
        ):
            match = re.search(
                r"/problem/(\d+)/([A-Za-z0-9]+)",
                problem_url
            )

            if match:
                filename = (
                    f"{match.group(1)}"
                    f"{match.group(2)}.pdf"
                )
            else:
                filename = f"problem_{idx}.pdf"

            pdf_path = os.path.join(
                output_dir,
                filename
            )

            print(
                f"[{idx}/{len(problem_urls)}] "
                f"{problem_url}"
            )

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
                    print(
                        "    Verification page detected..."
                    )

                    await page.wait_for_timeout(6000)

                await page.wait_for_timeout(2000)

                # Keep only the problem statement
                await page.evaluate(
                    """
                    () => {
                        const statement =
                            document.querySelector(
                                '.problem-statement'
                            );

                        if (!statement) return;

                        /*
                         * Remove elements containing only
                         * the word "Copy".
                         */
                        statement
                            .querySelectorAll('*')
                            .forEach(element => {
                                const text =
                                    element.textContent
                                        .trim()
                                        .toLowerCase();

                                if (
                                    element.children.length === 0
                                    && text === 'copy'
                                ) {
                                    element.remove();
                                }
                            });

                        document.body.innerHTML = '';
                        document.body.appendChild(statement);

                        document.body.style.margin = '20px';
                        document.body.style.background = 'white';
                    }
                    """
                )

                # PDF styling
                await page.add_style_tag(
                    content="""
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

                    /*
                     * Each sample-test contains one input
                     * and its corresponding output.
                     */
                    .sample-tests .sample-test {
                        display: grid !important;
                        grid-template-columns:
                            minmax(0, 1fr)
                            minmax(0, 1fr);
                        gap: 10px;
                        align-items: start;
                        margin-bottom: 10px;
                    }

                    /*
                     * Input goes in the left column.
                     */
                    .sample-tests .sample-test > .input {
                        grid-column: 1;
                        min-width: 0;
                        width: auto !important;
                        margin: 0 !important;
                    }

                    /*
                     * Output goes in the right column.
                     */
                    .sample-tests .sample-test > .output {
                        grid-column: 2;
                        min-width: 0;
                        width: auto !important;
                        margin: 0 !important;
                    }

                    /*
                     * Keep input/output blocks together
                     * when possible.
                     */
                    .sample-tests .input,
                    .sample-tests .output {
                        break-inside: avoid;
                    }

                    /*
                     * Compact Input and Output headings.
                     */
                    .sample-tests .title {
                        padding: 4px 6px !important;
                        margin: 0 !important;
                    }

                    /*
                     * Make samples fit inside half-page
                     * columns.
                     */
                    .sample-tests pre {
                        white-space: pre-wrap !important;
                        overflow-wrap: anywhere;
                        word-break: break-word;
                        margin: 0 !important;
                        font-size: 10pt !important;
                    }

                    /*
                     * Hide known Codeforces copy controls.
                     */
                    .sample-tests button,
                    .sample-tests
                        .test-example-line-copy-button,
                    .sample-tests
                        .input-output-copier,
                    .sample-tests .copy-button {
                        display: none !important;
                    }
                    """
                )

                await page.emulate_media(media="print")

                # Generate the PDF
                client = await context.new_cdp_session(page)

                pdf_data = await client.send(
                    "Page.printToPDF",
                    {
                        "printBackground": True,
                        "paperWidth": 8.27,
                        "paperHeight": 11.69,
                        "marginTop": 0.4,
                        "marginBottom": 0.4,
                        "marginLeft": 0.4,
                        "marginRight": 0.4,
                        "preferCSSPageSize": True
                    }
                )

                with open(pdf_path, "wb") as file:
                    file.write(
                        base64.b64decode(
                            pdf_data["data"]
                        )
                    )

                print(f"    Saved: {filename}")

            except Exception as error:
                print(f"    Failed: {error}")

            await page.wait_for_timeout(2000)

        await browser.close()

    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(scrape_and_save_pdfs())