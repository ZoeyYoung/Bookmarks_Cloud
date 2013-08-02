#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import re
import sys
import urllib.parse

from . import urlfetch

from collections import namedtuple
from lxml.etree import tostring
from lxml.etree import tounicode
from lxml.html import document_fromstring
from lxml.html import fragment_fromstring

from .cleaners import clean_attributes
from .cleaners import html_cleaner
from .htmls import build_doc
from .htmls import get_body
from .htmls import get_title
from .htmls import shorten_title
from .htmls import get_description
from .htmls import get_keywords


logging.basicConfig(level=logging.INFO)
log = logging.getLogger()


PAGE_CLASS = 'article-page'
BLOCK_CONTENT_TAG = ['div', 'header', 'article', 'section']
REGEXES = {
    'unlikelyCandidatesRe': re.compile('answer|avatar|banner|blurb|combx|comment|community|disqus|extra|foot|header|menu|nav|notify|remark|rss|shoutbox|sidebar|sponsor|ad-break|agegate|pagination|pager|popup|tweet|twitter|footer|dig|rat|tool|share|vote|bottom|uyan_frame|google_ads|user', re.I),
    'okMaybeItsACandidateRe': re.compile('and|article|body|brand|column|main|shadow|post|topic|document|news|highlight|accept|section', re.I),
    'positiveRe': re.compile('article|body|content|entry|hentry|main|page|pagination|post|text|blog|story|topic|document|section|news|highlight|code', re.I),
    'negativeRe': re.compile('combx|comment|com-|contact|foot|footer|footnote|masthead|media|meta|outbrain|promo|related|scroll|shoutbox|sidebar|sponsor|shopping|tags|tool|widget', re.I),
    'extraneous': re.compile(r'print|archive|comment|discuss|e[\-]?mail|share|reply|all|login|sign|single', re.I),
    # Block-level elements
    # https://developer.mozilla.org/en-US/docs/HTML/Block-level_elements
    'divToPElementsRe': re.compile('<(address|blockquote|canvas|dd|dl|div|fig|h1|h2|h3|h4|h5|h6|hr|img|noscript|ol|p|pre|section|table|ul|video)', re.I),
    # Match: next, continue, >, >>, but not >|, as those usually mean last.
    'nextLink': re.compile(r'(next|weiter|continue|>[^\|]$)', re.I),  # Match: next, continue, >, >>, but not >|, as those usually mean last.
    'prevLink': re.compile(r'(prev|earl|old|new|<)', re.I),
    'page': re.compile(r'pag(e|ing|inat)', re.I),
    'firstLast': re.compile(r'(first|last)', re.I)
    #'replaceBrsRe': re.compile('(<br[^>]*>[ \n\r\t]*){2,}',re.I),
    #'replaceFontsRe': re.compile('<(\/?)font[^>]*>',re.I),
    #'trimRe': re.compile('^\s+|\s+$/'),
    #'normalizeRe': re.compile('\s{2,}/'),
    #'killBreaksRe': re.compile('(<br\s*\/?>(\s|&nbsp;?)*){1,}/'),
    #'videoRe': re.compile('http:\/\/(www\.)?(youtube|vimeo)\.com', re.I),
    # skipFootnoteLink: /^\s*(\[?[a-z0-9]{1,2}\]?|^|edit|citation
    # needed)\s*$/i,
}


class Unparseable(ValueError):
    pass


# We want to change over the Summary to a nametuple to be more memory
# effecient and because it doesn't need to be mutable.
Summary = namedtuple('Summary', ['html', 'confidence', 'title', 'short_title', 'description', 'keywords'])


def describe(node, depth=1):
    if not hasattr(node, 'tag'):
        return "[%s]" % type(node)
    name = node.tag
    if node.get('id', ''):
        name += '#' + node.get('id')
    if node.get('class', ''):
        name += '.' + node.get('class').replace(' ', '.')
    if name[:4] in ['div#', 'div.']:
        name = name[3:]
    if depth and node.getparent() is not None:
        return name + ' - ' + describe(node.getparent(), depth - 1)
    return name


def get_clean_html(doc):
    """暂时没用到"""
    # print("get_clean_html", type(doc))
    return clean_attributes(tounicode(doc))


def to_int(x):
    """没有用到?"""
    if not x:
        return None
    x = x.strip()
    if x.endswith('px'):
        return int(x[:-2])
    if x.endswith('em'):
        return int(x[:-2]) * 12
    return int(x)


