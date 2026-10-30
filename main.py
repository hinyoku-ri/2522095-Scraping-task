"""武蔵野大学Webサイトのサイトマップ抽出

トップページから同じドメインのリンクをたどり、
全ページの URL と <title> を辞書に保存して CSV に書き出す。
"""
import csv
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# 武蔵野大学のトップページ
START_URL = "https://www.musashino-u.ac.jp/"

# サーバーへの負荷を減らすための待ち時間（秒）
SLEEP_SEC = 1

# 保存するCSVファイル名
CSV_NAME = "sitemap_titles.csv"

# HTMLではないファイル（ダウンロードしても意味がないもの）
SKIP_EXT = (".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".zip",
            ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".mp3", ".mp4")

# 同じドメインかどうか確認するために使う
domain = urlparse(START_URL).netloc

# key: URL, value: <title></title>で挟まれた文字列
data = {}


def clean_url(url):
    """URLを整える（#以降を削除し、httpをhttpsに統一する）"""
    url = url.split("#")[0]
    if url.startswith("http://"):
        url = "https://" + url[len("http://"):]
    return url


def is_target(url):
    """たどるべきURLか判定する"""
    parsed = urlparse(url)
    if parsed.scheme != "https":      # mailto: や tel: などを除く
        return False
    if parsed.netloc != domain:       # 同一ドメインのみ
        return False
    if parsed.path.lower().endswith(SKIP_EXT):
        return False
    return True


def save_csv():
    """辞書の内容をCSVに保存する"""
    # utf-8-sig にするとExcelで開いても文字化けしない
    with open(CSV_NAME, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["URL", "Title"])
        for page_url, title in data.items():
            writer.writerow([page_url, title])


def main():
    to_visit = [clean_url(START_URL)]   # これから調べるURL
    seen = set(to_visit)                # 一度でも予定に入れたURL（重複防止）

    try:
        while to_visit:
            current_url = to_visit.pop(0)

            time.sleep(SLEEP_SEC)       # アクセスの前に必ず待つ
            try:
                response = requests.get(current_url, timeout=10)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                print("アクセスエラー:", current_url, e)
                continue

            # HTML以外は飛ばす
            if "text/html" not in response.headers.get("Content-Type", "").lower():
                continue

            response.encoding = response.apparent_encoding
            soup = BeautifulSoup(response.text, "html.parser")

            # <title>を取得して辞書に保存
            title = soup.title.get_text(strip=True) if soup.title else ""
            data[current_url] = title
            print(f"[{len(data)}] {current_url} : {title}")

            # ページ内のリンクを集める
            for a in soup.find_all("a", href=True):
                new_url = clean_url(urljoin(current_url, a["href"]))
                if is_target(new_url) and new_url not in seen:
                    seen.add(new_url)
                    to_visit.append(new_url)

            # 100ページごとに途中保存（止まってもデータが残るように）
            if len(data) % 100 == 0:
                save_csv()

    except KeyboardInterrupt:
        print("\nCtrl+Cで中断しました。ここまでの結果を保存します。")

    save_csv()
    print(f"完了: {len(data)} ページを {CSV_NAME} に保存しました")


if __name__ == "__main__":
    main()