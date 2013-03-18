# -*- coding: utf-8 -*-
from __future__ import with_statement
import os
import webob
import webtest
import webtest_selenium
from webob import exc

try:
    # py < 2.7
    import unittest2 as unittest
except ImportError:
    import unittest

try:
    unicode()
except NameError:
    b = bytes

    def u(value):
        if isinstance(value, bytes):
            return value.decode('utf-8')
        return value
else:
    def b(value):
        return str(value)

    def u(value):
        if isinstance(value, unicode):
            return value
        return unicode(value, 'utf-8')

files = os.path.dirname(__file__)


def application(environ, start_response):
    req = webob.Request(environ)
    resp = webob.Response()
    if req.method == 'GET':
        filename = req.path_info.strip('/') or 'index.html'
        if filename in ('302',):
            redirect = req.params['redirect']
            resp = exc.HTTPFound(location=redirect)
            return resp(environ, start_response)
        if filename.isdigit():
            resp.status = filename
            filename = 'index.html'
        filename = os.path.join(files, 'html', filename)
        if os.path.isfile(filename):
            kw = dict(message=req.params.get('message', ''),
                      redirect=req.params.get('redirect', ''))
            resp.unicode_body = u(open(filename).read()) % kw
            _, ext = os.path.splitext(filename)
            if ext == '.html':
                resp.content_type = 'text/html'
            elif ext == '.js':
                resp.content_type = 'text/javascript'
            elif ext == '.json':
                resp.content_type = 'application/json'
    else:
        redirect = req.params.get('redirect', '')
        if redirect:
            resp = exc.HTTPFound(location=redirect)
        else:
            resp.body = req.body
    return resp(environ, start_response)


class TestApp(unittest.TestCase):

    def setUp(self):
        self.app = webtest.TestApp(application)

    def test_webtest(self):
        resp = self.app.get('/',
                            {'redirect': '/message.html?message=submited'})
        resp.mustcontain('It Works!')
        form = resp.forms['myform']
        form.lint()

        self.assertEqual(form['mytext'].value, '')
        resp.mustcontain(no='Form submited')

        with webtest_selenium.selenium(resp) as sresp:
            if sresp:
                sform = sresp.forms['myform']
                sform['mytext'] = 'foo'
                sresp = sform.submit(name='go', timeout=0)
                sresp.mustcontain('Form submited')

        if resp.updated:
            resp.mustcontain('Form submited')
            form = resp.forms['myform']
            self.assertEqual(form['mytext'].value, 'foo')

        resp = form.submit(name='go')
        resp = resp.follow()
        resp.mustcontain('<pre>submited</pre>')

    @webtest_selenium.selenium
    def test_selenium(self):
        resp = self.app.get('/',
                            {'redirect': '/message.html?message=submited'})
        resp.mustcontain('It Works!')
        form = resp.forms['myform']
        form.lint()

        form['mytext'] = 'foo'
        self.assertEqual(form['mytext'].value, 'foo')

        # file upload are only supported with *firefox *chrome drivers
        filename = os.path.join(files, 'html', 'index.html')
        file = form['myfile']
        file.value = (filename,)

        form['myradio'] = 'true'
        self.assertEqual(form['myradio'].value, 'true')
        check = form.get('mycheckbox', index=0)
        check.value = 'true'
        self.assertEqual(check.value, 'true')
        form['myselect'] = 'value2'
        form['myselect'] = 'value2'
        self.assertEqual(form['myselect'].value, 'value2')
        form['mymultiselect'] = ['value1', 'value3']
        self.assertEqual(form['mymultiselect'].value, ['value1', 'value3'])

        # there is an ajax hook on the page
        resp = form.submit(name='go', timeout=0)
        resp.mustcontain('Form submited')

        # but we can submit the form to get the non-javascript behavior
        resp = form.submit()
        resp = resp.follow()
        resp.mustcontain('<pre>submited</pre>')


class TestStatus(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = webtest_selenium.SeleniumApp(application)

    def test_302(self):
        resp = self.app.get('/302', dict(redirect='/500'))
        self.assertRaises(webtest.AppError, resp.follow)
        resp.follow(status=500)

        resp = self.app.get('/302', dict(redirect='/404.html'))
        self.assertRaises(webtest.AppError, resp.follow)

    def test_404(self):
        self.assertRaises(webtest.AppError, self.app.get, '/404')
        self.app.get('/404', status=404)
        self.assertRaises(webtest.AppError, self.app.get, '/404.html')

    def test_500(self):
        self.assertRaises(webtest.AppError, self.app.get, '/500')
        self.app.get('/500', status=500)

    @classmethod
    def tearDownClass(cls):
        cls.app.close()

TestStatus = webtest_selenium.selenium(TestStatus)


class TestJQueryUI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = webtest_selenium.SeleniumApp(url='http://jqueryui.com/')

    def setUp(self):
        self.resp = self.app.get('http://jqueryui.com/demos/')

    def test_datepicker(self):
        resp = self.resp.click('Datepicker')
        field = resp.doc.datepicker
        field.fireEvent('focus')
        resp.doc.link('16').wait_and_click()
        self.assertIn('/16/', field.value)

    def test_dropable(self):
        resp = self.resp.click('Droppable')
        draggable = resp.doc.draggable
        droppable = resp.doc.droppable
        self.assertFalse(droppable.hasClass('ui-state-highlight'))
        draggable.drag_and_drop(droppable)
        self.assertTrue(droppable.hasClass('ui-state-highlight'))

        resp.doc.link('Shopping Cart Demo').click()
        cart = resp.doc.css('#cart ol.ui-droppable')
        cart.wait()
        item = resp.doc.xpath('//li[.="Lolcat Shirt"]')
        self.assertNotIn(item, cart)
        item.drag_and_drop(cart)
        self.assertIn(item, cart)

    @classmethod
    def tearDownClass(cls):
        cls.app.close()

TestJQueryUI = webtest_selenium.selenium(TestJQueryUI)
