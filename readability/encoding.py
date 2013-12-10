import logging
import re
from bs4 import UnicodeDammit

LOG = logging.getLogger("bc_log")


BROTHER_ENCODINGS = [
    ('GB2312', 'GBK', 'GB18030'),
]


def decode_html(html_string):
    """使用BS4的UnicodeDammit来检测网页编码, 并返回unicode文档, 不能保证正确率100%, 因此加上备选方案
    """
    dammit = UnicodeDammit(html_string, ['GB2312', 'GBK', 'GB18030'], smart_quotes_to="html", is_html=True)
    doc = dammit.unicode_markup
    # print("dammit —— ", dammit.original_encoding)
    # FIXME 部分网页判断是'ISO-8859-2', 不知道为什么, 这时使用备选方案进行判断
    if dammit.original_encoding == 'ISO-8859-2':
        enc = get_encoding(html_string)
        # print("chardet —— ", enc)
        doc = html_string.decode(enc, 'replace')
        print(enc)
    elif not dammit.unicode_markup:
        raise UnicodeDecodeError("Failed to detect encoding, tried [%s]", ', '.join(dammit.triedEncodings))
    # print(doc.encode('utf-8'))
    return doc


def get_encoding(page):
    """测试编码的备选方案
    """
    def is_enc(enc):
        try:
            diff = text.decode(enc, 'ignore').encode(enc)
            sizes = len(diff), len(text)
            # 99% of utf-8
            if abs(len(text) - len(diff)) < max(sizes) * 0.01:
                return True
        except UnicodeDecodeError:
            return False

    text = re.sub(b'</?[^>]*>\s*', b'', page)
    enc = 'utf-8'
    if not text.strip() or len(text) < 10:
        return enc  # can't guess

    if is_enc(enc):
        return enc

    def get_brothers(ec):
        for i in BROTHER_ENCODINGS:
            if ec in i:
                return i
        return None

    possible_encodings = get_brothers(enc) or ('GBK', enc)
    for p_enc in possible_encodings:
        if is_enc(p_enc):
            return p_enc

    raise UnicodeDecodeError("Failed to detect encoding, tried [%s]", 'raw result from chardet: %s' % res)
