"""
Scrapes BoldVoice App Store reviews using the iTunes RSS API.
Extracts up to 500 reviews (10 pages × 50 reviews) without auth.
Also tries the amp-api with a default credential approach.
"""
import requests
import pandas as pd
import json
import time
import random
from datetime import datetime

APP_ID = '1567841142'
COUNTRY = 'us'
OUTPUT_CSV = 'boldvoice_all_reviews.csv'

print("=" * 60)
print("BoldVoice Review Scraper (iTunes RSS Feed)")
print("=" * 60)

all_reviews = []

# ── Method 1: iTunes RSS Feed (most recent 500) ───────────────
print("\n📡 Fetching via iTunes RSS API (up to 500 reviews)...")

for page in range(1, 11):
    url = f'https://itunes.apple.com/{COUNTRY}/rss/customerreviews/page={page}/id={APP_ID}/sortby=mostrecent/json'
    headers = {
        'User-Agent': 'iTunes/12.0 (Macintosh; Intel Mac OS X 13_4)',
        'Accept': 'application/json',
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            print(f"  Page {page}: HTTP {resp.status_code} — stopping")
            break
        
        data = resp.json()
        entries = data.get('feed', {}).get('entry', [])
        
        # Page 1 has an extra entry (the app info itself) — skip it
        if page == 1 and entries:
            # Filter out non-review entries
            entries = [e for e in entries if 'im:rating' in e]
        
        if not entries:
            print(f"  Page {page}: no reviews — stopping")
            break
        
        for entry in entries:
            review = {
                'review_id': entry.get('id', {}).get('label', ''),
                'date': entry.get('updated', {}).get('label', ''),
                'rating': int(entry.get('im:rating', {}).get('label', 0)),
                'title': entry.get('title', {}).get('label', ''),
                'review': entry.get('content', {}).get('label', ''),
                'username': entry.get('author', {}).get('name', {}).get('label', ''),
                'version': entry.get('im:version', {}).get('label', ''),
                'vote_count': entry.get('im:voteCount', {}).get('label', ''),
                'vote_sum': entry.get('im:voteSum', {}).get('label', ''),
                'source': 'rss',
            }
            all_reviews.append(review)
        
        print(f"  Page {page}: {len(entries)} reviews (total: {len(all_reviews)})")
        time.sleep(0.3)
    
    except Exception as e:
        print(f"  Page {page}: Error — {e}")
        break

print(f"\n✅ RSS scrape complete: {len(all_reviews)} reviews collected")

# ── Flatten & clean ───────────────────────────────────────────
print("\n🧹 Cleaning data...")
df = pd.DataFrame(all_reviews)

if df.empty:
    print("❌ No reviews collected!")
    exit(1)

# Parse dates
df['date'] = pd.to_datetime(df['date'], errors='coerce', utc=True)
df['date'] = df['date'].dt.tz_convert('US/Eastern').dt.tz_localize(None)

# Convert rating to int
df['rating'] = pd.to_numeric(df['rating'], errors='coerce').fillna(0).astype(int)

# Drop duplicates
before = len(df)
df.drop_duplicates(subset='review_id', inplace=True)
after = len(df)
print(f"  Removed {before - after} duplicates. Final: {after} reviews")

# Sort by date descending
df.sort_values('date', ascending=False, inplace=True, ignore_index=True)

# Save
df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
print(f"\n💾 Saved {len(df)} reviews to: {OUTPUT_CSV}")

# ── Summary ───────────────────────────────────────────────────
print(f"\n📊 Summary:")
print(f"  Total reviews:  {len(df)}")
if not df['date'].isna().all():
    print(f"  Date range:     {df['date'].min().date()} → {df['date'].max().date()}")
print(f"  Avg rating:     {df['rating'].mean():.2f} ⭐")
print(f"  Rating breakdown:")
for r in sorted(df['rating'].unique(), reverse=True):
    count = (df['rating'] == r).sum()
    pct = 100 * count / len(df)
    bar = '█' * int(pct / 2)
    print(f"    {int(r)}⭐  {bar:<25} {count:>5} ({pct:.1f}%)")

print(f"\n🎉 Done! File saved to '{OUTPUT_CSV}'")
