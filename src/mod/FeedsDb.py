import sqlite3
import os
import operator
# フィードマスターDB
class FeedsDb:
    def __init__(self, path):
        self.__schema_ram = 'r'
        self.conn = sqlite3.connect(':memory:')
        self.conn.cursor().execute("attach '"+path+"' as '"+self.__schema_ram+"';")
        self.conn.row_factory = sqlite3.Row
        self.__create_table()
        self.__create_table(schema_name=self.__schema_ram)
        self.feeds = []
    def __del__(self): self.conn.close()
    # schema_name: main, temp, (attach-db-name)
    def __schema_name(self, schema_name=None): return (
        '' if schema_name is None or 0 == len(schema_name) else (schema_name 
           if schema_name.endswith('.') else schema_name + '.'))
    def __create_table(self, schema_name=''):
        cur = self.conn.cursor()
        cur.executescript(self.__create_table_sql(schema_name=schema_name))
    def __create_table_sql(self, schema_name=''):
        return '''
create table if not exists {schema_name}feeds(
  id               integer primary key,
  url              text not null unique,
  latest_published text not null default ''
);'''.format(schema_name=self.__schema_name(schema_name))
    def __get_id_sql(self, url, schema_name=''): return """
select id
from {schema_name}feeds
where url='"+url+"';""".format(schema_name=self.__schema_name(schema_name))
    def get_id(self, url):
        row = self.conn.cursor().execute(self.__get_id_sql(url, schema_name=self.__schema_ram)).fetchone()
        if row is None: raise Exception('指定したURLは未登録です。append(), insert(), upsert()で予め登録してください。: {}'.format(url))
        return row['id']
    def __get_latest_sql(self, url, schema_name=''): return """
select latest_published 
from {schema_name}feeds
where url='{url}';""".format(schema_name=self.__schema_name(schema_name), url=url)
    def get_latest(self, url):
        row = self.conn.cursor().execute(self.__get_latest_sql(url, schema_name=self.__schema_ram)).fetchone()
        return None if row is None else row['latest_published']
    def append(self, url, latest_published):
        self.feeds.append({'url': url, 'latest_published': latest_published})
    def __upsert(self, schema_name=''):
        try:
            # https://sfnovicenotes.blogspot.com/2019/07/sqlite3-on-conflict.html
            # やりたいことはinsert on conflict。だが、SQLite 3.24.0以降でないと使えない
#            return '''
#insert into {schema_name}feeds(url,latest_published) values(?,?) 
#on conflict(url) do update set latest_published=?'''.format(schema_name=self.__schema_name(schema_name))
            self.conn.cursor().executemany(
"insert or ignore into {schema_name}feeds(url,latest_published) values(:url,:latest_published);".format(schema_name=self.__schema_name(schema_name)), self.feeds)
            self.conn.cursor().executemany("""
update {schema_name}feeds 
  set latest_published=:latest_published 
  where url=:url and latest_published < :latest_published;""".format(schema_name=self.__schema_name(schema_name)), self.feeds)
            self.conn.commit()
        except:
            import traceback
            traceback.print_exc()
            self.conn.rollback()
        finally: self.feeds.clear()
    def upsert_memory(self): self.__upsert()
    def upsert_ram(self): self.__upsert(schema_name=self.__schema_ram)

