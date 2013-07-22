#!/usr/bin/env python
# -*- coding: utf-8 -*-
# import urllib2
# from bs4 import BeautifulSoup
from tornado import httpclient
# import lxml.html
# from lxml import etree
from readability.readability import Document
from functools import lru_cache


# 格式化标签
def format_tags(str):
    str = str.replace("|", ",")
    str = str.replace("，", ",")
    tags = str.split(",")
    tags = [tag.strip() for tag in tags]
    tags = [tag for tag in tags if len(tag) > 0]
    tags = list(set(tags))
    return tags


# TODO(Zoey) 需要调整到尽量快, 主要是为了防止连续多次抓取同一个网站
@lru_cache(maxsize=32)
def get_html(url):
    http_client = httpclient.HTTPClient()
    request = httpclient.HTTPRequest(url)
    response = http_client.fetch(request)
    http_client.close()
    return response.body


def get_bookmark_info(url):
    html = get_html(url)
    print(get_html.cache_info())
    # import chardet
    # encoding = chardet.detect(html)['encoding']
    # htmlEl = etree.HTML(html.decode(encoding, 'ignore'))

    # title = htmlEl.find(".//title").text.encode('utf-8')
    title = Document(html).short_title()
    article = Document(html).summary()
    # description = htmlEl.xpath("//meta[translate(@name, 'ABCDEFGHJIKLMNOPQRSTUVWXYZ', 'abcdefghjiklmnopqrstuvwxyz')='description']")
    # if len(description) > 0:
    #     description = description[0].attrib["content"].encode('utf-8')
    # else:
    #     description = ""
    description = Document(html).description()
    keywords = Document(html).keywords()
    # tags = htmlEl.xpath("//meta[translate(@name, 'ABCDEFGHJIKLMNOPQRSTUVWXYZ', 'abcdefghjiklmnopqrstuvwxyz')='keywords']")
    # if len(tags) > 0:
    #     tags = tags[0].attrib["content"].encode('utf-8')
    # else:
    #     tags = ""

    return dict(title=title, favicon="", article=article, description=description, tags=keywords)


# def get_link_info(url):
#     http_client = httpclient.HTTPClient()
#     response = http_client.fetch(url)
#     try:
#         # request = urllib2.Request(url)
#         # request.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1485.0 Safari/537.36')
#         # html_doc = urllib2.urlopen(request, timeout=10)
#         html_doc = response.body
#         soup = BeautifulSoup(html_doc)
#         title = soup.title.string
#         favicon = soup.select('link[href*="fav"]')
#         if len(favicon) > 0:
#             favicon = favicon[0]['href']
#             if not 'http' in favicon:
#                 proto, rest = urllib2.splittype(url)
#                 host, rest = urllib2.splithost(rest)
#                 favicon = proto + '://' + host + favicon
#         description = soup.select('meta[name="description"]')
#         if len(description) > 0:
#             description = description[0]['content']
#         else:
#             description = [text for text in soup.stripped_strings][0]
#         tags = soup.select('meta[name="keywords"]')
#         if len(tags) > 0:
#             tags = tags[0]['content']
#         http_client.close()
#         return dict(title=title, favicon=favicon, description=description, tags=tags)
#     except:
#         return dict(title='', favicon='', description='', tags='')

import math


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
