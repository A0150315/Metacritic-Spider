import scrapy
import re
from ..items import GameItem


class MetacriticDirectSpider(scrapy.Spider):
    name = "metacritic_direct_spider"
    allowed_domains = ["metacritic.com"]
    current_page = 1
    max_page = None
    start_urls = [
        f"https://www.metacritic.com/browse/game/?releaseYearMin=1958&releaseYearMax=2027&page=1"
    ]

    # CSS选择器映射表 - 便于网页更新时维护
    SELECTORS = {
        # 游戏列表页面选择器
        "game_cards": "[data-testid='filter-results']",
        "game_link": "a::attr(href)",
        "game_name": "h3[data-testid='product-title'] span:last-child::text",
        "list_metascore": ".c-siteReviewScore span::text",
        "max_page": ".c-navigation-pagination__page .c-navigation-pagination__item-content::text",

        # 游戏详情页面选择器
        "release_date": ".c-product-details__section__value::text",
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
        "CONCURRENT_REQUESTS_PER_DOMAIN": 128,
        "CONCURRENT_REQUESTS_PER_IP": 128,
        "RETRY_TIMES": 1,
        "RETRY_DELAY": 0.5,
        "COOKIES_ENABLED": False,
        "AUTOTHROTTLE_ENABLED": False,
        "ROBOTSTXT_OBEY": False,
        "DNSCACHE_ENABLED": True,
        "DNSCACHE_SIZE": 2048,
        "REACTOR_THREADPOOL_MAXSIZE": 64,
        "LOGSTATS_INTERVAL": 30,
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

        next_page = f"https://www.metacritic.com/browse/game/?releaseYearMin=1958&releaseYearMax=2027&page={self.current_page}"
        self.logger.info(f"找到下一页: {next_page}")
        yield scrapy.Request(
            url=response.urljoin(next_page),
            callback=self.parse,
            headers={"Referer": response.url},
        )

    def get_max_page(self, response):
        """从分页导航动态获取总页数"""
        # 分页数字可能有多个，取最后一个（即最大页码）
        page_texts = response.css(self.SELECTORS["max_page"]).getall()
        page_nums = [t.strip() for t in page_texts if t.strip().isdigit()]

        if page_nums:
            max_page = int(page_nums[-1])
            self.logger.info(f"从分页导航获取到最大页数: {max_page}")
            return max_page

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

            # 解析用户评分 - 取所有 bg-score span 中的第二个（第一个是 metascore）
            all_scores = response.css('[class*="bg-score"] span::text').getall()
            all_scores = [s.strip() for s in all_scores if s.strip()]
            user_score = all_scores[1] if len(all_scores) > 1 else "N/A"
            if user_score == "tbd":
                user_score = "N/A"

            # 解析用户评论数量 - 从 "Based on X User Ratings" 提取
            user_reviews = "0"
            review_texts = response.css('[data-testid="global-score-review-count"] a::text').getall()
            for text in review_texts:
                match = re.search(r"Based on\s+([\d,]+)\s+User", text)
                if match:
                    user_reviews = match.group(1).replace(",", "")
                    break

            # 解析发布日期
            release_date = response.css(self.SELECTORS["release_date"]).get()
            release_date = release_date.strip() if release_date else "N/A"

            # 解析游戏平台
            platform = response.css('[data-testid="platform-selector"] ::text').get()
            platform = platform.strip() if platform else "N/A"

            yield GameItem(
                name=name,
                slug=slug,
                metascore=metascore,
                user_score=user_score,
                user_reviews=user_reviews,
                release_date=release_date,
                platform=platform,
            )
        except Exception as e:
            self.logger.error(f"解析游戏详情失败: {e}")
            return
