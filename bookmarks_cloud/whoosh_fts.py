import os
from whoosh.analysis import Tokenizer,Token
import jieba
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, ID, KEYWORD
from whoosh import qparser

class ChineseTokenizer(Tokenizer):
    def __call__(self, value, positions=False, chars=False,
                 keeporiginal=False, removestops=True,
                 start_pos=0, start_char=0, mode='', **kwargs):
        # assert isinstance(value, text_type), "%r is not unicode" % value
        t = Token(positions, chars, removestops=removestops, mode=mode,
            **kwargs)
        seglist=jieba.cut_for_search(value)
        #使用结巴分词库进行分词
        for w in seglist:
            t.original = t.text = w
            t.boost = 1.0
            if positions:
                t.pos=start_pos+value.find(w)
            if chars:
                t.startchar=start_char+value.find(w)
                t.endchar=start_char+value.find(w)+len(w)
            yield t  #通过生成器返回每个分词的结果token


def ChineseAnalyzer():
    return ChineseTokenizer()


class SearchIndex(object):
    """
    Object utilising Whoosh (http://woosh.ca/) to create a search index of all
    crawled rss feeds, parse queries and search the index for related mentions.
    """
    def __init__(self):
        """
        Instantiate the whoosh schema and writer and create/open the index.
        """
        # get the absolute path and create the dir if required
        if not os.path.exists("index"):
            os.mkdir("index")
            create_in("index", self.get_schema(), indexname="bookmarks")
        # create an index obj and buffered writer
        self.ix = open_dir("index", indexname="bookmarks")


    def get_schema(self):
        return Schema(
            nid=ID(unique=True, stored=True),
            url=ID(unique=True, stored=True),
            title=TEXT(stored=True, phrase=False),
            tags=KEYWORD,
            note=TEXT(stored=True, analyzer=ChineseAnalyzer()),
            article=TEXT(stored=True, analyzer=ChineseAnalyzer())
        )


    def commit(self, writer):
        """
        Commit the data to index.
        """
        writer.commit()
        return True

    def update(self, bookmark):
        """
        Add an item to the index. If commit is set to False, remember to commit
        the data to the index manually using self.commit().
        """
        # instantiate the writer
        writer = self.ix.writer()
        # add the document to the search index and commit
        writer.update_document(
            nid=str(bookmark['_id']),
            url=bookmark['url'],
            title=bookmark['title'],
            tags=bookmark['tags'],
            note=bookmark['note'],
            article=bookmark['article']
        )
        self.commit(writer)

    def get(self, id):
        """
        Get an index object by its hashed id.
        """
        with self.ix.searcher() as searcher:
            result = searcher.document(uid=id)
            searcher.close()
            return result

    def parse_query(self, query):
        """
        Parses the the string query into a usable format.
        """
        parser = qparser.MultifieldParser(["url", "title", "tags", "note", "article"], self.ix.schema)
        return parser.parse(query)

    def search(self, query, page):
        """
        Search the index and return the results list to be processed further.
        """
        results = []
        with self.ix.searcher() as searcher:
            page = searcher.search_page(self.parse_query(query), page, pagelen=20)
            # create a results list from the search results
            for result in page.results:
            # for result in searcher.search(self.parse_query(query)):
                results.append(dict(result))
        return { 'results': results, 'total': page.total }


    def delele_by_url(self, url):
        self.ix.delete_by_term('url', url)
        self.ix.commit()


    def close(self):
        """
        Closes the searcher obj. Must be done manually.
        """
        self.ix.close()

