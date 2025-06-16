import scrapy
from scrapy.http import Request
from scrapy.spidermiddlewares.httperror import HttpError


class MetacriticSpider(scrapy.Spider):
    name = "metacritic"
    start_urls = [
        "https://api.rawg.io/api/games?page=1&page_size=40&key=c9dd580def464602b88d070054e355c6&ordering=-rating&dates=2000-01-01,2024-08-22"
    ]

    custom_settings = {"HTTPERROR_ALLOW_ALL": True}

    def parse(self, response):
        data = response.json()
        for game in data["results"]:
            slug = game["slug"]
            # log slug
            self.logger.info(f"Processing {slug}")
            metacritic_url = f"https://www.metacritic.com/game/{slug}/"
            yield Request(
                metacritic_url,
                callback=self.parse_metacritic,
                errback=self.errback_httpbin,
                meta={"slug": slug, "handle_httpstatus_list": [404]},
                dont_filter=True,
            )

        next_page = data.get("next")
        if next_page:
            yield Request(next_page, callback=self.parse, dont_filter=True)

    def parse_metacritic(self, response):
        slug = response.meta["slug"]

        if response.status in [404]:
            yield {
                "slug": slug,
                "user_score": "N/A",
                "user_reviews": "N/A",
                "metascore": "N/A",
            }
            return

        user_score = (
            response.xpath(
                "/html/body/div[1]/div/div/div[2]/div[1]/div[1]/div/div/div[2]/div[3]/div[4]/div[2]/div[1]/div[2]/div/div/span/text()"
            ).get()
            or "0"
        )
        if user_score == "tbd":
            user_score = "0"

        user_reviews = (
            response.xpath(
                "/html/body/div[1]/div/div/div[2]/div[1]/div[1]/div/div/div[2]/div[3]/div[4]/div[2]/div[1]/div[1]/span[3]/a/span/text()"
            ).re_first(r"\b\d{1,3}(?:,\d{3})*\b")
            
        )

        if not user_reviews:
            user_reviews = (
                response.xpath(
                    "/html/body/div[1]/div/div/div[2]/div[1]/div[1]/div/div/div[2]/div[3]/div[4]/div[2]/div[1]/div[1]/span[2]/text()"
                ).re_first(r"\b\d{1,3}(?:,\d{3})*\b")
                
            )

        # 移除逗号
        if user_reviews:
            user_reviews = user_reviews.replace(",", "")
        else:
            user_reviews = "0"

        metascore = (
            response.xpath(
                "/html/body/div[1]/div/div/div[2]/div[1]/div[1]/div/div/div[2]/div[3]/div[4]/div[1]/div/div[1]/div[2]/div/div/span/text()"
            ).get()
            or "0"
        )
        if metascore == "tbd":
            metascore = "0"

        yield {
            "slug": slug,
            "user_score": user_score,
            "user_reviews": user_reviews,
            "metascore": metascore,
        }

    def errback_httpbin(self, failure):
        slug = failure.request.meta["slug"]

        if failure.check(HttpError):
            response = failure.value.response
            if response.status in [404, 500]:
                yield {
                    "slug": slug,
                    "user_score": "N/A",
                    "user_reviews": "N/A",
                    "metascore": "N/A",
                }
