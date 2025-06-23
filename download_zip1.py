#!/usr/bin/env python3
import os
import re
import sys
import requests
from bs4 import BeautifulSoup

def fetch_links(url, keyword):
    """指定URLのHTMLから、キーワードを含んだ .zip1 リンクを抽出する"""
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.endswith(".zip1") and keyword in href:
            links.append(href)
    return links

def download_file(url, target_dir):
    """ファイルをダウンロードして target_dir に保存する"""
    os.makedirs(target_dir, exist_ok=True)
    local_name = os.path.join(target_dir, url.split("/")[-1])
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_name, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    print(f"Downloaded: {local_name}")
    return local_name

def main():
    VK_URL   = os.environ.get("VK_URL")
    KEYWORD  = os.environ.get("KEYWORD", "")
    OUT_DIR  = os.environ.get("OUT_DIR", "downloads")

    if not VK_URL:
        print("Error: VK_URL is not set", file=sys.stderr)
        sys.exit(1)

    print(f"Fetching links from {VK_URL} containing keyword '{KEYWORD}'…")
    links = fetch_links(VK_URL, KEYWORD)
    if not links:
        print("No matching .zip1 links found.")
        sys.exit(0)

    for link in links:
        # vk.comの相対パス対策
        if link.startswith("/"):
            link = "https://vk.com" + link
        download_file(link, OUT_DIR)

if __name__ == "__main__":
    main()
