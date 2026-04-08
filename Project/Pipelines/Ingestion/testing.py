from playwright.sync_api import sync_playwright
import json

# list view

def open_browser_and_fetch(url: str, first_value: int):
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
            "query": """query RentalListingSearch($after: String, $before: String, $last: PositiveInt, $first: PositiveInt, $place: PlaceInput!, $filters: RentalListingsConnectionFilterSet, $sortType: SortType, $imagesStartIndex: Int, $imagesEndIndex: Int) {
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
}""",
            "variables": {
                "filters": {},
                "first": first_value,
                "place": {
                    "namedArea": "toronto, on, ca"
                },
                "sortType": "relevant"
            }
        }

        data = page.evaluate(
            """
            async ({payload, authHeader}) => {
                const response = await fetch("https://rentals.ca/graphql", {
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
            {"payload": payload, "authHeader": auth_header}
        )

        browser.close()
        return data


if __name__ == "__main__":
    data = open_browser_and_fetch("https://rentals.ca/toronto", 2000)

    if data and data.get("data") and data["data"].get("rentalListings"):
        meta = data["data"]["rentalListings"]["meta"]
        edges = data["data"]["rentalListings"]["edges"]
        page_info = data["data"]["rentalListings"]["pageInfo"]

        print("Total count:", meta["totalCount"])
        print("Returned rows:", len(edges))
        print("Has next page:", page_info["hasNextPage"])
        print("End cursor:", page_info["endCursor"])
    else:
        print("Request failed")
        print(json.dumps(data, indent=2))