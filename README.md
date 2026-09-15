# GitHub Trending Daily

> 🌐 **Web 界面**：[https://keeper-jie.github.io/github_trending_daily/](https://keeper-jie.github.io/github_trending_daily/)

每日自动抓取多源技术热门信息，生成结构化数据报告。

## 功能特点

- **GitHub Trending**：每日全站热门项目（HTML 抓取）
- **GitHub Rising Stars**：近两周新创建且 star 数最高的仓库（Search API）
- **Hacker News**：每日 Top Stories（官方 Firebase API）
- **Hugging Face**：每日热门模型（Hub API，按 trendingScore 排序）
- **Reddit**：多版块热门帖子（公开 JSON API：programming / MachineLearning / datascience / LocalLLaMA）
- **arXiv**：最新 AI/ML 论文（公开 API：cs.AI / cs.CL / cs.LG / cs.CV）
- **Dev.to**：每日热门文章（公开 REST API）
- **Lobste.rs**：高质量技术社区热帖（公开 JSON API）
- **Hugging Face Papers**：每日 AI 论文精选（公开 API）
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
├── daily_reddit.py           # Reddit 热门帖子
├── daily_arxiv.py            # arXiv 最新论文
├── daily_devto.py            # Dev.to 热门文章
├── daily_lobsters.py         # Lobste.rs 热帖
├── daily_hf_papers.py        # Hugging Face 每日论文精选
├── generate_manifest.py      # 生成数据清单
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

**Reddit**：rank、subreddit、title、score、num_comments、author、url、reddit_url、date

**arXiv**：title、authors、summary、categories、published、pdf_url、abs_url、date

**Dev.to**：title、description、author、tags、positive_reactions_count、comments_count、url、published_at、date

**Lobste.rs**：title、url、author、score、comments_count、tags、created_at、lobsters_url、date

**HF Papers**：title、authors、summary、upvotes、url、paper_url、published_at、date

## 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 运行（各脚本独立运行，读取同一份 config.yaml）
python daily_trending.py
python daily_github_stars.py
python daily_hackernews.py
python daily_huggingface.py
python daily_reddit.py
python daily_arxiv.py
python daily_devto.py
python daily_lobsters.py
python daily_hf_papers.py
python generate_manifest.py

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

reddit:
  subreddits: ["programming", "MachineLearning", "datascience", "LocalLLaMA"]
  limit_per_sub: 10
  limit: 30

arxiv:
  categories: ["cs.AI", "cs.CL", "cs.LG", "cs.CV"]
  limit: 30

devto:
  limit: 30

lobsters:
  limit: 30

hf_papers:
  limit: 30
```

<!-- DAILY_TRENDING -->

## Trending Daily

| Date | Count | Link |
|------|-------|------|
| 2026-09-15 | 20 | [Trending](md/github-trending/2026-09-15.md) |
| 2026-09-14 | 19 | [Trending](md/github-trending/2026-09-14.md) |
| 2026-09-13 | 16 | [Trending](md/github-trending/2026-09-13.md) |
| 2026-09-12 | 16 | [Trending](md/github-trending/2026-09-12.md) |
| 2026-09-11 | 16 | [Trending](md/github-trending/2026-09-11.md) |
| 2026-09-10 | 13 | [Trending](md/github-trending/2026-09-10.md) |

<!-- HACKER_NEWS -->

## Hacker News Daily

| Date | Count | Link |
|------|-------|------|
| 2026-09-15 | 30 | [Hacker News](md/hacker-news/2026-09-15.md) |
| 2026-09-14 | 30 | [Hacker News](md/hacker-news/2026-09-14.md) |
| 2026-09-13 | 30 | [Hacker News](md/hacker-news/2026-09-13.md) |
| 2026-09-12 | 29 | [Hacker News](md/hacker-news/2026-09-12.md) |
| 2026-09-11 | 30 | [Hacker News](md/hacker-news/2026-09-11.md) |
| 2026-09-10 | 30 | [Hacker News](md/hacker-news/2026-09-10.md) |

<!-- HUGGINGFACE -->

## HF Models Daily

| Date | Count | Link |
|------|-------|------|
| 2026-09-15 | 30 | [HF Models](md/huggingface/2026-09-15.md) |
| 2026-09-14 | 30 | [HF Models](md/huggingface/2026-09-14.md) |
| 2026-09-13 | 30 | [HF Models](md/huggingface/2026-09-13.md) |
| 2026-09-12 | 30 | [HF Models](md/huggingface/2026-09-12.md) |
| 2026-09-11 | 30 | [HF Models](md/huggingface/2026-09-11.md) |
| 2026-09-10 | 30 | [HF Models](md/huggingface/2026-09-10.md) |

<!-- GITHUB_STARS -->

## GitHub Stars Daily

| Date | Count | Link |
|------|-------|------|
| 2026-09-15 | 30 | [GitHub Stars](md/github-stars/2026-09-15.md) |
| 2026-09-14 | 30 | [GitHub Stars](md/github-stars/2026-09-14.md) |
| 2026-09-13 | 30 | [GitHub Stars](md/github-stars/2026-09-13.md) |
| 2026-09-12 | 30 | [GitHub Stars](md/github-stars/2026-09-12.md) |
| 2026-09-11 | 30 | [GitHub Stars](md/github-stars/2026-09-11.md) |
| 2026-09-10 | 30 | [GitHub Stars](md/github-stars/2026-09-10.md) |

<!-- REDDIT -->

## Reddit Daily

| Date | Count | Link |
|------|-------|------|
| 2026-09-15 | 10 | [Reddit](md/reddit/2026-09-15.md) |
| 2026-09-14 | 10 | [Reddit](md/reddit/2026-09-14.md) |
| 2026-09-13 | 10 | [Reddit](md/reddit/2026-09-13.md) |
| 2026-09-12 | 10 | [Reddit](md/reddit/2026-09-12.md) |
| 2026-09-11 | 20 | [Reddit](md/reddit/2026-09-11.md) |

<!-- ARXIV -->

## arXiv Daily

| Date | Count | Link |
|------|-------|------|
| 2026-09-12 | 30 | [arXiv](md/arxiv/2026-09-12.md) |
| 2026-09-11 | 30 | [arXiv](md/arxiv/2026-09-11.md) |

<!-- DEVTO -->

## Dev.to Daily

| Date | Count | Link |
|------|-------|------|
| 2026-09-15 | 30 | [Dev.to](md/devto/2026-09-15.md) |
| 2026-09-14 | 30 | [Dev.to](md/devto/2026-09-14.md) |
| 2026-09-13 | 30 | [Dev.to](md/devto/2026-09-13.md) |
| 2026-09-12 | 30 | [Dev.to](md/devto/2026-09-12.md) |
| 2026-09-11 | 30 | [Dev.to](md/devto/2026-09-11.md) |

<!-- LOBSTERS -->

## Lobsters Daily

| Date | Count | Link |
|------|-------|------|
| 2026-09-15 | 25 | [Lobsters](md/lobsters/2026-09-15.md) |
| 2026-09-14 | 25 | [Lobsters](md/lobsters/2026-09-14.md) |
| 2026-09-13 | 25 | [Lobsters](md/lobsters/2026-09-13.md) |
| 2026-09-12 | 25 | [Lobsters](md/lobsters/2026-09-12.md) |
| 2026-09-11 | 25 | [Lobsters](md/lobsters/2026-09-11.md) |

<!-- HF_PAPERS -->

## HF Papers Daily

| Date | Count | Link |
|------|-------|------|
| 2026-09-15 | 19 | [HF Papers](md/hf-papers/2026-09-15.md) |
| 2026-09-14 | 6 | [HF Papers](md/hf-papers/2026-09-14.md) |
| 2026-09-12 | 26 | [HF Papers](md/hf-papers/2026-09-12.md) |
| 2026-09-11 | 8 | [HF Papers](md/hf-papers/2026-09-11.md) |

