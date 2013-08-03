#!/usr/bin/env python
# -*- coding: utf-8 -*-
from tornado import httpclient
from readability.readability import Document
from functools import lru_cache
import math
import re
import jieba
import jieba.analyse
import logging
import urllib

log = logging.getLogger('bookmarks_cloud_log')

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
    # request.add_header()
    # html_doc = urllib2.urlopen(request, timeout=10)
    # url = parse_url(url)
    http_client = httpclient.HTTPClient()
    try:
        request = httpclient.HTTPRequest(
            url,
            method='GET',
            headers={"content-type": "text/html", "Referer": 'http://www.baidu.com'},
            # body=None,
            # auth_username=None,
            # auth_password=None,
            # auth_mode=None,
            # connect_timeout=60,
            request_timeout=60,
            # if_modified_since=None,
            follow_redirects=True,
            # max_redirects=None,
            user_agent='Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1485.0 Safari/537.36',
            # use_gzip=None,
            # network_interface=None,
            # streaming_callback=None,
            # header_callback=None,
            # prepare_curl_callback=None,
            # proxy_host=None,
            # proxy_port=None,
            # proxy_username=None,
            # proxy_password=None,
            # allow_nonstandard_methods=None,
            # validate_cert=False,
            # ca_certs=None,
            allow_ipv6=True,
            # client_key=None,
            # client_cert=None
        )
        response = http_client.fetch(request)
    except httpclient.HTTPError as e:
        log.debug("Error In get_html func:", url, e.code)
        response = None
    http_client.close()
    if not response:
        return None
    return response.body


# def parse_url(url):
#     url = urllib.quote(url.split('#')[0].encode('utf8'), safe="%/:=&?~#+!$,;'@()*[]")
#     return url


def get_bookmark_info(url, html=None):
    if not html:
        html = get_html(url)
        # log.info(get_html.cache_info())
        if not html:
            log.error("Error: html is None", url)
            return dict(html='', title='[html is null]', favicon="", article="[no-article]", description="[something wrong happened]", tags="")
    doc = Document(html, url=url, debug=True, multipage=False)
    summary_obj = doc.summary_with_metadata(enclose_with_html_tag=False)
    title = summary_obj.short_title
    article = summary_obj.html
    description = summary_obj.description
    keywords = get_keywords(str(title) + str(article))
    if keywords:
        keywords = ",".join(keywords) + ',' + summary_obj.keywords
    else:
        keywords = summary_obj.keywords
    if title and article:
        segmentation = text_segmentation(str(title) + str(article))
    elif title:
        segmentation = text_segmentation(str(title))
    else:
        segmentation = ' '
    bookmark = dict(html=html, title=title, favicon="", article=article, segmentation=segmentation, description=description, tags=keywords)
    return bookmark


def text_content(s):
    if not s:
        return ''
    s = re.sub(r'<pre>.*</pre>', '', s)
    s = re.sub(r'</?\w+[^>]*>', '', s)
    return ' '.join(s.split())


def text_segmentation(article):
    if not article:
        return ''
    words = "/ ".join(jieba.cut(text_content(article)))
    return words.encode('utf-8')


def get_keywords(article):
    if not article:
        return ''
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