def clean(text):
    """移除多余的\n与\t"""
    text = re.sub('\s*\n+\s*', '\n', text)
    text = re.sub('[ \t]{2,}', ' ', text)
    return text.strip()


def text_length(i):
    """返回文本长度, 含子元素"""
    return len(clean(i.text_content() or ""))


def tags(node, *tag_names):
    """返回不包含根元素的所有特定标签元素"""
    for tag_name in tag_names:
        # print(tag_name)
        for e in node.findall('.//%s' % tag_name):
            yield e


def class_weight(e):
    """id、class属性权重
    return weight: -50 -25 0 25 50
    """
    weight = 0
    if e.get('class', None):
        if REGEXES['negativeRe'].search(e.get('class')):
            weight -= 25

        if REGEXES['positiveRe'].search(e.get('class')):
            weight += 25

    if e.get('id', None):
        if REGEXES['negativeRe'].search(e.get('id')):
            weight -= 25

        if REGEXES['positiveRe'].search(e.get('id')):
            weight += 25

    return weight


def score_node(elem):
    # TODO 仍需要调整
    content_score = class_weight(elem)
    name = elem.tag.lower()
    if name in ["div", "p"]:
        content_score += 5
    elif name in ["article", "section"]:
        content_score += 50
    elif name in ["pre", "td", "blockquote", "aside", "code", "table"]:
        content_score += 3
    elif name in ["ol", "ul", "li", "dd", "dt"]:
        content_score -= 1
    elif name in ["address", "form"]:
        content_score -= 3
    # elif name in ["h1", "h2", "h3", "h4", "h5", "h6", "th"]:
    elif name in ["h1", "h2"]:
        content_score -= 2
    return {
        'content_score': content_score,
        'elem': elem
    }


def transform_misused_divs_into_paragraphs(doc):
    """首先将不含任何块级元素的<div>变成<p>
    然后为<div>中不含<p>的段落加上<p>
    例如 <div>TEXT<P>HELLO</P>TAIL<br/>TAIL2</div>
    转变后变成 <div><p>TEXT</p><p>HELLO</p><p>TAIL</p><p>TAIL2</p></div>
    """
    for elem in tags(doc, *BLOCK_CONTENT_TAG):
    # for elem in tags(doc, 'div'):
        # transform <div>s that do not contain other block elements into <p>s
        if not REGEXES['divToPElementsRe'].search(
                ''.join(str(list(map(tostring, list(elem)))))):
            # log.debug("Altering %s to p" % (describe(elem)))
            elem.tag = "p"
            # print("Fixed element "+describe(elem))
    for elem in tags(doc, *BLOCK_CONTENT_TAG):
    # for elem in tags(doc, 'div'):
        if elem.text and elem.text.strip():
            p = fragment_fromstring('<p/>')
            p.text = elem.text
            elem.text = None
            elem.insert(0, p)
            # log.debug("Appended %s to %s" % (tounicode(p), describe(elem)))
            # print("Appended "+tounicode(p)+" to "+describe(elem))

        for pos, child in reversed(list(enumerate(elem))):
            if child.tail and child.tail.strip():
                p = fragment_fromstring('<p/>')
                p.text = child.tail
                child.tail = None
                elem.insert(pos + 1, p)
                # log.debug("Inserted %s to %s" % (
                    # tounicode(p),
                    # describe(elem)))
                # print("Inserted "+tounicode(p)+" to "+describe(elem))
            if child.tag == 'br':
                # print('Dropped <br> at '+describe(elem))
                child.drop_tree()


def remove_unlikely_candidates(doc):
    """移除可能不会作为正文的元素
    注意: 可能会误删
    """
    allelem = doc.iter()
    for elem in allelem:
        s = "%s %s" % (elem.get('class', ''), elem.get('id', ''))
        # log.debug(s)
        # output = open('elem.txt', 'a')
        # print("_tree %s class-id %s" % (describe(elem), s), file=output)
        if REGEXES['unlikelyCandidatesRe'].search(s) and (not REGEXES['okMaybeItsACandidateRe'].search(s)) and elem.tag != 'body' and elem.getparent() is not None:
            # print("_drop_tree %s" % (describe(elem)), file=output)
            for i in range(len(elem.findall('.//*'))):
                allelem.__next__()
            elem.getparent().remove(elem)


def get_link_density(elem):
    """获得链接密度
    注意: 有的正文也会有很多链接
    """
    link_length = 0
    for i in elem.findall(".//a"):
        link_length += text_length(i)
    # if len(elem.findall(".//div") or elem.findall(".//p")):
    #    link_length = link_length
    total_length = text_length(elem)
    # print(describe(elem), "link_density", float(link_length), max(total_length, 1))
    return float(link_length) / max(total_length, 1)


