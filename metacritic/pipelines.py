import re
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem


class DataValidationPipeline:
    """数据验证和清洗管道"""
    
    def process_item(self, item, spider=None):
        adapter = ItemAdapter(item)
        
        # 验证必要字段
        if not adapter.get('name') or not adapter.get('slug'):
            raise DropItem(f"缺少必要字段: {item}")
        
        # 清洗和验证评分数据
        self._clean_scores(adapter)
        
        # 清洗用户评论数量
        self._clean_user_reviews(adapter)
        
        # 清洗日期格式
        self._clean_release_date(adapter)
        
        # 清洗平台信息
        self._clean_platform(adapter)
        
        return item
    
    def _clean_scores(self, adapter):
        """清洗评分数据"""
        # 清洗metascore
        metascore = adapter.get('metascore', 'N/A')
        if metascore not in ['N/A', 'tbd']:
            try:
                score = int(metascore)
                if not (0 <= score <= 100):
                    adapter['metascore'] = 'N/A'
            except (ValueError, TypeError):
                adapter['metascore'] = 'N/A'
        
        # 清洗user_score
        user_score = adapter.get('user_score', 'N/A')
        if user_score not in ['N/A', 'tbd']:
            try:
                score = float(user_score)
                if not (0.0 <= score <= 10.0):
                    adapter['user_score'] = 'N/A'
            except (ValueError, TypeError):
                adapter['user_score'] = 'N/A'
    
    def _clean_user_reviews(self, adapter):
        """清洗用户评论数量"""
        user_reviews = adapter.get('user_reviews', '0')
        if user_reviews:
            # 移除非数字字符
            cleaned = re.sub(r'[^\d]', '', str(user_reviews))
            adapter['user_reviews'] = cleaned if cleaned else '0'
        else:
            adapter['user_reviews'] = '0'
    
    def _clean_release_date(self, adapter):
        """清洗发布日期"""
        release_date = adapter.get('release_date', 'N/A')
        if release_date and release_date.strip():
            # 基本的日期格式验证
            cleaned_date = release_date.strip()
            adapter['release_date'] = cleaned_date
        else:
            adapter['release_date'] = 'N/A'
    
    def _clean_platform(self, adapter):
        """清洗平台信息"""
        platform = adapter.get('platform', '')
        if platform:
            # 移除多余空格和逗号
            cleaned = re.sub(r'\s*,\s*', ', ', str(platform).strip())
            cleaned = re.sub(r'^,\s*|,\s*$', '', cleaned)  # 移除首尾逗号
            adapter['platform'] = cleaned if cleaned else 'Unknown'
        else:
            adapter['platform'] = 'Unknown'


class DuplicatesPipeline:
    """去重管道"""
    
    def __init__(self):
        self.ids_seen = set()
    
    def process_item(self, item, spider=None):
        adapter = ItemAdapter(item)
        slug = adapter['slug']
        
        if slug in self.ids_seen:
            raise DropItem(f"重复的游戏: {slug}")
        else:
            self.ids_seen.add(slug)
            return item


class MetacriticPipeline:
    """兼容性保留的原始Pipeline"""
    def process_item(self, item, spider=None):
        return item
