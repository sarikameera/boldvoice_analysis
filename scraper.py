from app_store_scraper import AppStore
import pandas as pd
import sys

# App configuration
APP_NAME = "boldvoice-accent-training"
APP_ID = 1567841142
COUNTRY = "us"

def main():
    print(f"Fetching reviews for {APP_NAME} ({APP_ID}) from the {COUNTRY.upper()} App Store...")
    
    # Initialize AppStore instance
    app = AppStore(country=COUNTRY, app_name=APP_NAME, app_id=APP_ID)
    
    # Fetch all reviews
    app.review(how_many=10000) # Fetch up to 10k to be safe
    
    if not app.reviews:
        print("No reviews found or could not scrape.")
        sys.exit(0)
        
    print(f"Successfully fetched {len(app.reviews)} reviews.")
    
    # Convert to DataFrame
    df = pd.DataFrame(app.reviews)
    
    # Clean up the dataset a bit
    # Output file name
    output_file = "boldvoice_reviews.csv"
    
    # Save to CSV
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"Saved cleaned data to {output_file}")

if __name__ == "__main__":
    main()
