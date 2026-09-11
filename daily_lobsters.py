import os
import logging
import argparse
import datetime

from utils import (make_session, load_config, save_json,
                   generate_daily_md, update_readme_links)

LOBSTERS_API_URL = "https://lobste.rs/hottest.json"
MARKER = '<!-- LOBSTERS -->'
LABEL = 'Lobsters'


def fetch_lobsters_stories(session, limit):
    logging.info(f"Fetching Lobsters hottest stories (limit={limit})")

    resp = session.get(LOBSTERS_API_URL, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"Lobsters API returned {resp.status_code}")

    stories = resp.json()
    today = datetime.date.today().isoformat()

    result = []
    for s in stories[:limit]:
        result.append({
            "title": s.get("title", ""),
            "url": s.get("url", ""),
            "author": s.get("submitter_user", ""),
            "score": s.get("score", 0),
            "comments_count": s.get("comment_count", 0),
            "tags": ", ".join(s.get("tags", [])),
            "created_at": (s.get("created_at") or "")[:10],
            "lobsters_url": s.get("comments_url", ""),
            "date": today,
        })
        logging.info(f"Found: {s.get('title', '')[:60]} | Score: {s.get('score', 0)}")

    logging.info(f"Fetched {len(result)} Lobsters stories")
    return result


def build_md_rows(items):
    rows = []
    for s in items:
        title = s["title"].replace("|", r"\|")
        link_url = s["url"] or s["lobsters_url"]
        rows.append(
            f"| **[{title}]({link_url})** | {s['author']} "
            f"| {s['score']} | {s['comments_count']} "
            f"| {s['tags']} | [Discuss]({s['lobsters_url']}) |"
        )
    return rows


def demo(**config):
    cfg = config.get("lobsters", {})
    limit = cfg.get("limit", 30)
    today = datetime.date.today().isoformat()

    logging.info("GET daily lobsters begin")

    session = make_session()
    try:
        stories = fetch_lobsters_stories(session, limit)
    except Exception as e:
        logging.error(f"Failed to fetch Lobsters stories: {e}")
        return

    if not stories:
        logging.warning("No stories collected, skipping file generation")
        return

    json_dir = config.get("json_dir", "./json")
    save_json(os.path.join(json_dir, "lobsters", f"{today}.json"), stories)

    md_dir = config.get("md_dir", "./md")
    header = "| Title | Author | Score | Comments | Tags | Link |"
    generate_daily_md(
        os.path.join(md_dir, "lobsters", f"{today}.md"),
        f"Lobsters Hottest Stories — {today}",
        header,
        build_md_rows(stories),
    )

    update_readme_links(os.path.join(md_dir, "lobsters"),
                        config.get("md_readme_path", "README.md"),
                        MARKER, LABEL)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config_path", type=str, default="config.yaml",
                        help="configuration file path")
    args = parser.parse_args()
    config = load_config(args.config_path)
    demo(**config)
