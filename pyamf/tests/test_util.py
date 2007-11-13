# -*- encoding: utf-8 -*-
#
# Copyright (c) 2007 The PyAMF Project. All rights reserved.
# 
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""
Tests for PyAMF.

@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.1.0
"""

import unittest

from datetime import datetime
from StringIO import StringIO

from pyamf import util

class TimestampTestCase(unittest.TestCase):
    def test_get_timestamp(self):
        self.assertEqual(util.get_timestamp(datetime(2007, 11, 12)), 1194825600)

    def test_get_datetime(self):
        self.assertEqual(util.get_datetime(1194825600), datetime(2007, 11, 12))

class StringIOProxyTestCase(unittest.TestCase):
    def setUp(self):
        from StringIO import StringIO

        self.previous = util.StringIOProxy._wrapped_class
        util.StringIOProxy._wrapped_class = StringIO

    def tearDown(self):
        util.StringIOProxy._wrapped_class = self.previous

    def test_create(self):
        sp = util.StringIOProxy()

        self.assertEquals(sp._buffer.tell(), 0)
        self.assertEquals(sp._buffer.getvalue(), '')
        self.assertEquals(len(sp), 0)
        self.assertEquals(sp.getvalue(), '')

        sp = util.StringIOProxy(None)

        self.assertEquals(sp._buffer.tell(), 0)
        self.assertEquals(sp._buffer.getvalue(), '')
        self.assertEquals(len(sp), 0)
        self.assertEquals(sp.getvalue(), '')

        sp = util.StringIOProxy('')

        self.assertEquals(sp._buffer.tell(), 0)
        self.assertEquals(sp._buffer.getvalue(), '')
        self.assertEquals(len(sp), 0)
        self.assertEquals(sp.getvalue(), '')

        sp = util.StringIOProxy('foo')

        self.assertEquals(sp._buffer.tell(), 0)
        self.assertEquals(sp._buffer.getvalue(), 'foo')
        self.assertEquals(len(sp), 3)
        self.assertEquals(sp.getvalue(), 'foo')

        sp = util.StringIOProxy(StringIO('this is a test'))
        self.assertEquals(sp._buffer.tell(), 0)
        self.assertEquals(sp._buffer.getvalue(), 'this is a test')
        self.assertEquals(len(sp), 14)
        self.assertEquals(sp.getvalue(), 'this is a test')

        self.assertRaises(TypeError, util.StringIOProxy, self)

    def test_close(self):
        sp = util.StringIOProxy()

        sp.close()

        self.assertEquals(len(sp), 0)
        self.assertRaises(ValueError, sp.write, 'asdfasdf')

    def test_flush(self):
        sp = util.StringIOProxy('foobar')

        self.assertEquals(sp.getvalue(), 'foobar')
        self.assertEquals(len(sp), 6)
        self.assertEquals(sp.tell(), 0)

        sp.flush()

        self.assertEquals(sp.getvalue(), 'foobar')
        self.assertEquals(len(sp), 6)
        self.assertEquals(sp.tell(), 0)

    def test_getvalue(self):
        sp = util.StringIOProxy()

        sp.write('asdfasdf')
        self.assertEquals(sp.getvalue(), 'asdfasdf')
        sp.write('foo')
        self.assertEquals(sp.getvalue(), 'asdfasdffoo')

    def test_read(self):
        sp = util.StringIOProxy('this is a test')

        self.assertEquals(len(sp), 14)
        self.assertEquals(sp.read(1), 't')
        self.assertEquals(sp.getvalue(), 'this is a test')
        self.assertEquals(len(sp), 14)
        self.assertEquals(sp.read(10), 'his is a t')
        self.assertEquals(sp.read(), 'est')

    def test_readline(self):
        sp = util.StringIOProxy("this is a test\nfoo and bar")
        
        self.assertEquals(len(sp), 26)
        self.assertEquals(sp.getvalue(), "this is a test\nfoo and bar")
        self.assertEquals(sp.readline(), 'this is a test\n')

        self.assertEquals(len(sp), 26)
        self.assertEquals(sp.getvalue(), "this is a test\nfoo and bar")
        self.assertEquals(sp.readline(), 'foo and bar')

    def test_readlines(self):
        sp = util.StringIOProxy("\n".join([
            "line 1",
            "line 2",
            "line 3",
            "line 4",
        ]))

        self.assertEquals(len(sp), 27)
        self.assertEquals(sp.readlines(), [
            "line 1\n",
            "line 2\n",
            "line 3\n",
            "line 4",
        ])

        self.assertEquals(len(sp), 27)
        self.assertEquals(sp.getvalue(), "\n".join([
            "line 1",
            "line 2",
            "line 3",
            "line 4",
        ]))

    def test_seek(self):
        sp = util.StringIOProxy('abcdefghijklmnopqrstuvwxyz')

        self.assertEquals(sp.getvalue(), 'abcdefghijklmnopqrstuvwxyz')
        self.assertEquals(sp.tell(), 0)

        # Relative to the beginning of the stream
        sp.seek(0, 0)
        self.assertEquals(sp.tell(), 0)
        self.assertEquals(sp.getvalue(), 'abcdefghijklmnopqrstuvwxyz')
        self.assertEquals(sp.read(1), 'a')
        self.assertEquals(len(sp), 26)

        sp.seek(10, 0)
        self.assertEquals(sp.tell(), 10)
        self.assertEquals(sp.getvalue(), 'abcdefghijklmnopqrstuvwxyz')
        self.assertEquals(sp.read(1), 'k')
        self.assertEquals(len(sp), 26)

        sp.seek(-5, 1)
        self.assertEquals(sp.tell(), 6)
        self.assertEquals(sp.getvalue(), 'abcdefghijklmnopqrstuvwxyz')
        self.assertEquals(sp.read(1), 'g')
        self.assertEquals(len(sp), 26)

        sp.seek(-3, 2)
        self.assertEquals(sp.tell(), 23)
        self.assertEquals(sp.getvalue(), 'abcdefghijklmnopqrstuvwxyz')
        self.assertEquals(sp.read(1), 'x')
        self.assertEquals(len(sp), 26)

    def test_tell(self):
        sp = util.StringIOProxy('abcdefghijklmnopqrstuvwxyz')

        self.assertEquals(sp.getvalue(), 'abcdefghijklmnopqrstuvwxyz')
        self.assertEquals(len(sp), 26)

        self.assertEquals(sp.tell(), 0)
        sp.read(1)
        self.assertEquals(sp.tell(), 1)

        self.assertEquals(sp.getvalue(), 'abcdefghijklmnopqrstuvwxyz')
        self.assertEquals(len(sp), 26)

        sp.read(5)
        self.assertEquals(sp.tell(), 6)

    def test_truncate(self):
        sp = util.StringIOProxy('abcdef')

        self.assertEquals(sp.getvalue(), 'abcdef')
        self.assertEquals(len(sp), 6)

        sp.truncate()
        self.assertEquals(sp.getvalue(), '')
        self.assertEquals(len(sp), 0)

    def test_write(self):
        sp = util.StringIOProxy()

        self.assertEquals(sp.getvalue(), '')
        self.assertEquals(len(sp), 0)
        self.assertEquals(sp.tell(), 0)

        sp.write('hello')
        self.assertEquals(sp.getvalue(), 'hello')
        self.assertEquals(len(sp), 5)
        self.assertEquals(sp.tell(), 5)

        sp = util.StringIOProxy('xyz')

        self.assertEquals(sp.getvalue(), 'xyz')
        self.assertEquals(len(sp), 3)
        self.assertEquals(sp.tell(), 0)

        sp.write('abc')
        self.assertEquals(sp.getvalue(), 'abc')
        self.assertEquals(len(sp), 3)
        self.assertEquals(sp.tell(), 3)

    def test_writelines(self):
        lines = ["line 1", "line 2", "line 3", "line 4"]
        sp = util.StringIOProxy()

        self.assertEquals(sp.getvalue(), '')
        self.assertEquals(len(sp), 0)
        self.assertEquals(sp.tell(), 0)

        sp.writelines(lines)

        self.assertEquals(sp.getvalue(), "".join(lines))
        self.assertEquals(len(sp), 24)
        self.assertEquals(sp.tell(), 24)

    def test_len(self):
        sp = util.StringIOProxy()

        self.assertEquals(sp.getvalue(), '')
        self.assertEquals(len(sp), 0)
        self.assertEquals(sp.tell(), 0)

        sp.write('xyz')

        self.assertEquals(len(sp), 3)

        sp = util.StringIOProxy('foo')

        self.assertEquals(len(sp), 3)

        sp.seek(0, 2)
        sp.write('xyz')

        self.assertEquals(len(sp), 6)

class cStringIOProxyTestCase(StringIOProxyTestCase):
    def setUp(self):
        from cStringIO import StringIO

        self.previous = util.StringIOProxy._wrapped_class
        util.StringIOProxy._wrapped_class = StringIO

def suite():
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(TimestampTestCase))
    suite.addTest(unittest.makeSuite(StringIOProxyTestCase))

    try:
        import cStringIO
        suite.addTest(unittest.makeSuite(cStringIOProxyTestCase))
    except ImportError:
        pass

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
