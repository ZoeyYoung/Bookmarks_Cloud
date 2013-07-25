import argparse
import sys

from .readability import VERSION
from .readability.readability import Document


def parse_args():
    desc = "fast python port of arc90's readability tool"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('--version',
                        action='version', version=VERSION)

    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        default=False,
                        help='Increase logging verbosity to DEBUG.')

    parser.add_argument('-m', '--metadata',
                        action='store_true',
                        default=False,
                        help='print all metadata as well as content for the content')

    parser.add_argument('path', metavar='P', type=str, nargs=1,
                        help="The url or file path to process in readable form.")

    args = parser.parse_args()
    return args


def main():
    args = parse_args()

    target = args.path[0]

    if target.startswith('http') or target.startswith('www'):
        is_url = True
        url = target
    else:
        is_url = False
        url = None

    if is_url:
        import urllib.request
        import urllib.parse
        import urllib.error
        target = urllib.request.urlopen(target)
    else:
        target = open(target, 'rt')

    enc = sys.__stdout__.encoding or 'utf-8'

    try:
        doc = Document(target.read(),
                       debug=args.verbose,
                       url=url)
        if args.metadata:
            m = doc.summary_with_metadata()
            print(m.title())
            print(m.short_title())
            print(m.confidence)
            print(m.html.encode(enc, 'replace'))
        else:
            print(doc.summary().encode(enc, 'replace'))

    finally:
        target.close()


if __name__ == '__main__':
    main()
