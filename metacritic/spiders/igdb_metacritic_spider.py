import json
import scrapy


class IgdbMetacriticSpider(scrapy.Spider):
    name = "igdb_metacritic_spider"

    client_id = "8uov8a6v0s9c0mu39j4ffjb6th7h3b"
    client_secret = "dkzmqu5umisrb2xdfyywncg2tqm2q7"
    token_url = "https://id.twitch.tv/oauth2/token"
    token = None
    offset = 0
    limit = 500
    platforms = {}  # 存储平台数据

    custom_settings = {
        'FEEDS': {
            'new_results.csv': {
                'format': 'csv',
                'encoding': 'utf8',
                'store_empty': False,
                'fields': ['slug', 'user_score', 'user_reviews', 'metascore','platforms','release_date'],
                'overwrite': True,
            }
        }
    }

    def start_requests(self):
        # 首先获取 Access Token
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
        }

        yield scrapy.FormRequest(
            url=self.token_url, formdata=data, callback=self.parse_token
        )

    def parse_token(self, response):
        # 解析 token
        data = json.loads(response.text)
        self.token = data['access_token']

        # 用 token 获取平台数据
        url = 'https://api.igdb.com/v4/platforms'
        headers = {
            'Client-ID': '8uov8a6v0s9c0mu39j4ffjb6th7h3b',
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'text/plain'
        }
        yield scrapy.Request(url, headers=headers, method='POST', body='fields name;limit 500;', callback=self.parse_platforms)

    def parse_platforms(self, response):
        # 解析平台数据并保存到字典
        platforms_data = json.loads(response.text)
        self.platforms = {platform['id']: platform['name'] for platform in platforms_data}

        # 开始爬取 IGDB 游戏数据
        yield from self.fetch_igdb_games()

    def fetch_igdb_games(self):
        # 生成 IGDB 请求
        igdb_url = 'https://api.igdb.com/v4/games'
        headers = {
            'Client-ID': self.client_id,
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'text/plain',
        }
        data = f'fields slug,platforms;limit {self.limit};sort total_rating desc;offset {self.offset};where first_release_date >= 946656000 & total_rating_count > 10;'
        
        yield scrapy.Request(
            url=igdb_url,
            method="POST",
            headers=headers,
            body=data,
            callback=self.parse_igdb
        )

    def parse_igdb(self, response):
        games = json.loads(response.text)

        # 如果游戏列表为空，则停止请求
        if not games:
            self.logger.info("All games processed, stopping...")
            return

        for game in games:
            slug = game['slug']
            platforms = [self.platforms.get(platform_id, 'Unknown') for platform_id in game['platforms']]
            meta = {'slug': slug, 'platforms': platforms, 'handle_httpstatus_list': [404]}
            metacritic_url = f'https://www.metacritic.com/game/{slug}/'

            yield scrapy.Request(metacritic_url, callback=self.parse_metacritic, meta=meta, headers={
                'referer': 'https://www.metacritic.com/',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
            })

        # 增加 offset 并继续请求
        self.offset += self.limit
        yield from self.fetch_igdb_games()

    def parse_metacritic(self, response):
        slug = response.meta['slug']
        platforms = response.meta['platforms']
        
        if response.status == 404:
            self.logger.info(f'{slug} not found on Metacritic. Marking as N/A')
            yield {
                'slug': slug,
                'user_score': 'N/A',
                'user_reviews': 'N/A',
                'metascore': 'N/A',
                'platforms': ', '.join(platforms)
            }
            return
        
        # 解析Metacritic数据
        user_score = response.xpath('/html/body/div[1]/div/div/div[2]/div[1]/div[1]/div/div/div[2]/div[3]/div[4]/div[2]/div[1]/div[2]/div/div/span/text()').get() or "0"
        user_score = "0" if user_score == "tbd" else user_score
        
        user_reviews = response.xpath('/html/body/div[1]/div/div/div[2]/div[1]/div[1]/div/div/div[2]/div[3]/div[4]/div[2]/div[1]/div[1]/span[3]/a/span/text()').re_first(r"\b\d{1,3}(?:,\d{3})*\b")
        user_reviews = user_reviews.replace(",", "") if user_reviews else "0"
        
        metascore = response.xpath('/html/body/div[1]/div/div/div[2]/div[1]/div[1]/div/div/div[2]/div[3]/div[4]/div[1]/div/div[1]/div[2]/div/div/span/text()').get() or "0"
        metascore = "0" if metascore == "tbd" else metascore

        release_date = response.xpath('/html/body/div[1]/div/div/div[2]/div[1]/div[1]/div/div/div[2]/div[3]/div[3]/span[2]/text()').get() or "N/A"
        
        yield {
            'slug': slug,
            'user_score': user_score,
            'user_reviews': user_reviews,
            'metascore': metascore,
            'platforms': ', '.join(platforms),
            'release_date': release_date
        }