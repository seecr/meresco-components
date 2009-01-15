class FunctionCommand(object):
    def __init__(self, method, **kwargs):
        self._method = method
        self._kwargs = kwargs

    def execute(self):
        return self._method(**self._kwargs)
