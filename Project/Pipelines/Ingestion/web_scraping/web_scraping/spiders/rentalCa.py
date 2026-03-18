import scrapy


class RentalcaSpider(scrapy.Spider):
    name = "rentalCa"
    allowed_domains = ["rentals.ca"]
    start_urls = ["https://rentals.ca/"]

    def parse(self, response):
        pass
