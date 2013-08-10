#!/usr/bin/env python
# -*- coding: utf-8 -*-
from bookmarks_cloud.whoosh_fts import WhooshBookmarks
import pymongo
db = pymongo.Connection().bookmarks_cloud
WhooshBookmarks(db).rebuild_index()