import os
import time
import logging
import argparse
import datetime
import xml.etree.ElementTree as ET

from utils import (make_session, load_config, save_json,
                   generate_daily_md, update_readme_links)

ARXIV_API_URL = "http://export.arxiv.org/api/query"
ATOM_NS = "{http://www.w3.org/2005/Atom}"
ARXIV_NS = "{http://arxiv.org/schemas/atom}"
MARKER = '<!-- ARXIV -->'
LABEL = 'arXiv'


def fetch_arxiv_papers(session, categories, limit):
    cat_query = " OR ".join(f"cat:{c}" for c in categories)
    params = {
        "search_query": cat_query,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": limit,
    }
    logging.info(f"Fetching arXiv papers: categories={categories}, limit={limit}")

    resp = session.get(ARXIV_API_URL, params=params, timeout=120)
    if resp.status_code != 200:
        raise RuntimeError(f"arXiv API returned {resp.status_code}")

    root = ET.fromstring(resp.text)
    entries = root.findall(f"{ATOM_NS}entry")
    today = datetime.date.today().isoformat()

    result = []
    for entry in entries:
        title_el = entry.find(f"{ATOM_NS}title")
        if title_el is None or not title_el.text:
            continue
        title = " ".join(title_el.text.strip().split())

        authors = []
        for author in entry.findall(f"{ATOM_NS}author"):
            name_el = author.find(f"{ATOM_NS}name")
            if name_el is not None and name_el.text:
                authors.append(name_el.text.strip())

        summary_el = entry.find(f"{ATOM_NS}summary")
        summary = " ".join(summary_el.text.strip().split()) if summary_el is not None and summary_el.text else ""

        cats = []
        for cat in entry.findall(f"{ARXIV_NS}category"):
            term = cat.get("term", "")
            if term:
                cats.append(term)

        published_el = entry.find(f"{ATOM_NS}published")
        published = published_el.text.strip() if published_el is not None and published_el.text else ""

        pdf_url = ""
        abs_url = ""
        for link in entry.findall(f"{ATOM_NS}link"):
            if link.get("title") == "pdf":
                pdf_url = link.get("href", "")
            elif link.get("type") == "text/html":
                abs_url = link.get("href", "")
        if not abs_url:
            id_el = entry.find(f"{ATOM_NS}id")
            abs_url = id_el.text.strip() if id_el is not None and id_el.text else ""

        result.append({
            "title": title,
            "authors": ", ".join(authors[:5]) + ("..." if len(authors) > 5 else ""),
            "summary": summary[:200],
            "categories": ", ".join(cats[:5]),
            "published": published[:10],
            "pdf_url": pdf_url,
            "abs_url": abs_url,
            "date": today,
        })
        logging.info(f"Found: {title[:60]} | {cats[:3]}")

    logging.info(f"Fetched {len(result)} arXiv papers")
    return result


def build_md_rows(items):
    rows = []
    for p in items:
        title = p["title"].replace("|", r"\|")
        rows.append(
            f"| **{title}** | {p['authors']} "
            f"| {p['categories']} | {p['published']} "
            f"| [PDF]({p['pdf_url']}) / [Abs]({p['abs_url']}) |"
        )
    return rows


def demo(**config):
    cfg = config.get("arxiv", {})
    categories = cfg.get("categories", ["cs.AI", "cs.CL", "cs.LG", "cs.CV"])
    limit = cfg.get("limit", 30)
    today = datetime.date.today().isoformat()

    logging.info("GET daily arxiv begin")

    session = make_session()
    try:
        papers = fetch_arxiv_papers(session, categories, limit)
    except Exception as e:
        logging.error(f"Failed to fetch arXiv papers: {e}")
        return

    if not papers:
        logging.warning("No papers collected, skipping file generation")
        return

    json_dir = config.get("json_dir", "./json")
    save_json(os.path.join(json_dir, "arxiv", f"{today}.json"), papers)

    md_dir = config.get("md_dir", "./md")
    header = "| Title | Authors | Categories | Published | Link |"
    generate_daily_md(
        os.path.join(md_dir, "arxiv", f"{today}.md"),
        f"arXiv Latest Papers — {today}",
        header,
        build_md_rows(papers),
    )

    update_readme_links(os.path.join(md_dir, "arxiv"),
                        config.get("md_readme_path", "README.md"),
                        MARKER, LABEL)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config_path", type=str, default="config.yaml",
                        help="configuration file path")
    args = parser.parse_args()
    config = load_config(args.config_path)
    demo(**config)
