import os
import re
import json
import glob
import yaml
import logging
import argparse
import datetime

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup

logging.basicConfig(format='[%(asctime)s %(levelname)s] %(message)s',
                    datefmt='%m/%d/%Y %H:%M:%S',
                    level=logging.INFO)

TRENDING_URL = "https://github.com/trending/{language}?since={since}"


def _make_session(retries=3, backoff_factor=0.5, status_forcelist=(429, 500, 502, 503, 504)):
    session = requests.Session()
    retry = Retry(total=retries, backoff_factor=backoff_factor,
                  status_forcelist=status_forcelist, raise_on_status=False)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    return session


def load_config(config_file: str) -> dict:
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    logging.info(f'config = {config}')
    return config


def parse_number(text: str) -> int:
    if not text:
        return 0
    text = text.strip().replace(',', '')
    match = re.search(r'[\d,]+', text)
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

            lang_span = article.find('[itemprop="programmingLanguage"]')
            language_name = lang_span.get_text(strip=True) if lang_span else ""

            stats_section = article.find_all('a', class_='Link--muted')
            stars = 0
            forks = 0

            for stat_link in stats_section:
                svg = stat_link.find('svg')
                if svg:
                    classes = svg.get('class', [])
                    text = stat_link.get_text(strip=True)

                    if 'octicon-star' in classes:
                        stars = parse_number(text)
                    elif 'octicon-repo-forked' in classes:
                        forks = parse_number(text)

            today_stars_span = article.find('span', class_='d-inline-block float-sm-right')
            today_stars = 0
            if today_stars_span:
                today_text = today_stars_span.get_text()
                match = re.search(r'([\d,]+)\s+stars?\s+today', today_text)
                if match:
                    today_stars = int(match.group(1).replace(',', ''))

            repo_data = {
                "repo": repo_path,
                "description": description,
                "language": language_name,
                "stars": stars,
                "forks": forks,
                "today_stars": today_stars,
                "url": repo_url,
                "date": datetime.date.today().isoformat(),
            }

            repos.append(repo_data)
            logging.info(f"Found: {repo_path} | Stars: {stars} | Today: {today_stars}")

        except Exception as e:
            logging.warning(f"Failed to parse article: {e}")
            continue

    logging.info(f"Scraped {len(repos)} trending repos")
    return repos


def save_date_json(filepath, repos):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(repos, f, ensure_ascii=False, indent=2)

    logging.info(f"Saved {len(repos)} repos to {filepath}")


def generate_daily_md(repos, md_path):
    today = datetime.date.today().isoformat()

    os.makedirs(os.path.dirname(md_path), exist_ok=True)

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# GitHub Trending — {today}\n\n")
        f.write(f"[Back to README](../README.md)\n\n")

        if not repos:
            f.write("No trending repos found today.\n")
            return

        f.write(f"## Trending Repositories ({len(repos)} projects)\n\n")
        f.write("| Project | Description | Language | Stars | Forks | Today | Link |\n")
        f.write("|---------|-------------|----------|-------|-------|-------|------|\n")

        for repo in repos:
            repo_name = repo.get('repo', '')
            description = repo.get('description', '').replace('|', r'\|')
            language = repo.get('language', '')
            stars = repo.get('stars', 0)
            forks = repo.get('forks', 0)
            today_stars = repo.get('today_stars', 0)
            url = repo.get('url', '')

            if len(description) > 80:
                description = description[:77] + "..."

            f.write(f"| **{repo_name}** | {description} | {language} | {stars:,} | {forks:,} | +{today_stars} | [Link]({url}) |\n")

        f.write('\n')

    logging.info(f"Generated {md_path} with {len(repos)} repos")


def update_readme_links(md_dir, readme_path):
    md_files = sorted(glob.glob(os.path.join(md_dir, '*.md')), reverse=True)
    if not md_files:
        return

    rows = []
    for fp in md_files:
        date_str = os.path.splitext(os.path.basename(fp))[0]
        count = 0
        with open(fp, encoding='utf-8') as f:
            for line in f:
                if line.startswith('| **'):
                    count += 1
        rows.append((date_str, count, os.path.relpath(fp, os.path.dirname(readme_path))))

    marker = '<!-- DAILY_TRENDING -->'
    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        content = ''

    if marker in content:
        header = content[:content.index(marker) + len(marker)]
    else:
        header = content + '\n' + marker

    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(header)
        f.write('\n\n## Daily Trending\n\n')
        f.write('| Date | Repos | Link |\n')
        f.write('|------|-------|------|\n')
        for date_str, count, rel_path in rows:
            f.write(f'| {date_str} | {count} | [Trending]({rel_path}) |\n')
        f.write('\n')

    logging.info(f"Updated README links with {len(rows)} daily entries")


def demo(**config):
    language_list = config.get('language_list', [""])
    since = config.get('since', 'daily')
    today = datetime.date.today().isoformat()

    logging.info("GET daily trending begin")

    session = _make_session()
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
    date_json = os.path.join(json_dir, f"github-trending-{today}.json")
    save_date_json(date_json, all_repos)

    md_dir = config.get('md_dir', './md')
    date_md = os.path.join(md_dir, f"{today}.md")
    generate_daily_md(all_repos, date_md)

    readme_path = config.get('md_readme_path', 'README.md')
    update_readme_links(md_dir, readme_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_path', type=str, default='config.yaml',
                        help='configuration file path')
    args = parser.parse_args()
    config = load_config(args.config_path)
    demo(**config)
