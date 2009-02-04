/* begin license *
 *
 *     Meresco Components are components to build searchengines, repositories
 *     and archives, based on Meresco Core.
 *     Copyright (C) 2007-2008 Seek You Too (CQ2) http://www.cq2.nl
 *     Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
 *     Copyright (C) 2007-2008 Stichting Kennisnet Ict op school.
 *        http://www.kennisnetictopschool.nl
 *
 *     This file is part of Meresco Components.
 *
 *     Meresco Components is free software; you can redistribute it and/or modify
 *     it under the terms of the GNU General Public License as published by
 *     the Free Software Foundation; either version 2 of the License, or
 *     (at your option) any later version.
 *
 *     Meresco Components is distributed in the hope that it will be useful,
 *     but WITHOUT ANY WARRANTY; without even the implied warranty of
 *     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *     GNU General Public License for more details.
 *
 *     You should have received a copy of the GNU General Public License
 *     along with Meresco Components; if not, write to the Free Software
 *     Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 *
 * end license */
#include "pyjava.h"
#include "docsetlist.h"
#include "integerlist.h"

extern "C" {
    #include "zipper.h"
}

#include <math.h>
#include <vector>
#include <algorithm>

/**************** C++ implementation of DocSetList****************************/

DocSetList::DocSetList() {
    termIndex2 = TrieNode_create(fwValueNone);
}

DocSetList::~DocSetList() {
    for ( unsigned int i = 0; i < size(); i++) {
       DocSet_delete(at(i));
    }
    TrieNode_free(termIndex2);
}

void DocSetList::addDocSet(fwPtr docset) {
    push_back(docset);
    if ( pDS(docset)->_term != fwStringNone )
        TrieNode_addValue(termIndex2, docset.ptr, pDS(docset)->_term, fwString_get);
}

void DocSetList::removeDoc(guint32 doc) {
    for (unsigned int i = 0; i < size(); i++ ) {
        DocSet* docset = pDS(at(i));
        docset->remove(doc);
    }
}

fwPtr DocSetList::forTerm(char* term) {
    guint32 docsetptr = TrieNode_getValue(termIndex2, term, fwString_get);
    if ( docsetptr == fwValueNone )
        return fwNONE;
    fwPtr docset = {0, docsetptr};
    return docset;
}


bool cmpCardinalityResults(const cardinality_t& lhs, const cardinality_t& rhs) {
    return lhs.cardinality > rhs.cardinality;
}


CardinalityList*
DocSetList::combinedCardinalities(DocSet* docset, guint32 maxResults, int doSort) {
    CardinalityList* results = new CardinalityList();
    results->reserve(size()+1);
    unsigned int minCardinality = 0;
    if ( doSort ) {
        for ( DocSetList::iterator it = begin(); it < end(); it++ ) {
            if ( pDS(*it)->size() < minCardinality ) {
                break;
            }
            guint32 cardinality = pDS(*it)->combinedCardinality(docset);
            if ( cardinality ) {
                cardinality_t t = { pDS(*it)->term(), cardinality };
                results->push_back(t);
                if ( results->size() > maxResults ) {
                    sort(results->begin(), results->end(), cmpCardinalityResults);
                    results->pop_back();
                    minCardinality = results->back().cardinality;
                }
            }
        }
        if ( results->size() <= maxResults ) {
            sort(results->begin(), results->end(), cmpCardinalityResults);
        }
    } else {
        for( unsigned int i=0; i < size() && results->size() < maxResults; i++ ) {
            guint32 cardinality = pDS(at(i))->combinedCardinality(docset);
            if ( cardinality ) {
                cardinality_t t = { pDS(at(i))->term(), cardinality };
                results->push_back(t);
            }
        }
    }
    return results;
}
bool cmpCardinality(fwPtr lhs, fwPtr rhs) {
    return pDS(lhs)->size() > pDS(rhs)->size();
}

class DummyDocSet : public DocSet {
    public:
        DummyDocSet(size_t size) : DocSet(size) { }
};

