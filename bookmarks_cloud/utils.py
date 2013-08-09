#!/usr/bin/env python
# -*- coding: utf-8 -*-
from tornado import httpclient
from functools import lru_cache
from readability.readability import Document
import math
import re
import jieba
import jieba.analyse
import logging
# import urllib

log = logging.getLogger('bookmarks_cloud_log')

jieba.initialize()

# 格式化标签
def format_tags(str):
    tags = re.split('[,，|]', str)
    tags = [tag.strip() for tag in tags]
    tags = [tag for tag in tags if len(tag) > 0]
    tags = list(set(tags))
    return tags


@lru_cache(maxsize=32)
def fetch_url(url):
    request = httpclient.HTTPRequest(
        url,
        method='GET',
        headers={"content-type": "text/html", 'Referer': 'http://www.google.com', "Accept": "*/*"},
        request_timeout=10,
        follow_redirects=True,
        user_agent='Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1485.0 Safari/537.36',
        allow_ipv6=True
    )
    return httpclient.AsyncHTTPClient().fetch(request)


def video_site(url):
    players_settings = {
        r'http://v\.youku\.com/v_show/id_(\S+)\.html': '<div><iframe class="video_player" src="http://player.youku.com/embed/%s?wmode=transparent" frameborder=0 allowfullscreen wmode="transparent"></iframe></div>',
        r'http://www\.xiami\.com/song/(\d+).*': '<div><embed src="http://www.xiami.com/widget/0_%s/singlePlayer.swf" type="application/x-shockwave-flash" width="257" height="33" wmode="transparent"></embed></div>',
        r'http://www\.xiami\.com/album/(\d+).*': '<div><embed src="http://www.xiami.com/widget/0_%s_235_346_FF8719_494949/albumPlayer.swf" type="application/x-shockwave-flash" width="235" height="346" wmode="transparent"></embed></div>',
        r'http://v\.ku6\.com/show/(\S+)\.\.\.html.*': '<div><embed src="http://player.ku6.com/refer/%s../v.swf" class="video_player" allowscriptaccess="always" wmode="transparent" allowfullscreen="true" type="application/x-shockwave-flash" flashvars="from=ku6"></embed></div>',
        r'http://v\.qq\.com/cover/.+/.+\.html\?vid=(\w+)': '<div><embed src="http://static.video.qq.com/TPout.swf?vid=%s&auto=0" allowFullScreen="true" quality="high" width="480" height="400" wmode="transparent" align="middle" allowScriptAccess="always" type="application/x-shockwave-flash"></embed></div>',
        r'http://v\.qq\.com/cover/.+/.+/(\w+)\.html': '<div><embed src="http://static.video.qq.com/TPout.swf?vid=%s&auto=0" allowFullScreen="true" quality="high" width="480" height="400" wmode="transparent" align="middle" allowScriptAccess="always" type="application/x-shockwave-flash"></embed></div>',
        r'http://www\.yinyuetai\.com/video/(\d+)': '<div><embed src="http://player.yinyuetai.com/video/player/%s/v_2932937.swf" class="video_player" quality="high" align="middle" wmode="transparent" allowScriptAccess="sameDomain" allowfullscreen="true" type="application/x-shockwave-flash"></embed></div>'
    }
    for (k, v) in players_settings.items():
        p = re.compile(k, re.I)
        m = p.match(url)
        if m:
            html = v % (m.group(1))
            return html
        else:
            return None


def get_bookmark_info(url, html=None):
    if not html:
        # html = get_html(url)
        # if not html:
        print("Error: html is None", url)
        return None
    doc = Document(html, url=url, debug=True, multipage=False)
    summary_obj = doc.summary_with_metadata(enclose_with_html_tag=False)
    title = summary_obj.short_title
    article = video_site(url)
    if article is None:
        article = summary_obj.html
    description = summary_obj.description
    keywords_t = []
    keywords_a = []
    segmentation = ''
    segmentation_t = ''
    segmentation_a = ''
    if title:
        keywords_t = get_keywords(title)
        segmentation_t = text_segmentation(title)
    if article:
        keywords_a = get_keywords(article)
        segmentation_a = text_segmentation(article)
    keywords = keywords_t + keywords_a
    segmentation = segmentation_t + segmentation_a
    if summary_obj.keywords:
        keywords = keywords + format_tags(summary_obj.keywords)
    if keywords:
        keywords = ",".join(set(keywords))
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
    return words


def get_keywords(article):
    if not article:
        return ''
    return jieba.analyse.extract_tags(text_content(article), 10)


def get_tags_cloud(tags):
    max_count = max(tag['count'] for tag in tags)
    if max_count < 2:
        max_count = 2
    return [{'tag': tag, 'font_size': round(math.log(tag['count'], max_count), 1)*14 + 8} for tag in tags if tag['count'] > 0]
