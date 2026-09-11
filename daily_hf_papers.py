import os
import logging
import argparse
import datetime

from utils import (make_session, load_config, save_json,
                   generate_daily_md, update_readme_links)

HF_PAPERS_URL = "https://huggingface.co/api/daily_papers"
MARKER = '<!-- HF_PAPERS -->'
LABEL = 'HF Papers'


def fetch_hf_papers(session, date_str, limit):
    params = {"date": date_str}
    logging.info(f"Fetching HF daily papers for {date_str} (limit={limit})")

    resp = session.get(HF_PAPERS_URL, params=params, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"HF Papers API returned {resp.status_code}")

    papers = resp.json()
    if isinstance(papers, dict):
        papers = papers.get("papers", [])

    if not papers:
        yesterday = (datetime.date.fromisoformat(date_str) - datetime.timedelta(days=1)).isoformat()
        logging.info(f"No papers for {date_str}, trying {yesterday}")
        resp = session.get(HF_PAPERS_URL, params={"date": yesterday}, timeout=60)
        if resp.status_code == 200:
            papers = resp.json()
            if isinstance(papers, dict):
                papers = papers.get("papers", [])
            date_str = yesterday

    result = []
    for p in papers[:limit]:
        paper = p.get("paper", p)
        authors_list = paper.get("authors", [])
        authors = ", ".join(
            a.get("name", "") for a in authors_list[:5]
        ) + ("..." if len(authors_list) > 5 else "")

        paper_id = paper.get("id", "")
        paper_url = f"https://huggingface.co/papers/{paper_id}" if paper_id else ""
        arxiv_url = f"https://arxiv.org/abs/{paper_id}" if paper_id else ""

        result.append({
            "title": paper.get("title", "") or p.get("title", ""),
            "authors": authors,
            "summary": (paper.get("summary") or p.get("summary") or "")[:200],
            "upvotes": paper.get("upvotes", 0),
            "url": paper_url,
            "paper_url": arxiv_url,
            "published_at": (paper.get("publishedAt") or "")[:10],
            "date": date_str,
        })
        logging.info(f"Found: {paper.get('title', '')[:60]} | Upvotes: {paper.get('upvotes', 0)}")

    logging.info(f"Fetched {len(result)} HF daily papers")
    return result


def build_md_rows(items):
    rows = []
    for p in items:
        title = p["title"].replace("|", r"\|")
        rows.append(
            f"| **[{title}]({p['url']})** | {p['authors']} "
            f"| {p['upvotes']} | [arXiv]({p['paper_url']}) |"
        )
    return rows


def demo(**config):
    cfg = config.get("hf_papers", {})
    limit = cfg.get("limit", 30)
    today = datetime.date.today().isoformat()

    logging.info("GET daily hf papers begin")

    session = make_session()
    try:
        papers = fetch_hf_papers(session, today, limit)
    except Exception as e:
        logging.error(f"Failed to fetch HF papers: {e}")
        return

    if not papers:
        logging.warning("No papers collected, skipping file generation")
        return

    json_dir = config.get("json_dir", "./json")
    save_json(os.path.join(json_dir, "hf-papers", f"{today}.json"), papers)

    md_dir = config.get("md_dir", "./md")
    header = "| Title | Authors | Upvotes | Link |"
    generate_daily_md(
        os.path.join(md_dir, "hf-papers", f"{today}.md"),
        f"Hugging Face Daily Papers — {today}",
        header,
        build_md_rows(papers),
    )

    update_readme_links(os.path.join(md_dir, "hf-papers"),
                        config.get("md_readme_path", "README.md"),
                        MARKER, LABEL)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config_path", type=str, default="config.yaml",
                        help="configuration file path")
    args = parser.parse_args()
    config = load_config(args.config_path)
    demo(**config)