def score_paragraphs(doc, options):
    # output = open('elem.txt', 'a')
    candidates = {}
    # log.debug(str([describe(node) for node in tags(doc, "div")]))

    ordered = []
    for elem in tags(doc, "p", "pre", "td"):
        # log.debug('Scoring %s' % describe(elem))
        parent_node = elem.getparent()
        if parent_node is None:
            continue
        grand_parent_node = parent_node.getparent()

        inner_text = clean(elem.text_content() or "")
        inner_text_len = len(inner_text)

        # If this paragraph is less than 25 characters, don't even count it.
        if inner_text_len < options['min_text_length']:
            continue

        if parent_node not in candidates:
            candidates[parent_node] = score_node(parent_node)
            # print("parent_node", describe(parent_node), candidates[parent_node]['content_score'], file=output)
            ordered.append(parent_node)

        if grand_parent_node is not None and grand_parent_node not in candidates:
            candidates[grand_parent_node] = score_node(grand_parent_node)
            # print("grand_parent_node", describe(grand_parent_node), candidates[grand_parent_node]['content_score'], file=output)
            ordered.append(grand_parent_node)

        content_score = 1
        content_score += len(re.split('[,，.。]', inner_text))
        content_score += min((inner_text_len / 100), 3)
        # print("content_score", content_score, len(re.split('[,，.。]', inner_text)), min((inner_text_len / 100), 3), file=output)
        # if elem not in candidates:
        #    candidates[elem] = score_node(elem)

        # WTF? candidates[elem]['content_score'] += content_score
        candidates[parent_node]['content_score'] += content_score
        if grand_parent_node is not None:
            candidates[grand_parent_node]['content_score'] += content_score / 2.0

    # Scale the final candidates score based on link density. Good content
    # should have a relatively small link density (5% or less) and be mostly
    # unaffected by this operation.
    for elem in ordered:
        candidate = candidates[elem]
        ld = get_link_density(elem)
        score = candidate['content_score']
        # log.debug("Candid: %6.3f %s link density %.3f -> %6.3f" % (
            # score,
            # describe(elem),
            # ld,
            # score * (1 - ld)))
        candidate['content_score'] *= (1 - ld)

    return candidates


def select_best_candidate(candidates):
    sorted_candidates = sorted(candidates.values(),
                               key=lambda x: x['content_score'],
                               reverse=True)

    for candidate in sorted_candidates[:5]:
        elem = candidate['elem']
        log.debug("Top 5 : %6.3f %s" % (
            candidate['content_score'],
            describe(elem)))

    if len(sorted_candidates) == 0:
        return None

    best_candidate = sorted_candidates[0]
    return best_candidate


def reverse_tags(node, *tag_names):
    for tag_name in tag_names:
        for e in reversed(node.findall('.//%s' % tag_name)):
            yield e


