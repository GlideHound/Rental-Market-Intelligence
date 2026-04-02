from playwright.sync_api import sync_playwright
import json
import pandas as pd

# listens and captures the graphql api response, converts api response into data
# Name:
# Purpose:
# Parameters:
# Returns:
def handle_response(response):
    # create the empty list item, we will append to it later
    items = []

    if response.url == "https://rentals.ca/graphql":
        data = response.json()

        if "rentalListings" in data.get("data", {}):
            print("This is the listings response")

            edges = data["data"]["rentalListings"]["edges"]
            
            for edge in edges:
                node = edge["node"]

                # Store results in a cleaned python dictionary
                item = {
                    "id": node["id"],
                    "longitude": node["location"][0],
                    "latitude": node["location"][1],
                    "rent_min": node["rentRange"][0],
                    "rent_max": node["rentRange"][1]
                }
                items.append(item)


def open_browser(url: str):
    items = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # listens and captures the graphql api response, converts api response into data
        def handle_response(response):
            if response.url == "https://rentals.ca/graphql":
                data = response.json()
                
                if "rentalListings" in data.get("data", {}):
                    print("This is the listings response")
                    
                    edges = data["data"]["rentalListings"]["edges"]
                    
                    for edge in edges:
                        node = edge["node"]
                        
                        # Store results in a cleaned python dictionary
                        item = {
                            "id": node["id"],
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

if __name__ == "__main__":
    items = open_browser("https://rentals.ca/toronto")
    output_data(items)