#!/usr/bin/env python3
"""
Relay 10 public Google Drive image links through GitHub Pages and publish
as an Instagram carousel via Buffer's GraphQL API.

Modes:
  --stage-only    Download GDrive images into docs/images/<batch_id>/ and write manifest.json
  --publish-only  Publish the staged manifest.json GitHub Pages URLs to Buffer
  (default)       Run both stage and publish (for local use after Pages is live)
"""

import argparse
import json
import os
import sys
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image

PAGES_BASE_URL = "https://swaltnuscord-sketch.github.io/thriving-allegedly-image-host/images"
DEFAULT_CHANNEL_ID = "6afbe91bece6dfde5ff25adf"
DEFAULT_STAGING_FILE = "staging/gdrive_batch.json"


def download_gdrive_image(url: str, dest_path: Path) -> None:
    session = requests.Session()
    headers = {"User-Agent": "Mozilla/5.0 (compatible; ThrivingAllegedlyRelay/1.0)"}
    resp = session.get(url, headers=headers, allow_redirects=True, timeout=45)
    resp.raise_for_status()

    content_type = resp.headers.get("Content-Type", "")
    if "text/html" in content_type.lower():
        raise ValueError(f"Expected image from {url}, got HTML (check Drive public sharing)")

    img = Image.open(BytesIO(resp.content)).convert("RGB")
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest_path, format="JPEG", quality=92)


def stage_batch(staging_path: Path) -> Path:
    data = json.loads(staging_path.read_text(encoding="utf-8"))
    batch_id = data["batch_id"]
    caption = data.get("caption", "")
    gdrive_urls = data["gdrive_urls"]

    if not gdrive_urls or len(gdrive_urls) > 10:
        raise ValueError(f"Expected 1-10 gdrive_urls, got {len(gdrive_urls)}")

    batch_dir = Path("docs/images") / batch_id
    batch_dir.mkdir(parents=True, exist_ok=True)

    pages_urls = []
    for idx, url in enumerate(gdrive_urls, start=1):
        filename = f"slide_{idx:02d}.jpg"
        dest = batch_dir / filename
        print(f"Downloading slide {idx}/{len(gdrive_urls)} -> {dest}")
        download_gdrive_image(url, dest)
        pages_urls.append(f"{PAGES_BASE_URL}/{batch_id}/{filename}")

    manifest_path = batch_dir / "manifest.json"
    manifest = {
        "batch_id": batch_id,
        "caption": caption,
        "gdrive_urls": gdrive_urls,
        "slides": pages_urls,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Staged manifest at {manifest_path}")
    return manifest_path


def publish_manifest(manifest_path: Path, channel_id: str, mode: str) -> None:
    token = os.environ.get("BUFFER_API_KEY")
    if not token:
        raise RuntimeError("Missing BUFFER_API_KEY environment variable")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    slides = manifest["slides"]
    caption = manifest.get("caption", "")

    mutation = """
    mutation CreatePost($input: CreatePostInput!) {
      createPost(input: $input) {
        ... on PostActionSuccess {
          post { id text status }
        }
        ... on MutationError { message }
      }
    }
    """

    ig_type = "carousel" if len(slides) > 1 else "post"
    variables = {
        "input": {
            "channelId": channel_id,
            "text": caption,
            "schedulingType": "automatic",
            "mode": mode,
            "assets": [{"image": {"url": u}} for u in slides],
            "metadata": {
                "instagram": {
                    "type": ig_type,
                    "shouldShareToFeed": True,
                }
            },
        }
    }

    resp = requests.post(
        "https://api.buffer.com",
        json={"query": mutation, "variables": variables},
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )
    resp.raise_for_status()
    res_json = resp.json()
    print("Buffer Response:", json.dumps(res_json, indent=2))

    create_post = res_json.get("data", {}).get("createPost", {})
    if "errors" in res_json or "message" in create_post:
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Relay GDrive carousel to GitHub Pages and Buffer")
    parser.add_argument("--staging-file", default=DEFAULT_STAGING_FILE)
    parser.add_argument("--channel-id", default=os.environ.get("CHANNEL_ID", DEFAULT_CHANNEL_ID))
    parser.add_argument("--mode", default="shareNow", choices=["shareNow", "addToQueue", "shareNext"])
    parser.add_argument("--stage-only", action="store_true")
    parser.add_argument("--publish-only", action="store_true")
    args = parser.parse_args()

    staging_path = Path(args.staging_file)
    data = json.loads(staging_path.read_text(encoding="utf-8"))
    manifest_path = Path("docs/images") / data["batch_id"] / "manifest.json"

    if not args.publish_only:
        manifest_path = stage_batch(staging_path)
    if not args.stage_only:
        publish_manifest(manifest_path, args.channel_id, args.mode)


if __name__ == "__main__":
    main()