def sanitize(node, candidates, options):
    # 不过滤标题
    # for header in tags(node, "h1", "h2", "h3", "h4", "h5", "h6"):
    #     if class_weight(header) < 0 or get_link_density(header) > 0.33:
    #         header.drop_tree()

    for elem in tags(node, "form", "iframe", "textarea"):
        elem.drop_tree()
    allowed = {}
    # Conditionally clean <table>s, <ul>s, and <div>s
    for el in reverse_tags(node, "ul", "div"):
    # for el in reverse_tags(node, "table", "ul", "div"):
        if el in allowed:
            continue
        weight = class_weight(el)
        if el in candidates:
            content_score = candidates[el]['content_score']
            # print '!',el, '-> %6.3f' % content_score
        else:
            content_score = 0
        tag = el.tag

        if weight + content_score < 0:
            # log.debug("Cleaned %s with score %6.3f and weight %-3s" %
                # (describe(el), content_score, weight, ))
            el.drop_tree()
        elif el.text_content().count(",") < 10:
            counts = {}
            for kind in ['p', 'img', 'li', 'a', 'embed', 'input']:
                counts[kind] = len(el.findall('.//%s' % kind))
            counts["li"] -= 100

            # Count the text length excluding any surrounding whitespace
            content_length = text_length(el)
            link_density = get_link_density(el)
            parent_node = el.getparent()
            if parent_node is not None:
                if parent_node in candidates:
                    content_score = candidates[parent_node]['content_score']
                else:
                    content_score = 0
            # if parent_node is not None:
                # pweight = class_weight(parent_node) + content_score
                # pname = describe(parent_node)
            # else:
                # pweight = 0
                # pname = "no parent"
            to_remove = False
            reason = ""

            # if el.tag == 'div' and counts["img"] >= 1:
            #    continue
            if counts["p"] and counts["img"] > counts["p"]:
                reason = "too many images (%s)" % counts["img"]
                to_remove = True
            elif counts["li"] > counts["p"] and tag != "ul" and tag != "ol":
                reason = "more <li>s than <p>s"
                to_remove = True
            elif counts["input"] > (counts["p"] / 3):
                reason = "less than 3x <p>s than <input>s"
                to_remove = True
            elif content_length < options['min_text_length'] and (counts["img"] == 0 or counts["img"] > 2):
                reason = "too short content length %s without a single image" % content_length
                to_remove = True
            elif weight < 25 and link_density > 0.2:
                    reason = "too many links %.3f for its weight %s" % (
                        link_density, weight)
                    to_remove = True
            elif weight >= 25 and link_density > 0.5:
                reason = "too many links %.3f for its weight %s" % (
                    link_density, weight)
                to_remove = True
            elif (counts["embed"] == 1 and content_length < 75) or counts["embed"] > 1:
                reason = "<embed>s with too short content length, or too many <embed>s"
                to_remove = True

                # don't really understand what this is doing. Originally
                # the i/j were =+ which sets the value to 1. I think that
                # was supposed to be += which would increment. But then
                # it's compared to x which is hard set to 1. So you only
                # ever do one loop in each iteration and don't understand
                # it. Will have to investigate when we get to testing more
                # pages.

                # find x non empty preceding and succeeding siblings
                i, j = 0, 0
                x = 1
                siblings = []
                for sib in el.itersiblings():
                    # log.debug(sib.text_content())
                    sib_content_length = text_length(sib)
                    if sib_content_length:
                        i += 1
                        siblings.append(sib_content_length)
                        if i == x:
                            break
                for sib in el.itersiblings(preceding=True):
                    # log.debug(sib.text_content())
                    sib_content_length = text_length(sib)
                    if sib_content_length:
                        j += 1
                        siblings.append(sib_content_length)
                        if j == x:
                            break
                # log.debug(str(siblings))
                if siblings and sum(siblings) > 1000:
                    to_remove = False
                    log.debug("Allowing %s" % describe(el))
                    # for desnode in tags(el, "table", "ul", "div"):
                    for desnode in tags(el, "ul", "div"):
                        allowed[desnode] = True

            if to_remove:
                log.debug("Cleaned %6.3f %s with weight %s cause it has %s." % (content_score, describe(el), weight, reason))
                # print tounicode(el)
                # log.debug("pname %s pweight %.3f" %(pname, pweight))
                el.drop_tree()

    # for el in ([node] + [n for n in node.iter()]):
        # if not (options['attributes']):
            # el.attrib = {}  # FIXME:Checkout the effects of disabling this
            # pass
    return clean_attributes(tounicode(node))
    # return get_clean_html(node)


def get_raw_article(candidates, best_candidate, enclose_with_html_tag=True):
    # Now that we have the top candidate, look through its siblings for
    # content that might also be related. Things like preambles, content
    # split by ads that we removed, etc.
    sibling_score_threshold = max([10, best_candidate['content_score'] * 0.2])
    if enclose_with_html_tag:
        output = document_fromstring('<div/>')
        output.getchildren()[0].attrib['id'] = 'page'
    else:
        output = fragment_fromstring('<div/>')
        output.attrib['id'] = 'page'
    best_elem = best_candidate['elem']
    if best_elem.getparent() is not None:
        for sibling in best_elem.getparent().getchildren():
            # if isinstance(sibling, NavigableString): continue#in lxml there no
            # concept of simple text
            append = False
            if sibling is best_elem:
                append = True
            sibling_key = sibling  # HashableElement(sibling)

            # Print out sibling information for debugging.
            if sibling_key in candidates:
                sibling_candidate = candidates[sibling_key]
                log.debug(
                    "Sibling: %6.3f %s" %
                    (sibling_candidate['content_score'], describe(sibling))
                )
            else:
                log.debug("Sibling: %s" % describe(sibling))

            if sibling_key in candidates and candidates[sibling_key]['content_score'] >= sibling_score_threshold:
                append = True

            if sibling.tag == "p":
                link_density = get_link_density(sibling)
                node_content = sibling.text or ""
                node_length = len(node_content)

                if node_length > 80 and link_density < 0.25:
                    append = True
                elif node_length < 80 and link_density == 0 and re.search('\.( |$)', node_content):
                    append = True

            if append:
                # We don't want to append directly to output, but the div
                # in html->body->div
                if enclose_with_html_tag:
                    if sibling.tag == 'body':
                        for elem in sibling.getchildren():
                            output.getchildren()[
                                0].getchildren()[0].append(elem)
                    else:
                        output.getchildren()[
                            0].getchildren()[0].append(sibling)
                else:
                    output.append(sibling)

    else:
        output = best_elem
    return output


