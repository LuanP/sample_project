import json
import requests
import urllib

from bson.json_util import dumps
from bottle import Bottle, response, request
from bottle.ext.mongo import MongoPlugin


app = Bottle()
plugin = MongoPlugin(uri="mongodb://127.0.0.1", db="mdb", json_mongo=True)
app.install(plugin)

BASE_URL = 'http://www.omdbapi.com/?'
TYPE_OPTIONS = ('movie', 'series', 'episode')


@app.get('/search/', method='GET')
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
        response.status = 400
        return json.dumps({
            'message': u'"query" was not provided'
        })

    if type_ and type_ not in TYPE_OPTIONS:
        response.status = 400
        return json.dumps({
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

        resp = json.loads(requests.get(u'{}{}'.format(BASE_URL, params)).text)

        if resp.get('Response', True) is False:
            return json.dumps({
                'status': u'no_results',
                'message': u'no results found',
            })

        result = resp['Search']
        params_dict['result'] = result
        mongodb['queries'].insert_one(params_dict)

        resp_text = json.dumps(result)
    return resp_text


@app.get('/detail/<mdbid>/', method='GET')
def index(mongodb, imdbid):
    """
    searches for movies, series and episodes by `imdb id`.

    There's also an optional parameter called `type` which filter the results
    by the given value.

    results are stored in a 'data' collection in mongodb for future use
    """
    movie = mongodb['data'].find_one({'imdbID': imdbid})

    if movie:
        movie.pop('_id')
        resp_text = json.dumps(movie)
    else:
        params = urllib.urlencode({'i': imdbid})
        resp_text = requests.get(u'{}{}'.format(BASE_URL, params)).text
        resp = json.loads(resp_text)
        # save response if ok
        if resp['Response'] == 'True':
            mongodb['data'].insert_one(resp)

    response.content_type = 'application/json'
    return resp_text


@app.get('/favorites/')
def list_favorites(mongodb):
    """
    retrieve all the favorites saved
    """
    favorites = mongodb['favorites'].find()
    return dumps(favorites)


@app.post('/favorites/add/')
def add_favorite(mongodb):
    """
    saves a favorite movie, series or episode in db
    """
    data = dict(request.POST.items())
    mongodb['favorites'].insert_one(data)
    response.status = 201  # CREATED status response
    return data


@app.delete('/favorites/delete/')
def delete_favorite(mongodb):
    """
    deletes a favorite movie, series or episode in db
    """
    imdbid = request.POST.get('imdbid')
    mongodb['favorites'].delete_one({'imdbID': imdbid})
    return ''


@app.error(404)
def error404(error):
    return u"I'm sorry, there is nothing here"


app.run(host='localhost', port=8080)
