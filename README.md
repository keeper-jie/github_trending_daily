# GitHub Trending Daily

自动抓取每日 GitHub Trending 热门项目，生成结构化数据报告。

## 功能特点

- 每日自动抓取 GitHub Trending 页面热门项目
- 支持按编程语言筛选
- 生成 JSON 和 Markdown 格式的报告
- 通过 GitHub Actions 自动定时运行

## 项目结构

```
github_trending_daily/
├── .github/workflows/       # GitHub Actions 定时任务
├── daily_trending.py        # 主脚本
├── config.yaml              # 配置文件
├── requirements.txt         # Python 依赖
├── json/                    # 每日 JSON 数据
└── md/                      # 每日 Markdown 报告
```

## 数据字段

每个热门项目包含以下信息：

| 字段 | 说明 |
|------|------|
| repo | 项目名称 (owner/repo) |
| description | 项目描述 |
| language | 编程语言 |
| stars | Star 总数 |
| forks | Fork 数 |
| today_stars | 今日新增 Star 数 |
| url | 项目链接 |

## 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 运行脚本
python daily_trending.py

# 指定配置文件
python daily_trending.py --config_path config.yaml
```

## 配置说明

编辑 `config.yaml` 自定义抓取行为：

```yaml
# 抓取的语言列表（空字符串表示所有语言）
language_list: [""]

# 时间范围: daily, weekly, monthly
since: "daily"

# 输出目录
json_dir: './json'
md_dir: './md'
```

<!-- DAILY_TRENDING -->

## Daily Trending