def get_article(doc, options, enclose_with_html_tag=True):
    try:
        ruthless = True
        while True:
            # for i in tags(doc, 'script', 'style'):
            #     i.drop_tree()
            for i in tags(doc, 'body'):
                i.set('id', 'readabilityBody')
            if ruthless:
                remove_unlikely_candidates(doc)
            transform_misused_divs_into_paragraphs(doc)
            candidates = score_paragraphs(doc, options)
            best_candidate = select_best_candidate(candidates)
            if best_candidate:
                confidence = best_candidate['content_score']
                article = get_raw_article(candidates, best_candidate,
                                          enclose_with_html_tag=enclose_with_html_tag)
            else:
                if ruthless:
                    log.debug("ruthless removal did not work. ")
                    ruthless = False
                    log.debug(
                        "ended up stripping too much - going for a safer parse")
                    # try again
                    continue
                else:
                    log.debug(
                        "Ruthless and lenient parsing did not work. Returning raw html")
                    return Summary(None, 0, '', '', '', '')

            cleaned_article = sanitize(article, candidates, options)

            of_acceptable_length = len(
                cleaned_article or '') >= options['retry_length']
            if ruthless and not of_acceptable_length:
                ruthless = False
                continue  # try again
            else:
                return Summary(confidence=confidence,
                               html=cleaned_article,
                               short_title=shorten_title(doc),
                               title=get_title(doc),
                               description=get_description(doc),
                               keywords=get_keywords(doc))

    except Exception as e:
        log.exception('error getting summary: ')
        raise Unparseable(str(e), None, sys.exc_info()[2])


def clean_segment_extension(segments, index, segment):
    if segment.find('.') == -1:
        return segment
    else:
        split_segment = segment.split('.')
        possible_type = split_segment[1]
        has_non_alpha = re.search(r'[^a-zA-Z]', possible_type)
        if has_non_alpha:
            return segment
        else:
            return split_segment[0]


def clean_segment_ewcms(segments, index, segment):
    """
    EW-CMS specific segment cleaning.  Quoth the original source:
        "EW-CMS specific segment replacement. Ugly.
         Example: http://www.ew.com/ew/article/0,,20313460_20369436,00.html"
    """
    return segment.replace(',00', '')


def clean_segment_page_number(segments, index, segment):
    # If our first or second segment has anything looking like a page number,
    # remove it.
    if index >= (len(segments) - 2):
        pattern = r'((_|-)?p[a-z]*|(_|-))[0-9]{1,2}$'
        cleaned = re.sub(pattern, '', segment, re.IGNORECASE)
        if cleaned == '':
            return None
        else:
            return cleaned
    else:
        return segment


def clean_segment_number(segments, index, segment):
    # If this is purely a number, and it's the first or second segment, it's
    # probably a page number.  Remove it.
    if index >= (len(segments) - 2) and re.search(r'^\d{1,2}$', segment):
        return None
    else:
        return segment


def clean_segment_index(segments, index, segment):
    if index == (len(segments) - 1) and segment.lower() == 'index':
        return None
    else:
        return segment


def clean_segment_short(segments, index, segment):
    # It is not clear to me what this is accomplishing.  The original
    # readability source just says:
    #
    #   "If our first or second segment is smaller than 3 characters, and the
    #    first segment was purely alphas, remove it."
    #
    # However, the code actually checks to make sure that there are no alphas
    # in the segment, rather than checking for purely alphas.
    alphas = re.search(r'[a-z]', segments[-1], re.IGNORECASE)
    if index >= (len(segments) - 2) and len(segment) < 3 and not alphas:
        return None
    else:
        return segment


def clean_segment(segments, index, segment):
    """
    Cleans a single segment of a URL to find the base URL.  The base URL is as
    a reference when evaluating URLs that might be next-page links.  Returns a
    cleaned segment string or None, if the segment should be omitted entirely
    from the base URL.
    """
    funcs = [
        clean_segment_extension,
        clean_segment_ewcms,
        clean_segment_page_number,
        clean_segment_number,
        clean_segment_index,
        clean_segment_short
    ]
    cleaned_segment = segment
    for func in funcs:
        if cleaned_segment is None:
            break
        cleaned_segment = func(segments, index, cleaned_segment)
    return cleaned_segment


