# -*- encoding: utf8 -*-
#
# Copyright (c) 2007 The PyAMF Project. All rights reserved.
# 
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
AMF Remoting support.

References:
 - U{http://osflash.org/documentation/amf/envelopes/remoting}
 - U{http://osflash.org/amf/envelopes/remoting/headers}
"""

import sys, traceback

import pyamf
from pyamf import util

__all__ = ['Envelope', 'Request', 'decode', 'encode']

#: Succesful call.
STATUS_OK = 0
#: Reserved for runtime errors.
STATUS_ERROR = 1
#: Debug information.
#: 
#: Reference: U{http://osflash.org/documentation/amf/envelopes/remoting/debuginfo}
STATUS_DEBUG = 2
#: AMF mimetype.
CONTENT_TYPE       = 'application/x-amf'

STATUS_CODES = {
    STATUS_OK:    '/onResult',
    STATUS_ERROR: '/onStatus',
    STATUS_DEBUG: '/onDebugEvents'
}

class RemotingError(pyamf.BaseError):
    """
    Generic remoting error class
    """

class HeaderCollection(dict):
    """
    Collection of AMF message headers.
    """
    def __init__(self, raw_headers={}):
        self.required = []

        for (k, ig, v) in raw_headers:
            self[k] = v
            if ig:
                self.required.append(k)

    def is_required(self, idx):
        if not idx in self:
            raise KeyError("Unknown header %s" % str(idx))

        return idx in self.required

    def set_required(self, idx, value=True):
        if not idx in self:
            raise KeyError("Unknown header %s" % str(idx))

        if not idx in self.required:
            self.required.append(idx)

class Envelope(dict):
    """
    I wrap an entire request, encapsulating headers and bodies (there may more
    than one request in one transaction).
    """

    def __init__(self, amfVersion=None, clientType=None, context=None):
        self.amfVersion = amfVersion
        self.clientType = clientType
        self.context = context

        self.headers = HeaderCollection()

    def __repr__(self):
        r = "<Envelope amfVersion=%s clientType=%s>\n" % (
            self.amfVersion, self.clientType)

        for h in self.headers:
            r += " " + repr(h) + "\n"

        for request in iter(self):
            r += " " + repr(request) + "\n"

        r += "</Envelope>"

        return r

    def __setitem__(self, idx, value):
        if isinstance(value, (tuple, set, list)):
            value = Message(self, value[0], value[1], value[2])
        elif not isinstance(value, Message):
            raise TypeError("value must be a tuple/set/list")

        value.envelope = self
        dict.__setitem__(self, idx, value)

    def __iter__(self):
        return self.iteritems()

class Message(object):
    """
    I represent a singular message, containing a collection of headers and
    one body of data.

    I am used to iterate over all requests in the L{Envelope}
    """

    def __init__(self, envelope, target, status, body):
        self.envelope = envelope
        self.target = target
        self.status = status
        self.body = body

    def _get_headers(self):
        return self.envelope.headers

    headers = property(_get_headers)

    def __repr__(self):
        return "<%s target=%s status=%s>%s</Message>" % (
            type(self).__name__, self.target,
            _get_status(self.status), self.body)

class BaseGateway(object):
    """
    """

    def __init__(self, services):
        """
        @param services: Initial services
        @type services: dict
        """
        self.services = {}

        for name, service in services.iteritems():
            self.addService(service, name)

    def addService(self, service, name=None):
        """
        Adds a service to the gateway

        @param service: The service to add to the gateway
        @type service: callable or a class instance
        @param name: The name of the service
        @type name: str
        """
        if name is None:
            # TODO: include the module in the name
            name = service.__class__.__name__

        if name in self.services.keys():
            raise RemotingError("Service %s already exists" % name)

        self.services[name] = service

    def removeService(self, service):
        """
        Removes a service from the gateway
        """
        self.services.popitem(service)

    def getTarget(self, target):
        """
        Returns a callable based on the target
        
        @param target: The target to retrieve
        @type target: str
        @rettype callable
        """
        try:
            obj = self.services[target]
            meth = None
        except KeyError:
            try:
                name, meth = target.rsplit('.', 1)
                obj = self.services[name]
            except KeyError:
                raise RemotingError("Unknown target %s" % target)

        if not callable(obj):
            raise TypeError("Not callable")

        return obj

    def get_error_response(self, (cls, e, tb)):
        details = traceback.format_exception(cls, e, tb)

        return dict(
            code='SERVER.PROCESSING',
            level='Error',
            description='%s: %s' % (cls.__name__, e),
            type=cls.__name__,
            details=''.join(details),
        )

    def getProcessor(self, request):
        if 'DescribeService' in request.headers:
            return NotImplementedError

        return self.processRequest

    def processRequest(self, request):
        """
        Processes a request

        @param request: The request to be processed
        @type request: L{Message}
        @return The response to the request
        @rettype L{Message}
        """
        func = self.getTarget(request.target)
        response = Message(None, None, None, None)

        try:
            response.body = func(*request.body)
            response.status = STATUS_OK
        except (SystemExit, KeyboardInterrupt):
            raise
        except:
            response.body = self.get_error_response(sys.exc_info())
            response.status = STATUS_ERROR

        return response

def _read_header(stream, decoder):
    """
    Read AMF message header.

    I return a tuple containing:
     - The name of the header.
     - A boolean determining if understanding this header is required.
     - value of the header.
     
    @type   stream: L{BufferedByteStream}
    @param  stream: AMF data
    @type   decoder: L{pyamf.amf0.Decoder} or L{pyamf.amf3.Decoder}
    @param  decoder: AMF decoder instance      
    """
    name_len = stream.read_ushort()
    name = stream.read_utf8_string(name_len)

    required = bool(stream.read_uchar())

    data_len = stream.read_ulong()
    pos = stream.tell()

    data = decoder.readElement()

    if pos + data_len != stream.tell():
        raise pyamf.DecodeError(
            "Data read from stream does not match header length")

    return (name, required, data)

def _write_header(name, header, required, stream, encoder):
    """
    Write AMF message header.

    @type   name: string
    @param  name: Name of header
    @type   header: 
    @param  header: Raw header data
    @type   required: L{bool}
    @param  required: Required header
    @type   stream: L{BufferedByteStream}
    @param  stream: AMF data
    @type   encoder: L{pyamf.amf0.Encoder} or L{pyamf.amf3.Encoder}
    @param  encoder: AMF encoder instance
    """
    stream.write_ushort(len(name))
    stream.write_utf8_string(name)

    stream.write_uchar(required)
    write_pos = stream.tell()

    stream.write_ulong(0)
    old_pos = stream.tell()
    encoder.writeElement(header)
    new_pos = stream.tell()

    stream.seek(write_pos)
    stream.write_ulong(new_pos - old_pos)
    stream.seek(new_pos)

def _read_body(stream, decoder):
    """
    Read AMF message body.

    I return a tuple containing:
     - The target of the body.
     - The id (as sent by the client) of the body.
     - The data of the body.

    @type   stream: L{BufferedByteStream}
    @param  stream: AMF data
    @type   decoder: L{pyamf.amf0.Decoder} or L{pyamf.amf3.Decoder}
    @param  decoder: AMF decoder instance  
    """
    target_len = stream.read_ushort()
    target = stream.read_utf8_string(target_len)

    response_len = stream.read_ushort()
    response = stream.read_utf8_string(response_len)

    status = STATUS_OK

    for (code, s) in STATUS_CODES.iteritems():
        if response.endswith(s):
            status = code
            response = response[:0 - len(s)]

    data_len = stream.read_ulong()
    pos = stream.tell()
    data = decoder.readElement()

    if not isinstance(data, list):
        raise RemotingError("Expected list type for remoting body")

    # Remove the last object in the decoder context, it is the body of the
    # request and Flash does not appear to index the reference 
    decoder.context.objects.pop()

    if pos + data_len != stream.tell():
        raise pyamf.DecodeError(
            "Data read from stream does not match body length")

    return (target, response, status, data)

def _write_body(name, body, stream, encoder):
    """
    Write AMF message body.

    @type   name: string
    @param  name: Name of body
    @type   body: 
    @param  body: Raw body data
    @type   stream: L{BufferedByteStream}
    @param  stream: AMF data
    @type   encoder: 
    @param  encoder: L{pyamf.amf0.Encoder} or L{pyamf.amf3.Encoder}
    """
    response = "%s%s" % (name, _get_status(body.status))

    stream.write_ushort(len(response))
    stream.write_utf8_string(response)

    response = 'null'
    stream.write_ushort(len(response))
    stream.write_utf8_string(response)

    write_pos = stream.tell()
    stream.write_ulong(0)
    old_pos = stream.tell()
    encoder.writeElement(body.body)
    new_pos = stream.tell()

    stream.seek(write_pos)
    stream.write_ulong(new_pos - old_pos)
    stream.seek(new_pos)

def _get_status(status):
    if status not in STATUS_CODES.keys():
        raise ValueError("Unknown status code")

    return STATUS_CODES[status]

def decode(stream, context=None):
    """
    Decodes the incoming stream and returns a L{Envelope} object.

    @type   stream: L{BufferedByteStream}
    @param  stream: AMF data
    @type   context: L{Context}
    @param  context: Context
    """
    if not isinstance(stream, util.BufferedByteStream):
        stream = util.BufferedByteStream(stream)

    msg = Envelope()

    msg.amfVersion = stream.read_uchar()
    decoder = pyamf._get_decoder(msg.amfVersion)(stream, context=context)
    msg.clientType = stream.read_uchar()

    header_count = stream.read_ushort()

    for i in xrange(header_count):
        name, required, data = _read_header(stream, decoder)
        msg.headers[name] = data

        if required:
            msg.headers.set_required(name)

    body_count = stream.read_short()

    for i in range(body_count):
        target, response, status, data = _read_body(stream, decoder)
        msg[response] = (target, status, data)

    if stream.remaining() > 0:
        raise RuntimeError("Unable to fully consume the buffer")

    msg.context = decoder.context

    return msg

def encode(msg):
    """
    Encodes AMF stream and returns file object.

    @type   msg: 
    @param  msg: Python data
    @type   context: L{Context}
    @param  context: Context
    """
    stream = util.BufferedByteStream()

    context = pyamf.Context()
    context.amf3_objs = msg.context.amf3_objs

    encoder = pyamf._get_encoder(msg.amfVersion)(stream, context=context)

    stream.write_uchar(msg.amfVersion)
    stream.write_uchar(msg.clientType)
    stream.write_short(len(msg.headers))

    for name, header in msg.headers.iteritems():
        _write_header(name, header, msg.headers.is_required(name), stream, encoder)

    stream.write_short(len(msg))

    for name, body in msg.iteritems():
        _write_body(name, body, stream, encoder)

    return stream
