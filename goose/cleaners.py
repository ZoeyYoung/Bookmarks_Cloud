# -*- coding: utf-8 -*-
"""\
This is a python port of "Goose" orignialy licensed to Gravity.com
under one or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.

Python port was written by Xavier Grangier for Recrutae

Gravity.com licenses this file
to you under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from goose.utils import ReplaceSequence
import re

BLOCK_CONTENT_TAG = ['div', 'article', 'section']

bad_attrs = ['xmlns:wb', 'width', 'height', '[-a-z]*color', 'background[-a-z]*', 'on*']
single_quoted = "'[^']+'"
double_quoted = '"[^"]+"'
c_double_quoted = '“[^”]+”'
non_space = '[^ "\'>]+'
cstr = ("<"  # open
        "([^>]+) "  # prefix
        "(?:%s) *" % ('|'.join(bad_attrs),) +  # undesirable attributes
        '= *(?:%s|%s|%s)' % (non_space, single_quoted, double_quoted) +  # value
        "([^>]*)" +  # postfix
        ">")
htmlstrip = re.compile("<"  # open
                       "([^>]+) "  # prefix
                       "(?:%s) *" % ('|'.join(bad_attrs),) +  # undesirable attributes
                       '= *(?:%s|%s|%s|%s)' % (non_space, single_quoted, double_quoted, c_double_quoted) +  # value
                       "([^>]*)"  # postfix
                       ">",       # end
                       re.I)

def clean_attributes(html_str):
    """移除HTML标签中无用的属性, 即上面的bad_attrs
    例如: <div id="main" class="content" style="font-size:18px;">content</div>
    变成: <div id="main" class="content">content</div>
    考虑连id和class一起移除
    """
    # empty_tag = re.compile(r"<\w+[^>]*>[\s|&nbsp;]*</\w+>", re.I)
    # html_str = re.sub(empty_tag, '', html_str)
    while htmlstrip.search(html_str):
        html_str = htmlstrip.sub(r'<\1\2>', html_str)
    return html_str

def normalize_spaces(s):
    """replace any sequence of whitespace characters with a single space
    将多个空格变成一个空格
    """
    if isinstance(s, bytes):
        s = s.decode('utf-8')
    return ' '.join(s.split())


def clean_empty_tag(s):
    if isinstance(s, bytes):
        s = s.decode('utf-8')
    empty_tag = re.compile(r"<\w+[^>]*>[\s|&nbsp;]*</\w+>", re.I)
    s = re.sub(empty_tag, '', s)
    return s

def clean_tags(s, tags):
    if isinstance(s, bytes):
        s = s.decode('utf-8')
    for tag in tags:
        clean_tag = re.compile(r"<" + tag + r"[^>]*>.*?</" + tag + r">", re.S)
        s = re.sub(clean_tag, '', s)
    return s


def text_content(s):
    if not s:
        return ''
    return re.sub(r'</?\w+[^>]*>', '', s)


class DocumentCleaner(object):

    def __init__(self, config):
        self.config = config
        # parser
        self.parser = self.config.get_parser()
        self.remove_nodes_re = (
            "^side$|combx|retweet|mediaarticlerelated|menucontainer|navbar"
            "|comment|PopularQuestions|contact|foot|footer|Footer|footnote"
            "|cnn_strycaptiontxt|links|cnn_html_slideshow|cnn_strylftcntnt|meta$|scroll|shoutbox|sponsor"
            "|tags|socialnetworking|socialNetworking|cnnStryHghLght"
            "|cnn_stryspcvbx|^inset$|pagetools|post-attributes"
            "|welcome_form|contentTools2|the_answers"
            "|communitypromo|runaroundLeft|subscribe|vcard|articleheadings"
            "|date|^print$|popup|author-dropdown|tools|socialtools|byline"
            "|konafilter|KonaFilter|^breadcrumb|^fn$|wp-caption-text"
            "|legende|ajoutVideo|timestamp|js_replies"
            "|adpack|copyright|disqus|google_ads|navigation|uyan_frame|ujian|^jiathis|banner|db-usr-profile|discuss|feedback|menu|nav"
            "|dropdown|dropdown-menu|btn-group|avatar|share"
        )
        self.regexp_namespace = "http://exslt.org/regular-expressions"
        self.nauthy_tags = ["head", "script", "style", "header", "footer", "nav", "input", "textarea", "button"]
        self.nauthy_ids_re = "//*[re:test(@id, '%s', 'i')]" % self.remove_nodes_re
        self.nauthy_classes_re = "//*[re:test(@class, '%s', 'i')]" % self.remove_nodes_re
        self.nauthy_names_re = "//*[re:test(@name, '%s', 'i')]" % self.remove_nodes_re
        self.nauthy_roles_re = "//*[re:test(@role, '%s', 'i')]" % self.remove_nodes_re
        self.div_to_p_re = r"<(a|blockquote|dl|div|img|ol|p|pre|table|ul)"
        self.caption_re = "^caption$"
        self.google_re = " google "
        self.entries_re = "^[^entry-]more.*$"
        self.facebook_re = "[^-]facebook"
        self.facebook_braodcasting_re = "facebook-broadcasting"
        self.twitter_re = "[^-]twitter"
        self.tablines_replacements = ReplaceSequence()\
            .create("\n", "\n\n")\
            .append("\t")\
            .append("^\\s+$")

    def clean(self, article):
        doc_to_clean = article.doc
        # doc_to_clean = self.clean_article_tags(doc_to_clean)
        # doc_to_clean = self.clean_em_tags(doc_to_clean)
        # doc_to_clean = self.remove_drop_caps(doc_to_clean)
        # doc_to_clean = self.remove_scripts_styles(doc_to_clean)
        doc_to_clean = self.remove_nauthy_tags(doc_to_clean)
        doc_to_clean = self.remove_nodes_display_none(doc_to_clean)
        doc_to_clean = self.clean_bad_tags(doc_to_clean)
        doc_to_clean = self.remove_nodes_regex(doc_to_clean, self.caption_re)
        doc_to_clean = self.remove_nodes_regex(doc_to_clean, self.google_re)
        doc_to_clean = self.remove_nodes_regex(doc_to_clean, self.entries_re)
        doc_to_clean = self.remove_nodes_regex(doc_to_clean, self.facebook_re)
        doc_to_clean = self.remove_nodes_regex(
            doc_to_clean, self.facebook_braodcasting_re)
        doc_to_clean = self.remove_nodes_regex(doc_to_clean, self.twitter_re)
        # doc_to_clean = self.clean_para_spans(doc_to_clean)
        # doc_to_clean = self.div_to_para(doc_to_clean, 'div')
        # doc_to_clean = self.div_to_para(doc_to_clean, 'span')
        doc_to_clean = self.div_to_para(doc_to_clean)
        return doc_to_clean

    # def clean_article_tags(self, doc):
    #     articles = self.parser.getElementsByTag(doc, tag='article')
    #     for article in articles:
    #         for attr in ['id', 'name', 'class']:
    #             self.parser.delAttribute(article, attr=attr)
    #     return doc

    # def clean_em_tags(self, doc):
    #     ems = self.parser.getElementsByTag(doc, tag='em')
    #     for node in ems:
    #         images = self.parser.getElementsByTag(node, tag='img')
    #         if len(images) == 0:
    #             self.parser.drop_tag(node)
    #     return doc

    # def remove_drop_caps(self, doc):
    #     items = self.parser.css_select(
    #         doc, "span[class~=dropcap], span[class~=drop_cap]")
    #     for item in items:
    #         self.parser.drop_tag(item)
    #     return doc

    # def remove_scripts_styles(self, doc):
    #     # remove scripts
    #     scripts = self.parser.getElementsByTag(doc, tag='script')
    #     for item in scripts:
    #         self.parser.remove(item)

    #     # remove styles
    #     styles = self.parser.getElementsByTag(doc, tag='style')
    #     for item in styles:
    #         self.parser.remove(item)

    #     return doc

    def remove_nauthy_tags(self, doc):
        for tag in self.nauthy_tags:
            nodes = self.parser.getElementsByTag(doc, tag=tag)
            for item in nodes:
                self.parser.remove(item)

        # remove comments
        comments = self.parser.getComments(doc)
        for item in comments:
            self.parser.remove(item)
        return doc

    def remove_nodes_display_none(self, doc):
        reg = "//*[re:test(@style, 'display:\s*none', 'i')]"
        naughty_list = self.parser.xpath_re(doc, reg)
        for node in naughty_list:
            self.parser.remove(node)
        return doc

    def clean_bad_tags(self, doc):
        # ids
        naughty_list = self.parser.xpath_re(doc, self.nauthy_ids_re)
        for node in naughty_list:
            self.parser.remove(node)

        # class
        naughty_classes = self.parser.xpath_re(doc, self.nauthy_classes_re)
        for node in naughty_classes:
            self.parser.remove(node)

        # name
        naughty_names = self.parser.xpath_re(doc, self.nauthy_names_re)
        for node in naughty_names:
            self.parser.remove(node)

        naughty_roles = self.parser.xpath_re(doc, self.nauthy_roles_re)
        for node in naughty_roles:
            self.parser.remove(node)

        return doc

    def remove_nodes_regex(self, doc, pattern):
        for selector in ['id', 'class']:
            reg = "//*[re:test(@%s, '%s', 'i')]" % (selector, pattern)
            naughty_list = self.parser.xpath_re(doc, reg)
            for node in naughty_list:
                self.parser.remove(node)
        return doc

    # def clean_para_spans(self, doc):
    #     spans = self.parser.css_select(doc, 'p > span')
    #     for item in spans:
    #         self.parser.drop_tag(item)
    #     return doc

    # def get_flushed_buffer(self, replacement_text, doc):
    #     return self.parser.textToPara(replacement_text)

    # def get_replacement_nodes(self, doc, div):
    #     replacement_text = []
    #     nodes_to_return = []
    #     nodes_to_remove = []
    #     childs = self.parser.childNodesWithText(div)

    #     for kid in childs:
    #         # node is a p
    #         # and already have some replacement text
    #         if self.parser.getTag(kid) == 'p' and len(replacement_text) > 0:
    #             newNode = self.get_flushed_buffer(
    #                 ''.join(replacement_text), doc)
    #             nodes_to_return.append(newNode)
    #             replacement_text = []
    #             nodes_to_return.append(kid)
    #         # node is a text node
    #         elif self.parser.isTextNode(kid):
    #             kid_text_node = kid
    #             kid_text = self.parser.getText(kid)
    #             replace_text = self.tablines_replacements.replaceAll(kid_text)
    #             if(len(replace_text)) > 1:
    #                 previous_sibling_node = self.parser.previousSibling(
    #                     kid_text_node)
    #                 while previous_sibling_node is not None \
    #                     and self.parser.getTag(previous_sibling_node) == "a" \
    #                         and self.parser.getAttribute(previous_sibling_node, 'grv-usedalready') != 'yes':
    #                     outer = " " + \
    #                         self.parser.outerHtml(previous_sibling_node) + " "
    #                     replacement_text.append(outer)
    #                     nodes_to_remove.append(previous_sibling_node)
    #                     self.parser.setAttribute(previous_sibling_node,
    #                                              attr='grv-usedalready', value='yes')
    #                     prev = self.parser.previousSibling(
    #                         previous_sibling_node)
    #                     previous_sibling_node = prev if prev is not None else None
    #                 # append replace_text
    #                 replacement_text.append(replace_text)
    #                 #
    #                 next_sibling_node = self.parser.nextSibling(kid_text_node)
    #                 while next_sibling_node is not None \
    #                     and self.parser.getTag(next_sibling_node) == "a" \
    #                         and self.parser.getAttribute(next_sibling_node, 'grv-usedalready') != 'yes':
    #                     outer = " " + \
    #                         self.parser.outerHtml(next_sibling_node) + " "
    #                     replacement_text.append(outer)
    #                     nodes_to_remove.append(next_sibling_node)
    #                     self.parser.setAttribute(next_sibling_node,
    #                                              attr='grv-usedalready', value='yes')
    #                     next = self.parser.nextSibling(next_sibling_node)
    #                     previous_sibling_node = next if next is not None else None

    #         # otherwise
    #         else:
    #             nodes_to_return.append(kid)

    #     # flush out anything still remaining
    #     if(len(replacement_text) > 0):
    #         new_node = self.get_flushed_buffer(''.join(replacement_text), doc)
    #         nodes_to_return.append(new_node)
    #         replacement_text = []

    #     for n in nodes_to_remove:
    #         self.parser.remove(n)

    #     return nodes_to_return

    # def replace_with_para(self, doc, div):
    #     self.parser.replaceTag(div, 'p')

    # def div_to_para(self, doc, dom_type):
    #     bad_divs = 0
    #     else_divs = 0
    #     divs = self.parser.getElementsByTag(doc, tag=dom_type)
    #     tags = ['a', 'address', 'blockquote', 'canvas',
    #             'dd','dl', 'div', 'fig',
    #             'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr',
    #             'img', 'noscript', 'ol', 'p', 'pre', 'section',
    #             'table', 'ul', 'video']

    #     for div in divs:
    #         items = self.parser.getElementsByTags(div, tags)
    #         if div is not None and len(items) == 0:
    #             self.replace_with_para(doc, div)
    #             bad_divs += 1
    #         elif div is not None:
    #             replaceNodes = self.get_replacement_nodes(doc, div)
    #             div.clear()

    #             for c, n in enumerate(replaceNodes):
    #                 div.insert(c, n)

    #             else_divs += 1
    #     return doc

    def wrap_body(self, doc):
        """http://zoeyyoung.github.io/python-lxml-wrapping-elements.html
        """
        for elem in doc.findall(".//body"):
            # 1. 为Text包装<span>, 即将Text变成<span>Text</span>
            if elem.text and elem.text.strip():
                p = self.parser.fromstring('<span/>')
                p.text = elem.text
                elem.text = None
                elem.insert(0, p)
            # 2. 为body的子元素包装div
            div = self.parser.fromstring("<div/>")
            for e in elem.iterchildren():
                div.append(e)
            elem.insert(0, div)
        return doc

    def div_to_para(self, doc):
        """首先将不含任何块级元素的<div>变成<p>
        然后为<div>中不含<p>的段落加上<p>
        例如 <div>TEXT<P>HELLO</P>TAIL<br/>TAIL2</div>
        转变后变成 <div><p>TEXT</p><p>HELLO</p><p>TAIL</p><p>TAIL2</p></div>
        """
        doc = self.wrap_body(doc)
        div_to_para_re = re.compile('<(address|blockquote|canvas|dd|dl|div|fig|h1|h2|h3|h4|h5|h6|hr|img|noscript|ol|p|pre|section|table|ul|video)', re.I)
        for elem in self.parser.getElementsByTags(doc, BLOCK_CONTENT_TAG):
            # transform <div>s that do not contain other block elements into <p>s
            if not div_to_para_re.search(''.join(str(list(map(self.parser.nodeToString, list(elem)))))):
                self.parser.replaceTag(elem, 'p')
            elif elem.text and elem.text.strip():
                p = self.parser.fromstring('<p/>')
                p.text = elem.text
                elem.text = None
                elem.insert(0, p)

            for pos, child in reversed(list(enumerate(elem))):
                if child.tail and child.tail.strip():
                    p = self.parser.fromstring('<span/>')
                    p.text = child.tail
                    child.tail = None
                    elem.insert(pos + 1, p)
                if child.tag == 'br':
                    child.drop_tree()
        return doc


class StandardDocumentCleaner(DocumentCleaner):
    pass
