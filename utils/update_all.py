#!/usr/bin/env python
# -*- coding: utf-8 -*-
from bookmarks_cloud.models import Bookmark
import pymongo
output = open('except.txt', 'a')
db = pymongo.Connection().bookmarks_cloud
bookmarks_collection = db.bookmarks
i = 1
for bookmark in bookmarks_collection.find(timeout=False):
    try:
        print("=====bookmark%d=====" % i)
        i = i + 1
        bookmark = Bookmark(db).refresh(bookmark)
        # if 'segmentation' not in bookmark:
        #     bookmark = Bookmark.refresh(bookmark)
        if not bookmark['article']:
            print("article not found", bookmark['url'], bookmark['title'], file=output)
    except:
        print("except:", bookmark['url'], bookmark['title'], file=output)

print("=====Update Over=====")
