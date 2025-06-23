#!/usr/bin/env python3
import os
import re
import sys
import argparse
import requests
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " \
     "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"

def fetch_zip1_links(url, keyword):
    """指定URLのHTMLから、キーワードを含んだ .zip1 リンクを抽出する"""
    resp = requests.get(url, headers={"User-Agent": UA})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.endswith(".zip1") and keyword in href:
            if href.startswith("/"):
                href = "https://vk.com" + href
            links.append(href)
    return links

def download_file(url, target_dir):
    """ファイルをダウンロードして target_dir に保存する"""
    os.makedirs(target_dir, exist_ok=True)
    local_name = os.path.join(target_dir, os.path.basename(url))
    with requests.get(url, headers={"User-Agent": UA}, stream=True) as r:
        r.raise_for_status()
        with open(local_name, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    print(f"Downloaded: {local_name}")
    return local_name

def extract_post_links(url):
    """
    モバイル版ページから /wall-xxx_yyy リンクを正規表現で抽出
    → タイトル:URL をリストで返す
    """
    # モバイル版に差し替え
    mobile_url = url.replace("vk.com", "m.vk.com")
    resp = requests.get(mobile_url, headers={"User-Agent": UA})
    resp.raise_for_status()
    html = resp.text

    # パターンにマッチするリンクをすべて抽出
    matches = set(re.findall(r'href="(/wall[-\d]+_\d+)"', html))
    posts = []
    for href in matches:
        full_url = "https://vk.com" + href
        # タイトル取得（なければURLをタイトルとして使う）
        soup = BeautifulSoup(html, "html.parser")
        a = soup.find("a", href=href)
        title = (a.get_text().strip() if a and a.get_text().strip() else full_url)
        posts.append((title, full_url))

    return posts

def save_posts_txt(posts, target_file):
    """(タイトル, URL)リストをtarget_fileに保存"""
    os.makedirs(os.path.dirname(target_file) or ".", exist_ok=True)
    with open(target_file, "w", encoding="utf-8") as f:
        for title, url in posts:
            f.write(f"{title}\t{url}\n")
    print(f"Saved post links to: {target_file}")

def main():
    parser = argparse.ArgumentParser(description="VKページから.zip1ダウンロード＆投稿リンク抽出")
    parser.add_argument("--url",    "-u", required=True, help="VKの投稿ページURL")
    parser.add_argument("--keyword","-k", default="", help=".zip1リンクに含めるキーワード")
    parser.add_argument("--out-dir","-d", default="downloads", help="ダウンロード保存先ディレクトリ")
    parser.add_argument("--out-txt","-t", default="posts.txt", help="投稿リンクのタイトルとURLを保存するテキストファイル")
    parser.add_argument("--download", action="store_true", help=".zip1をダウンロード")
    parser.add_argument("--extract",  action="store_true", help="投稿リンクを抽出してテキスト保存")
    args = parser.parse_args()

    # 両方フラグが無い場合は両方実行
    if not args.download and not args.extract:
        args.download = args.extract = True

    if args.download:
        print(f"[DOWNLOAD] Fetching .zip1 links from {args.url} (keyword='{args.keyword}')")
        zip_links = fetch_zip1_links(args.url, args.keyword)
        if zip_links:
            for link in zip_links:
                download_file(link, args.out_dir)
        else:
            print("No .zip1 links found.")

    if args.extract:
        print(f"[EXTRACT] Extracting post links from {args.url}")
        posts = extract_post_links(args.url)
        if posts:
            save_posts_txt(posts, args.out_txt)
        else:
            print("No post links found.")

if __name__ == "__main__":
    main()
