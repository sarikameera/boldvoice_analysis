"""
BoldVoice App Store Reviews Scraper
Uses the apple-app-reviews-scraper library by glennfang:
  https://github.com/glennfang/apple-app-reviews-scraper

Tested to scrape ~15,000 reviews with no rate limiting.
App ID: 1567841142 (BoldVoice - American English)
"""

import pandas as pd
import json
import os
from datetime import datetime
from apple_app_reviews_scraper import get_token, fetch_reviews

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────
COUNTRY   = 'us'
APP_NAME  = 'boldvoice-american-english'
APP_ID    = '1567841142'
MAX_PAGES = 2000        # Safety cap; reviews stop naturally when offset returns None

OUTPUT_CSV  = 'boldvoice_all_reviews.csv'
CHECKPOINT  = 'boldvoice_reviews_checkpoint.json'

USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
]

# ──────────────────────────────────────────────
# Resume from checkpoint if available
# ──────────────────────────────────────────────
all_reviews = []
start_offset = '1'

if os.path.exists(CHECKPOINT):
    print(f"📂 Checkpoint found — resuming from checkpoint...")
    with open(CHECKPOINT, 'r') as f:
        ckpt = json.load(f)
    all_reviews = ckpt['reviews']
    start_offset = ckpt['next_offset']
    print(f"   Resuming from offset {start_offset} with {len(all_reviews)} reviews already collected.")
else:
    print("🆕 No checkpoint found — starting fresh.")

# ──────────────────────────────────────────────
# Get auth token
# ──────────────────────────────────────────────
print(f"\n🔑 Fetching bearer token for {APP_NAME} (id={APP_ID}) ...")
token = get_token(COUNTRY, APP_NAME, APP_ID, USER_AGENTS)
if not token:
    print("❌ Failed to get token. Exiting.")
    exit(1)
print(f"✅ Token obtained\n")

# ──────────────────────────────────────────────
# Paginate through all reviews
# ──────────────────────────────────────────────
current_offset = start_offset
page = 1

print(f"🚀 Starting scrape — fetching up to {MAX_PAGES} pages (20 reviews/page)...")
print(f"{'='*60}")

while current_offset is not None and page <= MAX_PAGES:
    print(f"📄 Page {page:>4} | offset={current_offset} | total so far={len(all_reviews)}")

    try:
        reviews, next_offset, status = fetch_reviews(
            COUNTRY, APP_NAME, APP_ID, USER_AGENTS, token, offset=current_offset
        )
    except Exception as e:
        print(f"⚠️  Exception during fetch: {e}")
        break

    if not reviews:
        print(f"   No reviews returned on page {page}. Stopping.")
        break

    all_reviews.extend(reviews)

    # Save checkpoint periodically (every 50 pages)
    if page % 50 == 0:
        ckpt_data = {'reviews': all_reviews, 'next_offset': next_offset or ''}
        with open(CHECKPOINT, 'w') as f:
            json.dump(ckpt_data, f)
        print(f"   💾 Checkpoint saved at page {page} ({len(all_reviews)} total reviews)")

    current_offset = next_offset
    page += 1

print(f"\n{'='*60}")
print(f"✅ Scraping complete! Total raw reviews collected: {len(all_reviews)}")

# ──────────────────────────────────────────────
# Flatten & clean into DataFrame
# ──────────────────────────────────────────────
print("\n🧹 Flattening and cleaning data...")

df = pd.json_normalize(all_reviews)

# Rename columns for readability
rename_map = {
    'id':                               'review_id',
    'type':                             'type',
    'attributes.date':                  'date',
    'attributes.rating':                'rating',
    'attributes.title':                 'title',
    'attributes.review':                'review',
    'attributes.isEdited':              'is_edited',
    'attributes.userName':              'username',
    'attributes.developerResponse.id':  'dev_response_id',
    'attributes.developerResponse.body':'dev_response_body',
    'attributes.developerResponse.modified': 'dev_response_date',
    'offset':                           'next_offset',
    'n_batch':                          'batch_size',
    'app_id':                           'app_id',
}
df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}, inplace=True)

# Drop duplicates by review_id
before_dedup = len(df)
df.drop_duplicates(subset='review_id', inplace=True)
after_dedup = len(df)
print(f"   Removed {before_dedup - after_dedup} duplicate reviews. Final count: {after_dedup}")

# Parse dates
if 'date' in df.columns:
    df['date'] = pd.to_datetime(df['date'], errors='coerce', utc=True)
    df['date'] = df['date'].dt.tz_convert('US/Eastern').dt.tz_localize(None)

# Sort by date descending
if 'date' in df.columns:
    df.sort_values('date', ascending=False, inplace=True)

# Select and reorder key columns
keep_cols = ['review_id', 'date', 'rating', 'title', 'review', 'username',
             'is_edited', 'dev_response_body', 'dev_response_date', 'app_id']
keep_cols = [c for c in keep_cols if c in df.columns]
df = df[keep_cols]

# ──────────────────────────────────────────────
# Save to CSV
# ──────────────────────────────────────────────
df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
print(f"\n💾 Saved {len(df)} reviews to: {OUTPUT_CSV}")

# ──────────────────────────────────────────────
# Summary stats
# ──────────────────────────────────────────────
print(f"\n📊 Quick Summary:")
print(f"   Total reviews:   {len(df)}")
if 'date' in df.columns and not df['date'].isna().all():
    print(f"   Date range:      {df['date'].min().date()} → {df['date'].max().date()}")
if 'rating' in df.columns:
    print(f"   Avg rating:      {df['rating'].mean():.2f} ⭐")
    print(f"   Rating breakdown:")
    for r in sorted(df['rating'].unique(), reverse=True):
        count = (df['rating'] == r).sum()
        pct = 100 * count / len(df)
        bar = '█' * int(pct / 2)
        print(f"     {int(r)}⭐  {bar:<25} {count:>5} ({pct:.1f}%)")

# Clean up checkpoint now that we're done
if os.path.exists(CHECKPOINT):
    os.remove(CHECKPOINT)
    print(f"\n🗑️  Checkpoint file removed.")

print(f"\n🎉 Done! Reviews saved to '{OUTPUT_CSV}'")
