#!/usr/bin/env python
from goose import Goose
#　url = 'http://edition.cnn.com/2012/02/22/world/europe/uk-occupy-london/index.html?hpt=ieu_c2'
url = "http://linux.chinaunix.net/"
# url = "http://www.keakon.net/category/Python"
# url = "http://www.oschina.net/news/46288/microsoft-should-open-windows-phone"
g = Goose({'debug': True})
article = g.extract(url=url)
# output = open('test_output.txt', 'a+')
# print(article.title, file=output)
# print(article.meta_description, file=output)
# print(article.meta_keywords, file=output)
# print(article.cleaned_text, file=output)
# print(article.tags, file=output)
