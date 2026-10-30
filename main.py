import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import csv

# 武蔵野大学のホームページ
url = "https://www.musashino-u.ac.jp/"

# 調べるURLを保存するリスト
url_list = [url]

# 調べたURLを保存するリスト
visited = []

# URLとタイトルを保存する辞書
data = {}

# 同じドメインか確認する
domain = urlparse(url).netloc


# CSVファイルに保存する
def save_csv():
    with open("sitemap_titles.csv", "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)

        writer.writerow(["URL", "Title"])

        for page_url, title in data.items():
            writer.writerow([page_url, title])


# Webサイトを巡回する
try:
    while len(url_list) > 0:

        # リストからURLを取り出す
        current_url = url_list.pop(0)

        # すでに調べたURLは飛ばす
        if current_url in visited:
            continue

        visited.append(current_url)

        try:
            # サーバーへの負担を減らす
            time.sleep(1)

            # Webページにアクセスする
            response = requests.get(current_url, timeout=10)
            response.raise_for_status()

            # HTML以外のファイルは飛ばす
            content_type = response.headers.get("Content-Type", "")

            if "text/html" not in content_type.lower():
                continue

            response.encoding = response.apparent_encoding

            # HTMLを解析する
            soup = BeautifulSoup(response.text, "html.parser")

            # titleタグを取得する
            if soup.title:
                title = soup.title.get_text(strip=True)
            else:
                title = ""

            # URLとタイトルを辞書に保存する
            data[current_url] = title

            print("URL:", current_url)
            print("Title:", title)
            print("--------------------")

            # ページ内のリンクを取得する
            links = soup.find_all("a", href=True)

            for link in links:

                # 相対URLを絶対URLに変換する
                new_url = urljoin(current_url, link["href"])

                # #以降を取り除く
                new_url = new_url.split("#")[0]

                # 同じドメインのリンクだけを追加する
                if urlparse(new_url).netloc == domain:

                    # httpとhttpsのURLだけを対象にする
                    if urlparse(new_url).scheme in ["http", "https"]:

                        # 重複していないURLを追加する
                        if new_url not in visited and new_url not in url_list:
                            url_list.append(new_url)

        except requests.exceptions.RequestException as e:
            print("アクセスエラー:", current_url)
            print(e)

        # 50ページごとにCSVを保存する
        if len(visited) % 50 == 0:
            save_csv()
            print("途中保存しました:", len(data))

# Ctrl + Cで停止した場合
except KeyboardInterrupt:
    print("\nプログラムを停止しました。")


# 最後にCSVファイルを保存する
save_csv()

print("\n--- 完了 ---")
print("確認したURL数:", len(visited))
print("保存したページ数:", len(data))
print("CSVファイル: sitemap_titles.csv")