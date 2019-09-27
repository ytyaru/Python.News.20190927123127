#!/usr/bin/env python3
# coding: utf8
import sys
import os
from readability.readability import Document
import html2text

class HtmlContentExtractor:
    def __init__(self, option=None):
        self.__html = None
        self.__text = None
        self.__md = None
    @property
    def Title(self): return self.__title
    @property
    def Html(self): return self.__html
    @property
    def Markdown(self): return self.__md
    @property
    def Text(self): return self.__text
    def extract(self, html):
        # https://github.com/buriy/python-readability/blob/master/readability/readability.py
        doc = Document(html)
        self.__title = doc.title()
        self.__html = doc.summary()
        self.__md = html2text.html2text(self.__html)
        self.__text = self.__format_to_text(self.__html)
        return self.__text
    def __format_to_text(self, html):
        import re
        import unicodedata
        st = re.sub(r"<p>([^　])", r"　\1", html) # 段落の先頭は全角スペース
        st = re.sub(r"</p>", "\n\n", st) # 段落の末尾は2つ改行する
        st = re.sub(r"</br>", "\n", st)
        st = re.sub(r"<br>", "\n", st)
        st = re.sub(r"<.+?>", "", st)
        # Convert from wide character to ascii
        if st and type(st) != str: st = unicodedata.normalize("NFKC", st)
        st = re.sub(r"[\u2500-\u253f\u2540-\u257f]", "", st)  # 罫線(keisen)
#        st = re.sub(r"&(.*?);", lambda x: self.CHARREF.get(x.group(1), x.group()), st)
        st = re.sub(r"[ \t]+", " ", st)
        return st.strip()