def filter_none(seq):
    return [x for x in seq if x is not None]


def clean_segments(segments):
    cleaned = [
        clean_segment(segments, i, s)
        for i, s in enumerate(segments)
    ]
    return filter_none(cleaned)


def find_base_url(url):
    if url is None:
        return None
    parts = urllib.parse.urlsplit(url)
    segments = parts.path.split('/')
    cleaned_segments = clean_segments(segments)
    new_path = '/'.join(cleaned_segments)
    new_parts = (parts.scheme, parts.netloc, new_path, '', '')
    base_url = urllib.parse.urlunsplit(new_parts)
    log.debug('url: %s' % url)
    log.debug('base_url: %s' % base_url)
    return base_url


class NextPageCandidate():

    '''
    An object that tracks a single href that is a candidate for the location of
    the next page.  Note that this is distinct from the candidates used when
    trying to find the elements containing the article.
    '''

    def __init__(self, link_text, href):
        self.link_text = link_text
        self.href = href
        self.score = 0


def same_domain(lhs, rhs):
    split_lhs = urllib.parse.urlsplit(lhs)
    split_rhs = urllib.parse.urlsplit(rhs)
    if split_lhs.netloc == '' or split_rhs.netloc == '':
        return True
    else:
        return split_lhs.netloc == split_rhs.netloc


def strip_trailing_slash(s):
    return re.sub(r'/$', '', s)


def eval_href(parsed_urls, url, base_url, link):
    raw_href = link.get('href')
    if raw_href is None:
        return None, None, False

    href = strip_trailing_slash(raw_href)
    # log.debug('evaluating next page link: %s' % href)

    # If we've already seen this page, ignore it.
    if href == base_url or href == url or href in parsed_urls:
        log.debug('rejecting %s: already seen page' % href)
        return raw_href, href, False

    # If it's on a different domain, skip it.
    if url is not None and not same_domain(url, href):
        # log.debug('rejecting %s: different domain' % href)
        return raw_href, href, False

    return raw_href, href, True


def eval_link_text(link):
    link_text = clean(link.text_content() or '')
    if REGEXES['extraneous'].search(link_text) or len(link_text) > 25:
        return link_text, False
    else:
        return link_text, True


def find_or_create_page_candidate(candidates, href, link_text):
    '''
    Finds or creates a candidate page object for a next-page href.  If one
    exists already, which happens if there are multiple links with the same
    href, it is just returned.  This returns the tuple: (<the found or created
    candidate>, <True iff the candidate was created, False if it already
    existed>).
    '''
    if href in candidates:
        return candidates[href], False
    else:
        candidate = NextPageCandidate(link_text, href)
        candidates[href] = candidate
        return candidate, True


