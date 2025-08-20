import scrapy
import re


class MetacriticDirectSpider(scrapy.Spider):
    name = "metacritic_direct_spider"
    allowed_domains = ["metacritic.com"]
    current_page = 1
    max_page = 567
    start_urls = [
        f"https://www.metacritic.com/browse/game/?releaseYearMin=1958&releaseYearMax=2025&page={current_page}"
    ]

    custom_settings = {
        "FEEDS": {
            "metacritic_games.csv": {
                "format": "csv",
                "encoding": "utf8",
                "store_empty": False,
                "fields": [
                    "name",
                    "slug",
                    "metascore",
                    "user_score",
                    "user_reviews",
                    "release_date",
                    "platform",
                ],
                "overwrite": True,
            }
        },
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        "DOWNLOAD_DELAY": 0,
        "RANDOMIZE_DOWNLOAD_DELAY": False,
        "CONCURRENT_REQUESTS": 128,
        "RETRY_TIMES": 1,
        "RETRY_DELAY": 0.5,
        "COOKIES_ENABLED": False,
        "AUTOTHROTTLE_ENABLED": False,
        "ROBOTSTXT_OBEY": False,
    }

    def parse(self, response):
        """解析游戏列表页面，提取游戏信息和链接"""
        self.logger.info(f"正在爬取页面: {response.url}")

        games = response.css("div.c-finderProductCard")

        for game in games:
            game_link = game.css("a::attr(href)").get()
            name = game.css(
                "h3.c-finderProductCard_titleHeading span:nth-child(2)::text"
            ).get()

            if game_link and name:
                name = name.strip()
                metascore = game.css("div.c-siteReviewScore span::text").get() or "N/A"

                yield scrapy.Request(
                    url=response.urljoin(game_link),
                    callback=self.parse_game_detail,
                    meta={"name": name, "metascore": metascore},
                    headers={"Referer": response.url},
                )

        # 处理下一页
        self.current_page += 1
        if self.current_page > self.max_page:
            return

        next_page = f"https://www.metacritic.com/browse/game/?releaseYearMin=1958&releaseYearMax=2025&page={self.current_page}"
        self.logger.info(f"找到下一页: {next_page}")
        yield scrapy.Request(
            url=response.urljoin(next_page),
            callback=self.parse,
            headers={"Referer": response.url},
        )

    def parse_game_detail(self, response):
        """解析游戏详情页面，提取详细信息"""
        try:
            name = response.meta["name"]
            metascore = response.meta["metascore"]

            # 从URL中提取slug
            url_parts = response.url.strip("/").split("/")
            slug = url_parts[-1] if len(url_parts) >= 2 else "unknown"

            self.logger.info(f"正在解析游戏详情: {name} (slug: {slug})")

            # 解析用户评分
            user_score = response.css(
                "div.c-productHero_scoreInfo.g-inner-spacing-top-medium.g-outer-spacing-bottom-medium.g-outer-spacing-top-medium > div.c-productScoreInfo.u-clearfix > div.c-productScoreInfo_scoreContent.u-flexbox.u-flexbox-alignCenter.u-flexbox-justifyFlexEnd.g-width-100.u-flexbox-nowrap > div.c-productScoreInfo_scoreNumber.u-float-right > div > div > span::text"
            ).get()
            user_score = user_score.strip() if user_score else "N/A"
            user_score = "N/A" if user_score == "tbd" else user_score

            # 解析用户评论数量
            review_text = response.css(
                "#__layout > div > div.c-layoutDefault_page > div.c-pageProductGame > div:nth-child(1) > div > div > div.c-productHero_player-scoreInfo.u-grid.g-grid-container > div.c-productHero_score-container.u-flexbox.u-flexbox-column.g-bg-white > div.c-productHero_scoreInfo.g-inner-spacing-top-medium.g-outer-spacing-bottom-medium.g-outer-spacing-top-medium > div.c-productScoreInfo.u-clearfix > div.c-productScoreInfo_scoreContent.u-flexbox.u-flexbox-alignCenter.u-flexbox-justifyFlexEnd.g-width-100.u-flexbox-nowrap > div.c-productScoreInfo_text.g-outer-spacing-right-auto > span:last-child > a > span::text"
            ).get()

            if not review_text:
                review_text = response.css(
                    "#__layout > div > div.c-layoutDefault_page > div.c-pageProductGame > div:nth-child(1) > div > div > div.c-productHero_player-scoreInfo.u-grid.g-grid-container > div.c-productHero_score-container.u-flexbox.u-flexbox-column.g-bg-white > div.c-productHero_scoreInfo.g-inner-spacing-top-medium.g-outer-spacing-bottom-medium.g-outer-spacing-top-medium > div:nth-child(1) > div > div.c-productScoreInfo_scoreContent.u-flexbox.u-flexbox-alignCenter.u-flexbox-justifyFlexEnd.g-width-100.u-flexbox-nowrap > div.c-productScoreInfo_text.g-outer-spacing-right-auto > span:last-child > a > span::text"
                ).get()

            if not review_text:
                review_text = "0"

            user_reviews = re.sub(
                r"[^\d]",
                "",
                (
                    re.search(r"\d+(?:,\d+)*", review_text).group(0)
                    if re.search(r"\d+(?:,\d+)*", review_text)
                    else "0"
                ),
            )

            # 解析发布日期
            release_date = response.css(
                "div.g-text-xsmall > span.u-text-uppercase::text"
            ).get()
            release_date = release_date.strip() if release_date else "N/A"

            # 解析游戏平台
            game_platform_wrapper_dom_list = response.css(
                "#__layout > div > div.c-layoutDefault_page > div.c-pageProductGame > div.c-PageProductGame_row > div.c-gamePlatformsSection.g-grid-container.g-outer-spacing-bottom-medium > div.c-gamePlatformsSection_list.u-grid-columns"
            )
            game_platform_title_dom_list = game_platform_wrapper_dom_list.css(
                "div:nth-child(1) > div > div > svg > title::text"
            )
            another_game_platform_title_dom_list = game_platform_wrapper_dom_list.css(
                "div:nth-child(1) > div > div::text"
            )
            game_platform_title_list = []
            for title_dom in (
                game_platform_title_dom_list + another_game_platform_title_dom_list
            ):
                title = title_dom.get()
                if title:
                    game_platform_title_list.append(title.strip())

            yield {
                "name": name,
                "slug": slug,
                "metascore": metascore,
                "user_score": user_score,
                "user_reviews": user_reviews,
                "release_date": release_date,
                "platform": ", ".join(game_platform_title_list),
            }
        except Exception as e:
            self.logger.error(f"解析游戏详情失败: {e}")
            yield None


if __name__ == "__main__":
    text = "Based on 10,223,11 User Ratings"
    all_digits = re.sub(
        r"[^\d]",
        "",
        (
            re.search(r"\d+(?:,\d+)*", text).group(0)
            if re.search(r"\d+(?:,\d+)*", text)
            else "0"
        ),
    )
    print(all_digits)