CardinalityList*
DocSetList::jaccards(DocSet* docset, int minimum, int maximum, int totaldocs, int algorithm) {
    CardinalityList* results = new CardinalityList();
    DocSetList::iterator lower = begin();
    DocSetList::iterator upper = end();
    if ( minimum > 0 ) {
        fwPtr dummyMax = DocSet_create(100*docset->size()/minimum);
        lower = lower_bound(lower, upper, dummyMax, cmpCardinality);
        DocSet_delete(dummyMax);
        fwPtr dummyMin = DocSet_create(docset->size()*minimum/100);
        upper = upper_bound(lower, upper, dummyMin, cmpCardinality);
        DocSet_delete(dummyMin);
    }

    while ( lower < upper ) {
        DocSet* candidate = pDS(*lower++);
        int c = candidate->combinedCardinality(docset);
        int j = 0;
        if ( c > 0 ) {
            j = 100 * c / (candidate->size() + docset->size() - c);
        }

        if ( j >= minimum && j <= maximum ) {
            if (algorithm == JACCARD_MI) {
                // Mutual Information (aka Information Gain)
                double N = totaldocs;

                double N11 = c;
                double N10 = docset->size() - c;
                double N01 = candidate->size() -c;

                // N = N00 + N01 + N10 + N11
                double N00 = N - (docset->size() + candidate->size() - c);
                assert(N00 == N - N01 - N10 - N11);
                assert(N == N00 + N10 + N01 + N11);
                double N1_ = N10 + N11;   // ==> docset->size()
                double N_1 = N01 + N11;   // ==> candidate->size()
                double N0_ = N01 + N00;
                double N_0 = N10 + N00;
                double MI = (N11/N)*log((N*N11)/(N1_*N_1)) +
                            (N01/N)*log((N*N01)/(N0_*N_1)) +
                            (N10/N)*log((N*N10)/(N1_*N_0)) +
                            (N00/N)*log((N*N00)/(N0_*N_0));
                if ( MI < 0.5 ) {
                    int n = int(MI * 10000.0);
                    cardinality_t t = { candidate->term(), n};
                    results->push_back(t);
                }
            } else if (algorithm == JACCARD_X2) {
                // X^2
/*                double X2 = ((N11+N10+N01+N00)*pow(N11*N00-N10*N01,2.0)) /
                            ((N11+N01)*(N11+N10)*(N10+N00)*(N01+N00));*/
            } else {
                cardinality_t t = { candidate->term(), j};
                results->push_back(t);
            }
        }
    }
    sort(results->begin(), results->end(), cmpCardinalityResults);
    return results;
}

/////////////// C Interface to CardinalityList ////////////////

cardinality_t* CardinalityList_at(CardinalityList* vector, int i) {
    return &vector->at(i);
}
int CardinalityList_size(CardinalityList* vector) {
    return vector->size();
}
void CardinalityList_free(CardinalityList* vector) {
    delete vector;
}

/////////////// C Interface to DocSetList ////////////////

DocSetList* DocSetList_create() {
    return new DocSetList();
}

void DocSetList_add(DocSetList* list, fwPtr docset) {
    list->addDocSet(docset);
}

void DocSetList_removeDoc(DocSetList* list, guint32 doc) {
    list->removeDoc(doc);
}

int DocSetList_size(DocSetList* list) {
    return list->size();
}

fwPtr DocSetList_get(DocSetList* list, int i) {
    try {
        return list->at(i);
    } catch (std::exception&) {
        return fwNONE;
    }
}

fwPtr DocSetList_getForTerm(DocSetList* list, char* term) {
    return list->forTerm(term);
}

CardinalityList* DocSetList_combinedCardinalities(DocSetList* list, fwPtr ds, guint32 maxResults, int doSort) {
    DocSet* docset = pDS(ds);
    return list->combinedCardinalities(docset, maxResults, doSort);
}

CardinalityList* DocSetList_jaccards(DocSetList* list, fwPtr ds, int minimum, int maximum, int totaldocs, int algorithm) {
    DocSet* docset = pDS(ds);
    return list->jaccards(docset, minimum, maximum, totaldocs, algorithm);
}

void DocSetList_delete(DocSetList* list) {
    delete list;
}

DocSetList* DocSetList_fromTermEnum(PyJObject* termEnum, PyJObject* termDocs, IntegerList *mapping) {
    TermDocs_seek seek = (TermDocs_seek) lookupIface(termDocs->jobject, &ITermDocs, 2);
    // Call methods on TermEnum via vtable lookup.  TermEnum is not an interface, but
    // multiple subclasses exists (Segment..., Multi...) and might be passed. The methods
    // are on offsets 7, 8 and 9. Start counting at Object::finalize() and add 2.
    TermEnum_next next       = (TermEnum_next)    lookupMethod(termEnum->jobject, 7);
    TermEnum_term getTerm    = (TermEnum_term)    lookupMethod(termEnum->jobject, 8);
    TermEnum_docFreq docFreq = (TermEnum_docFreq) lookupMethod(termEnum->jobject, 9);
    DocSetList* list = DocSetList_create();
    JString* field = NULL;
    JString* previousField = NULL;
    do {
        JObject* term = getTerm(termEnum->jobject);
        if ( !term )
            break;
        previousField = field;
        field = Term_field(term);
        if ( previousField && previousField != field ) {
            break;
        }
        seek(termDocs->jobject, termEnum->jobject);
        JString* text = Term_text(term);
        jint freq = docFreq(termEnum->jobject);

        fwPtr ds = DocSet::fromTermDocs(termDocs->jobject, freq, text, mapping);
        list->addDocSet(ds);
    } while ( next(termEnum->jobject) );

    return list;
}

void DocSetList_sortOnCardinality(DocSetList* docsetlist) {
    sort(docsetlist->begin(), docsetlist->end(), cmpCardinality);
}

bool cmpTerm(fwPtr lhs, fwPtr rhs) {
    DocSet* plhs = pDS(lhs);
    DocSet* prhs = pDS(rhs);
    return strcmp(plhs->term(), prhs->term()) < 0;
}

void DocSetList_sortOnTerm(DocSetList* list) {
    sort(list->begin(), list->end(), cmpTerm);
}

void DocSetList_printMemory(DocSetList* list) {
    nodecount();
}

