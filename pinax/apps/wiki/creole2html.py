#!/usr/bin/env python

r"""
WikiCreole to HTML converter
This program is an example of how the creole.py WikiCreole parser
can be used.

@copyright: 2007 MoinMoin:RadomirDopieralski
@license: BSD, see COPYING for details.

Test cases contributed by Jan Klopper (janklopper@underdark.nl),
modified by Radomir Dopieralski (MoinMoin:RadomirDopieralski).

>>> import lxml.html.usedoctest
>>> def parse(text):
...     print HtmlEmitter(Parser(text).parse()).emit()

>>> parse(u'test')
<p>test</p>

>>> parse(u'test\ntest')
<p>test test</p>

>>> HtmlEmitter(Parser(u'test\ntest').parse()).emit()
u'<p>test test</p>\n'

>>> parse(u'test\n\ntest')
<p>test</p><p>test</p>

>>> parse(u'test\\\\test')
<p>test<br>test</p>

>>> parse(u'ÓÔÕÖØÙÚÛÜÝßàáâãäåæçèéêëìíîïñòóôõöøùúûüýÿŒœ%0A')
<p>ÓÔÕÖØÙÚÛÜÝßàáâãäåæçèéêëìíîïñòóôõöøùúûüýÿŒœ%0A</p>

>>> parse(u'----')
<hr>

>>> parse(u'==test==')
<h2>test</h2>

>>> parse(u'== test')
<h2>test</h2>

>>> parse(u'==test====')
<h2>test</h2>

>>> parse(u'=====test')
<h5>test</h5>

>>> parse(u'==test==\ntest\n===test===')
<h2>test</h2>
<p>test</p>
<h3>test</h3>

>>> parse(u'test\n* test line one\n * test line two\ntest\n\ntest')
<p>test</p>
<ul>
    <li>test line one</li>
    <li>test line two test</li>
</ul>
<p>test</p>

>>> parse(u'* test line one\n* test line two\n** Nested item')
<ul>
    <li>test line one</li>
    <li>test line two<ul>
        <li>Nested item</li>
    </ul></li>
</ul>

>>> parse(u'* test line one\n* test line two\n# Nested item')
<ul>
    <li>test line one</li>
    <li>test line two<ol>
        <li>Nested item</li>
    </ol></li>
</ul>

>>> parse(u'test //test test// test **test test** test')
<p>test <i>test test</i> test <b>test test</b> test</p>

>>> parse(u'test //test **test// test** test')
<p>test <i>test <b>test<i> test<b> test</b></i></b></i></p>

>>> parse(u'**test')
<p><b>test</b></p>

>>> parse(u'|x|y|z|\n|a|b|c|\n|d|e|f|\ntest')
<table>
    <tr><td>x</td><td>y</td><td>z</td></tr>
    <tr><td>a</td><td>b</td><td>c</td></tr>
    <tr><td>d</td><td>e</td><td>f</td></tr>
</table>
<p>test</p>

>>> parse(u'|=x|y|=z=|\n|a|b|c|\n|d|e|f|')
<table>
    <tr><th>x</th><td>y</td><th>z</th></tr>
    <tr><td>a</td><td>b</td><td>c</td></tr>
    <tr><td>d</td><td>e</td><td>f</td></tr>
</table>

>>> parse(u'test http://example.com/test test')
<p>test <a href="http://example.com/test">http://example.com/test</a> test</p>

>>> parse(u'http://example.com/,test, test')
<p><a href="http://example.com/,test">http://example.com/,test</a>, test</p>

>>> parse(u'(http://example.com/test)')
<p>(<a href="http://example.com/test">http://example.com/test</a>)</p>

XXX This might be considered a bug, but it's impossible to detect in general.
>>> parse(u'http://example.com/(test)')
<p><a href="http://example.com/(test">http://example.com/(test</a>)</p>

>>> parse(u'http://example.com/test?test&test=1')
<p><a href="http://example.com/test?test&amp;test=1">http://example.com/test?test&amp;test=1</a></p>

>>> parse(u'~http://example.com/test')
<p>http://example.com/test</p>

>>> parse(u'http://example.com/~test')
<p><a href="http://example.com/~test">http://example.com/~test</a></p>

>>> parse(u'[[test]] [[tset|test]]')
<p><a href="test">test</a> <a href="tset">test</a></p>

>>> parse(u'[[http://example.com|test]]')
<p><a href="http://example.com">test</a></p>
"""

from __future__ import absolute_import, unicode_literals
import re
from creole import Parser

