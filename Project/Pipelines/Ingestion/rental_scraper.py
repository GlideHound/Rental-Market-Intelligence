from playwright.sync_api import sync_playwright
from pathlib import Path
import pandas as pd
import json

# currently it gets the listings for city of toronto

graphql_url = "https://rentals.ca/graphql"
target_url = "https://rentals.ca/toronto"
query = """
query RentalListingSearch(
  $after: String,
  $before: String,
  $last: PositiveInt,
  $first: PositiveInt,
  $place: PlaceInput!,
  $filters: RentalListingsConnectionFilterSet,
  $sortType: SortType
) {
  rentalListings(
    after: $after
    before: $before
    last: $last
    first: $first
    place: $place
    filters: $filters
    sortType: $sortType
  ) {
    meta {
      totalCount
      totalFloorPlanCount
    }
    pageInfo {
      endCursor
      hasNextPage
      hasPreviousPage
      startCursor
    }
    edges {
      node {
        id
        name
        path
        created
        modified
        highlightStatus
        imagesCount
        listingType
        type
        verified
        priority
        petOptions
        location
        rentRange
        bedsRange
        bathsRange
        sizeRange

        address {
          postalCode
          street
          neighbourhood {
            name
            path
          }
          city {
            id
          }
        }

        parking {
          parkingTypes {
            parkingType
            monthlyRate
          }
          parkingSpotsPerRental
          visitorParking
        }

        building {
          yearBuilt
          yearRenovated
          stories
          totalUnits
          isCertified
        }
      }
    }
  }
}
"""

# Name: open_browser()
# Purpose: This function opens playwright, creates a page and goes to the url to bypass cloudflare
# Parameters: url (str): This is the url of the website we wish to scrape
# Returns: playwright controller, headless chrome browser and the page we interact with
def open_browser(url: str):
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto(url)

    return p, browser, page

# Name: capture_auth_header()
# Purpose: This function listens to the request and captures the authorization in graphql response
#          headers and returns it
# Parameters: page : This is the tab with the website url
# Returns: A python dictionary that contains the authorization header
def capture_auth_header(page):
    auth_state = {"auth_header": None}

    # helper function
    def handle_request(request):
        if request.url == graphql_url:
            headers = request.headers
            if "authorization" in headers:
                auth_state["auth_header"] = headers["authorization"]
                print("Captured authorization header")

    page.on("request", handle_request)
    page.reload()
    page.wait_for_timeout(5000)

    return auth_state["auth_header"]

# Name: fetch_one_batch()
# Purpose: This function defines the payload and sends api request to get one batch of data returned
#          in json format
# Parameters: page: This is the tab opened with the website url
#             auth_header: This is the authorization header we captured
#             first_value: This is the maximum number of entries of data we want in a batch
#             after_cursor: This is the after cursor key we will use later in pagination
# Returns: Scraped rental listings in json format
def fetch_one_batch(page, auth_header, first_value, after_cursor=None):
    payload = {
        "operationName": "RentalListingSearch",
        "query": query,
        "variables": {
            "filters": {},
            "after": after_cursor,
            "first": first_value,
            "place": {
                "namedArea": "toronto, on, ca"
            },
            "sortType": "cheapest"
        }
    }

    data = page.evaluate(
        """
        async ({graphqlUrl, authHeader, payload}) => {
            const response = await fetch(graphqlUrl, {
                method: "POST",
                credentials: "include",
                headers: {
                    "content-type": "application/json",
                    "authorization": authHeader
                },
                body: JSON.stringify(payload)
            });
            
            return await response.json();
        }
        """,
        {
            "graphqlUrl": graphql_url,
            "authHeader": auth_header,
            "payload": payload
        }
    )

    return data

# Name: fetch_all_batches()
# Purpose: This function loops through all the batches and returns the scraped data
# Parameters: page: This is the tab opened with the website url
#             auth_header: This is the authorization header we captured
#             first_value: This is the maximum number of entries of data we want in a batch
# Returns: A python list that contains all the scraped data
def fetch_all_batches(page, auth_header, first_value=2000):
    cursor = None
    seen_ids = set()
    all_nodes = []
    batch_num = 1

    while True:
        data = fetch_one_batch(page, auth_header, first_value, cursor)

        rental_listings = data["data"]["rentalListings"]
        meta = rental_listings["meta"]
        edges = rental_listings["edges"]
        page_info = rental_listings["pageInfo"]

        new_count = 0

        for edge in edges:
            node = edge["node"]
            listing_id = node["id"]

            if listing_id in seen_ids:
                continue

            seen_ids.add(listing_id)
            all_nodes.append(node)
            new_count += 1
        
        # can delete or comment out later since these are for sanity check purpose
        print(f"\nBatch {batch_num}")
        print("Total count:", meta["totalCount"])
        print("Rows returned:", len(edges))
        print("Has next page:", page_info["hasNextPage"])
        print("End cursor:", page_info["endCursor"])
        print("New unique rows added:", new_count)
        print("Unique total so far:", len(all_nodes))

        if page_info["hasNextPage"] == False:
            break

        cursor = page_info["endCursor"]
        batch_num += 1

    return all_nodes

# Name: build_df()
# Purpose: This function builds the pandas df
# Parameters: 
# Returns:
def build_df(all_nodes: list):

    def extract_row(node):
        address = node.get("address", {})
        location = node.get("location") or [None, None]
        rentRange = node.get("rentRange") or [None, None]
        bedsRange = node.get("bedsRange") or [None, None]
        bathRange = node.get("bathsRange") or [None, None]
        sizeRange = node.get("sizeRange") or [None, None]

        return {
            "name": node["name"],
            "listing_id": node["id"],
            "street": address.get("street"),
            "postal_code": address.get("postalCode"),
            "longitude": location[0] if len(location) > 0 else None,
            "latitude": location[1] if len(location) > 1 else None,
            "rent_min": rentRange[0],
            "rent_max": rentRange[1],
            "beds_min": bedsRange[0],
            "beds_max": bedsRange[1],
            "bath_min": bathRange[0],
            "bath_max": bathRange[1],
            "size_min": sizeRange[0] if len(sizeRange) > 0 else None,
            "size_max": sizeRange[1] if len(sizeRange) > 1 else None,
            "created_date": node["created"],
            "modified_date": node["modified"],
            "highlight_status": node["highlightStatus"],
            "images_count": node["imagesCount"],
            "property_type": node["type"],
            "verified": node["verified"]
        }
    
    rows = [extract_row(node) for node in all_nodes]
    df = pd.DataFrame(rows)

    return df


# Name: main()
# Purpose: The driver function
# Parameters: None
# Returns: None
def main():
    p, browser, page = open_browser(target_url)
    auth_header = capture_auth_header(page)

    if auth_header is None:
        print("Did not capture authorization header")
        browser.close()
        p.stop()
        return

    all_nodes = fetch_all_batches(page, auth_header, first_value=2000)
    df = build_df(all_nodes)
    
    base_dir = Path(__file__).resolve().parents[2]
    output_path = base_dir / "Data" / "Raw" / "toronto_rentals.parquet"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)

    browser.close()
    p.stop()

if __name__ == "__main__":
    main()