def eval_possible_next_page_link(parsed_urls, url, base_url, candidates, link):
    raw_href, href, ok = eval_href(parsed_urls, url, base_url, link)
    if not ok:
        return

    link_text, ok = eval_link_text(link)
    if not ok:
        return

    # If the leftovers of the URL after removing the base URL don't contain any
    # digits, it's certainly not a next page link.
    if base_url is not None:
        href_leftover = href.replace(base_url, '')
        if not re.search(r'\d', href_leftover):
            return

    candidate, created = find_or_create_page_candidate(
        candidates,
        href,
        link_text
    )

    if not created:
        candidate.link_text += ' | ' + link_text

    link_class_name = link.get('class') or ''
    link_id = link.get('id') or ''
    link_data = ' '.join([link_text, link_class_name, link_id])
    # log.debug('link: %s' % tostring(link))
    log.debug('link_data: %s' % link_data)

    if base_url is not None and href.find(base_url) != 0:
        log.debug('no base_url')
        candidate.score -= 25

    if REGEXES['nextLink'].search(link_data):
        log.debug('link_data nextLink regex match')
        candidate.score += 50

    if REGEXES['page'].search(link_data):
        log.debug('link_data page regex match')
        candidate.score += 25

    if REGEXES['firstLast'].search(link_data):
        # If we already matched on "next", last is probably fine. If we didn't,
        # then it's bad.  Penalize.
        if not REGEXES['nextLink'].search(candidate.link_text):
            log.debug('link_data matched last but not next')
            candidate.score -= 65

    neg_re = REGEXES['negativeRe']
    ext_re = REGEXES['extraneous']
    if neg_re.search(link_data) or ext_re.search(link_data):
        log.debug('link_data negative/extraneous regex match')
        candidate.score -= 50

    if REGEXES['prevLink'].search(link_data):
        log.debug('link_data prevLink match')
        candidate.score -= 200

    parent = link.getparent()
    positive_node_match = False
    negative_node_match = False
    while parent is not None:
        parent_class = parent.get('class') or ''
        parent_id = parent.get('id') or ''
        parent_class_and_id = ' '.join([parent_class, parent_id])
        if not positive_node_match:
            if REGEXES['page'].search(parent_class_and_id):
                log.debug('positive ancestor match')
                positive_node_match = True
                candidate.score += 25
        if not negative_node_match:
            if REGEXES['negativeRe'].search(parent_class_and_id):
                if not REGEXES['positiveRe'].search(parent_class_and_id):
                    log.debug('negative ancestor match')
                    negative_node_match = True
                    candidate.score -= 25
        parent = parent.getparent()

    if REGEXES['page'].search(href):
        log.debug('href regex match')
        candidate.score += 25

    if REGEXES['extraneous'].search(href):
        log.debug('extraneous regex match')
        candidate.score -= 15

    try:
        link_text_as_int = int(link_text)

        log.debug('link_text looks like %d' % link_text_as_int)
        # Punish 1 since we're either already there, or it's probably before
        # what we want anyways.
        if link_text_as_int == 1:
            candidate.score -= 10
        else:
            candidate.score += max(0, 10 - link_text_as_int)
    except ValueError as exc:
        pass

    log.debug('final score is %d' % candidate.score)


def find_next_page_url(parsed_urls, url, elem):
    links = tags(elem, 'a')
    base_url = find_base_url(url)
    # candidates is a mapping from URLs to NextPageCandidate objects that
    # represent information used to determine if a URL points to the next page
    # in the article.
    candidates = {}
    for link in links:
        eval_possible_next_page_link(
            parsed_urls,
            url,
            base_url,
            candidates,
            link
        )
    top_page = None
    for url, page in list(candidates.items()):
        log.debug('next page score of %s: %s' % (url, page.score))
        if 50 <= page.score and (not top_page or top_page.score < page.score):
            top_page = page

    if top_page:
        log.debug('next page link found: %s' % top_page.href)
        parsed_urls.add(top_page.href)
        return top_page.href
    else:
        return None


def page_id(i):
    return 'page-%d' % (i + 1)


def make_page_elem(page_index, elem):
    elem.attrib['id'] = page_id(page_index)
    elem.attrib['class'] = PAGE_CLASS


def first_paragraph(elem):
    paragraphs = elem.xpath('.//p')
    logging.debug('len(paragraphs) is %d' % len(paragraphs))
    if len(paragraphs) > 0:
        return paragraphs[0]
    else:
        return None


def is_suspected_duplicate(doc, page_doc):
    page_p = first_paragraph(page_doc)
    if page_p is None:
        return False
    pages = doc.xpath('//*[contains(@class, $name)]', name=PAGE_CLASS)
    for existing_page in pages:
        existing_page_p = first_paragraph(existing_page)
        if existing_page_p is not None:
            page_p_content = page_p.xpath('string()')
            existing_page_p_content = existing_page_p.xpath('string()')
            if page_p.xpath('string()') == existing_page_p.xpath('string()'):
                return True
    return False


def append_next_page(parsed_urls, page_index, page_url, doc, options):
    logging.debug('appending next page: %s' % page_url)
    fetcher = options['urlfetch']
    html = fetcher.urlread(page_url)
    orig_page_doc = parse(html, page_url)
    next_page_url = find_next_page_url(parsed_urls, page_url, orig_page_doc)
    page_article = get_article(orig_page_doc, options)
    log.debug('Appending ' + str(page_article))

    if page_article.html:
        page_doc = fragment_fromstring(page_article.html)
        make_page_elem(page_index, page_doc)

        if not is_suspected_duplicate(doc, page_doc):
            # page_doc is a singular element containing the page article elements.  We
            # want to add its children to the main article document to which we are
            # appending a page.
            if doc.tag == 'html':
                children = doc.getchildren()
                if children[0].tag == 'head':
                    for elem in page_doc:
                        doc.getchildren()[1].append(elem)
                else:
                    for elem in page_doc:
                        doc.getchildren()[0].append(elem)
            else:
                for elem in page_doc:
                    doc.append(elem)
            doc.append(page_doc)
            if next_page_url is not None:
                append_next_page(
                    parsed_urls,
                    page_index + 1,
                    next_page_url,
                    doc,
                    options
                )


