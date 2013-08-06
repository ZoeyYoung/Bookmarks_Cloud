# strip out a set of nuisance html attributes that can mess up rendering in
# RSS feeds
import re
from lxml.html.clean import Cleaner

bad_attrs = ['width', 'height', 'style', '[-a-z]*color',
             'background[-a-z]*', 'on*', 'id']
single_quoted = "'[^']+'"
double_quoted = '"[^"]+"'
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
                       '= *(?:%s|%s|%s)' % (non_space, single_quoted, double_quoted) +  # value
                       "([^>]*)"  # postfix
                       ">",       # end
                       re.I)


def clean_attributes(html_str):
    """移除HTML标签中无用的属性, 即上面的bad_attrs
    例如: <div id="main" class="content" style="font-size:18px;">content</div>
    变成: <div id="main" class="content">content</div>
    考虑连id和class一起移除
    """
    while htmlstrip.search(html_str):
        html_str = htmlstrip.sub(r'<\1\2>', html_str)
    return html_str


def normalize_spaces(s):
    """replace any sequence of whitespace characters with a single space
    将多个空格变成一个空格
    """
    if not s:
        return ''
    return ' '.join(s.split())


def text_content(s):
    if not s:
        return ''
    return re.sub(r'</?\w+[^>]*>', '', s)


html_cleaner = Cleaner(scripts=True, javascript=True, comments=True,
                       style=True, links=True, meta=False, add_nofollow=True,
                       page_structure=False, processing_instructions=True,
                       embedded=False, frames=False, forms=False,
                       annoying_tags=False, remove_tags=None,
                       kill_tags=['footer', 'nav', 'input'],
                       remove_unknown_tags=False, safe_attrs_only=False)

# kill_tags 不能删除tag说明
# form: 部分网站直接将form作为最外层- -|||
