import scrapy
import re
from ..items import GameItem


class MetacriticDirectSpider(scrapy.Spider):
    name = "metacritic_direct_spider"
    allowed_domains = ["metacritic.com"]
    current_page = 1
    max_page = None
    start_urls = [
        f"https://www.metacritic.com/browse/game/?releaseYearMin=1958&releaseYearMax=2025&page=1"
    ]

    # CSS选择器映射表 - 便于网页更新时维护
    SELECTORS = {
        # 游戏列表页面选择器
        "game_cards": "div.c-finderProductCard",
        "game_link": "a::attr(href)",
        "game_name": "h3.c-finderProductCard_titleHeading span:nth-child(2)::text",
        "list_metascore": "div.c-siteReviewScore span::text",
        "max_page": "#__layout > div > div > div > main > section > div > span > span:last-child > span > span > span::text",
        
        # 游戏详情页面选择器
        "user_score": "div.c-productHero_scoreInfo.g-inner-spacing-top-medium.g-outer-spacing-bottom-medium.g-outer-spacing-top-medium > div.c-productScoreInfo.u-clearfix > div.c-productScoreInfo_scoreContent.u-flexbox.u-flexbox-alignCenter.u-flexbox-justifyFlexEnd.g-width-100.u-flexbox-nowrap > div.c-productScoreInfo_scoreNumber.u-float-right > div > div > span::text",
        
        "user_reviews_primary": "#__layout > div > div.c-layoutDefault_page > div.c-pageProductGame > div:nth-child(1) > div > div > div.c-productHero_player-scoreInfo.u-grid.g-grid-container > div.c-productHero_score-container.u-flexbox.u-flexbox-column.g-bg-white > div.c-productHero_scoreInfo.g-inner-spacing-top-medium.g-outer-spacing-bottom-medium.g-outer-spacing-top-medium > div.c-productScoreInfo.u-clearfix > div.c-productScoreInfo_scoreContent.u-flexbox.u-flexbox-alignCenter.u-flexbox-justifyFlexEnd.g-width-100.u-flexbox-nowrap > div.c-productScoreInfo_text.g-outer-spacing-right-auto > span:last-child > a > span::text",
        
        "user_reviews_fallback": "#__layout > div > div.c-layoutDefault_page > div.c-pageProductGame > div:nth-child(1) > div > div > div.c-productHero_player-scoreInfo.u-grid.g-grid-container > div.c-productHero_score-container.u-flexbox.u-flexbox-column.g-bg-white > div.c-productHero_scoreInfo.g-inner-spacing-top-medium.g-outer-spacing-bottom-medium.g-outer-spacing-top-medium > div:nth-child(1) > div > div.c-productScoreInfo_scoreContent.u-flexbox.u-flexbox-alignCenter.u-flexbox-justifyFlexEnd.g-width-100.u-flexbox-nowrap > div.c-productScoreInfo_text.g-outer-spacing-right-auto > span:last-child > a > span::text",
        
        "release_date": "div.g-text-xsmall > span.u-text-uppercase::text",
        
        "platform_wrapper": "#__layout > div > div.c-layoutDefault_page > div.c-pageProductGame > div.c-PageProductGame_row > div.c-gamePlatformsSection.g-grid-container.g-outer-spacing-bottom-medium > div.c-gamePlatformsSection_list.u-grid-columns",
        "platform_svg_title": "div:nth-child(1) > div > div > svg > title::text",
        "platform_text": "div:nth-child(1) > div > div::text",
    }

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
        
        if self.max_page is None:
            self.max_page = self.get_max_page(response)
            self.logger.info(f"动态检测到总页数: {self.max_page}")

        games = response.css(self.SELECTORS["game_cards"])
        
        if not games:
            self.logger.warning(f"页面 {self.current_page} 没有找到游戏数据，可能已到最后一页")
            return

        for game in games:
            game_link = game.css(self.SELECTORS["game_link"]).get()
            name = game.css(self.SELECTORS["game_name"]).get()

            if game_link and name:
                name = name.strip()
                metascore = game.css(self.SELECTORS["list_metascore"]).get() or "N/A"

                yield scrapy.Request(
                    url=response.urljoin(game_link),
                    callback=self.parse_game_detail,
                    meta={"name": name, "metascore": metascore},
                    headers={"Referer": response.url},
                )

        # 处理下一页
        self.current_page += 1
        if self.max_page and self.current_page > self.max_page:
            self.logger.info(f"已达到最大页数 {self.max_page}，爬取完成")
            return

        next_page = f"https://www.metacritic.com/browse/game/?releaseYearMin=1958&releaseYearMax=2025&page={self.current_page}"
        self.logger.info(f"找到下一页: {next_page}")
        yield scrapy.Request(
            url=response.urljoin(next_page),
            callback=self.parse,
            headers={"Referer": response.url},
        )

    def get_max_page(self, response):
        """从分页导航动态获取总页数"""
        
        max_page_text = response.css(self.SELECTORS["max_page"]).get()
        
        if max_page_text and max_page_text.strip().isdigit():
            max_page = int(max_page_text.strip())
            self.logger.info(f"从分页导航获取到最大页数: {max_page}")
            return max_page
        
        # 如果无法获取，返回None，通过空页面检测自动停止
        self.logger.warning("无法从分页导航获取总页数，将通过空页面检测自动停止")
        return None

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
            user_score = response.css(self.SELECTORS["user_score"]).get()
            user_score = user_score.strip() if user_score else "N/A"
            user_score = "N/A" if user_score == "tbd" else user_score

            # 解析用户评论数量 - 使用回退策略
            review_text = response.css(self.SELECTORS["user_reviews_primary"]).get()

            if not review_text:
                review_text = response.css(self.SELECTORS["user_reviews_fallback"]).get()

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
            release_date = response.css(self.SELECTORS["release_date"]).get()
            release_date = release_date.strip() if release_date else "N/A"

            # 解析游戏平台
            game_platform_wrapper_dom_list = response.css(self.SELECTORS["platform_wrapper"])
            game_platform_title_dom_list = game_platform_wrapper_dom_list.css(self.SELECTORS["platform_svg_title"])
            another_game_platform_title_dom_list = game_platform_wrapper_dom_list.css(self.SELECTORS["platform_text"])
            
            game_platform_title_list = []
            for title_dom in (
                game_platform_title_dom_list + another_game_platform_title_dom_list
            ):
                title = title_dom.get()
                if title:
                    game_platform_title_list.append(title.strip())

            yield GameItem(
                name=name,
                slug=slug,
                metascore=metascore,
                user_score=user_score,
                user_reviews=user_reviews,
                release_date=release_date,
                platform=", ".join(game_platform_title_list),
            )
        except Exception as e:
            self.logger.error(f"解析游戏详情失败: {e}")
            return
