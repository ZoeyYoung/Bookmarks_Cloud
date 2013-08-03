#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pymongo

bookmarks_collection = pymongo.Connection().bookmarks_cloud.bookmarks

tags_dict = {
    "Ajax": ["ajax"],
    "Apache": ["Apach", "apache"],
    "论坛": ["bbs", "BBS"],
    "博客": ["Blog", "blog", "BLOG"],
    "Chrome": ["chrome"],
    "Chrome扩展": ["chrome extensions", "chrome扩展"],
    "CSS": ["css", "div+css布局"],
    "CSS3": ["css3"],
    "Drupal": ["Drupal CMS", "drupal", "drupal7", "drupalchina", "drupal中国", "drupal中文社区", "drupal中国", "drupal花园"],
    "div": ["Div"],
    "ExtJS": ["extjs", "EXTJS"],
    "Flex": ["flex"],
    "Firefox": ["firefox"],
    "Font": ["Fonts", "font", "font-face"],
    "Git": ["git", "gitshell", "git app", "git client", "git gui"],
    "GitHub": ["github", "Github"],
    "HTML": ["html"],
    "HTML5": ["html5"],
    "JSON": ["json"],
    "jQuery": ["jquery"],
    "jQuery插件": ["jQuery Plugin", "jquery插件"],
    "Java": ["java"],
    "Java EE": ["J2EE"],
    "Jekyll": ["jekyll"],
    "JavaScript": ["javascript", "js", "JS"],
    "MongoDB": ["mongodb", "mongoDB"],
    "PHP": ["php"],
    "Python": ["python"],
    "Python2": ["python2"],
    "Python3": ["python3"],
    "Ruby": ["ruby", "Ruby Gems", "ruby dev"],
    "Tornado": ["tornado"],
    "Unicode": ["unicode"],
    "Web": ["web"],
    "W3C": ["w3c"]
}

for (k, v) in tags_dict.items():
    print(k, v)
    for t in v:
        bookmarks_collection.update({'tags': t}, {'$set': {'tags.$': k}}, multi=True)
