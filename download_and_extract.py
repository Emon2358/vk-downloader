#!/usr/bin/env python3
import os
import re
import sys
import argparse
import requests
from bs4 import BeautifulSoup

# User-Agent を設定して静的HTMLを取得しやすくする
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")

def ensure_paths(out_dir, out_txt):
    """out_dir と out_txt の親ディレクトリを作成し、out_txt は空ファイルを用意"""
    os.makedirs(out_dir, exist_ok=True)
    txt_dir = os.path.dirname(out_txt) or "."
    os.makedirs(txt_dir, exist_ok=True)
    # txtファイルが無ければ空ファイルを作成
    if not os.path.exists(out_txt):
        with open(out_txt, "w", encoding="utf-8"):
            pass

def fetch_zip1_links(url, keyword):
    """指定URLのHTMLから、キーワードを含んだ .zip1 リンクを抽出"""
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
    """ファイルをダウンロードして target_dir に保存"""
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
    HTML全文から vk.com/wall-<owner>_<post> のパターンをすべて抽出し
    一意化した URL リストを返す
    """
    resp = requests.get(url, headers={"User-Agent": UA})
    resp.raise_for_status()
    html = resp.text

    # 相対パスと完全パス両方をキャッチ
    rel = re.findall(r'href="(/wall[-\d]+_\d+)"', html)
    full = re.findall(r'(https?://vk\.com/wall[-\d]+_\d+)', html)
    all_links = set()

    for r in rel:
        all_links.add("https://vk.com" + r)
    for f in full:
        all_links.add(f)

    return sorted(all_links)

def save_posts_txt(links, target_file):
    """各URLをタイトル代わりに posts.txt に書き出し"""
    with open(target_file, "w", encoding="utf-8") as f:
        for url in links:
            f.write(f"{url}\t{url}\n")
    print(f"Saved {len(links)} post links to: {target_file}")

def main():
    parser = argparse.ArgumentParser(
        description="VKページから .zip1 ダウンロード＆投稿リンク抽出"
    )
    parser.add_argument("-u", "--url",      required=True, help="VKページURL")
    parser.add_argument("-k", "--keyword",  default="",    help=".zip1に含むキーワード")
    parser.add_argument("-d", "--out-dir",  default="downloads", help=".zip1保存先ディレクトリ")
    parser.add_argument("-t", "--out-txt",  default="posts.txt",  help="投稿リンク保存テキストファイル")
    parser.add_argument("--download", action="store_true", help=".zip1をダウンロード")
    parser.add_argument("--extract",  action="store_true", help="投稿リンクを抽出")
    args = parser.parse_args()

    # ディレクトリと txt ファイルの雛形を必ず作成
    ensure_paths(args.out_dir, args.out_txt)

    # フラグ無し → 両方実行
    if not args.download and not args.extract:
        args.download = args.extract = True

    if args.download:
        print(f"[DOWNLOAD] {args.url} から .zip1 を取得（キーワード='{args.keyword}'）")
        zip_links = fetch_zip1_links(args.url, args.keyword)
        if zip_links:
            for link in zip_links:
                download_file(link, args.out_dir)
        else:
            print("No .zip1 links found.")

    if args.extract:
        print(f"[EXTRACT] {args.url} から投稿リンクを正規表現で抽出")
        links = extract_post_links(args.url)
        if links:
            save_posts_txt(links, args.out_txt)
        else:
            print("No post links found.")

if __name__ == "__main__":
    main()
