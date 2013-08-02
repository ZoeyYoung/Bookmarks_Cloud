#!/usr/bin/env python
# -*- coding: utf-8 -*-
from bookmarks_cloud.models import Bookmark
from bookmarks_cloud.config import config
output = open('except.txt', 'a')

bookmarks_collection = config['db'].bookmarks

for bookmark in bookmarks_collection.find(timeout=False):
    try:
        if not bookmark['article']:
            bookmark = Bookmark.refresh(bookmark)
        if not bookmark['article'] or bookmark['article'] == '':
            print(bookmark['url'], bookmark['title'], file=output)
    except:
        print(bookmark['url'], bookmark['title'], file=output)

print("=====Update Over=====")