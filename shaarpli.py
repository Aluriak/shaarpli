"""Entry point of the app.

"""

from shaarpli import core


def application(env, start_response):
    """Called by server on user question"""
    start_response('200 OK', [('Content-Type','text/html')])
    return core.page_for(env).encode()
