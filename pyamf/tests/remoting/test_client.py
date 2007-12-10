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
@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.1.0
"""

import unittest

import pyamf
from pyamf import remoting
from pyamf.remoting import client

class ServiceMethodProxyTestCase(unittest.TestCase):
    def test_create(self):
        x = client.ServiceMethodProxy('a', 'b')

        self.assertEquals(x.service, 'a')
        self.assertEquals(x.name, 'b')

    def test_call(self):
        tc = self

        class TestService(object):
            def __init__(self, s, args):
                self.service = s
                self.args = args

            def _call(self, service, *args):
                tc.assertTrue(self.service, service)
                tc.assertTrue(self.args, args)

        x = client.ServiceMethodProxy(None, None)
        ts = TestService(x, [1,2,3])
        x.service = ts

        x(1,2,3)

    def test_str(self):
        x = client.ServiceMethodProxy('foo', 'bar')
        self.assertEquals(str(x), 'foo.bar')

        x = client.ServiceMethodProxy('foo', None)
        self.assertEquals(str(x), 'foo')

class ServiceProxyTestCase(unittest.TestCase):
    def test_create(self):
        x = client.ServiceProxy('foo', 'bar')

        self.assertEquals(x._gw, 'foo')
        self.assertEquals(x._name, 'bar')
        self.assertEquals(x._auto_execute, True)

        x = client.ServiceProxy('hello', 'world', True)

        self.assertEquals(x._gw, 'hello')
        self.assertEquals(x._name, 'world')
        self.assertEquals(x._auto_execute, True)

        x = client.ServiceProxy(ord, chr, False)

        self.assertEquals(x._gw, ord)
        self.assertEquals(x._name, chr)
        self.assertEquals(x._auto_execute, False)

    def test_getattr(self):
        x = client.ServiceProxy(None, None)
        y = x.foo

        self.assertTrue(isinstance(y, client.ServiceMethodProxy))
        self.assertEquals(y.name, 'foo')

    def test_call(self):
        class DummyGateway(object):
            def __init__(self, tc):
                self.tc = tc

            def addRequest(self, method_proxy, args):
                self.tc.assertEquals(method_proxy, self.method_proxy)
                self.tc.assertEquals(args, self.args)

                self.request = pyamf.Bag({'method_proxy': method_proxy,
                    'args': args})
                return self.request

            def execute_single(self, request):
                self.tc.assertEquals(request, self.request)

                return pyamf.Bag({'body': None})

        gw = DummyGateway(self)
        x = client.ServiceProxy(gw, 'test')
        y = x.foo

        gw.method_proxy = y
        gw.args = ()

        y()
        gw.args = (1, 2, 3)

        y(1, 2, 3)

    def test_service_call(self):
        class DummyGateway(object):
            def __init__(self, tc):
                self.tc = tc

            def addRequest(self, method_proxy, args):
                self.tc.assertEquals(method_proxy.service, self.x)
                self.tc.assertEquals(method_proxy.name, None)

                return pyamf.Bag({'method_proxy': method_proxy, 'args': args})

            def execute_single(self, request):
                return pyamf.Bag({'body': None})

        gw = DummyGateway(self)
        x = client.ServiceProxy(gw, 'test')
        gw.x = x

        x()

    def test_pending_call(self):
        class DummyGateway(object):
            def __init__(self, tc):
                self.tc = tc

            def addRequest(self, method_proxy, args):
                self.tc.assertEquals(method_proxy, self.method_proxy)
                self.tc.assertEquals(args, self.args)

                self.request = pyamf.Bag({'method_proxy': method_proxy,
                    'args': args})

                return self.request

        gw = DummyGateway(self)
        x = client.ServiceProxy(gw, 'test', False)
        y = x.bar

        gw.method_proxy = y
        gw.args = ()

        res = y()

        self.assertEquals(id(gw.request), id(res))

    def test_str(self):
        x = client.ServiceProxy(None, 'test')

        self.assertEquals(str(x), 'test')

class RequestWrapperTestCase(unittest.TestCase):
    def test_create(self):
        x = client.RequestWrapper(1, 2, 3, 4)

        self.assertEquals(x.gw, 1)
        self.assertEquals(x.id, 2)
        self.assertEquals(x.service, 3)
        self.assertEquals(x.args, 4)

    def test_str(self):
        x = client.RequestWrapper(None, '/1', None, None)

        self.assertEquals(str(x), '/1')

    def test_null_response(self):
        x = client.RequestWrapper(None, None, None, None)

        self.assertRaises(AttributeError, getattr, x, 'result')

    def test_set_response(self):
        x = client.RequestWrapper(None, None, None, None)

        y = pyamf.Bag({'body': 'foo.bar'})

        x.setResponse(y)

        self.assertEquals(x.response, y)
        self.assertEquals(x.result, 'foo.bar')

class DummyResponse(object):
    tc = None

    def __init__(self, status, body, headers=()):
        self.status = status
        self.body = body
        self.headers = headers

    def getheader(self, header):
        if header in self.headers:
            return self.headers[header]

        return None

    def read(self, x=None):
        if x is None:
            return self.body

        return self.body[:x]

class DummyConnection(object):
    tc = None
    expected_value = None
    expected_url = None
    response = None

    def request(self, method, url, value):
        self.tc.assertEquals(method, 'POST')
        self.tc.assertEquals(url, self.expected_url)
        self.tc.assertEquals(value, self.expected_value)

    def getresponse(self):
        return self.response

class RemotingServiceTestCase(unittest.TestCase):
    def test_create(self):
        self.assertRaises(TypeError, client.RemotingService)
        x = client.RemotingService('http://example.org')

        self.assertEquals(x.url, ('http', 'example.org', '', '', '', ''))

        # amf version
        x = client.RemotingService('http://example.org', pyamf.AMF3)
        self.assertEquals(x.amf_version, pyamf.AMF3)

        # client type
        x = client.RemotingService('http://example.org', pyamf.AMF3,
            pyamf.ClientTypes.FlashCom)

        self.assertEquals(x.client_type, pyamf.ClientTypes.FlashCom)

    def test_schemes(self):
        x = client.RemotingService('http://example.org')
        self.assertEquals(x.connection.port, 80)

        x = client.RemotingService('https://example.org')
        self.assertEquals(x.connection.port, 443)

        self.assertRaises(ValueError, client.RemotingService,
            'ftp://example.org')

    def test_get_service(self):
        x = client.RemotingService('http://example.org')

        y = x.getService('foo')

        self.assertTrue(isinstance(y, client.ServiceProxy))
        self.assertEquals(y._name, 'foo')
        self.assertEquals(y._gw, x)

        self.assertRaises(TypeError, x.getService, 1)

    def test_add_request(self):
        gw = client.RemotingService('http://foobar.net')
        
        self.assertEquals(gw.request_number, 1)
        self.assertEquals(gw.requests, [])
        service = gw.getService('baz')
        wrapper = gw.addRequest(service, 1, 2, 3)

        self.assertEquals(gw.requests, [wrapper])
        self.assertEquals(wrapper.gw, gw)
        self.assertEquals(gw.request_number, 2)
        self.assertEquals(wrapper.id, '/1')
        self.assertEquals(wrapper.service, service)
        self.assertEquals(wrapper.args, (1, 2, 3))

        # add 1 arg
        wrapper2 = gw.addRequest(service, None)

        self.assertEquals(gw.requests, [wrapper, wrapper2])
        self.assertEquals(wrapper2.gw, gw)
        self.assertEquals(gw.request_number, 3)
        self.assertEquals(wrapper2.id, '/2')
        self.assertEquals(wrapper2.service, service)
        self.assertEquals(wrapper2.args, (None,))

    def test_remove_request(self):
        gw = client.RemotingService('http://foobar.net')
        self.assertEquals(gw.requests, [])
        
        service = gw.getService('baz')
        wrapper = gw.addRequest(service, (1, 2, 3))
        self.assertEquals(gw.requests, [wrapper])

        gw.removeRequest(wrapper)
        self.assertEquals(gw.requests, [])

        wrapper = gw.addRequest(service, 1, 2, 3)
        self.assertEquals(gw.requests, [wrapper])

        gw.removeRequest(service, 1, 2, 3)
        self.assertEquals(gw.requests, [])

        self.assertRaises(LookupError, gw.removeRequest, service, 1, 2, 3)

    def test_get_request(self):
        gw = client.RemotingService('http://foobar.net')
        
        service = gw.getService('baz')
        wrapper = gw.addRequest(service, 1, 2, 3)

        wrapper2 = gw.getRequest(str(wrapper))
        self.assertEquals(wrapper, wrapper2)

        wrapper2 = gw.getRequest('/1')
        self.assertEquals(wrapper, wrapper2)

        wrapper2 = gw.getRequest(wrapper.id)
        self.assertEquals(wrapper, wrapper2)

    def test_get_amf_request(self):
        gw = client.RemotingService('http://example.org', pyamf.AMF3,
            pyamf.ClientTypes.FlashCom)

        service = gw.getService('baz')
        method_proxy = service.gak
        wrapper = gw.addRequest(method_proxy, 1, 2, 3)

        envelope = gw.getAMFRequest([wrapper])

        self.assertEquals(envelope.amfVersion, pyamf.AMF3)
        self.assertEquals(envelope.clientType, pyamf.ClientTypes.FlashCom)
        self.assertEquals(envelope.keys(), ['/1'])

        request = envelope['/1']
        self.assertEquals(request.target, 'baz.gak')
        self.assertEquals(request.body, (1, 2, 3))
        
        envelope2 = gw.getAMFRequest(gw.requests)

        self.assertEquals(envelope2.amfVersion, pyamf.AMF3)
        self.assertEquals(envelope2.clientType, pyamf.ClientTypes.FlashCom)
        self.assertEquals(envelope2.keys(), ['/1'])

        request = envelope2['/1']
        self.assertEquals(request.target, 'baz.gak')
        self.assertEquals(request.body, (1, 2, 3))

    def test_execute_single(self):
        gw = client.RemotingService('http://example.org/x/y/z')
        dc = DummyConnection()
        gw.connection = dc

        dc.tc = self

        service = gw.getService('baz', auto_execute=False)
        wrapper = service.gak()
        
        response = DummyResponse(200, '\x00\x00\x00\x00\x00\x01\x00\ttest.test'
            '\x00\x02/1\x00\x00\x00\x00\x02\x00\x05hello', {
            'Content-Type': 'application/x-amf', 'Content-Length': 33})
        response.tc = self

        dc.expected_url = '/x/y/z'
        dc.expected_value = '\x00\x00\x00\x00\x00\x01\x00\x07baz.gak\x00' + \
            '\x02/1\x00\x00\x00\x00\n\x00\x00\x00\x01\n\x00\x00\x00\x00'
        dc.response = response

        gw.execute_single(wrapper)
        self.assertEquals(gw.requests, [])
        
        wrapper = service.gak()

        response = DummyResponse(200, '\x00\x00\x00\x00\x00\x01\x00\ttest.test'
            '\x00\x02/2\x00\x00\x00\x00\x02\x00\x05hello', {
            'Content-Type': 'application/x-amf'})
        response.tc = self

        dc.expected_url = '/x/y/z'
        dc.expected_value = '\x00\x00\x00\x00\x00\x01\x00\x07baz.gak\x00' + \
            '\x02/2\x00\x00\x00\x00\n\x00\x00\x00\x01\n\x00\x00\x00\x00'
        dc.response = response

        gw.execute_single(wrapper)

    def test_execute(self):
        gw = client.RemotingService('http://example.org/x/y/z')
        dc = DummyConnection()
        gw.connection = dc

        dc.tc = self

        baz = gw.getService('baz', auto_execute=False)
        foo = gw.getService('foo', auto_execute=False)
        wrapper = baz.gak()
        wrapper2 = foo.bar()

        response = DummyResponse(200, '\x00\x00\x00\x00\x00\x02\x00\ttest.test'
            '\x00\x02/1\x00\x00\x00\x00\x02\x00\x05hello\x00\ttest.test\x00'
            '\x02/2\x00\x00\x00\x00\x02\x00\x05hello', {
            'Content-Type': 'application/x-amf'})
        response.tc = self

        dc.expected_url = '/x/y/z'
        dc.expected_value = '\x00\x00\x00\x00\x00\x02\x00\x07foo.bar\x00' + \
            '\x02/2\x00\x00\x00\x00\n\x00\x00\x00\x01\n\x00\x00\x00\x00' + \
            '\x00\x07baz.gak\x00\x02/1\x00\x00\x00\x00\n\x00\x00\x00\x01\n' + \
            '\x00\x00\x00\x00'
        dc.response = response

        gw.execute()
        self.assertEquals(gw.requests, [])

    def test_get_response(self):
        gw = client.RemotingService('http://example.org/amf-gateway')
        dc = DummyConnection()
        gw.connection = dc

        response = DummyResponse(200, '\x00\x00\x00\x00\x00\x00', {
            'Content-Type': 'application/x-amf'})

        dc.response = response

        gw._getResponse()

        response = DummyResponse(404, '', {})
        dc.response = response

        self.assertRaises(remoting.RemotingError, gw._getResponse)

        # bad content type
        response = DummyResponse(200, '\x00\x00\x00\x00\x00\x00',
            {'Content-Type': 'text/html'})
        dc.response = response

        self.assertRaises(remoting.RemotingError, gw._getResponse)

def suite():
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(ServiceMethodProxyTestCase))
    suite.addTest(unittest.makeSuite(ServiceProxyTestCase))
    suite.addTest(unittest.makeSuite(RequestWrapperTestCase))
    suite.addTest(unittest.makeSuite(RemotingServiceTestCase))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
