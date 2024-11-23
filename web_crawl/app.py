import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
from urllib.parse import urljoin
import logging
import os

# Set up logging
logging.basicConfig(
    filename="crawler.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Custom headers to mimic a browser
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"
}

# Broad set of keywords for identifying "features" and "pricing" URLs
keywords = {
    "features": ["feature", "features", "spec", "specification", "overview", "capabilities", "function", "functions", "services", "solutions", "benefits"],
    "pricing": ["pricing", "price", "plan", "plans", "subscription", "cost", "rates", "fees", "packages", "billing", "quotes", "quote"]
}

def validate_url(url):
    """Validate the input URL."""
    if not url.startswith(("http://", "https://")):
        return False
    return True

def find_feature_pricing_urls(base_url):
    """Find features and pricing URLs from the given base URL."""
    try:
        response = requests.get(base_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a', href=True)

        urls = {"features": None, "pricing": None}
        for link in links:
            href = link['href'].lower()
            full_url = urljoin(base_url, link['href'])

            if "example.com" not in full_url:
                for key, terms in keywords.items():
                    if any(term in href for term in terms):
                        if key == "features" and "overview" in href and urls[key] is None:
                            urls[key] = full_url
                        elif urls[key] is None:
                            urls[key] = full_url

            if urls["features"] and urls["pricing"]:
                break

        return urls
    except requests.exceptions.RequestException as e:
        logging.error(f"Error retrieving the page {base_url}: {e}")
        return {}

def append_to_csv(input_url, features_url, pricing_url, status, filename):
    """Append crawl data to the specified CSV file."""
    try:
        if not os.path.exists(filename):
            pd.DataFrame(columns=["Input URL", "Features URL", "Pricing URL", "Status"]).to_csv(filename, index=False)
        
        df = pd.read_csv(filename)
        new_row = {"Input URL": input_url, "Features URL": features_url, "Pricing URL": pricing_url, "Status": status}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(filename, index=False)
        logging.info(f"Data saved for {input_url} - Status: {status}")
    except Exception as e:
        logging.error(f"Error writing to CSV: {e}")

# Streamlit interface
st.title("Automated Features and Pricing Crawler")

input_url = st.text_input("Enter the website URL:")
output_file = st.text_input("Enter the output file name (e.g., data.csv):", value="features_pricing_crawler_data.csv")
if st.button("Start Crawling"):
    if input_url and output_file:
        if validate_url(input_url):
            st.write("Crawling started...")

            urls = find_feature_pricing_urls(input_url)
            status = "Success" if urls else "No URLs Found"
            
            append_to_csv(
                input_url,
                urls.get("features", "Not Found"),
                urls.get("pricing", "Not Found"),
                status,
                output_file
            )

            if urls:
                st.write("Crawling complete. Results saved to:", output_file)
                st.write(pd.DataFrame([{
                    "Input URL": input_url,
                    "Features URL": urls.get("features", "Not Found"),
                    "Pricing URL": urls.get("pricing", "Not Found"),
                    "Status": status
                }]))
            else:
                st.error("No 'features' or 'pricing' URLs found on the page.")
        else:
            st.warning("Invalid URL. Please enter a valid URL starting with http:// or https://.")
    else:
        st.warning("Please enter a URL and output file name to crawl.")
