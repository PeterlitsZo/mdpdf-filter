#!/usr/bin/python3

# Author: John MacFarlane <jgm@berkeley.edu>
# Forker: Peterlits Zo <peterlitszo@outlook.com>
# Copyright: (C) 2013 John MacFarlane
# License: BSD3

"""
Functions to aid writing python scripts that process the pandoc
AST serialized as JSON.
"""


import codecs
import io
import json
import sys
from typing import List, Callable, Union


def walk(tree: Union[list, dict], action: Callable, format: str, meta: dict):
    """Walk a tree, applying an action to every object.
    Returns a modified tree.  An action is a function of the form
    `action(key, value, format, meta)`, where:

    * `key` is the type of the pandoc object (e.g. 'Str', 'Para') `value` is
    * the contents of the object (e.g. a string for 'Str', a list of
      inline elements for 'Para')
    * `format` is the target output format (as supplied by the
      `format` argument of `walk`)
    * `meta` is the document's metadata

    The return of an action is either:

    * `None`: this means that the object should remain unchanged
    * a pandoc object: this will replace the original object
    * a list of pandoc objects: these will replace the original object; the
      list is merged with the neighbors of the orignal objects (spliced into
      the list the original object belongs to); returning an empty list deletes
      the object
    """
    if isinstance(tree, list):
        array = []
        for item in tree:
            if isinstance(item, dict) and 't' in item:
                res = action(item['t'],
                             item['c'] if 'c' in item else None, format, meta)
                # deal with res by its return value
                if res is None:
                    array.append(walk(item, action, format, meta))
                elif isinstance(res, list):
                    for item in res:
                        array.append(walk(item, action, format, meta))
                else:
                    array.append(walk(res, action, format, meta))
            else:
                array.append(walk(item, action, format, meta))
        return array
    elif isinstance(tree, dict):
        for key in tree:
            tree[key] = walk(tree[key], action, format, meta)
        return tree
    else:
        return tree


def toJSONFilter(action: Callable):
    """Like `toJSONFilters`, but takes a single action as argument.
    """
    toJSONFilters([action])


def toJSONFilters(actions: List[Callable]):
    """Generate a JSON-to-JSON filter from stdin to stdout

    The filter:

    * reads a JSON-formatted pandoc document from stdin
    * transforms it by walking the tree and performing the actions
    * returns a new JSON-formatted pandoc document to stdout

    The argument `actions` is a list of functions of the form
    `action(key, value, format, meta)`, as described in more
    detail under `walk`.

    This function calls `applyJSONFilters`, with the `format`
    argument provided by the first command-line argument,
    if present.  (Pandoc sets this by default when calling
    filters.)
    """
    input_stream = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')

    source = input_stream.read()
    if len(sys.argv) > 1:
        format = sys.argv[1]
    else:
        format = ""

    sys.stdout.write(applyJSONFilters(actions, source, format))


def applyJSONFilters(actions: List[Callable], source: str, format:str = "") -> str:
    """Walk through JSON structure and apply filters

    This:

    * reads a JSON-formatted pandoc document from a source string
    * transforms it by walking the tree and performing the actions
    * returns a new JSON-formatted pandoc document as a string

    The `actions` argument is a list of functions (see `walk`
    for a full description).

    The argument `source` is a string encoded JSON object.

    The argument `format` is a string describing the output format.

    Returns a the new JSON-formatted pandoc document.
    """

    doc = json.loads(source)
    meta = doc.get('meta', {})

    for action in actions:
        doc = walk(doc, action, format, meta)

    return json.dumps(altered)


def stringify(tree):
    """Walks the tree 'tree' and returns concatenated string content,
    leaving out all formatting.
    """
    result = []

    def go(key, val, format, meta):
        if key in ['Str', 'MetaString']:
            result.append(val)
        elif key == 'Code':
            result.append(val[1])
        elif key == 'Math':
            result.append(val[1])
        elif key == 'LineBreak':
            result.append(" ")
        elif key == 'SoftBreak':
            result.append(" ")
        elif key == 'Space':
            result.append(" ")

    walk(tree, go, "", {})
    return ''.join(result)


def attributes(attrs: dict) -> tuple:
    """Returns an attribute list, constructed from the
    dictionary attrs.
    """
    attrs = attrs or {}
    ident = attrs.get("id", "")
    classes = attrs.get("classes", [])
    keyvals = [[x, attrs[x]] for x in attrs if (x != "classes" and x != "id")]
    return ident, classes, keyvals


def elt(eltType: str, num_args: int) -> 'function':
    def fun(*args):
        f"""{eltType}(*args)
        need {num_args} args to get the JSON-like dict.
        """
        len_args = len(args)
        if len_args != num_args:
            raise ValueError(f'{eltType} except {num_args} arguments, but given {len_args}')

        if num_args == 0:
            content = []
        elif len(args) == 1:
            content = args[0]
        else:
            content = list(args)
        return {'t': eltType, 'c': content}
    return fun


# function, using args to return a dict like: {'t': eltType, 'c': content}
# ---[ Constructors for block elements ]-------------------------------------------------

Plain = elt('Plain', 1)
Para = elt('Para', 1)
CodeBlock = elt('CodeBlock', 2)
RawBlock = elt('RawBlock', 2)
BlockQuote = elt('BlockQuote', 1)
OrderedList = elt('OrderedList', 2)
MetaInlines = elt('MetaInlines', 1)
MetaBlocks = elt('MetaBlocks', 1)
BulletList = elt('BulletList', 1)
DefinitionList = elt('DefinitionList', 1)
Header = elt('Header', 3)
HorizontalRule = elt('HorizontalRule', 0)
Table = elt('Table', 5)
Div = elt('Div', 2)
Null = elt('Null', 0)

# ---[ Constructors for inline elements ]------------------------------------------------

Str = elt('Str', 1)
Emph = elt('Emph', 1)
Strong = elt('Strong', 1)
Strikeout = elt('Strikeout', 1)
Superscript = elt('Superscript', 1)
Subscript = elt('Subscript', 1)
SmallCaps = elt('SmallCaps', 1)
Quoted = elt('Quoted', 2)
Cite = elt('Cite', 2)
Code = elt('Code', 2)
Space = elt('Space', 0)
LineBreak = elt('LineBreak', 0)
Math = elt('Math', 2)
MetaString = elt('MetaString', 1)
RawInline = elt('RawInline', 2)
Link = elt('Link', 3)
Image = elt('Image', 3)
Note = elt('Note', 1)
SoftBreak = elt('SoftBreak', 0)
Span = elt('Span', 2)
