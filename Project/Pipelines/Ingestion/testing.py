from playwright.sync_api import sync_playwright
import json

GRAPHQL_URL = "https://rentals.ca/graphql"
TARGET_URL = "https://rentals.ca/toronto"

QUERY = """
query RentalListingSearch($after: String, $before: String, $last: PositiveInt, $first: PositiveInt, $place: PlaceInput!, $filters: RentalListingsConnectionFilterSet, $sortType: SortType, $imagesStartIndex: Int, $imagesEndIndex: Int) {
  rentalListings(
    after: $after
    before: $before
    last: $last
    first: $first
    place: $place
    filters: $filters
    sortType: $sortType
  ) {
    cities {
      id
      name
      path
      regionCode
      __typename
    }
    meta {
      ...MetaFrag
      ...FocusFrag
      __typename
    }
    pageInfo {
      ...PageInfoFrag
      __typename
    }
    edges {
      node {
        ...RentalAddressFrag
        ...RentalFloorPlansFrag
        ...RentalImageFrag
        ...RentalListingFrag
        ...RentalPromotionsBadgeFrag
        building {
          yearBuilt
          yearRenovated
          clearanceHeight
          class
          size
          stories
          totalUnits
          isCertified
          __typename
        }
        tours {
          type
          __typename
        }
        bookables {
          name
          url
          type
          __typename
        }
        contact {
          name
          phoneNumber
          email
          __typename
        }
        images(startIndex: $imagesStartIndex, endIndex: $imagesEndIndex) {
          caption
          tags
          scales
          __typename
        }
        priority
        petOptions
        type
        __typename
      }
      __typename
    }
    __typename
  }
}

fragment RentalAddressFrag on RentalListing {
  address {
    city {
      id
      __typename
    }
    neighbourhood {
      name
      path
      __typename
    }
    postalCode
    street
    __typename
  }
  __typename
}

fragment RentalFloorPlansFrag on RentalListing {
  floorPlans {
    beds
    baths
    rent
    size
    furnished
    availability
    externalId
    parkingSpots
    __typename
  }
  __typename
}

fragment FocusFrag on RentalListingsMeta {
  focusedPlace {
    __typename
    ... on City {
      id
      location
      name
      slug
      __typename
    }
    ... on Neighbourhood {
      boundaries
      id
      location
      name
      slug
      city {
        id
        name
        slug
        __typename
      }
      __typename
    }
  }
  __typename
}

fragment RentalImageFrag on RentalListing {
  image {
    caption
    scales
    __typename
  }
  __typename
}

fragment RentalListingFrag on RentalListing {
  bathsRange
  bedsRange
  created
  highlightStatus
  id
  imagesCount
  listingType
  location
  modified
  name
  path
  priority
  rentRange
  sizeRange
  type
  verified
  parking {
    parkingTypes {
      parkingType
      monthlyRate
      __typename
    }
    parkingSpotsPerRental
    visitorParking
    __typename
  }
  __typename
}

fragment MetaFrag on RentalListingsMeta {
  totalCount
  totalFloorPlanCount
  __typename
}

fragment PageInfoFrag on PageInfo {
  __typename
  endCursor
  hasNextPage
  hasPreviousPage
  startCursor
}

fragment RentalPromotionsBadgeFrag on RentalListing {
  promotions {
    category
    startDate
    endDate
    __typename
  }
  __typename
}
"""

# Name: capture_auth_header()
# Purpose: This function 
# Parameters: url (str): This is the url of the website we wish to scrape
# Returns: 
def capture_auth_header(page, url: str):
    auth_header = None

    def handle_request(request):
        nonlocal auth_header

        if request.url == GRAPHQL_URL:
            headers = request.headers
            if "authorization" in headers:
                auth_header = headers["authorization"]
                print("Captured authorization header")

    page.on("request", handle_request)
    page.goto(url)
    page.wait_for_timeout(5000)

    return auth_header


def fetch_one_batch(page, auth_header: str, first_value: int, after_cursor=None):
    payload = {
        "operationName": "RentalListingSearch",
        "query": QUERY,
        "variables": {
            "after": after_cursor,
            "filters": {},
            "first": first_value,
            "place": {
                "namedArea": "toronto, on, ca"
            },
            "sortType": "cheapest"
        }
    }

    data = page.evaluate(
        """
        async ({payload, authHeader, graphqlUrl}) => {
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
            "payload": payload,
            "authHeader": auth_header,
            "graphqlUrl": GRAPHQL_URL
        }
    )

    return data


def fetch_all_listings(page, auth_header: str, first_value: int = 2000):
    cursor = None
    seen_ids = set()
    all_nodes = []
    batch_num = 1

    while True:
        data = fetch_one_batch(page, auth_header, first_value, cursor)

        if not data or "data" not in data or "rentalListings" not in data["data"]:
            print("Request failed")
            print(json.dumps(data, indent=2))
            break

        rental_listings = data["data"]["rentalListings"]
        meta = rental_listings["meta"]
        edges = rental_listings["edges"]
        page_info = rental_listings["pageInfo"]

        print(f"\nBatch {batch_num}")
        print("Total count:", meta["totalCount"])
        print("Rows returned:", len(edges))
        print("Has next page:", page_info["hasNextPage"])
        print("End cursor:", page_info["endCursor"])

        new_count = 0

        for edge in edges:
            node = edge["node"]
            listing_id = node["id"]

            if listing_id in seen_ids:
                continue

            seen_ids.add(listing_id)
            all_nodes.append(node)
            new_count += 1

        print("New unique rows added:", new_count)
        print("Unique total so far:", len(all_nodes))

        if not page_info["hasNextPage"]:
            break

        cursor = page_info["endCursor"]
        batch_num += 1

    return all_nodes


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        auth_header = capture_auth_header(page, TARGET_URL)

        if auth_header is None:
            print("Could not capture authorization header")
            browser.close()
            return

        all_nodes = fetch_all_listings(page, auth_header, first_value=2000)

        browser.close()

    print("\nFinal unique listings collected:", len(all_nodes))

    if all_nodes:
        print("\nFirst node sample:")
        print(json.dumps(all_nodes[0], indent=2))


if __name__ == "__main__":
    main()