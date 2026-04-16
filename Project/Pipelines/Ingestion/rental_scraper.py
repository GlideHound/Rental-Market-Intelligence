from playwright.sync_api import sync_playwright
import json

graphql_url = "https://rentals.ca/graphql"
target_url = "https://rentals.ca/toronto"
query = "query RentalListingSearch($after: String, $before: String, $last: PositiveInt, $first: PositiveInt, $place: PlaceInput!, $filters: RentalListingsConnectionFilterSet, $sortType: SortType, $imagesStartIndex: Int, $imagesEndIndex: Int) {\n  rentalListings(\n    after: $after\n    before: $before\n    last: $last\n    first: $first\n    place: $place\n    filters: $filters\n    sortType: $sortType\n  ) {\n    cities {\n      id\n      name\n      path\n      regionCode\n      __typename\n    }\n    meta {\n      ...MetaFrag\n      ...FocusFrag\n      __typename\n    }\n    pageInfo {\n      ...PageInfoFrag\n      __typename\n    }\n    edges {\n      node {\n        ...RentalAddressFrag\n        ...RentalFloorPlansFrag\n        ...RentalImageFrag\n        ...RentalListingFrag\n        ...RentalPromotionsBadgeFrag\n        building {\n          yearBuilt\n          yearRenovated\n          clearanceHeight\n          class\n          size\n          stories\n          totalUnits\n          isCertified\n          __typename\n        }\n        tours {\n          type\n          __typename\n        }\n        bookables {\n          name\n          url\n          type\n          __typename\n        }\n        contact {\n          name\n          phoneNumber\n          email\n          __typename\n        }\n        images(startIndex: $imagesStartIndex, endIndex: $imagesEndIndex) {\n          caption\n          tags\n          scales\n          __typename\n        }\n        priority\n        petOptions\n        type\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\nfragment RentalAddressFrag on RentalListing {\n  address {\n    city {\n      id\n      __typename\n    }\n    neighbourhood {\n      name\n      path\n      __typename\n    }\n    postalCode\n    street\n    __typename\n  }\n  __typename\n}\nfragment RentalFloorPlansFrag on RentalListing {\n  floorPlans {\n    beds\n    baths\n    rent\n    size\n    furnished\n    availability\n    externalId\n    parkingSpots\n    __typename\n  }\n  __typename\n}\nfragment FocusFrag on RentalListingsMeta {\n  focusedPlace {\n    __typename\n    ... on City {\n      id\n      location\n      name\n      slug\n      __typename\n    }\n    ... on Neighbourhood {\n      boundaries\n      id\n      location\n      name\n      slug\n      city {\n        id\n        name\n        slug\n        __typename\n      }\n      __typename\n    }\n  }\n  __typename\n}\nfragment RentalImageFrag on RentalListing {\n  image {\n    caption\n    scales\n    __typename\n  }\n  __typename\n}\nfragment RentalListingFrag on RentalListing {\n  bathsRange\n  bedsRange\n  created\n  highlightStatus\n  id\n  imagesCount\n  listingType\n  location\n  modified\n  name\n  path\n  priority\n  rentRange\n  sizeRange\n  type\n  verified\n  parking {\n    parkingTypes {\n      parkingType\n      monthlyRate\n      __typename\n    }\n    parkingSpotsPerRental\n    visitorParking\n    __typename\n  }\n  __typename\n}\nfragment MetaFrag on RentalListingsMeta {\n  totalCount\n  totalFloorPlanCount\n  __typename\n}\nfragment PageInfoFrag on PageInfo {\n  __typename\n  endCursor\n  hasNextPage\n  hasPreviousPage\n  startCursor\n}\nfragment RentalPromotionsBadgeFrag on RentalListing {\n  promotions {\n    category\n    startDate\n    endDate\n    __typename\n  }\n  __typename\n}"

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
# Purpose: 
# Parameters: 
# Returns: 
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

if __name__ == "__main__":
    open_browser()