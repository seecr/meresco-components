/* begin license *
 *
 *     Meresco Components are components to build searchengines, repositories
 *     and archives, based on Meresco Core.
 *     Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
 *     Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
 *        http://www.kennisnetictopschool.nl
 *     Copyright (C) 2009 Delft University of Technology http://www.tudelft.nl
 *     Copyright (C) 2009 Tilburg University http://www.uvt.nl
 *     Copyright (C) 2007-2009 Seek You Too (CQ2) http://www.cq2.nl
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


DocSetList::~DocSetList() {
    for ( unsigned int i = 0; i < size(); i++) {
       DocSet_delete(at(i));
    }
}


class CompareTerm {
    public:
        DocSetList* mii;
        CompareTerm(DocSetList* list) : mii(list) {}
        bool operator ()(fwPtr lhs, fwPtr rhs) {
            DocSet* plhs = pDS(lhs);
            DocSet* prhs = pDS(rhs);
            return strcmp(mii->getTermForDocset(plhs), mii->getTermForDocset(prhs)) < 0;
        }
};

class CompareTermId {
    public:
        CompareTermId(DocSetList* list) {}
        bool operator ()(fwPtr lhs, fwPtr rhs) {
            return pDS(lhs)->_termOffset < pDS(rhs)->_termOffset;
        }
};

void DocSetList::sortOnTerm(void) {
    sort(begin(), end(), CompareTerm(this));
}

void DocSetList::sortOnTermId(void) {
    sort(begin(), end(), CompareTermId(this));
}


DocSetIterator DocSetList::begin_docId(void) {
    return DocSetIterator();
}


void DocSetList::addDocSet(fwPtr docset, char *term) {
    push_back(docset);
    if ( term  ) {
        guint32 termId = dictionary.add(term, docset.ptr);
        pDS(docset)->setTermOffset(termId);
    }
    DocSet* ds = pDS(docset);
    for ( DocSet::iterator i = ds->begin(); i < ds->end(); i++ ) {
        guint32 docId = (*i);
        this->docId2terms_add(docId, docset);
    }
}

void DocSetList::docId2terms_add(guint32 docId, fwPtr docset) {

    TermList& terms = this->docId2TermList[docId];
    terms.push_back(docset);
}

void DocSetList::removeDoc(guint32 docId) {
    TermList& terms = this->docId2TermList[docId];
    for ( TermList::iterator t = terms.begin(); t < terms.end(); t++) {
        DocSet* docset = pDS(*t);
        docset->remove(docId);
    }
    docId2TermList.erase(docId);
}


fwPtr DocSetList::forTerm(char* term) {
    guint32 docsetptr = dictionary.getValue(term);
    if ( docsetptr == 0xFFFFFFFF )
        return fwNONE;
    fwPtr docset = {0, docsetptr};
    return docset;
}


bool cmpCardinalityResults(const cardinality_t& lhs, const cardinality_t& rhs) {
    return lhs.cardinality > rhs.cardinality;
}

char* DocSetList::getTermForDocset(DocSet *docset) {
    return dictionary.getTerm(docset->_termOffset);
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
                cardinality_t t = { getTermForDocset(pDS(*it)), cardinality };
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
                cardinality_t t = { getTermForDocset(pDS(at(i))), cardinality };
                results->push_back(t);
            }
        }
    }
    return results;
}

bool cmpCardinality(fwPtr lhs, fwPtr rhs) {
    return pDS(lhs)->size() > pDS(rhs)->size();
}

DocSetList* DocSetList::intersect(DocSet* docset) {
    DocSetList* results = new DocSetList();
    results->reserve(size() + 1);
    for( unsigned int i=0; i < size() ; i++ ) {
        fwPtr intersection = pDS(at(i))->intersect(docset);
        if ( ! pDS(intersection)->size() ) {
            DocSet_delete(intersection);
        } else {
            results->addDocSet(intersection, getTermForDocset(pDS(at(i))));
        }
    }
    return results;
}

DocSetList* DocSetList::termIntersect(DocSetList* rhs) {
    // ensure sorted on termID
    sortOnTermId();
    rhs->sortOnTermId();
    DocSetList* result = new DocSetList();

    DocSetList::iterator lhs_iter = begin();
    DocSetList::iterator rhs_iter = rhs->begin();

    while ( lhs_iter < end() && rhs_iter < rhs->end()) {
        if ( pDS(*lhs_iter)->_termOffset == pDS(*rhs_iter)->_termOffset ) {
            fwPtr d = DocSet_create(0);
            pDS(d)->assign(pDS(*lhs_iter)->begin(), pDS(*lhs_iter)->end());
            result->addDocSet(d, getTermForDocset(pDS(*lhs_iter)));
            lhs_iter++;
        }

        while ( lhs_iter < end() &&
                pDS(*lhs_iter)->_termOffset < pDS(*rhs_iter)->_termOffset )
            lhs_iter++;

        while ( rhs_iter < rhs->end() &&
                pDS(*rhs_iter)->_termOffset < pDS(*lhs_iter)->_termOffset )
            rhs_iter++;

    }

    return result;
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
                    char *term = getTermForDocset(candidate);
                    cardinality_t t = { term, n};
                    results->push_back(t);
                }
            } else if (algorithm == JACCARD_X2) {
                // X^2
/*                double X2 = ((N11+N10+N01+N00)*pow(N11*N00-N10*N01,2.0)) /
                            ((N11+N01)*(N11+N10)*(N10+N00)*(N01+N00));*/
            } else {
                cardinality_t t = { getTermForDocset(candidate), j};
                results->push_back(t);
            }
        }
    }
    sort(results->begin(), results->end(), cmpCardinalityResults);
    return results;
}

void DocSetList::nodecount(void) {
    dictionary.nodecount();
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

void DocSetList_add(DocSetList* list, fwPtr docset, char* term) {
    list->addDocSet(docset, term);
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

DocSetList* DocSetList_intersect(DocSetList* list, fwPtr ds) {
    DocSet* docset = pDS(ds);
    return list->intersect(docset);
}

DocSetList* DocSetList_termIntersect(DocSetList* self, DocSetList* rhs) {
    return self->termIntersect(rhs);
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

        fwPtr ds = DocSet::fromTermDocs(termDocs->jobject, freq, mapping);
        char* tmp = (char*) malloc(90000);
        int w = text->writeUTF8CharsIn((char*)tmp);
        tmp[w] = '\0';
        list->addDocSet(ds, tmp);
        free(tmp);

    } while ( next(termEnum->jobject) );

    return list;
}

void DocSetList_sortOnCardinality(DocSetList* docsetlist) {
    sort(docsetlist->begin(), docsetlist->end(), cmpCardinality);
}

void DocSetList_sortOnTerm(DocSetList* list) {
    list->sortOnTerm();
}

void DocSetList_sortOnTermId(DocSetList* list) {
    list->sortOnTermId();
}

void DocSetList_printMemory(DocSetList* list) {
    list->nodecount();
}

char* DocSetList_getTermForDocset(DocSetList *list, fwPtr docset) {
    return list->getTermForDocset(pDS(docset));
}

void DocSetList_docId2terms_add(DocSetList *list, guint32 docId, fwPtr docset) {
    list->docId2terms_add(docId, docset);
}
