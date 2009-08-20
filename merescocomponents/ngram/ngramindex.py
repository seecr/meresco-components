# -*- coding: utf-8 -*-

from merescocore.framework import Observable, Transparant, TransactionScope, be, ResourceManager
from merescocore.components.tokenizefieldlet import TokenizeFieldlet
from merescocomponents.facetindex import Fields2LuceneDocumentTx

from ngram import NGramFieldlet

class NGramIndex(Observable):
    def __init__(self, fieldNames):
        Observable.__init__(self)
        outside = Transparant()
        self.addObserver = outside.addObserver
        self.addStrand = outside.addStrand
        self._observers = outside._observers
        self._internalObserverTree = be(
            (TokenizeFieldlet(),
                (TransactionScope('ngram'),
                    (NGramFieldlet(2, 'ngrams', fieldNames=fieldNames),
                        (outside,),
                        (ResourceManager('ngram', lambda resourceManager: Fields2LuceneDocumentTx(resourceManager, untokenized=[])),
                            (outside,)
                        )
                    )
                )
            )
        )

    def addField(self, name, value):
        self._internalObserverTree.do.addField(name=name, value=value)
    