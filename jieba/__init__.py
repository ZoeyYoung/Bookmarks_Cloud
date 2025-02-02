#!/usr/bin/env python
# -*- coding: utf-8 -*-
__version__ = '0.31'
__license__ = 'MIT'

import re
import os
import sys
from . import finalseg
import time

import tempfile
import marshal
from math import log
import random
import threading
from functools import wraps

DICTIONARY = "dict.txt"
DICT_LOCK = threading.RLock()
trie = None  # to be initialized
FREQ = {}
min_freq = 0.0
total = 0.0
user_word_tag_tab = {}
initialized = False


def gen_trie(f_name):
    lfreq = {}
    trie = {}
    ltotal = 0.0
    with open(f_name, 'rb') as f:
        lineno = 0
        for line in f.read().rstrip().decode('utf-8').split('\n'):
            lineno += 1
            try:
                word, freq, _ = line.split(' ')
                freq = float(freq)
                lfreq[word] = freq
                ltotal += freq
                p = trie
                for c in word:
                    if c not in p:
                        p[c] = {}
                    p = p[c]
                p[''] = ''  # ending flag
            except ValueError as e:
                print(f_name, ' at line', lineno,line, file=sys.stderr)
                raise e
    return trie, lfreq, ltotal


def initialize(*args):
    global trie, FREQ, total, min_freq, initialized
    if len(args) == 0:
        dictionary = DICTIONARY
    else:
        dictionary = args[0]
    with DICT_LOCK:
        if initialized:
            return
        if trie:
            del trie
            trie = None
        _curpath = os.path.normpath(
            os.path.join(os.getcwd(), os.path.dirname(__file__)))

        abs_path = os.path.join(_curpath, dictionary)
        print("Building Trie..., from", abs_path, file=sys.stderr)
        t1 = time.time()
        if abs_path == os.path.join(_curpath, "dict.txt"):  # defautl dictionary
            cache_file = os.path.join(tempfile.gettempdir(), "jieba.cache")
        else:  # customer dictionary
            cache_file = os.path.join(
                tempfile.gettempdir(), "jieba.user." + str(hash(abs_path)) + ".cache")

        load_from_cache_fail = True
        if os.path.exists(cache_file) and os.path.getmtime(cache_file) > os.path.getmtime(abs_path):
            print("loading model from cache", cache_file, file=sys.stderr)
            try:
                trie, FREQ, total, min_freq = marshal.load(
                    open(cache_file, 'rb'))
                load_from_cache_fail = False
            except:
                load_from_cache_fail = True

        if load_from_cache_fail:
            trie, FREQ, total = gen_trie(abs_path)
            FREQ = dict([(k, log(float(v) / total))
                        for k, v in FREQ.items()])  # normalize
            min_freq = min(FREQ.values())
            print("dumping model to file cache", cache_file, file=sys.stderr)
            try:
                tmp_suffix = "." + str(random.random())
                with open(cache_file + tmp_suffix, 'wb') as temp_cache_file:
                    marshal.dump(
                        (trie, FREQ, total, min_freq), temp_cache_file)
                if os.name == 'nt':
                    import shutil
                    replace_file = shutil.move
                else:
                    replace_file = os.rename
                replace_file(cache_file + tmp_suffix, cache_file)
            except:
                import traceback
                print("dump cache file failed.", file=sys.stderr)
                print(traceback.format_exc(), file=sys.stderr)
        initialized = True

        print("loading model cost ", time.time() - t1, "seconds.", file=sys.stderr)
        print("Trie has been built succesfully.", file=sys.stderr)


def require_initialized(fn):
    global initialized, DICTIONARY

    @wraps(fn)
    def wrapped(*args, **kwargs):
        if initialized:
            return fn(*args, **kwargs)
        else:
            initialize(DICTIONARY)
            return fn(*args, **kwargs)

    return wrapped


def __cut_all(sentence):
    dag = get_DAG(sentence)
    old_j = -1
    for k, L in dag.items():
        if len(L) == 1 and k > old_j:
            yield sentence[k:L[0] + 1]
            old_j = L[0]
        else:
            for j in L:
                if j > k:
                    yield sentence[k:j + 1]
                    old_j = j


def calc(sentence, DAG, idx, route):
    N = len(sentence)
    route[N] = (0.0, '')
    for idx in range(N - 1, -1, -1):
        candidates = [(FREQ.get(sentence[idx:x + 1], min_freq) + route[x + 1][0], x)
                      for x in DAG[idx]]
        route[idx] = max(candidates)


@require_initialized
def get_DAG(sentence):
    N = len(sentence)
    i, j = 0, 0
    p = trie
    DAG = {}
    while i < N:
        c = sentence[j]
        if c in p:
            p = p[c]
            if '' in p:
                if i not in DAG:
                    DAG[i] = []
                DAG[i].append(j)
            j += 1
            if j >= N:
                i += 1
                j = i
                p = trie
        else:
            p = trie
            i += 1
            j = i
    for i in range(len(sentence)):
        if i not in DAG:
            DAG[i] = [i]
    return DAG


def __cut_DAG(sentence):
    DAG = get_DAG(sentence)
    route = {}
    calc(sentence, DAG, 0, route=route)
    x = 0
    buf = ''
    N = len(sentence)
    while x < N:
        y = route[x][1] + 1
        l_word = sentence[x:y]
        if y - x == 1:
            buf += l_word
        else:
            if len(buf) > 0:
                if len(buf) == 1:
                    yield buf
                    buf = ''
                else:
                    if (buf not in FREQ):
                        regognized = finalseg.cut(buf)
                        for t in regognized:
                            yield t
                    else:
                        for elem in buf:
                            yield elem
                    buf = ''
            yield l_word
        x = y

    if len(buf) > 0:
        if len(buf) == 1:
            yield buf
        else:
            if (buf not in FREQ):
                regognized = finalseg.cut(buf)
                for t in regognized:
                    yield t
            else:
                for elem in buf:
                    yield elem


