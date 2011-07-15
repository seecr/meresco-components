
from weightless.core import compose

def asyncreturn(func, *args, **kwargs):
    try:
        g = compose(func(*args, **kwargs))
        while True:
            g.next()
    except StopIteration, e:
        return e.args[0]
    raise Exception("no async return function")

