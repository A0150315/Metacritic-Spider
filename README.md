# Metacritic Spider

一个高性能的Metacritic游戏数据爬虫，支持快速并发抓取游戏评分、用户评价、发布日期和平台信息。

## 特性

- 🚀 **高性能并发**: 支持128并发请求，极速数据抓取
- 📊 **完整数据**: 爬取游戏名称、评分、用户评价、发布日期、平台信息
- 🛡️ **稳定可靠**: 智能重试机制，处理网络异常
- 📁 **多格式输出**: 支持CSV格式数据导出
- ⚡ **零延迟配置**: 针对Metacritic优化的无限流配置

## 安装

### 1. 克隆仓库
```bash
git clone <repository-url>
cd Metacritic-Spider
```

### 方法A：使用 uv（推荐）
1. 安装 uv（任选其一）：
   ```bash
   brew install uv                   # macOS（推荐）
   curl -LsSf https://astral.sh/uv/install.sh | sh  # 通用脚本
   ```
2. 同步依赖并创建隔离环境（uv 会默认创建并维护 `.venv/`）：
   ```bash
   uv sync
   ```
3. 进入虚拟环境（可选，`uv run` 会自动激活）：
   ```bash
   source .venv/bin/activate  # Linux/Mac
   .venv\\Scripts\\activate  # Windows
   ```

### 方法B：传统 pip（备用）
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\\Scripts\\activate  # Windows
pip install -r requirements.txt
```

## 使用方法

### 直接爬取Metacritic
```bash
# 使用 uv 运行（自动激活 .venv）
uv run python -m scrapy crawl metacritic_direct_spider

# 或手动激活虚拟环境后运行
source .venv/bin/activate
python -m scrapy crawl metacritic_direct_spider
```

### VS Code调试
项目包含预配置的VS Code调试配置：
1. 打开VS Code
2. 按F5选择"运行Scrapy爬虫: metacritic_direct_spider"
3. 开始调试

## 性能配置

当前配置针对速度优化：
- **并发请求**: 128个
- **下载延迟**: 0秒
- **重试次数**: 1次
- **自动限流**: 禁用

### 性能测试结果
- 1分钟内可爬取约50页数据
- 2分钟内可达到100+页
- 零错误率，稳定运行

## 输出数据

数据保存为 `metacritic_games.csv`，包含以下字段：

| 字段 | 描述 | 示例 |
|------|------|------|
| name | 游戏名称 | The Legend of Zelda: Ocarina of Time |
| slug | URL标识符 | the-legend-of-zelda-ocarina-of-time |
| metascore | 媒体评分 | 99 |
| user_score | 用户评分 | 9.1 |
| user_reviews | 用户评价数 | 11460 |
| release_date | 发布日期 | Nov 23, 1998 |
| platform | 游戏平台 | Nintendo 64 |

## 项目结构

```
Metacritic-Spider/
├── metacritic/
│   ├── spiders/
│   │   ├── metacritic_direct_spider.py  # 主爬虫
│   │   ├── igdb_metacritic_spider.py    # IGDB联合爬虫
│   │   └── metacritic_spider.py         # RAWG联合爬虫
│   ├── items.py                         # 数据模型
│   ├── middlewares.py                   # 中间件
│   ├── pipelines.py                     # 数据处理管道
│   └── settings.py                      # 全局配置
├── .vscode/
│   └── launch.json                      # VS Code调试配置
├── requirements.txt                     # 依赖列表
├── .gitignore                          # Git忽略文件
└── README.md                           # 项目说明
```

## 配置说明

### 爬虫配置
主要配置在 `metacritic_direct_spider.py` 的 `custom_settings`：

```python
custom_settings = {
    \"CONCURRENT_REQUESTS\": 128,        # 并发数
    \"DOWNLOAD_DELAY\": 0,               # 延迟时间
    \"RETRY_TIMES\": 1,                  # 重试次数
    \"AUTOTHROTTLE_ENABLED\": False,     # 自动限流
    \"ROBOTSTXT_OBEY\": False,           # robots.txt
}
```

### 页面范围
默认爬取1-567页，可在spider中修改：
```python
max_page = 567  # 修改此值调整爬取范围
```

## uv 使用速查

| 目的 | 命令 |
|------|------|
| 同步依赖 / 创建虚拟环境 | `uv sync` |
| 运行爬虫 | `uv run python -m scrapy crawl metacritic_direct_spider` |
| 升级依赖到最新次版本 | `uv pip upgrade --latest` |
| 导出 requirements.txt（供 CI 或兼容旧流程） | `uv export --format requirements-txt --output requirements.txt` |

> `pyproject.toml` 现在是依赖的唯一事实来源；`requirements.txt` 可以随时通过 `uv export` 重新生成。

## 注意事项

⚠️ **使用建议**：
- 当前配置为最高速度，长时间运行请适当降低并发数
- 建议在网络良好的环境下运行
- 大规模爬取前请确保遵守网站使用条款

⚠️ **安全提醒**：
- 请勿在生产环境暴露API密钥
- 建议使用环境变量管理敏感信息

## 故障排除

### 常见问题

1. **虚拟环境问题**
   ```bash
   # 重新创建虚拟环境
   rm -rf .venv
   uv sync
   ```

2. **网络超时**
   ```python
   # 在spider配置中增加超时时间
   \"DOWNLOAD_TIMEOUT\": 30
   ```

3. **内存不足**
   ```python
   # 降低并发数
   \"CONCURRENT_REQUESTS\": 32
   ```

## 贡献

欢迎提交Issue和Pull Request来改进项目！

## 许可证

MIT License