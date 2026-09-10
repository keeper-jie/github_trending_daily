import os
import logging
import argparse
import datetime

from utils import (make_session, load_config, save_json,
                   generate_daily_md, update_readme_links)

HN_API_BASE = "https://hacker-news.firebaseio.com/v0"
MARKER = '<!-- HACKER_NEWS -->'
LABEL = 'Hacker News'


def fetch_top_stories(session, limit: int):
    logging.info(f"Fetching HN top stories (limit={limit})")

    resp = session.get(f"{HN_API_BASE}/topstories.json", timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"HN request failed with status {resp.status_code}: topstories.json")

    story_ids = resp.json()[:limit]
    logging.info(f"Got {len(story_ids)} story IDs")

    stories = []
    for rank, story_id in enumerate(story_ids, start=1):
        try:
            item_resp = session.get(f"{HN_API_BASE}/item/{story_id}.json", timeout=60)
            if item_resp.status_code != 200:
                logging.warning(f"Failed to fetch story {story_id}: status {item_resp.status_code}")
                continue
            item = item_resp.json()
            if not item or item.get('type') != 'story':
                continue

            title = item.get('title', '').replace('|', r'\|')
            story_url = item.get('url') or f"https://news.ycombinator.com/item?id={story_id}"
            submitted = datetime.datetime.fromtimestamp(
                item.get('time', 0), tz=datetime.timezone.utc
            ).isoformat()

            stories.append({
                "rank": rank,
                "id": story_id,
                "title": item.get('title', ''),
                "url": story_url,
                "score": item.get('score', 0),
                "author": item.get('by', ''),
                "comments": item.get('descendants', 0),
                "submitted_at": submitted,
                "hn_url": f"https://news.ycombinator.com/item?id={story_id}",
            })
            logging.info(f"#{rank} {item.get('title', '')} | Score: {item.get('score')}")
        except Exception as e:
            logging.warning(f"Failed to parse story {story_id}: {e}")
            continue

    logging.info(f"Fetched {len(stories)} top stories")
    return stories


def build_md_rows(stories):
    rows = []
    for s in stories:
        title = s['title'].replace('|', r'\|')
        rows.append(
            f"| **{s['rank']}** | [{title}]({s['hn_url']}) "
            f"| {s.get('score', 0)} | {s.get('comments', 0)} "
            f"| {s.get('author', '')} | [Link]({s['url']}) |"
        )
    return rows


def demo(**config):
    cfg = config.get('hacker_news', {})
    limit = cfg.get('limit', 30)
    today = datetime.date.today().isoformat()

    logging.info("GET daily hacker news begin")

    session = make_session()
    try:
        stories = fetch_top_stories(session, limit)
    except Exception as e:
        logging.error(f"Failed to fetch HN stories: {e}")
        return

    if not stories:
        logging.warning("No stories collected, skipping file generation")
        return

    json_dir = config.get('json_dir', './json')
    save_json(os.path.join(json_dir, 'hacker-news', f"{today}.json"), stories)

    md_dir = config.get('md_dir', './md')
    header = "| Rank | Title | Score | Comments | Author | Link |"
    generate_daily_md(
        os.path.join(md_dir, 'hacker-news', f"{today}.md"),
        f"Hacker News Top Stories — {today}",
        header,
        build_md_rows(stories),
    )

    update_readme_links(os.path.join(md_dir, 'hacker-news'),
                        config.get('md_readme_path', 'README.md'),
                        MARKER, LABEL)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_path', type=str, default='config.yaml',
                        help='configuration file path')
    args = parser.parse_args()
    config = load_config(args.config_path)
    demo(**config)
