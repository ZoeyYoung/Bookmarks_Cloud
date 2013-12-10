# -*- coding: utf-8 -*-
# import types
# import datetime
# from decimal import Decimal
from bs4 import UnicodeDammit
import re

# class DjangoUnicodeDecodeError(UnicodeDecodeError):
#     def __init__(self, obj, *args):
#         self.obj = obj
#         UnicodeDecodeError.__init__(self, *args)

#     def __str__(self):
#         original = UnicodeDecodeError.__str__(self)
#         return '%s. You passed in %r (%s)' % (original, self.obj,
#                 type(self.obj))


# class StrAndUnicode(object):
#     """
#     A class whose __str__ returns its __unicode__ as a UTF-8 bytestring.

#     Useful as a mix-in.
#     """
#     def __str__(self):
#         return self.__unicode__().encode('utf-8')


# def smart_unicode(s, encoding='utf-8', strings_only=False, errors='strict'):
#     """
#     Returns a unicode object representing 's'. Treats bytestrings using the
#     'encoding' codec.

#     If strings_only is True, don't convert (some) non-string-like objects.
#     """
#     # if isinstance(s, Promise):
#     #     # The input is the result of a gettext_lazy() call.
#     #     return s
#     return force_unicode(s, encoding, strings_only, errors)


# def is_protected_type(obj):
#     """Determine if the object instance is of a protected type.

#     Objects of protected types are preserved as-is when passed to
#     force_unicode(strings_only=True).
#     """
#     return isinstance(obj, (
#         type(None),
#         int,
#         datetime.datetime, datetime.date, datetime.time,
#         float, Decimal)
#     )


# def force_unicode(s, encoding='utf-8', strings_only=False, errors='strict'):
#     """
#     Similar to smart_unicode, except that lazy instances are resolved to
#     strings, rather than kept as lazy objects.

#     If strings_only is True, don't convert (some) non-string-like objects.
#     """
#     # Handle the common case first, saves 30-40% in performance when s
#     # is an instance of unicode. This function gets called often in that
#     # setting.
#     if isinstance(s, str):
#         return s
#     if strings_only and is_protected_type(s):
#         return s
#     try:
#         # if not isinstance(s, basestring,):
#         if hasattr(s, '__unicode__'):
#             s = str(s)
#         else:
#             try:
#                 # s = str(str(s), encoding, errors)
#                 s = s.decode(encoding, errors)
#             except UnicodeEncodeError:
#                 if not isinstance(s, Exception):
#                     raise
#                 # If we get to here, the caller has passed in an Exception
#                 # subclass populated with non-ASCII data without special
#                 # handling to display as a string. We need to handle this
#                 # without raising a further exception. We do an
#                 # approximation to what the Exception's standard str()
#                 # output should be.
#                 s = ' '.join([force_unicode(arg, encoding, strings_only,
#                         errors) for arg in s])
#         # elif not isinstance(s, str):
#             # Note: We use .decode() here, instead of unicode(s, encoding,
#             # errors), so that if s is a SafeString, it ends up being a
#             # SafeUnicode at the end.
#             # s = s.decode(encoding, errors)
#     except UnicodeDecodeError as e:
#         if not isinstance(s, Exception):
#             raise DjangoUnicodeDecodeError(s, *e.args)
#         else:
#             # If we get to here, the caller has passed in an Exception
#             # subclass populated with non-ASCII bytestring data without a
#             # working unicode method. Try to handle this without raising a
#             # further exception by individually forcing the exception args
#             # to unicode.
#             s = ' '.join([force_unicode(arg, encoding, strings_only,
#                     errors) for arg in s])
#     return s


def smart_str(s, encoding='utf-8', strings_only=False, errors='strict'):
    """
    Returns a bytestring version of 's', encoded as specified in 'encoding'.

    If strings_only is True, don't convert (some) non-string-like objects.
    """
    if strings_only and isinstance(s, (type(None), int)):
        return s
    # if isinstance(s, Promise):
    #     return unicode(s).encode(encoding, errors)
    if not isinstance(s, str):
        try:
            return str(s)
        except UnicodeEncodeError:
            if isinstance(s, Exception):
                # An Exception subclass containing non-ASCII data that doesn't
                # know how to print itself properly. We shouldn't raise a
                # further exception.
                return ' '.join([smart_str(arg, encoding, strings_only,
                        errors) for arg in s])
            return str(s).encode(encoding, errors)
    elif isinstance(s, str):
        return s.encode(encoding, errors)
    elif s and encoding != 'utf-8':
        return s.decode('utf-8', errors).encode(encoding, errors)
    else:
        return s

def get_charset(s):
    """使用BS4的UnicodeDammit来检测网页编码, 并返回unicode文档, 不能保证正确率100%, 因此加上备选方案
    """
    dammit = UnicodeDammit(s, ['GB2312', 'GBK', 'GB18030'], smart_quotes_to="html", is_html=True)
    enc = dammit.original_encoding
    print("dammit —— ", dammit.original_encoding)
    # FIXME 部分网页判断是'ISO-8859-2', 不知道为什么, 这时使用备选方案进行判断
    if dammit.original_encoding.lower() == 'iso-8859-2':
        enc = _get_charset(s)
        print("chardet —— ", enc)
    return enc

def _get_charset(s):
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

    text = re.sub(b'</?[^>]*>\s*', b'', s)
    enc = 'utf-8'
    if not text.strip() or len(text) < 10:
        return enc  # can't guess

    if is_enc(enc):
        return enc

    possible_encodings = set(['GB2312', 'GBK', 'GB18030', enc])
    for p_enc in possible_encodings:
        if is_enc(p_enc):
            return p_enc

    raise UnicodeDecodeError("Failed to detect encoding, tried [%s]", 'raw result from chardet: %s' % enc)

def replace_meta_charset(s):
    pattern = re.compile('<meta http-equiv="content-type".*?>', re.I)
    s = re.sub(pattern, '', s)
    return s

def force_meta(s):
    pattern = re.compile('<meta charset="utf-8".*?>', re.I)
    if pattern.search(s) is None:
        s = s.replace('<head>', '<head><meta charset="utf-8">')
    return s
