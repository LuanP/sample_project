import json
import requests
import urllib

from bottle import Bottle, response, request
from bottle.ext.mongo import MongoPlugin


app = Bottle()
plugin = MongoPlugin(uri="mongodb://127.0.0.1", db="mdb", json_mongo=True)
app.install(plugin)

BASE_URL = 'http://www.omdbapi.com/?'
TYPE_OPTIONS = ('movie', 'series', 'episode')


@app.route('/search/', method='GET')
def search(mongodb):
    """
    searches for movies, series and episodes with a provided `query`.
    There's also an optional parameter called `type` which filter the results
    by the given value.

    type options:
        - movie
        - series
        - episode

    results are stored in a 'queries' collection in mongodb for future use
    """
    response.content_type = 'application/json'

    query = request.query.query
    type_ = request.query.type

    if not query:
        return json.dumps({
            'status': u'error',
            'message': u'"query" not provided'
        })

    if type_ and type_ not in TYPE_OPTIONS:
        return json.dumps({
            'status': u'error',
            'message': u'invalid "type". Options are: movie, series, episode'
        })

    params_dict = {'s': query}
    if type_:
        params_dict['type'] = type_

    result = mongodb['queries'].find_one(params_dict)
    if result:
        resp_text = json.dumps(result['result'])
    else:
        params = urllib.urlencode(params_dict)

        resp_text = requests.get(u'{}{}'.format(BASE_URL, params)).text
        resp = json.loads(resp_text)

        if resp.get('Response', True) is False:
            return json.dumps({
                'status': u'error',
                'message': u'no results found',
            })

        params_dict['result'] = resp['Search']
        mongodb['queries'].insert_one(params_dict)

    return resp_text


@app.route('/movies/<mdbid>', method='GET')
def index(mongodb, mdbid):
    """
    searches for movies, series and episodes by `imdb id`.

    There's also an optional parameter called `type` which filter the results
    by the given value.

    results are stored in a 'data' collection in mongodb for future use
    """
    movie = mongodb['data'].find_one({'imdbID': mdbid})

    if movie:
        movie.pop('_id')
        resp_text = json.dumps(movie)
    else:
        params = urllib.urlencode({'i': mdbid})
        resp_text = requests.get(u'{}{}'.format(BASE_URL, params)).text
        resp = json.loads(resp_text)
        # save response if ok
        if resp['Response'] == 'True':
            mongodb['data'].insert_one(resp)

    response.content_type = 'application/json'
    return resp_text


@app.error(404)
def error404(error):
    return u"I'm sorry, there is nothing here"


app.run(host='localhost', port=8080)
