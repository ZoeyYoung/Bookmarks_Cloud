#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Zoey Young (ydingmiao@gmail.com)"
import logging


def ensure_indexes(sync_db, drop=False):
    if drop:
        logging.info('Dropping indexes...')
        sync_db.bookmarks.drop_indexes()
    from pymongo import ASCENDING, DESCENDING
    sync_db.bookmarks.ensure_index([("post_time", DESCENDING)])
    sync_db.bookmarks.ensure_index([("title", ASCENDING)])
    sync_db.bookmarks.ensure_index([("description", ASCENDING)])
    sync_db.bookmarks.ensure_index([("note", ASCENDING)])
    sync_db.bookmarks.ensure_index([("url", ASCENDING)])
    sync_db.bookmarks.ensure_index([("tags", ASCENDING)])
    sync_db.bookmarks.ensure_index([("owner", ASCENDING), ("random", ASCENDING)])
