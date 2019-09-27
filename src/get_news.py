#!/usr/bin/env python3
# coding: utf8
# PythonでRSSからニュースを取得しSQLite3DBに保存する。
# stdin  : 必須。RSS URL
# 第1引数: 任意。SQLite3DBファイルパス（デフォルト＝カレントディレクトリ/news.db）
# 例1: echo -e 'RSS1\nRSS2\nRSS3' | python3 get_news.py ./news.db
# 例2: cat feeds_source1.txt   | python3 get_news.py ./news.db
import sys
import os
import feedparser
from mod import DateTimeString
from mod import HtmlGetter
from mod import HtmlContentExtractor
from mod import FeedsDb
from mod import NewsSummaryDb
from mod import NewsDb
from mod import NewsImagesDb

# 標準入力がなければ永久に待機してしまう！
feeds = [line.strip() for line in sys.stdin.readlines()]
if 0 == len(feeds):
    raise Error(("stdinにRSSのURLを指定してください。コード例は以下。\n" + 
                "echo 'RSS1' | python3 get_news.py" + 
                "echo -e 'RSS1\nRSS2\nRSS3' | python3 get_news.py ./news.db\n" + 
                "cat feeds_source1.txt   | python3 get_news.py ./news.db\n" + 
                "第1引数にSQLite3DBファイル出力パスを指定できます。デフォルトは「./news.db」です。"))
    exit()
newsDb_path = sys.argv[1] if (1 < len(sys.argv)) else os.path.join(os.getcwd(), 'news.db')

def has_def(obj, attr, default): 
    return getattr(obj, attr) if hasattr(obj, attr) else default

feedsDb_path = '/tmp/work/feeds.db'
summaryDb_path = '/tmp/work/news_summary.db'
os.makedirs(os.path.dirname(feedsDb_path), exist_ok=True)
os.makedirs(os.path.dirname(summaryDb_path), exist_ok=True)
dtCnv = DateTimeString.DateTimeString()
feedsDb = FeedsDb.FeedsDb(feedsDb_path)
summaryDb = NewsSummaryDb.NewsSummaryDb(summaryDb_path)
newsDb = NewsDb.NewsDb(newsDb_path)

# 概要（フィード内容）のみ取得
for feed in feeds:
    print('feed: ' + feed)
    latest_published = feedsDb.get_latest(feed)
    entries = feedparser.parse(feed).entries
    entries.sort(key=lambda entry: has_def(entry, 'published', entry.updated), reverse=True)
    for entry in entries:
        published = dtCnv.convert_utc((
            has_def(entry, 'published', entry.updated))
            ).strftime('%Y-%m-%dT%H:%M:%SZ')
        url = entry.link
        title = entry.title
        if latest_published is not None and published < latest_published: break
        if summaryDb.is_exists(published, url, title): continue
        summary = has_def(entry, 'summary', '')
        summaryDb.append_news(published,url,title,summary=summary)
    feedsDb.append(feed, dtCnv.convert_utc((
        has_def(entries[0], 'published', entries[0].updated))
        ).strftime('%Y-%m-%dT%H:%M:%SZ'))
    summaryDb.insert() # :memory:へ
feedsDb.upsert_ram()
summaryDb.marge() # 指定パスへ

# 取得したフィードのうちDB内の最新日時より新しいエントリのみ取得する
newer_entries = summaryDb.get_memory_news()
print('len(newer_entries): {}'.format(len(newer_entries)))

# ファイルDBへ挿入する（本文抽出も）
extractor = HtmlContentExtractor.HtmlContentExtractor(option={"threshold":50})
getter = HtmlGetter.HtmlGetter()
for entry in newer_entries:
    url, html = getter.get(entry['url']) # 「続きを読む」があればURLが変わる
    body = extractor.extract(html)
    newsDb.append_news(entry['published'], url, entry['title'], body)
newsDb.insert()

