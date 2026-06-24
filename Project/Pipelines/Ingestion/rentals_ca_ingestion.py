import pandas as pd
import time
from playwright.sync_api import sync_playwright
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

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


# Name: 
# Purpose: 
# Parameters: 
# Returns: 
def get_cookie_dict(page):
    cookies = page.context.cookies()
    return {cookie["name"]: cookie["value"] for cookie in cookies}

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
#             graphql_url: This is the url for the graphql API
# Returns: A python dictionary that contains the authorization header
def capture_auth_header(page, graphql_url):
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
# Parameters: 
# Returns: Scraped rental listings in json format
def fetch_one_batch(page, graphql_url, auth_header, city_config, first_value, after_cursor=None):
    payload = {
        "operationName": "RentalListingSearch",
        "query": query,
        "variables": {
            "filters": {},
            "after": after_cursor,
            "first": first_value,
            "place": {
                "namedArea": city_config["named_area"]
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
# Parameters: 
# Returns: A python list that contains all the scraped data
def fetch_all_batches(page, graphql_url, auth_header, city_config, first_value=2000):
    cursor = None
    seen_ids = set()
    all_nodes = []
    batch_num = 1

    print(f"\nFetching {city_config['city']}, {city_config['province']}")

    while True:
        data = fetch_one_batch(
            page=page,
            graphql_url=graphql_url,
            auth_header=auth_header,
            city_config=city_config,
            first_value=first_value,
            after_cursor=cursor
        )

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

        print(f"\n{city_config['city']} - Batch {batch_num}")
        print("Total count:", meta["totalCount"])
        print("Rows returned:", len(edges))
        print("Has next page:", page_info["hasNextPage"])
        print("New unique rows added:", new_count)
        print("Unique total so far:", len(all_nodes))

        if not page_info["hasNextPage"]:
            break

        cursor = page_info["endCursor"]
        batch_num += 1

    return all_nodes


# Name: build_df()
# Purpose: This function flattens the dictionaries and lists in the returned json data file
#          and put them into the corresponding columns of a created pandas dataframe
# Parameters: all_nodes (list): This is the list of all the nodes extracted
# Returns: A pandas dataframe that contains all the data returned by API call
def build_df(all_nodes: list, city_config: dict):

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
            "city": city_config["city"],
            "province": city_config["province"],
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


# Name:
# Purpose: 
# Parameters: 
# Returns: 
def fetch_city_with_browser(graphql_url, city_config, first_value):
    p = None
    browser = None

    try:
        print(f"\nStarting browser for {city_config['city']}, {city_config['province']}")

        p, browser, page = open_browser(city_config["target_url"])
        auth_header = capture_auth_header(page, graphql_url)

        if auth_header is None:
            raise RuntimeError("Did not capture authorization header")

        all_nodes = fetch_all_batches(
            page=page,
            graphql_url=graphql_url,
            auth_header=auth_header,
            city_config=city_config,
            first_value=first_value
        )

        df = build_df(all_nodes, city_config)

        print(f"\nFinished {city_config['city']}: {len(df)} rows")

        return df

    finally:
        if browser is not None:
            browser.close()

        if p is not None:
            p.stop()


# Name: run_ingestion()
# Purpose: run_ingestion() wires up everything in rentals_ca_ingestion script and serves as
#          the purpose of the driver function
# Parameters: config: The configurations in config.yml
# Returns: None
def run_ingestion(config):
    rentals_config = config["rentals_ca"]

    graphql_url = rentals_config["graphql_url"]
    first_value = rentals_config["first_value"]
    cities = rentals_config["cities"]
    output_file = rentals_config["output_file"]
    max_workers = rentals_config.get("max_workers", 3)

    start_time = time.time()

    city_dfs = []
    failed_cities = []

    # First pass: parallel scraping
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_city = {
            executor.submit(
                fetch_city_with_browser,
                graphql_url,
                city_config,
                first_value
            ): city_config
            for city_config in cities
        }

        for future in as_completed(future_to_city):
            city_config = future_to_city[future]

            try:
                df_city = future.result()
                city_dfs.append(df_city)

            except Exception as error:
                print(f"\nFailed to fetch {city_config['city']}, {city_config['province']}")
                print("Error type:", type(error).__name__)
                print("Error message:", error)
                failed_cities.append(city_config)

    # Second pass: slow retry
    retry_failed_cities = []

    if failed_cities:
        print("\nRetrying failed cities one by one...\n")

        for city_config in failed_cities:
            try:
                print(f"Retrying {city_config['city']}, {city_config['province']}")

                time.sleep(5)

                df_city = fetch_city_with_browser(
                    graphql_url=graphql_url,
                    city_config=city_config,
                    first_value=first_value
                )

                city_dfs.append(df_city)
                print(f"Retry succeeded for {city_config['city']}, {city_config['province']}")

            except Exception as error:
                print(f"\nRetry failed for {city_config['city']}, {city_config['province']}")
                print("Error type:", type(error).__name__)
                print("Error message:", error)
                retry_failed_cities.append(city_config)

    if not city_dfs:
        print("No city data was successfully fetched.")
        return

    df = pd.concat(city_dfs, ignore_index=True)

    before_dedup = len(df)
    df = df.drop_duplicates(subset=["listing_id"])
    after_dedup = len(df)

    print(f"\nRows before deduplication: {before_dedup}")
    print(f"Rows after deduplication: {after_dedup}")
    print(f"Duplicates removed: {before_dedup - after_dedup}")

    if retry_failed_cities:
        print("\nCities that still failed after retry:")
        for city in retry_failed_cities:
            print(f"- {city['city']}, {city['province']}")

    elapsed_seconds = time.time() - start_time
    print(f"\nIngestion completed in {elapsed_seconds:.2f} seconds")

    base_dir = Path(__file__).resolve().parents[2]
    output_path = base_dir / "Data" / "Raw" / output_file
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_parquet(output_path, index=False)

    print(f"\nSaved combined rentals data to: {output_path}")