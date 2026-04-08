from playwright.sync_api import sync_playwright
import pandas as pd

# listens and captures the graphql api response, converts api response into data
# Name: open_browser()
# Purpose: This function opens a headless chrome browser, accesses the rental.ca website and calls
#          the API to scrape data
# Parameters: url (str): This is the url of the website we wish to scrape
# Returns: One python list with all the scraped data
def open_browser(url: str):
    items = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # listens and captures the graphql api response, converts api response into data
        def handle_response(response):
            if response.url == "https://rentals.ca/graphql":
                try:
                    data = response.json()
                except Exception:
                    return

                if "rentalListings" in data.get("data", {}):
                    print("This is the listings response")

                    edges = data["data"]["rentalListings"]["edges"]

                    # testing purpose
                    meta = data["data"]["rentalListings"]["meta"]
                    print("Total count:", meta["totalCount"])

                    for edge in edges:
                        node = edge["node"]

                        # Store results in a cleaned python dictionary
                        item = {
                            "id": node.get("id"),
                            "longitude": node["location"][0],
                            "latitude": node["location"][1],
                            "rent_min": node["rentRange"][0],
                            "rent_max": node["rentRange"][1]
                        }
                        items.append(item)

        page.on("response", handle_response)

        page.goto(url)
        page.wait_for_timeout(5000)
        input("Press Enter to close")
        browser.close()

    return items


def output_data(items):
    df = pd.DataFrame(items)
    df = df.drop_duplicates(subset=["id"])
    print(df.head())
    print(f"Total rows: {len(df)}")
    return df


if __name__ == "__main__":
    items = open_browser("https://rentals.ca/toronto")
    df = output_data(items)