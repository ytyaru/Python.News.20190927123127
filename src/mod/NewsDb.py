import sqlite3
import os
import operator

class NewsDb:
    def __init__(self, path):
        self.conn = sqlite3.connect(path)
#        self.conn.row_factory = sqlite3.Row
        self.create_table()
        self.news = []
    def __del__(self): self.conn.close()
    def create_table(self):    
        cur = self.conn.cursor()
        cur.executescript(self.__create_table_sql())
    def __create_table_sql(self):
        return '''
create table if not exists news(
  id         integer primary key,
  published  text, 
  url        text,
  title      text,
  body       text, -- URL先から本文だけを抽出したプレーンテキスト
  UNIQUE(published,url) -- 記事の一意確認
);
create index if not exists idx_news on 
  news(published desc, url, title, id desc);
create table if not exists sources(
  id       integer primary key,
  domain   text, -- URLのドメイン名
  name     text, -- 情報源名
  created  text  -- 登録日時（同一ドメイン名が複数あるとき新しいほうを表示する）
);
create index if not exists idx_sources on 
  sources(domain, created desc, id desc, name);
'''
    def __insert_sql(self): 
        return 'insert or ignore into news(published,url,title,body) values(?,?,?,?)'
    def append_news(self, published, url, title, body):
        self.news.append((published, url, title, body))
    def insert(self):
        if 0 == len(self.news): return
        try:
            self.news = sorted(self.news, key=operator.itemgetter(1)) # 第2キー: URL昇順
            self.news = sorted(self.news, key=operator.itemgetter(0), reverse=True) # 第1キー: 公開日時降順
            self.conn.cursor().executemany(self.__insert_sql(), self.news)
            self.conn.commit()
        except: # それ以外
            import traceback
            traceback.print_exc()
            self.conn.rollback() # ロールバックする
        finally: self.news.clear()

