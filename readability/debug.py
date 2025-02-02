uids = {}


def save_to_file(text, filename):
    f = open(filename, 'wt')
    f.write("""
        <meta http-equiv="Content-Type"
            content="text/html; charset=UTF-8"
        />""")
    f.write(text.encode('utf-8'))
    f.close()


# def describe(node, depth=1):
#     if not hasattr(node, 'tag'):
#         return "[%s]" % type(node)
#     name = node.tag
#     if node.get('id', ''):
#         name += '#' + node.get('id')
#     if node.get('class', ''):
#         name += '.' + node.get('class').replace(' ', '.')
#     if name[:4] in ['div#', 'div.']:
#         name = name[3:]
#     if depth and node.getparent() is not None:
#         return name + ' - ' + describe(node.getparent(), depth - 1)
#     return name


def describe(node, depth=2):
    if not hasattr(node, 'tag'):
        return "[%s]" % type(node)
    name = node.tag
    if node.get('id', ''):
        name += '#' + node.get('id')
    if node.get('class', ''):
        name += '.' + node.get('class').replace(' ', '.')
    if name[:4] in ['div#', 'div.']:
        name = name[3:]
    if name in ['tr', 'td', 'div', 'p']:
        if not node in uids:
            uid = uids[node] = len(uids) + 1
        else:
            uid = uids.get(node)
        name += "%02d" % (uid)
    if depth and node.getparent() is not None:
        return name + ' - ' + describe(node.getparent(), depth - 1)
    return name
