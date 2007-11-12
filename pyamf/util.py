# -*- encoding: utf8 -*-
#
# Copyright (c) 2007 The PyAMF Project. All rights reserved.
# 
# Arnar Birgisson
# Thijs Triemstra
# Nick Joyce
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
AMF Utilities.

@author: U{Arnar Birgisson<mailto:arnarbi@gmail.com>}
@author: U{Thijs Triemstra<mailto:info@collab.nl>}
@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.1.0
"""

import struct, calendar, datetime

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

try:
    import xml.etree.ElementTree as ET
except ImportError:
    try:
        import cElementTree as ET
        ET._ElementInterface = ET.ElementTree
    except ImportError:
        import elementtree.ElementTree as ET

class StringIOProxy(object):
    """
    I am a C{StringIO} type object containing byte data from the AMF stream.

    @see: U{http://osflash.org/documentation/amf3#x0c_-_bytearray}
    @see: U{http://osflash.org/documentation/amf3/parsing_byte_arrays}
    """

    def __init__(self, buf):
        """
        @param buf:
        @type buf:
        @raise TypeError: Unable to coerce buffer to C{StringIO}.
        """
        self._buffer = StringIO()

        if isinstance(buf, (str, unicode)):
            self._buffer.write(buf)
        elif hasattr(buf, 'getvalue'):
            self._buffer.write(buf.getvalue())
        elif hasattr(buf, 'read') and hasattr(buf, 'seek') and hasattr(buf, 'tell'):
            old_pos = buf.tell()
            buf.seek(0)
            self._buffer.write(buf.read())
            buf.seek(old_pos)
        elif buf is None:
            pass
        else:
            raise TypeError("Unable to coerce buf->StringIO")

        self._len = self._buffer.tell()
        self._buffer.seek(0, 0)

    def close(self):
        self._buffer.close()
        self._len = -1

    def flush(self):
        self._buffer.flush()
        self._len = 0

    def getvalue(self):
        return self._buffer.getvalue()

    def next(self):
        return self._buffer.next()

    def read(self, n=-1):
        bytes = self._buffer.read(n)
        self._len = self._len - len(bytes)

        return bytes

    def readline(self, length=None):
        line = self._buffer.readline(length)
        self._len = self._len - len(line)

        return line

    def readlines(self, sizehint=0):
        lines = self._buffer.readlines(sizehint)
        self._get_len()

    def seek(self, pos, mode=0):
        return self._buffer.seek(pos, mode)

    def tell(self):
        return self._buffer.tell()

    def truncate(self, size=None):
        bytes = self._buffer.truncate(size)
        self._get_len()

    def write(self, s):
        self._buffer.write(s)
        self._len = self._len + len(s)

    def writelines(self, iterable):
        self._buffer.writelines(iterable)
        self._get_len()

    def _get_len(self):
        old_pos = self._buffer.tell()
        self._buffer.seek(0, 2)

        self._len = self._buffer.tell()
        self._buffer.seek(old_pos)

    def __len__(self):
        return self._len

class NetworkIOMixIn(object):
    """
    Provides mix-in methods for file-like objects to read and write basic
    datatypes in network (= big-endian) byte-order.
    """

    def read_uchar(self):
        return struct.unpack("!B", self.read(1))[0]

    def write_uchar(self, c):
        self.write(struct.pack("!B", c))

    def read_char(self):
        return struct.unpack("!b", self.read(1))[0]

    def write_char(self, c):
        self.write(struct.pack("!b", c))

    def read_ushort(self):
        return struct.unpack("!H", self.read(2))[0]

    def write_ushort(self, s):
        self.write(struct.pack("!H", s))

    def read_short(self):
        return struct.unpack("!h", self.read(2))[0]

    def write_short(self, s):
        self.write(struct.pack("!h", s))

    def read_ulong(self):
        return struct.unpack("!L", self.read(4))[0]

    def write_ulong(self, l):
        self.write(struct.pack("!L", l))

    def read_long(self):
        return struct.unpack("!l", self.read(4))[0]

    def write_long(self, l):
        self.write(struct.pack("!l", l))

    def read_double(self):
        return struct.unpack("!d", self.read(8))[0]

    def write_double(self, d):
        self.write(struct.pack("!d", d))

    def write_float(self, f):
        self.write(struct.pack("!f", f))

    def read_float(self):
        return struct.unpack("!f", self.read(4))[0]

    def read_utf8_string(self, length):
        """
        @param length:
        @type length:
        @rtype:
        @return:
        """
        str = struct.unpack("%ds" % length, self.read(length))[0]
        return unicode(str, "utf8")

    def write_utf8_string(self, u):
        self.write(u.encode("utf8"))

class BufferedByteStream(StringIOProxy, NetworkIOMixIn):
    """
    An extension of C{StringIO}.

    Features:
     - Raises C{EOFError} if reading past end.
     - Allows you to peek() at the next byte.
    """

    def __init__(self, buf=''):
        """
        @param buf:
        @type buf:
        """
        StringIOProxy.__init__(self, buf=buf)

    def read(self, length=-1):
        """
        Read bytes from stream.

        @raise EOFError: Reading past end of stream.
        @param length:
        @type length:
        @rtype:
        @return:
        """
        if length > 0 and self.at_eof():
            raise EOFError
        if length > 0 and self.tell() + length > len(self):
            length = len(self) - self.tell()
        return StringIOProxy.read(self, length)

    def peek(self, size=1):
        """
        Looks size bytes ahead in the stream, returning what it finds,
        returning the stream pointer to its initial position.

        @param length:
        @type length:
        @rtype:
        @return: Bytes.
        """
        if size == -1:
            return self.peek(len(self) - self.tell())

        bytes = ''
        pos = self.tell()

        while not self.at_eof() and len(bytes) != size:
            bytes += self.read(1)

        self.seek(pos)

        return bytes

    def at_eof(self):
        """
        Returns true if next .read(1) will trigger C{EOFError}.

        @rtype: bool
        @return:
        """
        return self.tell() >= len(self)

    def remaining(self):
        """
        Returns number of remaining bytes.

        @rtype: number
        @return: Number of remaining bytes.
        """
        return len(self) - self.tell()

def hexdump(data):
    """
    Get hexadecimal representation of C{StringIO} data.

    @type data:
    @param data:
    @rtype:
    @return: Buffer.
    """
    import string

    hex = ascii = buf = ""
    index = 0

    for c in data:
        hex += "%02x " % ord(c)
        if c in string.printable and c not in string.whitespace:
            ascii += c
        else:
            ascii += "."

        if len(ascii) == 16:
            buf += "%04x:  %s %s %s\n" % (index, hex[:24], hex[24:], ascii)
            hex = ascii = ""
            index += 16

    if len(ascii):
        buf += "%04x:  %-24s %-24s %s\n" % (index, hex[:24], hex[24:], ascii)

    return buf

def get_timestamp(d):
    """
    Returns a UTC timestamp for a C{datetime.datetime} object.

    @type d:
    @param d:
    @return: UTC timestamp.
    @rtype: str
    
    @see: Inspiration taken from the U{Intertwingly blog
    <http://intertwingly.net/blog/2007/09/02/Dealing-With-Dates>}.
    """
    return calendar.timegm(d.utctimetuple())

def get_datetime(ms):
    """
    Return a UTC date from a timestamp.

    @type ms:
    @param ms: Nanoseconds since 1970.
    @return: UTC timestamp.
    @rtype: C{datetime.datetime}
    """
    return datetime.datetime.utcfromtimestamp(ms)
