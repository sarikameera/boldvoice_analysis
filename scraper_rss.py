import requests
import pandas as pd
import sys
import time

APP_ID = "1567841142"
COUNTRY = "us"

def fetch_reviews():
    all_reviews = []
    
    print(f"Fetching reviews for App ID {APP_ID} from iTunes RSS...")
    # Apple RSS feed limits at 10 pages (each has max 50 reviews)
    for page in range(1, 11):
        url = f"https://itunes.apple.com/{COUNTRY}/rss/customerreviews/page={page}/id={APP_ID}/sortby=mostrecent/json"
        
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                print(f"Error fetching page {page}: Status {resp.status_code}")
                break
                
            data = resp.json()
            # The structure is data['feed']['entry']
            feed = data.get("feed", {})
            entries = feed.get("entry", [])
            
            # If there's no entries (e.g. fewer than 10 pages total)
            if not entries:
                print(f"Reached end of reviews at page {page}.")
                break
                
            # If the response just has 1 entry, it might be a dict instead of a list (Apple metadata),
            # but usually it's a list. The first item in the list on page 1 is sometimes the app info.
            for entry in entries:
                # App info entry doesn't have author name label as standard review
                if 'author' in entry and 'name' in entry['author']:
                    review = {
                        "date": entry.get("updated", {}).get("label", ""),
                        "rating": entry.get("im:rating", {}).get("label", ""),
                        "title": entry.get("title", {}).get("label", ""),
                        "review": entry.get("content", {}).get("label", ""),
                        "version": entry.get("im:version", {}).get("label", ""),
                        "author": entry.get("author", {}).get("name", {}).get("label", "")
                    }
                    if review["rating"]: # ensure it's a user review
                        all_reviews.append(review)
            
            print(f"Fetched page {page}... Total reviews so far: {len(all_reviews)}")
            time.sleep(1) # Be polite
            
        except Exception as e:
            print(f"Failed to parse page {page}: {e}")
            break
            
    if not all_reviews:
        print("No reviews found.")
        sys.exit(0)
        
    df = pd.DataFrame(all_reviews)
    output_file = "boldvoice_reviews_cleaned.csv"
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"\nSuccess! Saved {len(df)} reviews to {output_file}")

if __name__ == "__main__":
    fetch_reviews()
