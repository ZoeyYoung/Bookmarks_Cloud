from lxml.html import html5parser
from lxml.html import fragment_fromstring
from lxml.html import tostring
html = """
<html>
<head>
</head>
<body>
    Text
    <h1>Title</h1>
    Tail1
    <div>p1<p>inner text</p></div>
    <p>p2</p>
    Tail2
</body>
"""
html5doc = html5parser.document_fromstring(html, guess_charset=False)
root = fragment_fromstring(tostring(html5doc))
for elem in root.findall(".//body"):
    # 1. 为Text包装<p>, 即将Text变成<p>Text</p>
    if elem.text and elem.text.strip():
        p = fragment_fromstring('<p/>')
        p.text = elem.text
        elem.text = None
        elem.insert(0, p)
    # 2. 为body的子元素包装div
    div = fragment_fromstring("<div/>")
    for e in elem.iterchildren():
        print(e, e.text)
        div.append(e)
        print(tostring(div))
    elem.insert(0, div)

print(tostring(root))
