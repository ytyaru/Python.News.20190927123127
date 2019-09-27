import sqlite3
import os
import operator
# フィード内容をDBにする。本文取得が完了するまでの間だけ使う予定（本文取得が10分以上と遅すぎるため）
# RAMディスクに配置する想定
class NewsSummaryDb:
    def __init__(self, path):
        self.__schema_ram = 'r'
        self.conn = sqlite3.connect(':memory:')
        self.conn.cursor().execute("attach '"+path+"' as '"+self.__schema_ram+"';")
        self.conn.row_factory = sqlite3.Row
        self.__create_table()
        self.__create_table(schema_name=self.__schema_ram)
        self.__latest_row = self.__get_latest_row(schema_name=self.__schema_ram)
        self.news = []
    def __del__(self): self.conn.close()
    @property
    def LatestRow(self): return self.__latest_row
    # schema_name: main, temp, (attach-db-name)
    def __schema_name(self, schema_name=None): return (
        '' if schema_name is None or 0 == len(schema_name) else (schema_name 
           if schema_name.endswith('.') else schema_name + '.'))
    def __create_table(self, schema_name=''):
        cur = self.conn.cursor()
        cur.executescript(self.__create_table_sql(schema_name=schema_name))
    def __create_table_sql(self, schema_name=''):
        return '''
create table if not exists {schema_name}news(
  id         integer primary key,
  published  text not null,
  url        text not null,
  title      text not null,
  summary    text not null default '',
  UNIQUE(url,title) -- 記事の一意確認
);
create index if not exists {schema_name}idx_news on 
  news(published desc, url, title, id desc);
'''.format(schema_name=self.__schema_name(schema_name))
    def __get_latest_sql(self, schema_name=''): return '''
with 
  latest(max_published) as (select max(published) max_published from {schema_name}news),
  maximum(max_id) as (
    select max(id) as max_id
    from {schema_name}news,latest
    where {schema_name}news.published=latest.max_published
  )
select 
  {schema_name}news.published, 
  {schema_name}news.url, 
  {schema_name}news.title
from {schema_name}news,maximum
where {schema_name}news.id=maximum.max_id;
'''.format(schema_name=self.__schema_name(schema_name))
    def __get_latest_row(self, schema_name=''):
        return self.conn.cursor().execute(self.__get_latest_sql(schema_name=self.__schema_ram)).fetchone()
    def __insert_sql(self, schema_name=''): 
        return 'insert or ignore into {schema_name}news(published,url,title,summary) values(?,?,?,?)'.format(schema_name=self.__schema_name(schema_name))
    def __is_exists_sql(self, published, url, title, schema_name=''): 
        return """
select exists(
  select * 
  from {schema_name}news 
  where published='{published}' 
    and url='{url}' and title='{title}') as is_exists;
""".format(schema_name=self.__schema_name(schema_name), 
            published=published, url=url, title=title)
    def is_exists(self, published, url, title):
        if self.__latest_row is None: return False
        if self.__latest_row['published'] < published: return True
        result = self.conn.cursor().execute(
            self.__is_exists_sql(published, url, title, self.__schema_ram), 
            ).fetchone()['is_exists']
        print(result)
        return True if 1 == result else False
    def append_news(self, published, url, title, summary=''):
        self.news.append((published, url, title, summary))
    def __get_news_sql(self, schema_name='', published=''):
        where = ''
        if published is not None and 0 < len(published.strip()): 
            where = " where published > '" + published + "'"
        return 'select published,url,title from {schema_name}news {where};'.format(schema_name=self.__schema_name(schema_name), where=where)
#    # 今回のプロセスで取得した全フィードを返す（feeds表の最終公開日時より新しいエントリのみ）
    def get_memory_news(self):
        return self.conn.cursor().execute(self.__get_news_sql()).fetchall()
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
    def __marge_sql(self):
        return 'insert or ignore into {schema_ram}news(published,url,title,summary) select published,url,title,summary from {schema_mem}news;'.format(
            schema_ram=self.__schema_name(self.__schema_ram),
            schema_mem=''
        )
    # インメモリDBからRAMディスクDBへ
    def marge(self):
        try:
            self.conn.cursor().execute(self.__marge_sql())
            self.conn.commit()
            self.__latest_row = self.__get_latest_row(schema_name=self.__schema_ram)
        except sqlite3.IntegrityError as err_sql_integ:
            import traceback
            import sys
            msg = str(err_sql_integ.with_traceback(sys.exc_info()[2])).lower() # UNIQUE constraint failed: news.published, news.url
            # DB既存と重複した時点で中断する（それまでの挿入データはそのままにしたいのでロールバックしない）
            if ('UNIQUE'.lower() in msg and 'published' in msg and 'url' in msg): pass
            # それ以外ならエラー表示＆ロールバックする
            else: 
                traceback.print_exc()
                self.conn.rollback() 
        except: # それ以外
            import traceback
            traceback.print_exc()
            self.conn.rollback() # ロールバックする

