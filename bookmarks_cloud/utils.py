#!/usr/bin/env python
# -*- coding: utf-8 -*-
from tornado import httpclient
from readability.readability import Document
from functools import lru_cache
import math
import re
import jieba
import jieba.analyse


jieba.initialize()


# 格式化标签
def format_tags(str):
    tags = re.split('[,，|]', str)
    tags = [tag.strip() for tag in tags]
    tags = [tag for tag in tags if len(tag) > 0]
    tags = list(set(tags))
    return tags


# TODO(Zoey) 需要调整到尽量快, 主要是为了防止连续多次抓取同一个网站
@lru_cache(maxsize=32)
def get_html(url):
    # request = urllib2.Request(url)
    # request.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1485.0 Safari/537.36')
    # html_doc = urllib2.urlopen(request, timeout=10)
    http_client = httpclient.HTTPClient()
    try:
        request = httpclient.HTTPRequest(url)
        response = http_client.fetch(request)
    except httpclient.HTTPError as e:
        print("Error In get_html func:", url, e)
        response = None
    http_client.close()
    if not response:
        return None
    return response.body


def get_bookmark_info(url, html=None):
    if html is '':
        html = get_html(url)
        print(get_html.cache_info())
    if not html:
        print("Error: html is None")
        return dict(title='', favicon="", article="[no-article]", description="[no-description]", tags="")
    doc = Document(html, url=url, debug=True, multipage=False)
    summary_obj = doc.summary_with_metadata(enclose_with_html_tag=False)
    title = summary_obj.short_title
    # print(summary_obj.title)
    # print(summary_obj.short_title)
    article = summary_obj.html
    description = summary_obj.description
    keywords = ",".join(get_keywords(summary_obj.title + article)) + ',' + summary_obj.keywords
    segmentation = text_segmentation(summary_obj.title + article)
    # print(title, description, keywords)
    bookmark = dict(title=title, favicon="", article=article, segmentation=segmentation, description=description, tags=keywords)
    return bookmark


def text_content(s):
    if not s:
        return ''
    s = re.sub(r'<pre>.*</pre>', '', s)
    s = re.sub(r'</?\w+[^>]*>', '', s)
    return ' '.join(s.split())


def text_segmentation(article):
    words = "/ ".join(jieba.cut(text_content(article)))
    return words.encode('utf-8')


def get_keywords(article):
    return jieba.analyse.extract_tags(text_content(article), 10)


def get_tags_cloud(tags):
    tags_cloud = []
    max = 2
    for tag in tags:
        if max < tag['count']:
            max = tag['count']
    for tag in tags:
        if tag['count'] > 0:
            temp = math.log(tag['count'], max)
        else:
            temp = 0
        font_size = round(temp, 1)*14 + 8
        tags_cloud.append({'tag': tag, 'font_size': font_size})
    return tags_cloud
