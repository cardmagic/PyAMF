# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
General gateway tests.

@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.1.0
"""

import unittest, sys

import pyamf
from pyamf import remoting
from pyamf.remoting import gateway, amf0

class TestService(object):
    def spam(self):
        return 'spam'

    def echo(self, x):
        return x

class FaultTestCase(unittest.TestCase):
    def test_create(self):
        x = remoting.ErrorFault()

        self.assertEquals(x.code, '')
        self.assertEquals(x.details, '')
        self.assertEquals(x.description, '')

        x = remoting.ErrorFault(code=404, details='Not Found', description='Spam eggs')

        self.assertEquals(x.code, 404)
        self.assertEquals(x.details, 'Not Found')
        self.assertEquals(x.description, 'Spam eggs')

    def test_build(self):
        fault = None

        try:
            raise TypeError, "unknown type"
        except TypeError, e:
            fault = amf0.build_fault(*sys.exc_info())

        self.assertTrue(isinstance(fault, remoting.ErrorFault))
        self.assertEquals(fault.level, 'error')
        self.assertEquals(fault.code, 'TypeError')
        self.assertTrue("\\n" not in fault.details)

    def test_encode(self):
        encoder = pyamf.get_encoder(pyamf.AMF0)
        decoder = pyamf.get_decoder(pyamf.AMF0)
        decoder.stream = encoder.stream

        try:
            raise TypeError, "unknown type"
        except TypeError, e:
            encoder.writeElement(amf0.build_fault(*sys.exc_info()))

        buffer = encoder.stream
        buffer.seek(0, 0)

        fault = decoder.readElement()
        old_fault = amf0.build_fault(*sys.exc_info())

        self.assertEquals(fault.level, old_fault.level)
        self.assertEquals(fault.type, old_fault.type)
        self.assertEquals(fault.code, old_fault.code)
        self.assertEquals(fault.details, old_fault.details)
        self.assertEquals(fault.description, old_fault.description)

    def test_explicit_code(self):
        class X(Exception):
            _amf_code = 'Server.UnknownResource'

        try:
            raise X
        except X, e:
            fault = amf0.build_fault(*sys.exc_info())

        self.assertEquals(fault.code, 'Server.UnknownResource')

class ServiceWrapperTestCase(unittest.TestCase):
    def test_create(self):
        x = gateway.ServiceWrapper('blah')

        self.assertEquals(x.service, 'blah')

    def test_cmp(self):
        x = gateway.ServiceWrapper('blah')
        y = gateway.ServiceWrapper('blah')
        z = gateway.ServiceWrapper('bleh')

        self.assertEquals(x, y)
        self.assertNotEquals(y, z)

    def test_call(self):
        def add(x, y):
            self.assertEquals(x, 1)
            self.assertEquals(y, 2)

            return x + y

        x = gateway.ServiceWrapper(add)

        self.assertTrue(callable(x))
        self.assertEquals(x(None, [1, 2]), 3)

        x = gateway.ServiceWrapper('blah')

        self.assertRaises(gateway.UnknownServiceMethodError, x, None, [])

        x = gateway.ServiceWrapper(TestService)

        self.assertRaises(gateway.UnknownServiceMethodError, x, None, [])
        self.assertEquals(x('spam', []), 'spam')

        self.assertRaises(gateway.UnknownServiceMethodError, x, 'xyx', [])
        self.assertRaises(gateway.InvalidServiceMethodError, x, '_private', [])

        self.assertEquals(x('echo', [x]), x)

class ServiceRequestTestCase(unittest.TestCase):
    def test_create(self):
        sw = gateway.ServiceWrapper(TestService)
        request = remoting.Envelope()

        x = gateway.ServiceRequest(request, sw, None)

        self.assertEquals(x.request, request)
        self.assertEquals(x.service, sw)
        self.assertEquals(x.method, None)

    def test_call(self):
        sw = gateway.ServiceWrapper(TestService)
        request = remoting.Envelope()

        x = gateway.ServiceRequest(request, sw, None)

        self.assertRaises(gateway.UnknownServiceMethodError, x)

        x = gateway.ServiceRequest(request, sw, 'spam')
        self.assertEquals(x(), 'spam')

        x = gateway.ServiceRequest(request, sw, 'echo')
        self.assertEquals(x(x), x)

class ServiceCollectionTestCase(unittest.TestCase):
    def test_contains(self):
        x = gateway.ServiceCollection()

        self.assertFalse(TestService in x)
        self.assertFalse('spam.eggs' in x)

        x['spam.eggs'] = gateway.ServiceWrapper(TestService)

        self.assertTrue(TestService in x)
        self.assertTrue('spam.eggs' in x)

class BaseGatewayTestCase(unittest.TestCase):
    def test_create(self):
        x = gateway.BaseGateway()
        self.assertEquals(x.services, {})

        x = gateway.BaseGateway({})
        self.assertEquals(x.services, {})

        x = gateway.BaseGateway({})
        self.assertEquals(x.services, {})

        x = gateway.BaseGateway({'x': TestService})
        self.assertEquals(x.services, {'x': TestService})

        self.assertRaises(TypeError, gateway.BaseGateway, [])

    def test_add_service(self):
        gw = gateway.BaseGateway()
        self.assertEquals(gw.services, {})

        gw.addService(TestService)
        self.assertTrue(TestService in gw.services)
        self.assertTrue('TestService' in gw.services)

        del gw.services['TestService']

        gw.addService(TestService, 'spam.eggs')
        self.assertTrue(TestService in gw.services)
        self.assertTrue('spam.eggs' in gw.services)

        del gw.services['spam.eggs']

        class SpamService(object):
            def __str__(self):
                return 'spam'

            def __call__(*args, **kwargs):
                pass

        x = SpamService()

        gw.addService(x)
        self.assertTrue(x in gw.services)
        self.assertTrue('spam' in gw.services)

        del gw.services['spam']

        self.assertEquals(gw.services, {})

        self.assertRaises(TypeError, gw.addService, 1)

        import imp

        temp = imp.new_module('temp')
        gw.addService(temp)

        self.assertTrue(temp in gw.services)
        self.assertTrue('temp' in gw.services)

        del gw.services['temp']

        self.assertEquals(gw.services, {})

    def test_remove_service(self):
        gw = gateway.BaseGateway({'test': TestService})
        self.assertTrue('test' in gw.services)
        wrapper = gw.services['test']

        gw.removeService('test')

        self.assertFalse('test' in gw.services)
        self.assertFalse(TestService in gw.services)
        self.assertFalse(wrapper in gw.services)
        self.assertEquals(gw.services, {})

        gw = gateway.BaseGateway({'test': TestService})
        self.assertTrue(TestService in gw.services)
        wrapper = gw.services['test']

        gw.removeService(TestService)

        self.assertFalse('test' in gw.services)
        self.assertFalse(TestService in gw.services)
        self.assertFalse(wrapper in gw.services)
        self.assertEquals(gw.services, {})

        gw = gateway.BaseGateway({'test': TestService})
        self.assertTrue(TestService in gw.services)
        wrapper = gw.services['test']

        gw.removeService(wrapper)

        self.assertFalse('test' in gw.services)
        self.assertFalse(TestService in gw.services)
        self.assertFalse(wrapper in gw.services)
        self.assertEquals(gw.services, {})

        self.assertRaises(NameError, gw.removeService, 'test')
        self.assertRaises(NameError, gw.removeService, TestService)
        self.assertRaises(NameError, gw.removeService, wrapper)

    def test_service_request(self):
        gw = gateway.BaseGateway({'test': TestService})
        envelope = remoting.Envelope()

        message = remoting.Request('spam', [], envelope=envelope)
        self.assertRaises(gateway.UnknownServiceError, gw.getServiceRequest,
            message, 'spam')

        message = remoting.Request('test.spam', [], envelope=envelope)
        sr = gw.getServiceRequest(message, 'test.spam')

        self.assertTrue(isinstance(sr, gateway.ServiceRequest))
        self.assertEquals(sr.request, envelope)
        self.assertEquals(sr.service, TestService)
        self.assertEquals(sr.method, 'spam')

        message = remoting.Request('test')
        sr = gw.getServiceRequest(message, 'test')

        self.assertTrue(isinstance(sr, gateway.ServiceRequest))
        self.assertEquals(sr.request, None)
        self.assertEquals(sr.service, TestService)
        self.assertEquals(sr.method, None)

        gw = gateway.BaseGateway({'test': TestService})
        envelope = remoting.Envelope()
        message = remoting.Request('test')

        sr = gw.getServiceRequest(message, 'test')

        self.assertTrue(isinstance(sr, gateway.ServiceRequest))
        self.assertEquals(sr.request, None)
        self.assertEquals(sr.service, TestService)
        self.assertEquals(sr.method, None)

        # try to access an unknown service
        message = remoting.Request('spam')
        self.assertRaises(gateway.UnknownServiceError, gw.getServiceRequest,
            message, 'spam')

        # check x.x calls
        message = remoting.Request('test.test')
        sr = gw.getServiceRequest(message, 'test.test')

        self.assertTrue(isinstance(sr, gateway.ServiceRequest))
        self.assertEquals(sr.request, None)
        self.assertEquals(sr.service, TestService)
        self.assertEquals(sr.method, 'test')

    def test_long_service_name(self):
        gw = gateway.BaseGateway({'a.c.b.d': TestService})
        envelope = remoting.Envelope()

        message = remoting.Request('a.c.b.d', [], envelope=envelope)
        sr = gw.getServiceRequest(message, 'a.c.b.d.spam')

        self.assertTrue(isinstance(sr, gateway.ServiceRequest))
        self.assertEquals(sr.request, envelope)
        self.assertEquals(sr.service, TestService)
        self.assertEquals(sr.method, 'spam')

    def test_get_response(self):
        gw = gateway.BaseGateway({'test': TestService})
        envelope = remoting.Envelope()

        self.assertRaises(NotImplementedError, gw.getResponse, envelope)

    def test_process_request(self):
        gw = gateway.BaseGateway({'test': TestService})
        envelope = remoting.Envelope()

        request = remoting.Request('test.spam', envelope=envelope)

        processor = gw.getProcessor(request)
        response = processor(request)

        self.assertTrue(isinstance(response, remoting.Response))
        self.assertEquals(response.status, remoting.STATUS_OK)
        self.assertEquals(response.body, 'spam')

        # Test a non existant service call
        request = remoting.Request('nope', envelope=envelope)
        processor = gw.getProcessor(request)
        response = processor(request)

        self.assertTrue(isinstance(response, remoting.Message))
        self.assertEquals(response.status, remoting.STATUS_ERROR)
        self.assertTrue(isinstance(response.body, remoting.ErrorFault))

        self.assertEquals(response.body.code, 'Service.ResourceNotFound')
        self.assertEquals(response.body.description, 'Unknown service nope')

    def test_malformed_credentials_header(self):
        gw = gateway.BaseGateway({'test': TestService})
        envelope = remoting.Envelope()

        request = remoting.Request('test.spam', envelope=envelope)
        request.headers['Credentials'] = {'spam': 'eggs'}

        processor = gw.getProcessor(request)
        response = processor(request)

        self.assertTrue(isinstance(response, remoting.Response))
        self.assertEquals(response.status, remoting.STATUS_ERROR)
        self.assertTrue(isinstance(response.body, remoting.ErrorFault))

        self.assertEquals(response.body.code, 'KeyError')

    def test_authenticate(self):
        gw = gateway.BaseGateway({'test': TestService})
        sr = gateway.ServiceRequest(None, gw.services['test'], None)

        self.assertTrue(gw.authenticateRequest(sr, None, None))

        def auth(u, p):
            if u == 'spam' and p == 'eggs':
                return True

            return False

        gw = gateway.BaseGateway({'test': TestService}, authenticator=auth)

        self.assertFalse(gw.authenticateRequest(sr, None, None))
        self.assertTrue(gw.authenticateRequest(sr, 'spam', 'eggs'))

class QueryBrowserTestCase(unittest.TestCase):
    def test_request(self):
        gw = gateway.BaseGateway()
        echo = lambda x: x

        gw.addService(echo, 'echo', description='This is a test')

        envelope = remoting.Envelope()
        request = remoting.Request('echo')
        envelope['/1'] = request

        request.headers['DescribeService'] = None

        processor = gw.getProcessor(request)
        response = processor(request)

        self.assertEquals(response.status, remoting.STATUS_OK)
        self.assertEquals(response.body, 'This is a test')

class AuthenticatorTestCase(unittest.TestCase):
    def setUp(self):
        self.called = False

    def tearDown(self):
        if self.called is False:
            self.fail("authenticator not called")

    def _auth(self, username, password):
        self.called = True

        if username == 'fred' and password == 'wilma':
            return True

        return False

    def test_gateway(self):
        gw = gateway.BaseGateway(authenticator=self._auth)
        echo = lambda x: x

        gw.addService(echo, 'echo')

        envelope = remoting.Envelope()
        request = remoting.Request('echo', body=['spam'])
        envelope.headers['Credentials'] = dict(userid='fred', password='wilma')
        envelope['/1'] = request

        processor = gw.getProcessor(request)
        response = processor(request)

        self.assertEquals(response.status, remoting.STATUS_OK)
        self.assertEquals(response.body, 'spam')

    def test_service(self):
        gw = gateway.BaseGateway()
        echo = lambda x: x

        gw.addService(echo, 'echo', authenticator=self._auth)

        envelope = remoting.Envelope()
        request = remoting.Request('echo', body=['spam'])
        envelope.headers['Credentials'] = dict(userid='fred', password='wilma')
        envelope['/1'] = request

        processor = gw.getProcessor(request)
        response = processor(request)

        self.assertEquals(response.status, remoting.STATUS_OK)
        self.assertEquals(response.body, 'spam')

    def test_class_decorator(self):
        class TestService:
            def echo(self, x):
                return x

        TestService.echo = gateway.authenticate(TestService.echo, self._auth)

        gw = gateway.BaseGateway({'test': TestService})

        envelope = remoting.Envelope()
        request = remoting.Request('test.echo', body=['spam'])
        envelope.headers['Credentials'] = dict(userid='fred', password='wilma')
        envelope['/1'] = request

        processor = gw.getProcessor(request)
        response = processor(request)

        self.assertEquals(response.status, remoting.STATUS_OK)
        self.assertEquals(response.body, 'spam')

    def test_func_decorator(self):
        def echo(x):
            return x

        echo = gateway.authenticate(echo, self._auth)

        gw = gateway.BaseGateway({'echo': echo})

        envelope = remoting.Envelope()
        request = remoting.Request('echo', body=['spam'])
        envelope.headers['Credentials'] = dict(userid='fred', password='wilma')
        envelope['/1'] = request

        processor = gw.getProcessor(request)
        response = processor(request)

        self.assertEquals(response.status, remoting.STATUS_OK)
        self.assertEquals(response.body, 'spam')

class ExposeRequestTestCase(unittest.TestCase):
    def test_default(self):
        gw = gateway.BaseGateway()

        gw.addService(lambda x: x, 'test')

        envelope = remoting.Envelope()
        request = remoting.Request('test')
        envelope['/1'] = request

        service_request = gateway.ServiceRequest(envelope, gw.services['test'], None)

        self.assertFalse(gw.mustExposeRequest(service_request))

    def test_gateway(self):
        gw = gateway.BaseGateway(expose_request=True)

        gw.addService(lambda x: x, 'test')

        envelope = remoting.Envelope()
        request = remoting.Request('test')
        envelope['/1'] = request

        service_request = gateway.ServiceRequest(envelope, gw.services['test'], None)

        self.assertTrue(gw.mustExposeRequest(service_request))

    def test_service(self):
        gw = gateway.BaseGateway()

        gw.addService(lambda x: x, 'test', expose_request=True)

        envelope = remoting.Envelope()
        request = remoting.Request('test')
        envelope['/1'] = request

        service_request = gateway.ServiceRequest(envelope, gw.services['test'], None)

        self.assertTrue(gw.mustExposeRequest(service_request))

    def test_decorator(self):
        def echo(x):
            return x

        gateway.expose_request(echo)

        gw = gateway.BaseGateway()

        gw.addService(echo, 'test')

        envelope = remoting.Envelope()
        request = remoting.Request('test')
        envelope['/1'] = request

        service_request = gateway.ServiceRequest(envelope, gw.services['test'], None)

        self.assertTrue(gw.mustExposeRequest(service_request))

def suite():
    suite = unittest.TestSuite()

    # basics first
    suite.addTest(unittest.makeSuite(FaultTestCase))
    suite.addTest(unittest.makeSuite(ServiceWrapperTestCase))
    suite.addTest(unittest.makeSuite(ServiceRequestTestCase))
    suite.addTest(unittest.makeSuite(ServiceCollectionTestCase))
    suite.addTest(unittest.makeSuite(BaseGatewayTestCase))
    suite.addTest(unittest.makeSuite(QueryBrowserTestCase))
    suite.addTest(unittest.makeSuite(AuthenticatorTestCase))
    suite.addTest(unittest.makeSuite(ExposeRequestTestCase))

    try:
        import wsgiref
    except ImportError:
        wsgiref = None

    if wsgiref:
        from pyamf.tests.gateway import test_wsgi

        suite.addTest(test_wsgi.suite())

    try:
        import twisted
    except ImportError:
        twisted = None

    if twisted:
        from pyamf.tests.gateway import test_twisted

        suite.addTest(test_twisted.suite())

    try:
        import django
    except ImportError:
        django = None

    if django:
        import os, sys

        if 'DJANGO_SETTINGS_MODULE' not in os.environ:
            import imp, sys

            mod = imp.new_module('pyamf.test_django')
            os.environ['DJANGO_SETTINGS_MODULE'] = 'pyamf.test_django'
            sys.modules['pyamf.test_django'] = mod

            setattr(mod, 'DATABASE_ENGINE', 'sqlite3')
            setattr(mod, 'DATABASE_NAME', ':memory:')

        from pyamf.tests.gateway import test_django

        suite.addTest(test_django.suite())

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
