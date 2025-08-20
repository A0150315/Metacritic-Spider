import scrapy


class GameItem(scrapy.Item):
    """游戏数据模型"""
    name = scrapy.Field()
    slug = scrapy.Field()
    metascore = scrapy.Field()
    user_score = scrapy.Field()
    user_reviews = scrapy.Field()
    release_date = scrapy.Field()
    platform = scrapy.Field()


class MetacriticItem(scrapy.Item):
    """兼容性保留的原始Item"""
    pass
