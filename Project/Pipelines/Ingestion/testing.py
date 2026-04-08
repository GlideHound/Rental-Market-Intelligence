from playwright.sync_api import sync_playwright
import json


def open_browser_and_fetch(url: str):
    auth_header = None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        def handle_request(request):
            nonlocal auth_header

            if request.url == "https://rentals.ca/graphql":
                headers = request.headers

                if "authorization" in headers:
                    auth_header = headers["authorization"]
                    print("Captured authorization header")

        page.on("request", handle_request)

        page.goto(url)
        page.wait_for_timeout(5000)

        if auth_header is None:
            print("Could not capture authorization header")
            browser.close()
            return None

        payload = {
            "operationName": "RentalListingSearch",
            "query": """query RentalListingSearch($last: PositiveInt, $first: PositiveInt, $place: PlaceInput!, $filters: RentalListingsConnectionFilterSet, $sortType: SortType) {
  rentalListings(
    last: $last
    first: $first
    place: $place
    filters: $filters
    sortType: $sortType
  ) {
    meta {
      ...MetaFrag
      __typename
    }
    edges {
      node {
        id
        location
        rentRange
        __typename
      }
      __typename
    }
    __typename
  }
}
fragment MetaFrag on RentalListingsMeta {
  totalCount
  totalFloorPlanCount
  __typename
}""",
            "variables": {
                "filters": {},
                "first": 2000, # max limit 2000
                "place": {
                    "namedAreaDistance": {
                        "distance": 2000, # initially 20000, change it to see the total count change
                        "namedArea": "toronto, on, ca"
                    }
                }
            }
        }

        data = page.evaluate(
            """
            async ({payload, authHeader}) => {
                const response = await fetch("https://rentals.ca/graphql", {
                    method: "POST",
                    credentials: "include",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": authHeader
                    },
                    body: JSON.stringify(payload)
                });

                return await response.json();
            }
            """,
            {"payload": payload, "authHeader": auth_header}
        )

        browser.close()
        return data


if __name__ == "__main__":
    data = open_browser_and_fetch("https://rentals.ca/toronto")
    
    if data.get("data") and data["data"].get("rentalListings"):
        meta = data["data"]["rentalListings"]["meta"]
        edges = data["data"]["rentalListings"]["edges"]
        
        print("Total count:", meta["totalCount"])
        print("Returned rows:", len(edges))
    else:
        print("Request failed")
        print(json.dumps(data, indent=2))