def cut(sentence, cut_all=False):
    if isinstance(sentence, bytes):
        try:
            sentence = sentence.decode('utf-8')
        except UnicodeDecodeError:
            sentence = sentence.decode('gbk', 'ignore')

    re_han, re_skip = re.compile(
        "([\u4E00-\u9FA5a-zA-Z0-9+#&\._]+)"), re.compile("(\r\n|\s)")

    if cut_all:
        re_han, re_skip = re.compile(
            "([\u4E00-\u9FA5]+)"), re.compile("[^a-zA-Z0-9+#\n]")

    blocks = re_han.split(sentence)
    cut_block = __cut_DAG
    if cut_all:
        cut_block = __cut_all
    for blk in blocks:
        if len(blk) == 0:
            continue
        if re_han.match(blk):
            for word in cut_block(blk):
                yield word
        else:
            tmp = re_skip.split(blk)
            for x in tmp:
                if re_skip.match(x):
                    yield x
                elif not cut_all:
                    for xx in x:
                        yield xx
                else:
                    yield x


def cut_for_search(sentence):
    words = cut(sentence)
    for w in words:
        if len(w) > 2:
            for i in range(len(w) - 1):
                gram2 = w[i:i + 2]
                if gram2 in FREQ:
                    yield gram2
        if len(w) > 3:
            for i in range(len(w) - 2):
                gram3 = w[i:i + 3]
                if gram3 in FREQ:
                    yield gram3
        yield w


@require_initialized
def load_userdict(f):
    global trie, total, FREQ
    if isinstance(f, str):
        f = open(f, 'rb')
    content = f.read().decode('utf-8')
    line_no = 0
    for line in content.split("\n"):
        line_no += 1
        if line.rstrip() == '':
            continue
        tup = line.split(" ")
        word, freq = tup[0], tup[1]
        if line_no == 1:
            word = word.replace('\ufeff', "")  # remove bom flag if it exists
        if len(tup) == 3:
            add_word(word, freq, tup[2])
        else:
            add_word(word, freq)


def add_word(word, freq, tag=None):
    global FREQ, trie, total, user_word_tag_tab
    freq = float(freq)
    FREQ[word] = log(freq / total)
    if tag is not None:
        user_word_tag_tab[word] = tag.strip()
    p = trie
    for c in word:
        if c not in p:
            p[c] = {}
        p = p[c]
    p[''] = ''                  # ending flag

__ref_cut = cut
__ref_cut_for_search = cut_for_search


def __lcut(sentence):
    return list(__ref_cut(sentence, False))


def __lcut_all(sentence):
    return list(__ref_cut(sentence, True))


def __lcut_for_search(sentence):
    return list(__ref_cut_for_search(sentence))


@require_initialized
def enable_parallel(processnum=None):
    global pool, cut, cut_for_search
    if os.name == 'nt':
        raise Exception("jieba: parallel mode only supports posix system")
    if sys.version_info[0] == 2 and sys.version_info[1] < 6:
        raise Exception(
            "jieba: the parallel feature needs Python version>2.5 ")
    from multiprocessing import Pool, cpu_count
    if processnum == None:
        processnum = cpu_count()
    pool = Pool(processnum)

    def pcut(sentence, cut_all=False):
        parts = re.compile(b'([\r\n]+)').split(sentence)
        if cut_all:
            result = pool.map(__lcut_all, parts)
        else:
            result = pool.map(__lcut, parts)
        for r in result:
            for w in r:
                yield w

    def pcut_for_search(sentence):
        parts = re.compile(b'([\r\n]+)').split(sentence)
        result = pool.map(__lcut_for_search, parts)
        for r in result:
            for w in r:
                yield w

    cut = pcut
    cut_for_search = pcut_for_search


def disable_parallel():
    global pool, cut, cut_for_search
    if 'pool' in globals():
        pool.close()
        pool = None
    cut = __ref_cut
    cut_for_search = __ref_cut_for_search


def set_dictionary(dictionary_path):
    global initialized, DICTIONARY
    with DICT_LOCK:
        abs_path = os.path.normpath(
            os.path.join(os.getcwd(), dictionary_path))
        if not os.path.exists(abs_path):
            raise Exception("jieba: path does not exists:" + abs_path)
        DICTIONARY = abs_path
        initialized = False


def get_abs_path_dict():
    _curpath = os.path.normpath(
        os.path.join(os.getcwd(), os.path.dirname(__file__)))
    abs_path = os.path.join(_curpath, DICTIONARY)
    return abs_path


def tokenize(unicode_sentence, mode="default"):
    # mode ("default" or "search")
    if not isinstance(unicode_sentence, str):
        raise Exception("jieba: the input parameter should  unicode.")
    start = 0
    if mode == 'default':
        for w in cut(unicode_sentence):
            width = len(w)
            yield (w, start, start + width)
            start += width
    else:
        for w in cut(unicode_sentence):
            width = len(w)
            if len(w) > 2:
                for i in range(len(w) - 1):
                    gram2 = w[i:i + 2]
                    if gram2 in FREQ:
                        yield (gram2, start + i, start + i + 2)
            if len(w) > 3:
                for i in range(len(w) - 2):
                    gram3 = w[i:i + 3]
                    if gram3 in FREQ:
                        yield (gram3, start + i, start + i + 3)
            yield (w, start, start + width)
            start += width
