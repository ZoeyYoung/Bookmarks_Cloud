#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pymongo
import json
from tornado import httpclient
from tornado import escape
db = pymongo.Connection().bookmarks_cloud
bookmarks_collection = db.bookmarks
webpages_collection = db.webpages_col
with open('error', 'a+') as error_url:
    i = 1
    http_client = httpclient.HTTPClient()
    for bookmark in bookmarks_collection.find(timeout=False):
            i = i + 1
            webpage = webpages_collection.find_one({'url': bookmark['url']})
            if not webpage:
                print("=====bookmark%d=====%s" % (i, bookmark['url']))
                try:
                    request = httpclient.HTTPRequest(
                        "https://readability.com/api/content/v1/parser?token=7f579fc61973e200632c9e43ff2639234817fbb3&url=" + escape.url_escape(bookmark['url']),
                        method='GET',
                        user_agent='Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1700.6 Safari/537.36'
                    )
                    response = http_client.fetch(request)
                    webpages_collection.save(json.loads(response.body.decode('utf-8')))
                except httpclient.HTTPError as e:
                    print("Error:", e, bookmark['url'], file=error_url)
    http_client.close()
print("=====Update Over=====")
