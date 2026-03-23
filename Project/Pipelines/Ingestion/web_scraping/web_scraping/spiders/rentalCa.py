import scrapy
import json


class RentalcaSpider(scrapy.Spider):
    name = "rentalCa"
    allowed_domains = ["rentals.ca"]
    start_urls = ["https://rentals.ca/"]

    def start_requests(self):
        url = "https://rentals.ca/graphql"

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
            "Origin": "https://rentals.ca",
            "Referer": "https://rentals.ca/toronto",
            "Cookie": "csrftoken=ykMBc58zyujTg0C9orQIKF9QIfxuEzpm; rt_anon_id=c507708c-ab95-48e0-bca2-8672ed919804; _gcl_au=1.1.1239233016.1773854864; _ga=GA1.1.1052096511.1773854864; __spdt=69f1ada2e169457ab78f4dfad67c1fb4; _tt_enable_cookie=1; _ttp=01KM0ZTCYB2FPQMBPZ5Z0R46VZ_.tt.1; _tac=false~self|not-available; _ta=ca~1~ce68b0088a6cb5cf603bbf65281339b3; cookies-analytics=true; cookies-functional=true; cookies-marketing=true; cookies-preferences=true; ll-visitor-id=bf33b735-2868-4cd4-bf4a-f5561ac15550; ll-commute-mode=car; rt_session_id=fbc8ddf3-96f7-4235-851c-5f9d511a378a; _ga_H10YQBE0W3=deleted; __cf_bm=c85z9SYW22MVKfF5_mCMrhy58ssmQgWXNzHj0ZGBaWk-1774297713.5874345-1.0.1.1-xKq5Rsurtj_YpZeYnL4RNf1hQ6Wz3qbfMP3eGxJ4BQQcAbh0ehVPwtFOw7llkiJd1qBlt.yj.xFS0CMxvH5nAAv5urCK4ftugicMn.gN34GrdqoaYsizkj4M.2dknuz2; cto_bundle=DWginV9FRTJBYnJMejNvdWpQTm1jOGtOVjhlaGJBYlZ4ZnYxSEhFanRhc2hSc2ZaT1ZXMHNRMnloUEclMkJKWkV4b20yME56JTJGaXNnRDFaYTY5ekRGejNWQWFSaTRPZjlFTTREbUF6ajNKd1p5aFkydGYxUTU3bWhKSFE4MnhmUDJMUEFUOUtmYzBWdXp2WiUyRlRpSHJHYTlheURjTVlhcDIxSXVJQ2tMVmNFY1lNb0RVVnRDOWlMNTE3ZHRLWk5GMHpjUE9uSng; _rdt_uuid=1773854864190.5fe4d0f5-b900-478c-bddb-e21d942d45ee; _ga_H10YQBE0W3=GS2.1.s1774295461$o4$g1$t1774298450$j58$l0$h2095014817; ttcsid=1774295464287::xNHs528weMVHTK9JGhJw.5.1774298451271.0; ttcsid_CJ6K7O3C77U7DSNBGBAG=1774295464287::HmaeN1NmZpaPDuivhiGR.5.1774298451271.1; _tas=0qrun9zp7pm; _rdt_pn=:270~0168d6678df06d960c4b37d3e36b5f202a8342d59a9ca7f011e80fb9966c8ce4|250~5c055d1d108487435cb5264db64cc4b0cce82c53c6aabf77c547c03afa21f5c4|250~2cb6602b4dbfeea4e3c1cfa5133bba2e7d272058d22ab14917f3cc81c9181bd4|175~21cba8dfe4af203f86e72983dd05f87eda78527bd6f8147d0a43fd60c043d9f8|175~fc406cbcc0283cce9531116c1c961df5bfb639842ced6e940d276af601594fbf"
        }

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
                "first": 1000,
                "place": {
                    "namedAreaDistance": {
                        "distance": 20000,
                        "namedArea": "toronto, on, ca"
                    }
                }
            }
        }

        yield scrapy.Request(
            url=url,
            method="POST",
            headers=headers,
            body=json.dumps(payload),
            callback=self.parse,
            meta={"handle_httpstatus_all": True}
        )

    def parse(self, response):
        print("Status:", response.status)

        if response.status != 200:
            print("Blocked response preview:")
            print(response.text[:500])
            return
        
        data = response.json()
        edges = data["data"]["rentalListings"]["edges"]

        for edge in edges [:5]:
            node = edge["node"]
            item = {
                "id": node.get("id"),
                "location": node.get("location"),
                "rentRange": node.get("rentRange")
            }

            print(item)
            yield item
