from playwright.sync_api import sync_playwright


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print("Opening page...")

        graphql_responses = []

        # 👇 Listen to ALL responses
        def handle_response(response):
            if "/graphql" in response.url:
                print("Captured GraphQL:", response.status)
                graphql_responses.append(response)

        page.on("response", handle_response)

        page.goto("https://rentals.ca/toronto", wait_until="domcontentloaded")

        # 👇 wait for network to finish
        page.wait_for_timeout(8000)

        print(f"Total GraphQL responses: {len(graphql_responses)}")

        # 👇 try to extract listings
        for response in graphql_responses:
            try:
                data = response.json()

                rental_data = data.get("data", {}).get("rentalListings", {})
                edges = rental_data.get("edges", [])

                if edges:
                    print("FOUND LISTINGS:", len(edges))

                    for edge in edges[:5]:
                        node = edge.get("node", {})
                        item = {
                            "id": node.get("id"),
                            "location": node.get("location"),
                            "rentRange": node.get("rentRange"),
                        }
                        print(item)

                    break

            except:
                continue

        input("Press Enter to close...")
        browser.close()


if __name__ == "__main__":
    main()