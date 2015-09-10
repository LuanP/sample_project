# -*- coding: utf-8 -*-

import os

from bottle import Bottle, jinja2_view, static_file

try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin


app = Bottle()

API_URL = 'http://localhost:8080/'
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_ROOT = os.path.join(PROJECT_DIR, 'static')


@app.route('/')
@jinja2_view('index.html', template_lookup=['templates'])
def index():
    return {
        'search_url': urljoin(API_URL, '/search/'),
        'detail_url': urljoin(API_URL, '/detail/0/'),
        'favorites_list_url': urljoin(API_URL, '/favorites/'),
        'favorites_add_url': urljoin(API_URL, '/favorites/add/'),
        'favorites_delete_url': urljoin(API_URL, '/favorites/delete/'),
    }


@app.route('/static/<filename:path>')
def send_static(filename):
    return static_file(filename, root=STATIC_ROOT)


app.run(host='localhost', port=8081, debug=True)
