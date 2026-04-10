"""
Apple App Store Reviews Scraper
Source: https://github.com/glennfang/apple-app-reviews-scraper
Author: glennfang (adapted for use without cloning)
"""

import random
import requests
import re
import time
from tqdm import tqdm


def get_token(country: str, app_name: str, app_id: str, user_agents: list):
    """
    Retrieves the bearer token required for API requests.
    Regex adapted from base.py of https://github.com/cowboy-bebug/app-store-scraper
    """
    response = requests.get(
        f'https://apps.apple.com/{country}/app/{app_name}/id{app_id}',
        headers={'User-Agent': random.choice(user_agents)},
    )

    if response.status_code != 200:
        print(f"GET request failed. Response: {response.status_code} {response.reason}")

    tags = response.text.splitlines()
    token = None
    for tag in tags:
        if re.match(r"<meta.+web-experience-app/config/environment", tag):
            token = re.search(r"token%22%3A%22(.+?)%22", tag).group(1)

    print(f"Bearer {token}")
    return token


def fetch_reviews(country: str, app_name: str, app_id: str, user_agents: list, token: str, offset: str = '1'):
    """
    Fetches reviews for a given app from the Apple App Store API.

    - Default sleep after each call to reduce risk of rate limiting
    - Retry with increasing backoff if rate-limited (429)
    - No known ability to sort by date, but the higher the offset, the older the reviews tend to be
    """

    ## Define request headers and params ------------------------------------
    landing_url = f'https://apps.apple.com/{country}/app/{app_name}/id{app_id}'
    request_url = f'https://amp-api.apps.apple.com/v1/catalog/{country}/apps/{app_id}/reviews'

    headers = {
        'Accept': 'application/json',
        'Authorization': f'bearer {token}',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': 'https://apps.apple.com',
        'Referer': landing_url,
        'User-Agent': random.choice(user_agents)
    }

    params = (
        ('l', 'en-GB'),                 # language
        ('offset', str(offset)),        # paginate this offset
        ('limit', '20'),                # max valid is 20
        ('platform', 'web'),
        ('additionalPlatforms', 'appletv,ipad,iphone,mac')
    )

    ## Perform request & exception handling ----------------------------------
    retry_count = 0
    MAX_RETRIES = 5
    BASE_DELAY_SECS = 10
    # Assign dummy variables in case of GET failure
    result = {'data': [], 'next': None}
    reviews = []
    response = None

    while retry_count < MAX_RETRIES:

        # Perform request
        response = requests.get(request_url, headers=headers, params=params)

        # SUCCESS
        if response.status_code == 200:
            result = response.json()
            reviews = result.get('data', [])
            if len(reviews) < 20:
                print(f"  {len(reviews)} reviews scraped. This is fewer than the expected 20.")
            break

        # FAILURE
        elif response.status_code != 200:
            print(f"GET request failed. Response: {response.status_code} {response.reason}")

            # RATE LIMITED
            if response.status_code == 429:
                retry_count += 1
                backoff_time = BASE_DELAY_SECS * retry_count
                print(f"Rate limited! Retrying ({retry_count}/{MAX_RETRIES}) after {backoff_time} seconds...")

                with tqdm(total=backoff_time, unit="sec", ncols=50) as pbar:
                    for _ in range(backoff_time):
                        time.sleep(1)
                        pbar.update(1)
                continue

            # NOT FOUND / NO MORE REVIEWS
            elif response.status_code == 404:
                print(f"{response.status_code} {response.reason}. There are no more reviews.")
                break

            else:
                break

    ## Final output ---------------------------------------------------------
    if 'next' in result and result['next'] is not None:
        offset_match = re.search(r"^.+offset=([0-9]+).*$", result['next'])
        offset = offset_match.group(1) if offset_match else None
        print(f"  Next offset: {offset}")
    else:
        offset = None
        print("  No offset found — reached end of reviews.")

    # Append offset, number of reviews in batch, and app_id
    for rev in reviews:
        rev['offset'] = offset
        rev['n_batch'] = len(reviews)
        rev['app_id'] = app_id

    # Default sleep to decrease rate of calls
    time.sleep(0.5)

    status_code = response.status_code if response is not None else None
    return reviews, offset, status_code
