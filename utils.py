import os
import json
import glob
import yaml
import logging

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(format='[%(asctime)s %(levelname)s] %(message)s',
                    datefmt='%m/%d/%Y %H:%M:%S',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def make_session(retries=3, backoff_factor=0.5, status_forcelist=(429, 500, 502, 503, 504)):
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
    logger.info(f'config = {config}')
    return config


def save_json(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved {filepath}")


def generate_daily_md(md_path, title, table_header, rows):
    os.makedirs(os.path.dirname(md_path), exist_ok=True)

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# {title}\n\n")
        f.write("[Back to README](../README.md)\n\n")

        if not rows:
            f.write("No data found today.\n")
            return

        f.write(table_header + "\n")
        f.write("|" + "---|" * (table_header.count("|") - 1) + "\n")
        for row in rows:
            f.write(row + "\n")

        f.write("\n")

    logger.info(f"Generated {md_path} with {len(rows)} rows")


def update_readme_links(md_dir, readme_path, marker, label):
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

    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        content = ''

    if marker in content:
        header = content[:content.index(marker) + len(marker)]
        rest = content[content.index(marker) + len(marker):]
        next_marker_pos = _find_next_section(rest)
        if next_marker_pos != -1:
            tail = rest[next_marker_pos:]
        else:
            tail = ''
    else:
        header = content + '\n' + marker
        tail = ''

    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(header)
        f.write(f"\n\n## {label} Daily\n\n")
        f.write('| Date | Count | Link |\n')
        f.write('|------|-------|------|\n')
        for date_str, count, rel_path in rows:
            f.write(f'| {date_str} | {count} | [{label}]({rel_path}) |\n')
        f.write('\n')
        f.write(tail)

    logger.info(f"Updated README section [{label}] with {len(rows)} daily entries")


def _find_next_section(text):
    markers = ['<!-- DAILY_TRENDING -->', '<!-- HACKER_NEWS -->',
               '<!-- HUGGINGFACE -->', '<!-- GITHUB_STARS -->',
               '<!-- REDDIT -->', '<!-- ARXIV -->', '<!-- DEVTO -->',
               '<!-- LOBSTERS -->', '<!-- HF_PAPERS -->']
    positions = [text.index(m) for m in markers if m in text]
    return min(positions) if positions else -1
