import os
import logging
import argparse
import datetime

from utils import (make_session, load_config, save_json,
                   generate_daily_md, update_readme_links)

DEVTO_API_URL = "https://dev.to/api/articles"
MARKER = '<!-- DEVTO -->'
LABEL = 'Dev.to'


def fetch_devto_articles(session, limit):
    params = {"top": 1, "per_page": limit}
    logging.info(f"Fetching Dev.to articles (limit={limit})")

    resp = session.get(DEVTO_API_URL, params=params, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"Dev.to API returned {resp.status_code}")

    articles = resp.json()
    today = datetime.date.today().isoformat()

    result = []
    for a in articles:
        author_info = a.get("user", {}) or {}
        result.append({
            "title": a.get("title", ""),
            "description": (a.get("description") or "")[:120],
            "author": author_info.get("name", "") or author_info.get("username", ""),
            "tags": ", ".join(a.get("tag_list", [])[:5]),
            "positive_reactions_count": a.get("positive_reactions_count", 0),
            "comments_count": a.get("comments_count", 0),
            "url": a.get("url", ""),
            "published_at": (a.get("published_at") or "")[:10],
            "date": today,
        })
        logging.info(f"Found: {a.get('title', '')[:60]} | Reactions: {a.get('positive_reactions_count', 0)}")

    logging.info(f"Fetched {len(result)} Dev.to articles")
    return result


def build_md_rows(items):
    rows = []
    for a in items:
        title = a["title"].replace("|", r"\|")
        rows.append(
            f"| **[{title}]({a['url']})** | {a['author']} "
            f"| {a['tags']} | {a['positive_reactions_count']:,} "
            f"| {a['comments_count']:,} | [Link]({a['url']}) |"
        )
    return rows


def demo(**config):
    cfg = config.get("devto", {})
    limit = cfg.get("limit", 30)
    today = datetime.date.today().isoformat()

    logging.info("GET daily devto begin")

    session = make_session()
    try:
        articles = fetch_devto_articles(session, limit)
    except Exception as e:
        logging.error(f"Failed to fetch Dev.to articles: {e}")
        return

    if not articles:
        logging.warning("No articles collected, skipping file generation")
        return

    json_dir = config.get("json_dir", "./json")
    save_json(os.path.join(json_dir, "devto", f"{today}.json"), articles)

    md_dir = config.get("md_dir", "./md")
    header = "| Title | Author | Tags | Reactions | Comments | Link |"
    generate_daily_md(
        os.path.join(md_dir, "devto", f"{today}.md"),
        f"Dev.to Top Articles — {today}",
        header,
        build_md_rows(articles),
    )

    update_readme_links(os.path.join(md_dir, "devto"),
                        config.get("md_readme_path", "README.md"),
                        MARKER, LABEL)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config_path", type=str, default="config.yaml",
                        help="configuration file path")
    args = parser.parse_args()
    config = load_config(args.config_path)
    demo(**config)
