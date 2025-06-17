import requests
from bs4 import BeautifulSoup
import csv
import time
import re

# NOTE: Facebook Ad Library uses dynamic content and may require Selenium for reliable scraping.
# This script uses requests and BeautifulSoup for simplicity, but may need Selenium if results are incomplete.

SEARCH_TERM = "skincare"  # Change this to your industry/keyword
RESULTS_LIMIT = 10
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

def extract_days_running(text):
    # Example: 'Running for 420 days'
    match = re.search(r'Running for (\d+) days', text)
    return int(match.group(1)) if match else 0

def scrape_ads(search_term):
    ads = []
    base_url = "https://www.facebook.com/ads/library/"
    params = {
        "active_status": "all",
        "ad_type": "all",
        "country": "ALL",
        "q": search_term,
        "sort_data[direction]": "desc",
        "sort_data[mode]": "relevancy_monthly_grouped",
        "media_type": "image"
    }

    response = requests.get(base_url, params=params, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Ad containers may differ, so adjust selectors as needed
    for ad_div in soup.find_all("div", class_=re.compile(r"^.*AdLibraryAd__*")):
        try:
            # Extract ad text/headline
            text = ad_div.find("div", class_=re.compile(r"^.*AdLibraryAdCreative__*")).get_text(separator=" ").strip()
            
            # Start date (look for something like "Started running on ...")
            start_date_elem = ad_div.find(string=re.compile(r"Started running on"))
            start_date = start_date_elem.strip() if start_date_elem else "N/A"
            
            # How long running (look for "Running for X days")
            running_elem = ad_div.find(string=re.compile(r"Running for \d+ days"))
            days_running = extract_days_running(running_elem) if running_elem else 0

            # Image URL (look for img tag with src)
            img_tag = ad_div.find("img")
            img_url = img_tag["src"] if img_tag else "N/A"
            
            # Ad preview link
            preview_link_tag = ad_div.find("a", href=True)
            ad_link = "https://www.facebook.com" + preview_link_tag["href"] if preview_link_tag else "N/A"
            
            ads.append({
                "headline": text,
                "start_date": start_date,
                "days_running": days_running,
                "image_url": img_url,
                "ad_link": ad_link,
            })
        except Exception as e:
            continue  # Skip incomplete ads

    return ads

def print_table(ads):
    print(f"{'Days':<6} {'Start Date':<25} {'Headline':<60} {'Image URL':<50} {'Ad Link'}")
    print("=" * 170)
    for ad in ads:
        print(f"{ad['days_running']:<6} {ad['start_date']:<25} {ad['headline'][:55]:<60} {ad['image_url'][:47]:<50} {ad['ad_link']}")

def save_csv(ads, filename="fb_ads.csv"):
    with open(filename, "w", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["headline", "start_date", "days_running", "image_url", "ad_link"])
        writer.writeheader()
        for ad in ads:
            writer.writerow(ad)

if __name__ == "__main__":
    print(f"Searching Facebook Ad Library for: {SEARCH_TERM}")
    ads = scrape_ads(SEARCH_TERM)
    # Only image ads & sort by days_running desc
    ads = [ad for ad in ads if ad['image_url'] != "N/A"]
    ads = sorted(ads, key=lambda x: x['days_running'], reverse=True)[:RESULTS_LIMIT]
    if not ads:
        print("No ads found. The Facebook Ad Library may require Selenium for scraping dynamic content.")
    else:
        print_table(ads)
        save_csv(ads)
        print(f"\nResults saved to fb_ads.csv")