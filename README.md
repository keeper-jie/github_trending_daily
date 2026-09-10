# GitHub Trending Daily

每日自动抓取多源技术热门信息，生成结构化数据报告。

## 功能特点

- **GitHub Trending**：每日全站热门项目（HTML 抓取）
- **GitHub Rising Stars**：近两周新创建且 star 数最高的仓库（Search API）
- **Hacker News**：每日 Top Stories（官方 Firebase API）
- **Hugging Face**：每日热门模型（Hub API，按 trendingScore 排序）
- 生成 JSON 和 Markdown 格式的报告，通过 GitHub Actions 自动定时运行

## 项目结构

```
github_trending_daily/
├── .github/workflows/        # GitHub Actions 定时任务
├── utils.py                  # 共享工具函数
├── daily_trending.py         # GitHub Trending 抓取
├── daily_github_stars.py     # GitHub 新晋热门仓库
├── daily_hackernews.py       # Hacker News Top Stories
├── daily_huggingface.py      # Hugging Face 热门模型
├── config.yaml               # 配置文件（按数据源分段）
├── requirements.txt          # Python 依赖
├── json/<source>/YYYY-MM-DD.json   # 每日 JSON 数据（按源分目录）
└── md/<source>/YYYY-MM-DD.md       # 每日 Markdown 报告（按源分目录）
```

## 数据字段

**GitHub Trending**：repo、description、language、stars、forks、today_stars、url、date

**GitHub Rising Stars**（近 `created_days` 天创建、star > `min_stars`）：repo、description、language、stars、forks、created_at、url、date

**Hacker News**：rank、id、title、url、score、author、comments、submitted_at、hn_url

**Hugging Face**：model、pipeline_tag、library、downloads、likes、trending_score、created_at、url、date

## 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 运行（各脚本独立运行，读取同一份 config.yaml）
python daily_trending.py
python daily_github_stars.py
python daily_hackernews.py
python daily_huggingface.py

# 指定配置文件
python daily_trending.py --config_path config.yaml
```

## 配置说明

编辑 `config.yaml` 自定义抓取行为（按数据源分段）：

```yaml
github_trending:
  language_list: [""]     # 语言筛选，空字符串为所有语言
  since: "daily"          # daily / weekly / monthly

github_stars:
  created_days: 14        # 创建时间窗口（天）
  min_stars: 50           # star 数阈值
  limit: 30               # 抓取条数

hacker_news:
  limit: 30

huggingface:
  limit: 30
```

<!-- DAILY_TRENDING -->

## Trending Daily

| Date | Count | Link |
|------|-------|------|
| 2026-09-10 | 13 | [Trending](md/github-trending/2026-09-10.md) |

<!-- HACKER_NEWS -->

## Hacker News Daily

| Date | Count | Link |
|------|-------|------|
| 2026-09-10 | 30 | [Hacker News](md/hacker-news/2026-09-10.md) |

<!-- HUGGINGFACE -->

## HF Models Daily

| Date | Count | Link |
|------|-------|------|
| 2026-09-10 | 30 | [HF Models](md/huggingface/2026-09-10.md) |

<!-- GITHUB_STARS -->

## GitHub Stars Daily

| Date | Count | Link |
|------|-------|------|
| 2026-09-10 | 30 | [GitHub Stars](md/github-stars/2026-09-10.md) |

