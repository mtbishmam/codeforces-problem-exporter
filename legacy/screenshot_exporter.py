import asyncio
import os
import re
from playwright.async_api import async_playwright
from urllib.parse import urljoin

async def scrape_and_screenshot_problems():
    # url = "https://codeforces.com/problemset?tags=1700-1700"
    url = "https://codeforces.com/problemset/page/2?tags=1700-1700"
    base_url = "https://codeforces.com"
    
    output_dir = "cf_problem_screenshots"
    os.makedirs(output_dir, exist_ok=True)
    
    async with async_playwright() as p:
        print("Launching clean stealth browser environment...")
        
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ]
        )
        
        # QUALITY UPGRADE 1: Set device_scale_factor to 2 or 3 (Acts like a Retina Display)
        # This doubles or triples the pixel density of your text, images, and MathJax formulas.
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900},
            device_scale_factor=2,  # Try 3 if you want extreme print-quality resolution
            is_mobile=False,
            has_touch=False
        )
        
        page = await context.new_page()
        
        await page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        
        print(f"Navigating to the main list: {url}")
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            print("Allowing Cloudflare challenge 5 seconds to clear naturally...")
            await page.wait_for_timeout(5000)
        except Exception as e:
            print(f"Failed to clear main Cloudflare wall: {e}")
            await browser.close()
            return
        
        # Gather problem elements
        links = await page.locator('table.problems a[href*="/problemset/problem/"]').all()
        
        problem_urls = set()
        for link in links:
            href = await link.get_attribute("href")
            if href:
                full_url = urljoin(base_url, href)
                problem_urls.add(full_url)
                
        sorted_urls = sorted(list(problem_urls))
        total_problems = len(sorted_urls)
        print(f"Found {total_problems} unique problem links. Commencing high-res captures...\n")
        
        for idx, p_url in enumerate(sorted_urls, start=1):
            match = re.search(r'/problem/(\d+)/([A-Za-z0-9]+)', p_url)
            filename = f"{match.group(1)}{match.group(2)}.png" if match else f"problem_{idx}.png"
            screenshot_path = os.path.join(output_dir, filename)
            
            print(f"[{idx}/{total_problems}] Processing: {p_url}")
            try:
                await page.goto(p_url, wait_until="load", timeout=20000)
                
                if "Just a moment..." in await page.title() or await page.locator("text=Verify you are human").count() > 0:
                    print("    [!] Encountered verification intercept. Waiting 6s to auto-clear...")
                    await page.wait_for_timeout(6000)
                
                # Allow rendering for text and math symbols
                await page.wait_for_timeout(2000)
                
                # QUALITY UPGRADE 2: Inject CSS to enforce hardware-accelerated, anti-aliased font rendering
                await page.add_style_tag(content="""
                    body, * {
                        -webkit-font-smoothing: antialiased !important;
                        -moz-osx-font-smoothing: grayscale !important;
                        text-rendering: optimizeLegibility !important;
                    }
                """)
                
                # QUALITY UPGRADE 3: Maximize quality variables
                # PNG is lossless, so omitting 'quality' argument is preferred over compression artifacts from JPEG.
                await page.screenshot(
                    path=screenshot_path, 
                    full_page=True,
                    animations="disabled"  # Freezes smooth scrolling transitions for a sharper static snap
                )
                print(f"    Saved high-res: {filename}")
                
            except Exception as e:
                error_msg = str(e).split('\n')[0]
                print(f"    Skipped: {error_msg}")
                
            await page.wait_for_timeout(4000)
            
        await browser.close()
        print("\nProcess finished! Check 'cf_problem_screenshots' folder.")

if __name__ == "__main__":
    asyncio.run(scrape_and_screenshot_problems())