def parse(input, url):
    # 含有样式和JS的lxml.html.HtmlElement对象
    raw_doc = build_doc(input)
    # 去除样式和JS的lxml.html.HtmlElement对象
    doc = html_cleaner.clean_html(raw_doc)
    log.debug('parse url: %s', url)
    if url:
        log.debug('making links absolute')
        doc.make_links_absolute(url, resolve_base_href=True)
    else:
        doc.resolve_base_href()
    return doc


class Document:

    """Class to build a etree document out of html."""
    TEXT_LENGTH_THRESHOLD = 10  # 25
    RETRY_LENGTH = 250

    def __init__(self, input_doc, **options):
        """Generate the document

        :param input_doc: string of the html content.

        kwargs:
            - attributes:
            - debug: output debug messages
            - min_text_length:
            - multipage: should we check for page 2/3 of article and build
              together?
            - retry_length:
            - url: will allow adjusting links to be absolute

        """
        if input_doc is None:
            raise ValueError('You must supply a document to process.')

        self.input_doc = input_doc
        self.options = options
        self.options['urlfetch'] = self.options.get('urlfetch',
                                                    urlfetch.UrlFetch())
        self.options['min_text_length'] = self.options.get('min_text_length',
                                                           self.TEXT_LENGTH_THRESHOLD)
        self.options['retry_length'] = self.options.get('retry_length',
                                                        self.RETRY_LENGTH)
        self._html = None

    @property
    def html(self):
        """The parsed html document from the input"""
        if not self._html:
            self._html = parse(self.input_doc, self.options.get('url'))

        return self._html

    def content(self):
        return get_body(self.html)

    def summary_with_metadata(self, enclose_with_html_tag=True):
        """Parse the input content and return a Summary object

        :param enclose_with_html_tag: Bool do you want a full <html> document
        or just the <div> html partial.

    def summary(self):
        doc = self._html(True)
        parsed_urls = set()
        url = self.options['url']
        if url is not None:
            parsed_urls.add(url)
        next_page_url = find_next_page_url(parsed_urls, url, doc)
        page_0 = get_article(doc, self.options)
        page_0_doc = fragment_fromstring(page_0.html)
        page_index = 0
        make_page_elem(page_index, page_0_doc)
        article_doc = B.DIV(page_0_doc)
        article_doc.attrib['id'] = 'article'
        if next_page_url is not None:
            append_next_page(
                    parsed_urls,
                    page_index + 1,
                    next_page_url,
                    article_doc,
                    self.options
                    )
        return Summary(page_0.confidence, tostring(article_doc))


        """
        summary = self._summary(enclose_with_html_tag=enclose_with_html_tag)
        # For this call return the raw Summary object.
        return summary

    def summary(self, enclose_with_html_tag=True):
        """Generate the summary of the html document

        :param enclose_with_html_tag: Bool do you want a full <html> document
        or just the <div> html partial.

        """
        summary = self._summary(enclose_with_html_tag=enclose_with_html_tag)
        # Only return the html to be consistent with the backwards api.
        return summary.html

    def _summary(self, enclose_with_html_tag=True):
        # the first page parsed into a elementree element
        doc = self.html

        # the set of urls we've processed so far
        parsed_urls = set()
        url = self.options.get('url', None)
        if url is not None:
            parsed_urls.add(url)

        # check the current doc for a next page if requested
        if self.options.get('multipage', False):
            next_page_url = find_next_page_url(parsed_urls, url, doc)

            page_0 = get_article(doc, self.options)
            page_0_doc = fragment_fromstring(page_0.html)
            page_index = 0
            make_page_elem(page_index, page_0_doc)

            if enclose_with_html_tag:
                output = document_fromstring('<div/>')
                output.getchildren()[0].attrib['id'] = 'article'
                output.getchildren()[0].append(page_0_doc)
            else:
                output = fragment_fromstring('<div/>')
                output.attrib['id'] = 'article'
                output.append(page_0_doc)

            if next_page_url is not None:
                append_next_page(
                    parsed_urls,
                    page_index + 1,
                    next_page_url,
                    output,
                    self.options
                )
            return Summary(tostring(output),
                           page_0.confidence,
                           short_title=shorten_title(output),
                           title=get_title(output),
                           description=get_description(output),
                           keywords=get_keywords(output))

        return get_article(doc, self.options,
                           enclose_with_html_tag=enclose_with_html_tag)
