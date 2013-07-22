#!/usr/bin/python
# -*- coding: utf-8 -*-
import re
import chardet

BROTHER_ENCODINGS = [
    ('GB2312', 'GBK', 'GB18030'),
]


def get_encoding(page):

    def is_enc(enc):
        try:
            diff = text.decode(enc, 'ignore').encode(enc)
            sizes = len(diff), len(text)
            if abs(len(text) - len(diff)) < max(sizes) * 0.01:  # 99% of utf-8
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

    res = chardet.detect(text)
    enc = res['encoding']

    if enc == 'MacCyrillic':
        enc = 'cp1251'

    # print '->', enc, "%.2f" % res['confidence']

    if res['confidence'] < 0.7:
        possible_encodings = get_brothers(enc) or ('GBK', enc)
        for p_enc in possible_encodings:
            if is_enc(p_enc):
                # print '->', p_enc
                return p_enc
    else:
        return enc

    raise DetectionFailed('raw result from chardet: %s' % res)


class DetectionFailed(Exception):
    pass
