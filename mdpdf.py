#!/usr/bin/python3


from pandocfilters import RawInline, RawBlock, MetaString, MetaInlines, MetaBlocks
import io
import sys
import json
from typing import Union, Callable


# ---[ unit ]----------------------------------------------------------------------------
def colored_head(string: str) -> str:
    return f'\033[38;5;167m[md_to_pdf \033[38;5;172m{string}\033[38;5;167m]\033[0m'

def colored_head_print(string: str) -> Callable:
    import builtins
    def print_with_head(*argv, **argkw):
        builtins.print(colored_head(string), end=' ', file=sys.stderr)
        if not 'file' in argkw:
            argkw['file'] = sys.stderr
        builtins.print(*argv, **argkw)
    return print_with_head

def _uncolored_str_str(str_: str) -> str:
    str_ = str(str_)
    return '    ' + '\n    '.join(item for item in str_.split('\n'))

def _uncolored_str_list(list_: list) -> str:
    return '\n'.join(_uncolored_str_str(item) for item in list_)

def _coll_str(coll: Union[dict, list, str], indent:int) -> str:
    indent_num, indent = indent, indent * ' '
    if isinstance(coll, dict):
        result = []
        for key in coll:
            coll_key_str = _coll_str(coll[key], indent_num)
            if '\n' in coll_key_str:
                after = ('\n' + indent).join(coll_key_str.split('\n'))
                result.append(f'{key}:\n{indent + after}')
            else:
                result.append(f'{key}: {coll_key_str}')
        return '\n'.join(result)
    elif isinstance(coll, list):
        result = []
        for item in coll:
            coll_item_str = _coll_str(item, indent_num)
            if '\n' in coll_item_str:
                after_indented = ('\n' + '  ').join(coll_item_str.split('\n'))
                result.append(after_indented)
            else:
                result.append(coll_item_str)
        return '- ' + '\n- '.join(result)
    else:
        return str(coll)

def coll_str(coll: Union[dict, list, str]):
    return ''.join(['\033[38;5;229m', _coll_str(coll, 4), '\033[0m'])

def MetaRawLatex(string: str) -> MetaInlines: 
    return MetaInlines([RawInline('tex', string)])
# ---------------------------------------------------------------------------------------


def get_code_in_para(tree: Union[dict, list]) -> 'tree':
    print = colored_head_print('get_code_in_para')
    if isinstance(tree, list):
        if all(isinstance(element, dict) for element in tree):
            has_code_block = False
            for element in tree:
                if 't' in element and element['t'] == 'CodeBlock':
                    has_code_block = True
            if has_code_block:
                per_block = None
                for index, block in enumerate(tree):
                    if block['t'] == 'CodeBlock' and per_block and per_block['t'] == 'Para':
                        if block['c'][0][1]:
                            block_c_begin = (r'\begin{lstlisting}'
                                             f'[language={block["c"][0][1][0]}]\n')
                        else:
                            block_c_begin = r'\begin{lstlisting}'
                        block = RawInline('latex', 
                                          ('\n'
                                          f'{block_c_begin}\n'
                                          f'{block["c"][1]}\n'
                                          f'\\end{{lstlisting}}'))
                        per_block['c'].append(block)
                        print(f'mede code in para: \n{coll_str(block)}')
                        del tree[index]
                    per_block = block
            else:
                tree = [get_code_in_para(ele) for ele in tree]
        else:
            tree = [get_code_in_para(ele) for ele in tree]
    elif isinstance(tree, dict):
        tree = {key: get_code_in_para(tree[key]) for key in tree}
    else:
        return tree
    return tree


def add_meta(doc: dict) -> None:
    print = colored_head_print('add_meta')
    doc['meta'] = {
        "CJKmainfont" : MetaString("AR PL KaitiM GB"),
        "papersize" : MetaString("a4"),
        "geometry" : MetaString("right=3cm, left=3cm, top=3.5cm, bottom=3.5cm"),
        "fontsize" : MetaString("12pt"),
        "header-includes" : MetaRawLatex(r"\usepackage{listing}"'\n'
                                         r"\lstset{"'\n'
                                         r"    basicstyle=\fontsize{10pt}{13pt}"
                                               r"\ttfamily\color{Green4!5!black},"'\n'
                                         r"    frame=tRBl,"'\n'
                                         r"    breakatwhitespace=false,"'\n'
                                         r"    keywordstyle=\color{Green4!50!black},"'\n'
                                         r"    commentstyle=\color{Gray0!50!black},"'\n'
                                         r"    stringstyle=\color{Orange4!50!black},"'\n'
                                         r"    breaklines=true,"'\n'
                                         r"    xleftmargin=2.5em,"'\n'
                                         r"    showstringspaces=false,"'\n'
                                         r"}"'\n'
                                         r"\usepackage{graphicx}"'\n'
                                         r"\usepackage{import}")
    }
    print(f'change meta to: \n{coll_str(doc["meta"])}')


def md_to_pdf():
    input = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8').read()
    print = colored_head_print('md_to_pdf')
    doc = json.loads(input)

    doc = get_code_in_para(doc)
    add_meta(doc)

    print('finish my work~')
    sys.stdout.write(json.dumps(doc))


if __name__ == '__main__':
    md_to_pdf()



