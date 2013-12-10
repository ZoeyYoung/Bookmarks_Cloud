#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Zoey Young (ydingmiao@gmail.com)"
import logging


def ensure_indexes(sync_db, drop=False):
    if drop:
        logging.info('Dropping indexes...')
        sync_db.bookmarks_col.drop_indexes()
        sync_db.webpages_col.drop_indexes()
    from pymongo import ASCENDING, DESCENDING
    sync_db.bookmarks_col.ensure_index([("post_time", DESCENDING)])
    sync_db.bookmarks_col.ensure_index([("title", ASCENDING)])
    sync_db.bookmarks_col.ensure_index([("excerpt", ASCENDING)])
    sync_db.bookmarks_col.ensure_index([("note", ASCENDING)])
    sync_db.bookmarks_col.ensure_index([("url", ASCENDING)])
    sync_db.bookmarks_col.ensure_index([("tags", ASCENDING)])
    sync_db.bookmarks_col.ensure_index([("owner", ASCENDING), ("random", ASCENDING)])
    sync_db.webpages_col.ensure_index([("url", ASCENDING)], unique=True, drop_dups=True)
