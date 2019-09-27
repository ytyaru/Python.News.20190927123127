import datetime
import pytz # pip3 install pytz
import re

class DateTimeString:
    def __init__(self):
        self.__re_dt = re.compile(r"(\d{4}[-/]\d{2}[-/]\d{2}[T ]\d{2}:\d{2}:\d{2})")
        self.__re_milli = re.compile(r"\.\d{1,}")
    def convert_utc(self, date_str):
        return self.convert(date_str).astimezone(pytz.timezone('UTC'))
    def convert(self, date_str):
        try: return self.__to_datetime_from_rfc1123(date_str)
        except ValueError: return self.__to_datetime_from_rfc3339(date_str)
    def __to_datetime_from_rfc1123(self, rfc1123):
        return datetime.datetime.strptime(rfc1123, '%a, %d %b %Y %H:%M:%S %z')
    # ISO-8601拡張っぽいテキストをdatetimeへ変換して返す
    def __to_datetime_from_rfc3339(self, rfc3339):
        m = self.__re_dt.search(rfc3339)
        if m is None: raise Exception('解析できませんでした。: ' + rfc3339 + "\n次の正規表現に一致するようにしてください。秒以下やタイムゾーンが必要ならこれ以降に記してください。: " + self.__re_dt.pattern)
        dt_str = m.group(0)
        tz_str = rfc3339.replace(dt_str, '')
        tz_str = self.__re_milli.sub("", tz_str) # ミリ秒以下があれば削除
        if '' == tz_str: return self.__case_local_time(dt_str + tz_str)
        if 'Z' == tz_str: return self.__case_utc_time(dt_str + tz_str)
        tz_str = tz_str.replace(':', '') # タイムゾーンのコロンを削除（Python3.7より前でも%zマッチさせるため）
        dt_str = dt_str.replace('/', '-') # 書式を統一するため
        dt_str = dt_str.replace(' ', 'T') # 書式を統一するため
        dt = datetime.datetime.strptime(dt_str + tz_str, '%Y-%m-%dT%H:%M:%S%z')
        return dt
    # 「yyyy-mm-dd HH:MM:SS」ならシステムのローカルタイムゾーンを指定する
    def __case_local_time(self, date_str):
        from tzlocal import get_localzone # pip3 install tzlocal
        return (datetime.datetime.strptime(
                    date_str, '%Y-%m-%d %H:%M:%S')
                .replace(tzinfo=get_localzone()))
    # 「yyyy-mm-dd HH:MM:SS」ならUTCタイムゾーンを指定する
    def __case_utc_time(self, date_str):
        return (datetime.datetime.strptime(
                    date_str, '%Y-%m-%dT%H:%M:%SZ')
               .replace(tzinfo=pytz.timezone('UTC')))

