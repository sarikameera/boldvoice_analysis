"""
Uses Playwright (non-headless) to navigate the App Store and intercept 
the bearer token from amp-api network requests.
"""
import asyncio
import sys
from playwright.async_api import async_playwright

TOKEN_FILE = 'apple_bearer_token.txt'

async def capture_token():
    token = None
    found = asyncio.Event()

    async with async_playwright() as p:
        # Use non-headless to ensure JS renders fully
        browser = await p.chromium.launch(headless=False, args=['--no-sandbox'])
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15',
            locale='en-US',
        )

        page = await context.new_page()

        # Listen for ALL requests
        def on_request(request):
            nonlocal token
            if 'amp-api.apps.apple.com' in request.url and not found.is_set():
                auth = request.headers.get('authorization', '')
                if auth.lower().startswith('bearer '):
                    token = auth[len('bearer '):]
                    print(f"✅ Token captured ({len(token)} chars): {token[:50]}...")
                    found.set()

        page.on('request', on_request)

        print("🌐 Loading App Store page...")
        await page.goto(
            'https://apps.apple.com/us/app/boldvoice-accent-training/id1567841142',
            wait_until='networkidle',
            timeout=30000
        )

        # Scroll to trigger lazy loading of reviews
        print("📜 Scrolling to trigger review API requests...")
        for i in range(10):
            if found.is_set():
                break
            await page.evaluate(f"window.scrollTo(0, {(i+1) * 400})")
            await page.wait_for_timeout(1000)

        if not found.is_set():
            # Navigate to reviews page
            print("🔄 Trying reviews page...")
            await page.goto(
                'https://apps.apple.com/us/app/boldvoice-accent-training/id1567841142?see-all=reviews',
                wait_until='networkidle',
                timeout=30000
            )
            for i in range(10):
                if found.is_set():
                    break
                await page.evaluate(f"window.scrollTo(0, {(i+1) * 400})")
                await page.wait_for_timeout(1000)

        await browser.close()

    if token:
        with open(TOKEN_FILE, 'w') as f:
            f.write(token)
        print(f"\n💾 Token saved to {TOKEN_FILE}")
        return token
    else:
        print("❌ Could not capture token from network requests.")
        return None

if __name__ == '__main__':
    token = asyncio.run(capture_token())
    if not token:
        sys.exit(1)
