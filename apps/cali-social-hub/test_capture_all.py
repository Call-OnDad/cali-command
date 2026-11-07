import asyncio
from playwright.async_api import async_playwright
from pathlib import Path

ARTIFACT_DIR = Path(r"C:\Users\amber\.gemini\antigravity\brain\e60e5a8e-52b0-4d26-bd2b-653156b29d9a\screenshots")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

async def capture_all():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})

        # 1. Social Hub (Port 8793)
        page1 = await context.new_page()
        await page1.goto("http://127.0.0.1:8793", wait_until="networkidle", timeout=15000)
        await page1.wait_for_timeout(1000)
        shot1 = ARTIFACT_DIR / "Social_Hub_Approval_And_Drafts.png"
        await page1.screenshot(path=str(shot1), full_page=True)
        print("Captured Social Hub:", shot1)
        
        # Test clicking on View Live Proof to see verified modal
        try:
            proof_btn = page1.locator("a:has-text('View Verified Receipt'), a:has-text('Live Proof')").first
            if await proof_btn.count() > 0:
                await proof_btn.click()
                await page1.wait_for_timeout(600)
                shot_proof = ARTIFACT_DIR / "Social_Hub_Verified_Receipt_Modal.png"
                await page1.screenshot(path=str(shot_proof), full_page=True)
                print("Captured Live Proof Modal:", shot_proof)
        except Exception as e:
            print("Modal click notice:", e)

        await page1.close()

        # 2. Community Sites & Shop (Port 8795)
        page2 = await context.new_page()
        await page2.goto("http://127.0.0.1:8795", wait_until="networkidle", timeout=15000)
        await page2.wait_for_timeout(1000)
        shot2 = ARTIFACT_DIR / "Community_Shop_With_New_Guide.png"
        await page2.screenshot(path=str(shot2), full_page=True)
        print("Captured Community Shop:", shot2)
        await page2.close()

        # 3. Central Hub (Port 8800)
        page3 = await context.new_page()
        await page3.goto("http://127.0.0.1:8800", wait_until="networkidle", timeout=15000)
        await page3.wait_for_timeout(1000)
        shot3 = ARTIFACT_DIR / "Central_Hub_Working_Links_And_Published.png"
        await page3.screenshot(path=str(shot3), full_page=True)
        print("Captured Central Hub:", shot3)
        await page3.close()

        await browser.close()
        print("All verification captures completed successfully!")

if __name__ == "__main__":
    asyncio.run(capture_all())

