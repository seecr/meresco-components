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
    for ( unsigned int i = 0; i < size(); i++)
       delete at(i);
    TrieNode_free(termIndex2);
}

void DocSetList::addDocSet(DocSet* docset) {
    push_back(docset);
    if ( docset->_term != fwStringNone )
        TrieNode_addValue(termIndex2, size()-1, docset->_term);
}

void DocSetList::removeDoc(guint32 doc) {
    for (unsigned int i = 0; i < size(); i++ )
        at(i)->remove(doc);
}

DocSet* DocSetList::forTerm(char* term) {
    guint32 termnr = TrieNode_getValue(termIndex2, term);
    if ( termnr == fwValueNone )
        return NULL;
    return at(termnr);
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
            if ( (*it)->size() < minCardinality ) {
                break;
            }
            guint32 cardinality = (*it)->combinedCardinality(docset);
            if ( cardinality ) {
                cardinality_t t = { (*it)->term(), cardinality };
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
            guint32 cardinality = at(i)->combinedCardinality(docset);
            if ( cardinality ) {
                cardinality_t t = { at(i)->term(), cardinality };
                results->push_back(t);
            }
        }
    }
    return results;
}
bool cmpCardinality(DocSet* lhs, DocSet* rhs) {
    return lhs->size() > rhs->size();
}

class DummyDocSet : public DocSet {
    public:
        DummyDocSet(size_t size) : DocSet(size) { }
};

CardinalityList*
DocSetList::jaccards(DocSet* docset, int minimum, int maximum) {

    CardinalityList* results = new CardinalityList();
    DocSetList::iterator lower = begin();
    DocSetList::iterator upper = end();
    if ( minimum > 0 ) {
        DummyDocSet dummyMax = DummyDocSet(100*docset->size()/minimum);
        lower = lower_bound(lower, upper, &dummyMax, cmpCardinality);
        DummyDocSet dummyMin = DummyDocSet(docset->size()*minimum/100);
        upper = upper_bound(lower, upper, &dummyMin, cmpCardinality);
    }

    while ( lower < upper ) {
        DocSet* candidate = (*lower++);
        int c = candidate->combinedCardinality(docset);
        int j = 100 * c / (candidate->size() + docset->size() - c);

        if ( j >= minimum && j <= maximum ) {
            double tf = (double)candidate->size() / (double) docset->size();
            double idf = log((double)candidate->size() / (double) c) + 1;
            printf("==> %s tf=%f idf=%f %f\n", candidate->term(), tf, idf, tf*idf);
            if (tf*idf < 2.0) {
                cardinality_t t = { candidate->term(), j };
                results->push_back(t);
            }
        }
    }
    sort(results->begin(), results->end(), cmpCardinalityResults);
    return results;
}




/////////////// C Interface to DocSetList ////////////////

cardinality_t* CardinalityList_at(CardinalityList* vector, int i) {
    return &vector->at(i);
}
int CardinalityList_size(CardinalityList* vector) {
    return vector->size();
}
void CardinalityList_free(CardinalityList* vector) {
    free(vector);
}

DocSetList* DocSetList_create() {
    return new DocSetList();
}

void DocSetList_add(DocSetList* list, DocSet* docset) {
    list->addDocSet(docset);
}

void DocSetList_removeDoc(DocSetList* list, guint32 doc) {
    list->removeDoc(doc);
}

int DocSetList_size(DocSetList* list) {
    return list->size();
}

DocSet* DocSetList_get(DocSetList* list, int i) {
    try {
        return list->at(i);
    } catch (std::exception&) {
        return NULL;
    }
}

DocSet* DocSetList_getForTerm(DocSetList* list, char* term) {
    return list->forTerm(term);
}

CardinalityList* DocSetList_combinedCardinalities(DocSetList* list, DocSet* docset, guint32 maxResults, int doSort) {
    return list->combinedCardinalities(docset, maxResults, doSort);
}

CardinalityList* DocSetList_jaccards(DocSetList* list, DocSet* docset, int minimum, int maximum) {
    return list->jaccards(docset, minimum, maximum);
}

void DocSetList_delete(DocSetList* list) {
    delete list;
}

DocSetList* DocSetList_fromTermEnum(PyJObject* termEnum, PyJObject* termDocs) {
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
        list->addDocSet(DocSet::fromTermDocs(termDocs->jobject, freq, text));
    } while ( next(termEnum->jobject) );
    return list;
}

void DocSetList_sortOnCardinality(DocSetList* docsetlist) {
    sort(docsetlist->begin(), docsetlist->end(), cmpCardinality);
}
