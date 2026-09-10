import re
import os
import logging
import argparse
import datetime

from bs4 import BeautifulSoup

from utils import (make_session, load_config, save_json,
                   generate_daily_md, update_readme_links)

TRENDING_URL = "https://github.com/trending/{language}?since={since}"
MARKER = '<!-- DAILY_TRENDING -->'
LABEL = 'Trending'


def parse_number(text: str) -> int:
    if not text:
        return 0
    match = re.search(r'[\d,]+', text.strip())
    if match:
        return int(match.group().replace(',', ''))
    return 0


def scrape_trending(session, language: str = "", since: str = "daily"):
    url = TRENDING_URL.format(language=language, since=since)
    logging.info(f"Fetching trending: {url}")

    resp = session.get(url, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"Trending request failed with status {resp.status_code}: {url}")

    soup = BeautifulSoup(resp.text, 'html.parser')
    repos = []

    articles = soup.find_all('article', class_='Box-row')

    for article in articles:
        try:
            h2 = article.find('h2')
            if not h2:
                continue
            link = h2.find('a')
            if not link:
                continue

            repo_path = link.get('href', '').strip('/')
            if not repo_path:
                continue

            repo_url = f"https://github.com/{repo_path}"

            desc_p = article.find('p', class_='col-9')
            description = desc_p.get_text(strip=True) if desc_p else ""

            lang_span = article.find(attrs={'itemprop': 'programmingLanguage'})
            language_name = lang_span.get_text(strip=True) if lang_span else ""

            stars = 0
            forks = 0
            for stat_link in article.find_all('a', class_='Link--muted'):
                svg = stat_link.find('svg')
                if svg:
                    classes = svg.get('class', [])
                    text = stat_link.get_text(strip=True)
                    if 'octicon-star' in classes:
                        stars = parse_number(text)
                    elif 'octicon-repo-forked' in classes:
                        forks = parse_number(text)

            today_stars = 0
            today_stars_span = article.find('span', class_='d-inline-block float-sm-right')
            if today_stars_span:
                match = re.search(r'([\d,]+)\s+stars?\s+today', today_stars_span.get_text())
                if match:
                    today_stars = int(match.group(1).replace(',', ''))

            repos.append({
                "repo": repo_path,
                "description": description,
                "language": language_name,
                "stars": stars,
                "forks": forks,
                "today_stars": today_stars,
                "url": repo_url,
                "date": datetime.date.today().isoformat(),
            })
            logging.info(f"Found: {repo_path} | Stars: {stars} | Today: {today_stars}")

        except Exception as e:
            logging.warning(f"Failed to parse article: {e}")
            continue

    logging.info(f"Scraped {len(repos)} trending repos")
    return repos


def build_md_rows(repos):
    rows = []
    for repo in repos:
        description = repo.get('description', '').replace('|', r'\|')
        if len(description) > 80:
            description = description[:77] + "..."
        rows.append(
            f"| **{repo['repo']}** | {description} | {repo.get('language', '')} "
            f"| {repo.get('stars', 0):,} | {repo.get('forks', 0):,} "
            f"| +{repo.get('today_stars', 0)} | [Link]({repo['url']}) |"
        )
    return rows


def demo(**config):
    language_list = config.get('github_trending', config).get('language_list', [""])
    since = config.get('github_trending', config).get('since', 'daily')
    today = datetime.date.today().isoformat()

    logging.info("GET daily trending begin")

    session = make_session()
    all_repos = []

    for language in language_list:
        lang_name = language if language else "all"
        logging.info(f"Language: {lang_name}")

        try:
            repos = scrape_trending(session, language=language, since=since)
            if not repos:
                logging.warning(f"No repos found for {lang_name}, skipping")
                continue
            all_repos.extend(repos)
        except Exception as e:
            logging.error(f"Failed to fetch trending for {lang_name}: {e}")

    logging.info("GET daily trending end")

    if not all_repos:
        logging.warning("No data collected, skipping file generation")
        return

    json_dir = config.get('json_dir', './json')
    save_json(os.path.join(json_dir, 'github-trending', f"{today}.json"), all_repos)

    md_dir = config.get('md_dir', './md')
    header = "| Project | Description | Language | Stars | Forks | Today | Link |"
    generate_daily_md(
        os.path.join(md_dir, 'github-trending', f"{today}.md"),
        f"GitHub Trending — {today}",
        header,
        build_md_rows(all_repos),
    )

    update_readme_links(os.path.join(md_dir, 'github-trending'),
                        config.get('md_readme_path', 'README.md'),
                        MARKER, LABEL)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_path', type=str, default='config.yaml',
                        help='configuration file path')
    args = parser.parse_args()
    config = load_config(args.config_path)
    demo(**config)