class Rules:
    # For the link targets:
    proto = r'http|https|ftp|nntp|news|mailto|telnet|file|irc'
    extern = r'(?P<extern_addr>(?P<extern_proto>{0}):.*)'.format(proto)
    interwiki = r'''
            (?P<inter_wiki> [A-Z][a-zA-Z]+ ) :
            (?P<inter_page> .* )
        '''

class HtmlEmitter:
    """
    Generate HTML output for the document
    tree consisting of DocNodes.
    """

    addr_re = re.compile('|'.join([
            Rules.extern,
            Rules.interwiki,
        ]), re.X | re.U) # for addresses

    def __init__(self, root):
        self.root = root

    def get_text(self, node):
        """Try to emit whatever text is in the node."""

        try:
            return node.children[0].content or ''
        except:
            return node.content or ''

    def html_escape(self, text):
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    def attr_escape(self, text):
        return self.html_escape(text).replace('"', '&quot')

    # *_emit methods for emitting nodes of the document:

    def document_emit(self, node):
        return self.emit_children(node)

    def text_emit(self, node):
        return self.html_escape(node.content)

    def separator_emit(self, node):
        return '<hr>';

    def paragraph_emit(self, node):
        return '<p>{0}</p>\n'.format(self.emit_children(node))

    def bullet_list_emit(self, node):
        return '<ul>\n{0}</ul>\n'.format(self.emit_children(node))

    def number_list_emit(self, node):
        return '<ol>\n{0}</ol>\n'.format(self.emit_children(node))

    def list_item_emit(self, node):
        return '<li>{0}</li>\n'.format(self.emit_children(node))

    def table_emit(self, node):
        return '<table>\n{0}</table>\n'.format(self.emit_children(node))

    def table_row_emit(self, node):
        return '<tr>{0}</tr>\n'.format(self.emit_children(node))

    def table_cell_emit(self, node):
        return '<td>{0}</td>'.format(self.emit_children(node))

    def table_head_emit(self, node):
        return '<th>{0}</th>'.format(self.emit_children(node))

    def emphasis_emit(self, node):
        return '<i>{0}</i>'.format(self.emit_children(node))

    def strong_emit(self, node):
        return '<b>{0}</b>'.format(self.emit_children(node))

    def header_emit(self, node):
        return '<h{0:d}>{1}</h{2:d}>\n'.format(
            node.level, self.html_escape(node.content), node.level
        )

    def code_emit(self, node):
        return '<tt>{0}</tt>'.format(self.html_escape(node.content))

    def link_emit(self, node):
        target = node.content
        if node.children:
            inside = self.emit_children(node)
        else:
            inside = self.html_escape(target)
        m = self.addr_re.match(target)
        if m:
            if m.group('extern_addr'):
                return '<a href="{0}">{1}</a>'.format(
                    self.attr_escape(target), inside
                )
            elif m.group('inter_wiki'):
                raise NotImplementedError
        return '<a href="{0}">{1}</a>'.format(
            self.attr_escape(target), inside
        )

    def image_emit(self, node):
        target = node.content
        text = self.get_text(node)
        m = self.addr_re.match(target)
        if m:
            if m.group('extern_addr'):
                return '<img src="{0}" alt="{1}">'.format(
                    self.attr_escape(target), self.attr_escape(text)
                )
            elif m.group('inter_wiki'):
                raise NotImplementedError
        return '<img src="{0}" alt="{1}">'.format(
            self.attr_escape(target), self.attr_escape(text)
        )

    def macro_emit(self, node):
        raise NotImplementedError

    def break_emit(self, node):
        return "<br>"

    def preformatted_emit(self, node):
        return "<pre>{0}</pre>".format(self.html_escape(node.content))

    def default_emit(self, node):
        """Fallback function for emitting unknown nodes."""

        raise TypeError

    def emit_children(self, node):
        """Emit all the children of a node."""

        return ''.join([self.emit_node(child) for child in node.children])

    def emit_node(self, node):
        """Emit a single node."""

        emit = getattr(self, '{0}_emit'.format(node.kind), self.default_emit)
        return emit(node)

    def emit(self):
        """Emit the document represented by self.root DOM tree."""

        return self.emit_node(self.root)

if __name__=="__main__":
    import sys
    document = Parser(unicode(sys.stdin.read(), 'utf-8', 'ignore')).parse()
    sys.stdout.write(HtmlEmitter(document).emit().encode('utf-8', 'ignore'))


