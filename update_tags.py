#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pymongo

bookmarks_collection = pymongo.Connection().bookmarks_cloud.bookmarks_col

# tags_dict = {
#     "Ajax": ["ajax"],
#     "Apache": ["Apach", "apache"],
#     "论坛": ["bbs", "BBS"],
#     "博客": ["Blog", "blog", "BLOG"],
#     "Chrome": ["chrome"],
#     "Chrome扩展": ["chrome extensions", "chrome扩展"],
#     "CSS": ["css", "div+css布局"],
#     "CSS3": ["css3"],
#     "Drupal": ["Drupal CMS", "drupal", "drupal7", "drupalchina", "drupal中国", "drupal中文社区", "drupal中国", "drupal花园"],
#     "div": ["Div"],
#     "ExtJS": ["extjs", "EXTJS"],
#     "Flex": ["flex"],
#     "Firefox": ["firefox"],
#     "Font": ["Fonts", "font", "font-face"],
#     "Git": ["git", "gitshell", "git app", "git client", "git gui"],
#     "GitHub": ["github", "Github"],
#     "HTML": ["html"],
#     "HTML5": ["html5"],
#     "JSON": ["json"],
#     "jQuery": ["jquery"],
#     "jQuery插件": ["jQuery Plugin", "jquery插件"],
#     "Java": ["java"],
#     "Java EE": ["J2EE"],
#     "Jekyll": ["jekyll"],
#     "JavaScript": ["javascript", "js", "JS"],
#     "MongoDB": ["mongodb", "mongoDB"],
#     "PHP": ["php"],
#     "Python": ["python"],
#     "Python2": ["python2"],
#     "Python3": ["python3"],
#     "Ruby": ["ruby", "Ruby Gems", "ruby dev"],
#     "Tornado": ["tornado"],
#     "Unicode": ["unicode"],
#     "Web": ["web"],
#     "W3C": ["w3c"]
# }
"""获得所有标签，以及链接数"""
# from bson.son import SON
# tags = bookmarks_collection.aggregate([
#     {"$unwind": "$tags"},
#     {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
#     {"$sort": SON([("_id", 1), ("count", -1)])}
# ])
# tags = tags['result']
# for tag in tags:
remove_list = ["QUEUE","RADIX","RAPHAELZHANG","READ","REFERENCE","REGEXBUDDY","REGULAR","REMAERD","REMOTING","RENDERED","REQ","REQUEST","RESP","RESPONSE","RESULTS","RETURNED","ROCK","ROTATION","ROW","RT","RTC","RUNNING","Ruby","SB","SCRAPY","SCRIPT","SCROLLTOP","SE","SEARCHER","SEGMENTFAULT","SET","SF","SHORT","SHOULD","SIMPLE","SINCE","SKINS","SMALLSEG","STACK_OVERFLOW","STATIC","STORY","STR","STRING","STRUCTURE","STRUTS","STYLE","SUCCESSFUL","SUN","TABLES","TAGUAGE","TANKYWOO","TCP/IP","TECHNOLOGIES","TEMPLATE","TEMPLATES","TEMPOR","TEXT","TEXT EXTRACTION", "TEXT-SHADOW","TF","THOSE","TIP","TITLES","TMP","TMPL","TOOL","TOOLBAR", "TOP","TRUE","TYPE","TYPECHO","UITEXTVIEW","UIWEBVIEW","UNDEFINED","URLLIB","URLLIB2","URLOPEN","URLPARSE","USE","USED","USEFUL","USER","VACANTI","VALIDATE","VALUE","VAR","VARCHAR","VERSION CONTROL","VERSIONS","VINICIUS","VISUALIZATION","W3HELP", "WEB DESIGN","WEB SERVER","WEBSITE"]
for r in remove_list:
    bookmarks_collection.update({}, {'$pull': {'tags': r}}, multi=True)
