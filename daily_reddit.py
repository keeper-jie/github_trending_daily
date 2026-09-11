import os
import logging
import argparse
import datetime
import xml.etree.ElementTree as ET

from utils import (make_session, load_config, save_json,
                   generate_daily_md, update_readme_links)

REDDIT_RSS_URL = "https://www.reddit.com/r/{subreddit}/hot.rss"
MARKER = '<!-- REDDIT -->'
LABEL = 'Reddit'
ATOM_NS = "{http://www.w3.org/2005/Atom}"


def fetch_reddit_posts(session, subreddits, limit_per_sub, limit):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    all_posts = []
    seen_ids = set()

    for sub in subreddits:
        url = REDDIT_RSS_URL.format(subreddit=sub)
        logging.info(f"Fetching Reddit r/{sub} RSS (limit={limit_per_sub})")
        try:
            resp = session.get(url, headers=headers,
                               params={"limit": limit_per_sub}, timeout=60)

            logging.info(f"r/{sub}: status={resp.status_code}, content-length={len(resp.text)}")

            if resp.status_code != 200:
                logging.warning(f"Reddit r/{sub} returned {resp.status_code}: {resp.text[:200]}")
                continue

            root = ET.fromstring(resp.text)
            entries = root.findall(f"{ATOM_NS}entry")
            logging.info(f"r/{sub}: found {len(entries)} entries in RSS feed")

            for entry in entries:
                id_el = entry.find(f"{ATOM_NS}id")
                post_id = id_el.text.strip() if id_el is not None and id_el.text else ""
                if not post_id or post_id in seen_ids:
                    continue
                seen_ids.add(post_id)

                title_el = entry.find(f"{ATOM_NS}title")
                title = title_el.text.strip() if title_el is not None and title_el.text else ""

                author_el = entry.find(f"{ATOM_NS}author")
                author = ""
                if author_el is not None:
                    name_el = author_el.find(f"{ATOM_NS}name")
                    if name_el is not None and name_el.text:
                        author = name_el.text.strip()
                        if author.startswith("/u/"):
                            author = author[3:]

                links = entry.findall(f"{ATOM_NS}link")
                reddit_url = ""
                post_url = ""
                for link in links:
                    href = link.get("href", "")
                    if href and not reddit_url:
                        reddit_url = href
                    if href and "reddit.com" not in href:
                        post_url = href

                if not post_url:
                    post_url = reddit_url
                if not reddit_url and links:
                    reddit_url = links[0].get("href", "")

                all_posts.append({
                    "subreddit": sub,
                    "title": title,
                    "score": 0,
                    "num_comments": 0,
                    "author": author,
                    "url": post_url,
                    "reddit_url": reddit_url,
                })

            logging.info(f"r/{sub}: collected {len([p for p in all_posts if p['subreddit'] == sub])} posts")

        except Exception as e:
            logging.error(f"Failed to fetch r/{sub}: {type(e).__name__}: {e}", exc_info=True)
            continue

    today = datetime.date.today().isoformat()
    result = []
    for rank, post in enumerate(all_posts[:limit], start=1):
        post["rank"] = rank
        post["date"] = today
        result.append(post)
        logging.info(f"#{rank} r/{post['subreddit']} | {post['title'][:60]}")

    logging.info(f"Collected {len(result)} Reddit posts total")
    return result


def build_md_rows(items):
    rows = []
    for p in items:
        title = p["title"].replace("|", r"\|")
        rows.append(
            f"| **{p['rank']}** | r/{p['subreddit']} "
            f"| [{title}]({p['reddit_url']}) "
            f"| {p.get('author', '')} | [Link]({p['url']}) |"
        )
    return rows


def demo(**config):
    cfg = config.get("reddit", {})
    subreddits = cfg.get("subreddits", ["programming", "MachineLearning", "datascience", "LocalLLaMA"])
    limit_per_sub = cfg.get("limit_per_sub", 10)
    limit = cfg.get("limit", 30)
    today = datetime.date.today().isoformat()

    logging.info("GET daily reddit begin")

    session = make_session()
    try:
        posts = fetch_reddit_posts(session, subreddits, limit_per_sub, limit)
    except Exception as e:
        logging.error(f"Failed to fetch Reddit posts: {type(e).__name__}: {e}", exc_info=True)
        return

    if not posts:
        logging.warning("No posts collected, skipping file generation")
        return

    json_dir = config.get("json_dir", "./json")
    save_json(os.path.join(json_dir, "reddit", f"{today}.json"), posts)

    md_dir = config.get("md_dir", "./md")
    header = "| Rank | Sub | Title | Author | Link |"
    generate_daily_md(
        os.path.join(md_dir, "reddit", f"{today}.md"),
        f"Reddit Hot Posts — {today}",
        header,
        build_md_rows(posts),
    )

    update_readme_links(os.path.join(md_dir, "reddit"),
                        config.get("md_readme_path", "README.md"),
                        MARKER, LABEL)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config_path", type=str, default="config.yaml",
                        help="configuration file path")
    args = parser.parse_args()
    config = load_config(args.config_path)
    demo(**config)
