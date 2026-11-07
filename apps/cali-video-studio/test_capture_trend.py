import asyncio
from playwright.async_api import async_playwright
from pathlib import Path

ARTIFACT_DIR = Path(r"C:\Users\amber\.gemini\antigravity\brain\e60e5a8e-52b0-4d26-bd2b-653156b29d9a\screenshots")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

async def capture_verification():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        
        # 1. Video Studio (Port 8790) - Trend to Video Engine
        page1 = await context.new_page()
        print("Navigating to Video Studio on 8790...")
        await page1.goto("http://127.0.0.1:8790", wait_until="networkidle", timeout=15000)
        await page1.wait_for_timeout(1000)
        
        # Switch to Auto tab if exists
        try:
            auto_tab_btn = page1.locator("button:has-text('Autonomous'), button:has-text('Auto'), button:has-text('Trend')").first
            if await auto_tab_btn.count() > 0:
                await auto_tab_btn.click()
                await page1.wait_for_timeout(500)
            
            # Click scout live trends button
            scout_btn = page1.locator("button:has-text('Scout Live UK Trends')").first
            if await scout_btn.count() > 0:
                await scout_btn.click()
                await page1.wait_for_timeout(1500)
        except Exception as e:
            print("Tab click notice:", e)
            
        vid_shot = ARTIFACT_DIR / "Video_Studio_Trend_To_Video_Engine.png"
        await page1.screenshot(path=str(vid_shot), full_page=True)
        print("Saved Video Studio screenshot:", vid_shot)
        await page1.close()

        # 2. Central Hub (Port 8800)
        page2 = await context.new_page()
        print("Navigating to Central Hub on 8800...")
        await page2.goto("http://127.0.0.1:8800", wait_until="networkidle", timeout=15000)
        await page2.wait_for_timeout(2000)
        
        hub_shot = ARTIFACT_DIR / "Central_Hub_With_Trend_Dispatch.png"
        await page2.screenshot(path=str(hub_shot), full_page=True)
        print("Saved Central Hub screenshot:", hub_shot)
        await page2.close()

        await browser.close()
        print("Verification capture complete!")

if __name__ == "__main__":
    asyncio.run(capture_verification())

