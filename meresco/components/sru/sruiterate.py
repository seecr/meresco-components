from urllib2 import urlopen
from urllib import urlencode
from urlparse import urlsplit, parse_qs

from meresco.xml.namespaces import xpath, xpathFirst
from lxml.etree import parse, tostring, cleanup_namespaces
from StringIO import StringIO

def _first(collection, element, default=None):
    value = collection.get(element, [])
    return default if len(value) == 0 else value[0]

class SruQuery(object):
    def __init__(self, baseUrl, query, recordSchema, recordPacking="xml", maximumRecords=50, _urlopen=None):
        self._baseUrl = baseUrl
        self._query = query
        self._recordSchema = recordSchema
        self._recordPacking = recordPacking
        self._maximumRecords = maximumRecords
        self._urlopen = _urlopen or urlopen
        if self._query is None:
            raise ValueError("No query specified")
        if self._recordSchema is None:
            raise ValueError("No recordSchema specified")

    @classmethod
    def fromUrl(clazz, url, **kwargs):
        scheme, netloc, path, query, fragment = urlsplit(url)
        arguments = parse_qs(query)
        sruQueryKwargs = dict(
            query=_first(arguments, 'query'),
            recordSchema=_first(arguments, "recordSchema", kwargs.get("recordSchema")))
        recordPacking=_first(arguments, "recordPacking", kwargs.get("recordPacking"))
        if recordPacking:
            sruQueryKwargs['recordPacking'] = recordPacking
        return clazz("{}://{}{}".format(scheme, netloc, path), **sruQueryKwargs)

    def searchRetrieve(self, startRecord=None):
        url = '{}?{}'.format(
            self._baseUrl,
            urlencode(
                dict(operation="searchRetrieve",
                    version=1.2,
                    recordPacking=self._recordPacking,
                    recordSchema=self._recordSchema,
                    query=self._query,
                    startRecord=startRecord or 1,
                    maximumRecords=self._maximumRecords,
                )
            ))
        try:
            return SearchRetrieveResponse(self, parse(self._urlopen(url)))
        except:
            print url
            raise

class SearchRetrieveResponse(object):
    def __init__(self, sruQuery, response):
        self._sruQuery = sruQuery
        self._response = response

    def __iter__(self):
        for record in xpath(self._response, "/srw:searchRetrieveResponse/srw:records/srw:record"):
            yield SruRecord(record)

    def nextResponse(self):
        nextRecordPosition = xpathFirst(self._response, "/srw:searchRetrieveResponse/srw:nextRecordPosition/text()")
        if nextRecordPosition:
            return self._sruQuery.searchRetrieve(startRecord=nextRecordPosition)

class SruRecord(object):
    def __init__(self, data):
        self._data = data

    @property
    def identifier(self):
        return xpathFirst(self._data, "srw:recordIdentifier/text()")

    @property
    def recordSchema(self):
        return xpathFirst(self._data, "srw:recordSchema/text()")

    @property
    def recordPacking(self):
        return xpathFirst(self._data, "srw:recordPacking/text()")

    @property
    def data(self):
        _data = xpathFirst(self._data, "srw:recordData/*")
        if _data is None:
            raise ValueError("srw:recordData is empty")

        _data = parse(StringIO(tostring(_data)))
        cleanup_namespaces(_data)
        if self.recordPacking == "xml":
            return _data
        elif self.recordPacking == "text":
            return tostring(_data, pretty_print=True)
        else:
            raise TypeError("Unknown recordPacking '{}'".format(self.recordPacking))

def iterateSruQuery(*args, **kwargs):
    for record in _iterateSruQuery(SruQuery(*args, **kwargs)):
        yield record

def iterateSruQueryFromUrl(url, **kwargs):
    for record in _iterateSruQuery(SruQuery.fromUrl(url, **kwargs)):
        yield record

def _iterateSruQuery(sruQuery):
    sruResponse = sruQuery.searchRetrieve()
    while sruResponse:
        for record in sruResponse:
            yield record
        sruResponse = sruResponse.nextResponse()

