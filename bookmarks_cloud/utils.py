#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Zoey Young (ydingmiao@gmail.com)"
__about__ = """
应用中的一些功能函数
"""
from tornado import httpclient
from functools import lru_cache
from readability import htmls
from readability.readability import Document, Summary, get_clean_html
import math
import re
import jieba
import jieba.analyse
import logging
import json
import html.parser
html_parser = html.parser.HTMLParser()
from .config import LOG, DB
# import urllib
log = logging.getLogger(LOG)
predefine_sites_collection = DB.predefine_sites
jieba.initialize()

# 格式化标签
def format_tags(str=None):
    if str is None:
        str = ''
    tags = re.split('[,，|]', str)
    tags = [tag.strip() for tag in tags]
    tags = [tag for tag in tags if len(tag) > 0]
    tags = list(set([tag.upper() for tag in tags]))
    return tags

def readability_parser(url):
    """使用readability的API
    教程: http://www.readability.com/developers/api/parser
    """
    request = httpclient.HTTPRequest(
        "https://readability.com/api/content/v1/parser?token=7f579fc61973e200632c9e43ff2639234817fbb3&url=" + url,
        method='GET',
        user_agent='Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1700.6 Safari/537.36'
    )
    return httpclient.AsyncHTTPClient().fetch(request)

@lru_cache(maxsize=32)
def fetch_webpage(url):
    """抓取网页
    Args:
        url: 网址
    Returns:
        HTTPResponse
    """
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


def get_html_str(url, html=None):
    if not html:
        response = fetch_webpage(url)
        response = response.result()
        html = response.body
        if not html:
            print("Error: html is None", url)
            return "<html><head><title>Ooops, 抓取网页失败.</title></head><body>Ooops, 抓取网页失败.</body></html>"
    return html

def predefined_site(url, html):
    print(url, "=====================predefined_site？")
    pds = predefine_sites_collection.find()
    for pd in pds:
        if re.compile(pd['url_pattern'], re.I).search(url) is not None:
            print(url, "=====================predefined_site")
            doc = htmls.build_doc(html)
            for tag in doc.iter():
                allelem = doc.iter()
                for elem in allelem:
                    s = "%s %s" % (elem.get('class', ''), elem.get('id', ''))
                    if re.compile(pd['content_css']).search(s) is not None:
                        print(url, "=====================predefined_site", htmls.get_keywords(doc)+','+','.join(pd['tags']))
                        return Summary(get_clean_html(elem),
                           '',
                           short_title=htmls.shorten_title(doc),
                           title=htmls.get_title(doc),
                           description=htmls.get_description(doc),
                           keywords=htmls.get_keywords(doc)+','+','.join(pd['tags']))
    return None


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


def get_webpage_by_readability(url, readability):
    if readability:
        webpage = json.loads(readability.decode("utf-8"))
        webpage["favicon"] = ""
        webpage["tags"] = get_suggest_tags(webpage['title'], webpage['content'])
        webpage["segmentation"] = get_segmentation(webpage['title'], webpage['content'])
        webpage['excerpt'] = html_parser.unescape(webpage['excerpt'])
        return webpage
    else:
        print("Error: In get_bookmark_info_by_readability")


def get_webpage_by_html(url, html=None):
    html = get_html_str(url, html)
    summary_obj = predefined_site(url, html)
    article = video_site(url)
    if summary_obj is None:
        doc = Document(html, url=url, debug=True, multipage=False)
        summary_obj = doc.summary_with_metadata(enclose_with_html_tag=False)
    title = summary_obj.short_title
    if article is None:
        article = summary_obj.html
    return {
        "url": url,
        "short_url": url,
        "domain": url, # 这个应该可以根据URL生成
        "favicon": "",
        "title": title,
        "author" : None,
        "lead_image_url" : None,
        "excerpt" : summary_obj.description,
        "content": article,
        "segmentation" : get_segmentation(title, article),
        "tags": get_suggest_tags(title, article, summary_obj.keywords),
        "next_page_id": None,
        "direction" : "ltr",
        "dek" : None,
        "word_count": None,
        "total_pages" : 0,
        "date_published": None,
        "rendered_pages": 1,
    }


def get_suggest_tags(title, content, keywords_meta=None):
    """根据标题和内容获取推荐标签"""
    if keywords_meta is None:
        keywords_meta = ''
    if title is None:
        title = ''
    if content is None:
        content = ''
    # 关键字获取
    keywords_title = jieba.analyse.extract_tags(text_content(title), 10)
    keywords_content = jieba.analyse.extract_tags(text_content(content), 10)
    keywords = keywords_title + keywords_content + format_tags(keywords_meta)
    keywords = ",".join(set(keywords))
    # TODO: 还需要进行一系列处理
    return keywords


def get_segmentation(title, content):
    if title is None:
        title = ''
    if content is None:
        content = ''
    return text_segmentation(title + content)


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
