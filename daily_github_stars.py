import os
import logging
import argparse
import datetime

from utils import (make_session, load_config, save_json,
                   generate_daily_md, update_readme_links)

SEARCH_URL = "https://api.github.com/search/repositories"
MARKER = '<!-- GITHUB_STARS -->'
LABEL = 'GitHub Stars'


def fetch_rising_stars(session, created_days: int, min_stars: int, limit: int):
    since_date = (datetime.date.today() - datetime.timedelta(days=created_days)).isoformat()
    query = f"created:>{since_date} stars:>{min_stars}"
    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": limit,
    }
    logging.info(f"Fetching rising stars: {query}")

    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get('GITHUB_TOKEN')
    if token:
        headers["Authorization"] = f"Bearer {token}"
    else:
        logging.warning("GITHUB_TOKEN not set, using unauthenticated request (low rate limit)")

    resp = session.get(SEARCH_URL, params=params, headers=headers, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"GitHub search failed with status {resp.status_code}: {SEARCH_URL}")

    data = resp.json()
    logging.info(f"Total matching repos: {data.get('total_count')}")

    today = datetime.date.today().isoformat()
    repos = []
    for item in data.get('items', []):
        full_name = item.get('full_name', '')
        if not full_name:
            continue
        repos.append({
            "repo": full_name,
            "description": item.get('description') or '',
            "language": item.get('language') or '',
            "stars": item.get('stargazers_count', 0),
            "forks": item.get('forks_count', 0),
            "created_at": item.get('created_at', ''),
            "url": item.get('html_url', ''),
            "date": today,
        })
        logging.info(f"Found: {full_name} | Stars: {item.get('stargazers_count')}")

    logging.info(f"Fetched {len(repos)} rising star repos")
    return repos


def build_md_rows(repos):
    rows = []
    for r in repos:
        description = r.get('description', '').replace('|', r'\|')
        if len(description) > 80:
            description = description[:77] + "..."
        created = r.get('created_at', '')[:10]
        rows.append(
            f"| **{r['repo']}** | {description} | {r.get('language', '')} "
            f"| {r.get('stars', 0):,} | {r.get('forks', 0):,} "
            f"| {created} | [Link]({r['url']}) |"
        )
    return rows


def demo(**config):
    cfg = config.get('github_stars', {})
    created_days = cfg.get('created_days', 14)
    min_stars = cfg.get('min_stars', 50)
    limit = cfg.get('limit', 30)
    today = datetime.date.today().isoformat()

    logging.info("GET daily github rising stars begin")

    session = make_session()
    try:
        repos = fetch_rising_stars(session, created_days, min_stars, limit)
    except Exception as e:
        logging.error(f"Failed to fetch rising stars: {e}")
        return

    if not repos:
        logging.warning("No repos collected, skipping file generation")
        return

    json_dir = config.get('json_dir', './json')
    save_json(os.path.join(json_dir, 'github-stars', f"{today}.json"), repos)

    md_dir = config.get('md_dir', './md')
    header = "| Repo | Description | Language | Stars | Forks | Created | Link |"
    generate_daily_md(
        os.path.join(md_dir, 'github-stars', f"{today}.md"),
        f"GitHub Rising Stars (created in {created_days}d) — {today}",
        header,
        build_md_rows(repos),
    )

    update_readme_links(os.path.join(md_dir, 'github-stars'),
                        config.get('md_readme_path', 'README.md'),
                        MARKER, LABEL)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_path', type=str, default='config.yaml',
                        help='configuration file path')
    args = parser.parse_args()
    config = load_config(args.config_path)
    demo(**config)
