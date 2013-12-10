#!/usr/bin/env python
# -*- coding: utf-8 -*-
from bookmarks_cloud.whoosh_fts import WhooshBookmarks
import pymongo
db = pymongo.MongoClient().bc_db
WhooshBookmarks(db).rebuild_index()
