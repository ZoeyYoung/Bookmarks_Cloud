#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Zoey Young (ydingmiao@gmail.com)"
import os
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, ID, KEYWORD
from whoosh.analysis import Tokenizer, Token
from whoosh import qparser
from .config import *
from jieba.analyse import ChineseAnalyzer

analyzer = ChineseAnalyzer()


class WhooshBookmarks(object):

    """
    Object utilising Whoosh (http://woosh.ca/) to create a search index of all
    crawled rss feeds, parse queries and search the index for related mentions.
    """

    def __init__(self, db):
        """
        Instantiate the whoosh schema and writer and create/open the index.
        """
        self.bookmarks_collection = db.bookmarks_col
        self.webpages_collection = db.webpages_col
        self.indexdir = "index"
        self.indexname = "bookmarks"
        self.schema = self.get_schema()
        if not os.path.exists(self.indexdir):
            os.mkdir(self.indexdir)
            create_in(self.indexdir, self.schema, indexname=self.indexname)
        # create an index obj and buffered writer
        self.ix = open_dir(self.indexdir, indexname=self.indexname)

    def get_schema(self):
        return Schema(
            nid=ID(unique=True, stored=True),
            url=ID(unique=True, stored=True),
            title=TEXT(phrase=False),
            tags=KEYWORD(lowercase=True, commas=True, scorable=True),
            note=TEXT(analyzer=analyzer),
            content=TEXT(stored=True, analyzer=analyzer)
        )

    def rebuild_index(self):
        ix = create_in(self.indexdir, self.schema, indexname=self.indexname)
        writer = ix.writer()
        for bookmark in self.bookmarks_collection.find(timeout=False):
            webpage = self.webpages_collection.find_one({'_id': bookmark['webpage']})
            if webpage:
                writer.update_document(
                    nid=str(bookmark['_id']),
                    url=bookmark['url'],
                    title=bookmark['title'],
                    tags=bookmark['tags'],
                    note=bookmark['note'],
                    content=webpage['content']
                )
        writer.commit()

    def commit(self, writer):
        """
        Commit the data to index.
        """
        writer.commit()
        return True

    def update(self, bookmark, webpage, writer=None):
        if writer is None:
            writer = self.ix.writer()
        writer.update_document(
            nid=str(bookmark['_id']),
            url=bookmark['url'],
            title=bookmark['title'],
            tags=bookmark['tags'],
            note=bookmark['note'],
            content=webpage['content']
        )
        writer.commit()

    def parse_query(self, query):
        parser = qparser.MultifieldParser(
            ["url", "title", "tags", "note", "content"], self.ix.schema)
        return parser.parse(query)

    def search(self, query, page):
        """
        Search the index and return the results list to be processed further.
        """
        results = []
        with self.ix.searcher() as searcher:
            result_page = searcher.search_page(
                self.parse_query(query), page, pagelen=PAGE_SIZE)
            # create a results list from the search results
            for result in result_page:
            # for result in searcher.search(self.parse_query(query)):
                results.append(dict(result))
        return {'results': results, 'total': result_page.total}

    def delele_by_url(self, url):
        writer = self.ix.writer()
        result = writer.delete_by_term('url', url)
        writer.commit()
        return result

    def close(self):
        """
        Closes the searcher obj. Must be done manually.
        """
        self.ix.close()
