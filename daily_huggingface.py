import os
import logging
import argparse
import datetime

from utils import (make_session, load_config, save_json,
                   generate_daily_md, update_readme_links)

HF_MODELS_URL = "https://huggingface.co/api/models"
MARKER = '<!-- HUGGINGFACE -->'
LABEL = 'HF Models'


def fetch_trending_models(session, limit: int):
    params = {
        "sort": "trendingScore",
        "direction": -1,
        "limit": limit,
    }
    logging.info(f"Fetching HF models: {HF_MODELS_URL} (limit={limit})")

    resp = session.get(HF_MODELS_URL, params=params, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"HF request failed with status {resp.status_code}: {HF_MODELS_URL}")

    models = resp.json()
    today = datetime.date.today().isoformat()

    result = []
    for m in models:
        model_id = m.get('id') or m.get('modelId', '')
        if not model_id:
            continue
        result.append({
            "model": model_id,
            "pipeline_tag": m.get('pipeline_tag') or '',
            "library": m.get('library_name') or '',
            "downloads": m.get('downloads', 0),
            "likes": m.get('likes', 0),
            "trending_score": m.get('trendingScore', 0),
            "created_at": m.get('createdAt', ''),
            "url": f"https://huggingface.co/{model_id}",
            "date": today,
        })
        logging.info(f"Found: {model_id} | Trending: {m.get('trendingScore')} | Likes: {m.get('likes')}")

    logging.info(f"Fetched {len(result)} trending models")
    return result


def build_md_rows(models):
    rows = []
    for m in models:
        model = m['model'].replace('|', r'\|')
        rows.append(
            f"| **{model}** | {m.get('pipeline_tag', '')} | {m.get('library', '')} "
            f"| {m.get('downloads', 0):,} | {m.get('likes', 0):,} "
            f"| {m.get('trending_score', 0)} | [Link]({m['url']}) |"
        )
    return rows


def demo(**config):
    cfg = config.get('huggingface', {})
    limit = cfg.get('limit', 30)
    today = datetime.date.today().isoformat()

    logging.info("GET daily huggingface begin")

    session = make_session()
    try:
        models = fetch_trending_models(session, limit)
    except Exception as e:
        logging.error(f"Failed to fetch HF models: {e}")
        return

    if not models:
        logging.warning("No models collected, skipping file generation")
        return

    json_dir = config.get('json_dir', './json')
    save_json(os.path.join(json_dir, 'huggingface', f"{today}.json"), models)

    md_dir = config.get('md_dir', './md')
    header = "| Model | Task | Library | Downloads | Likes | Trending | Link |"
    generate_daily_md(
        os.path.join(md_dir, 'huggingface', f"{today}.md"),
        f"Hugging Face Trending Models — {today}",
        header,
        build_md_rows(models),
    )

    update_readme_links(os.path.join(md_dir, 'huggingface'),
                        config.get('md_readme_path', 'README.md'),
                        MARKER, LABEL)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_path', type=str, default='config.yaml',
                        help='configuration file path')
    args = parser.parse_args()
    config = load_config(args.config_path)
    demo(**config)
