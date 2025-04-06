import asyncio
from playwright.async_api import async_playwright
import csv
import os

async def scrape_all_pages():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        base_url = "https://www.shl.com/solutions/products/product-catalog/"
        all_data = []
        visited_pages = set()

        await page.goto(base_url)

        while True:
            try:
                await page.wait_for_selector("tr[data-course-id]", timeout=60000)
            except:
                print("⚠️ Timeout waiting for course rows. Skipping this page.")
                break

            rows = await page.locator("tr[data-course-id]").all()
            print(f"📦 Found {len(rows)} assessments on this page.")

            for row in rows:
                role = await row.locator("td.custom__table-heading__title a").inner_text()
                href = await row.locator("td.custom__table-heading__title a").get_attribute("href")
                full_link = "https://www.shl.com" + href

                # ✅ Remote Testing
                remote_test = await row.locator("td:nth-child(2) span.catalogue__circle.-yes").count()
                is_remote = "✅" if remote_test > 0 else "❌"

                # ✅ Adaptive/IRT
                adaptive = await row.locator("td:nth-child(3) span.catalogue__circle.-yes").count()
                is_adaptive = "✅" if adaptive > 0 else "❌"

                # ✅ Test Type Codes
                type_cells = await row.locator("td.product-catalogue__keys span.product-catalogue__key").all()
                type_codes = [await tag.inner_text() for tag in type_cells]

                # 🧠 Visit Detail Page
                detail_page = await browser.new_page()
                try:
                    await detail_page.goto(full_link, timeout=60000)
                    await detail_page.wait_for_selector("div[data-course-id]", timeout=10000)

                    # Extract all description rows
                    desc_blocks = await detail_page.locator("div[data-course-id] .product-catalogue-training-calendar__row.typ").all()
                    description_lines = [await d.inner_text() for d in desc_blocks if await d.inner_text()]
                    description = "\n".join(description_lines)

                    # Try to extract duration if any line mentions minutes
                    duration = ""
                    for line in description_lines:
                        if "minute" in line.lower():
                            duration = line.strip()
                            break

                except Exception as e:
                    print(f"❌ Failed to extract detail from {full_link}: {e}")
                    description = ""
                    duration = ""

                await detail_page.close()

                # Store everything
                all_data.append({
                    "role": role.strip(),
                    "link": full_link,
                    "remote_testing": is_remote,
                    "adaptive_irt": is_adaptive,
                    "test_types": ", ".join(type_codes),
                    "duration": duration,
                    "description": description
                })

            # 🔁 Handle pagination safely
            next_links = await page.locator("ul.pagination a.pagination__link").all()
            next_href = None
            for link in next_links:
                href = await link.get_attribute("href")
                full_url = "https://www.shl.com" + href if href else None
                if full_url and full_url not in visited_pages:
                    next_href = href
                    visited_pages.add(full_url)
                    break

            if not next_href:
                print("✅ No more pages.")
                break

            next_url = "https://www.shl.com" + next_href
            print(f"➡️ Navigating to: {next_url}")
            await page.goto(next_url, timeout=60000)

        await browser.close()

        if not all_data:
            print("⚠️ No data collected. Skipping file save.")
            return

        # 💾 Save to CSV with new fields
        filename = "shl_detailed_enriched.csv"
        with open(filename, "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "role", "link", "remote_testing", "adaptive_irt", "test_types", "duration", "description"
            ])
            writer.writeheader()
            writer.writerows(all_data)

        print(f"\n🎉 Finished! Scraped {len(all_data)} enriched assessments.")
        print(f"📁 CSV saved to: {os.path.abspath(filename)}")

# Run it
asyncio.run(scrape_all_pages())
