import asyncio
from playwright.async_api import async_playwright

async def scrape_all_pages():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Set True for headless
        page = await browser.new_page()
        base_url = "https://www.shl.com/solutions/products/product-catalog/"
        all_data = []
        visited_pages = set()

        await page.goto(base_url)

        while True:
            try:
                await page.wait_for_selector("tr[data-course-id]", timeout=60000)  # ⏳ Increased timeout
            except:
                print("⚠️ Timeout waiting for course rows. Skipping this page.")
                break

            rows = await page.locator("tr[data-course-id]").all()
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

                all_data.append({
                    "role": role.strip(),
                    "link": full_link,
                    "remote_testing": is_remote,
                    "adaptive_irt": is_adaptive,
                    "test_types": ", ".join(type_codes)
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

        # 💾 Save to CSV
        import csv
        with open("shl_detailed_assessments.csv", "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["role", "link", "remote_testing", "adaptive_irt", "test_types"])
            writer.writeheader()
            writer.writerows(all_data)

        print(f"\n🎉 Finished! Scraped {len(all_data)} assessments with details.")

asyncio.run(scrape_all_pages())
