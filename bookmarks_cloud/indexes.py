#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging


def ensure_indexes(sync_db, drop=False):
    if drop:
        logging.info('Dropping indexes...')
        sync_db.links.drop_indexes()
    from pymongo import ASCENDING, DESCENDING
    sync_db.links.ensure_index([("post_time", DESCENDING)])
    sync_db.links.ensure_index([("title", ASCENDING)])
    sync_db.links.ensure_index([("description", ASCENDING)])
    sync_db.links.ensure_index([("note", ASCENDING)])
    sync_db.links.ensure_index([("url", ASCENDING)])
    sync_db.links.ensure_index([("tags", ASCENDING)])
    sync_db.links.ensure_index([("random", ASCENDING)])
