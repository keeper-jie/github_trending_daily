import os
import logging
import argparse
import datetime

from utils import (make_session, load_config, save_json,
                   generate_daily_md, update_readme_links)

REDDIT_JSON_URL = "https://www.reddit.com/r/{subreddit}/hot.json"
MARKER = '<!-- REDDIT -->'
LABEL = 'Reddit'


def fetch_reddit_posts(session, subreddits, limit_per_sub, limit):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    all_posts = []
    seen_ids = set()

    for sub in subreddits:
        url = REDDIT_JSON_URL.format(subreddit=sub)
        logging.info(f"Fetching Reddit r/{sub} (limit={limit_per_sub})")
        try:
            resp = session.get(url, headers=headers,
                               params={"limit": limit_per_sub, "raw_json": 1},
                               timeout=60)

            logging.info(f"r/{sub}: status={resp.status_code}, content-length={len(resp.text)}")

            if resp.status_code != 200:
                logging.warning(f"Reddit r/{sub} returned {resp.status_code}: {resp.text[:200]}")
                continue

            try:
                data = resp.json()
            except Exception as json_err:
                logging.error(f"r/{sub}: JSON parse error: {json_err}")
                logging.debug(f"r/{sub}: response text: {resp.text[:500]}")
                continue

            children = data.get("data", {}).get("children", [])
            logging.info(f"r/{sub}: got {len(children)} posts")

            for child in children:
                post = child.get("data", {})
                post_id = post.get("id")
                if not post_id or post_id in seen_ids:
                    continue
                seen_ids.add(post_id)

                post_url = post.get("url", "")
                permalink = post.get("permalink", "")

                all_posts.append({
                    "subreddit": post.get("subreddit", sub),
                    "title": post.get("title", ""),
                    "score": post.get("score", 0),
                    "num_comments": post.get("num_comments", 0),
                    "author": post.get("author", ""),
                    "url": post_url,
                    "reddit_url": f"https://www.reddit.com{permalink}",
                })

        except Exception as e:
            logging.error(f"Failed to fetch r/{sub}: {type(e).__name__}: {e}", exc_info=True)
            continue

    all_posts.sort(key=lambda x: x["score"], reverse=True)
    today = datetime.date.today().isoformat()
    result = []
    for rank, post in enumerate(all_posts[:limit], start=1):
        post["rank"] = rank
        post["date"] = today
        result.append(post)
        logging.info(f"#{rank} r/{post['subreddit']} | {post['title'][:60]} | Score: {post['score']}")

    logging.info(f"Collected {len(result)} Reddit posts total")
    return result


def build_md_rows(items):
    rows = []
    for p in items:
        title = p["title"].replace("|", r"\|")
        rows.append(
            f"| **{p['rank']}** | r/{p['subreddit']} "
            f"| [{title}]({p['reddit_url']}) "
            f"| {p['score']:,} | {p['num_comments']:,} "
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
    header = "| Rank | Sub | Title | Score | Comments | Author | Link |"
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
