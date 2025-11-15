# Scrapy settings for metacritic project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "metacritic"

SPIDER_MODULES = ["metacritic.spiders"]
NEWSPIDER_MODULE = "metacritic.spiders"

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    "metacritic.pipelines.DataValidationPipeline": 300,
    "metacritic.pipelines.DuplicatesPipeline": 400,
}

# 日志配置
LOG_LEVEL = 'INFO'
LOG_FILE = 'scrapy.log'
LOG_ENCODING = 'utf-8'

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
