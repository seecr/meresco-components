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

#include <glib.h>

#include <gcj/cni.h>
#include "java/lang/Object.h"
#include "org/apache/lucene/index/TermEnum.h"
#include "org/apache/lucene/index/Term.h"

#include "docsetlist.h"
#include "docset.h"
#include "integerlist.h"

#include <assert.h>


extern "C" {
    #include "zipper.h"
}

#include <math.h>
#include <vector>
#include <algorithm>

using namespace org::apache;


/**************** C++ implementation of DocSetList****************************/


DocSetList::~DocSetList() {
    if (! _shadow ) {
        for ( unsigned int i = 0; i < size(); i++) {
           DocSet_delete(at(i));
        }
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
    return DocSetIterator(begin());
}

DocSetIterator DocSetList::end_docId(void) {
    return DocSetIterator(end());
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


void DocSetList::merge(DocSetList* anotherList) {
    for (DocSetList::iterator i = anotherList->begin(); i < anotherList->end(); i++) {
        char *term = anotherList->getTermForDocset(pDS(*i));

        fwPtr matchingDocSet = forTerm(term);
        if (matchingDocSet.ptr == fwNONE.ptr) {
            fwPtr newDocSet = DocSet_create(0);
            pDS(newDocSet)->merge(pDS(*i));
            addDocSet(newDocSet, term);
        } else {
            pDS(matchingDocSet)->merge(pDS(*i));
        }
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

int DocSetList::cardinalityForTerm(char* term) {
    guint32 docsetptr = dictionary.getValue(term);
    if ( docsetptr == 0xFFFFFFFF )
        return 0;
    fwPtr docset = {0, docsetptr};
    return DocSet_len(docset);
}


bool cmpCardinalityResults(const cardinality_t& lhs, const cardinality_t& rhs) {
    return lhs.cardinality > rhs.cardinality;
}

char* DocSetList::getTermForId(guint32 termId) {
    return dictionary.getTerm(termId);
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

DocSetList* DocSetList::intersect(fwPtr docset) {
    DocSetList* results = new DocSetList(false);
    results->reserve(size() + 1);
    for( unsigned int i=0; i < size() ; i++ ) {
        fwPtr intersection = DocSet_intersect(at(i), docset);
        if ( ! pDS(intersection)->size() ) {
            DocSet_delete(intersection);
        } else {
            results->addDocSet(intersection, getTermForDocset(pDS(at(i))));
        }
    }
    return results;
}

class TermCollector {
    private:
        DocSetList* _parent;
        DocSetList* _result;
    public:
        TermCollector(DocSetList* parent, DocSetList* result) : _parent( parent ), _result (result) {};
        TermCollector& operator++ (int i) { return *this; }
        TermCollector& operator* () { return *this; }
        TermCollector& operator= (guint32 termId) {
            char* term = _parent->getTermForId(termId);
            _result->addDocSet(_parent->forTerm(term), term);
            return *this;
        }
};

DocSetList* DocSetList::termIntersect(DocSetList* rhs) {
    // ensure sorted on termID
    sortOnTermId();
    rhs->sortOnTermId();
    DocSetList* result = new DocSetList(true);
    DocSetIterator from = begin_docId();
    DocSetIterator till = end_docId();
    DocSetIterator rhs_from = rhs->begin_docId();
    DocSetIterator rhs_till = rhs->end_docId();
    TermCollector onresult(this, result);
    intersect_generic<DocSetIterator, TermCollector>(from, till, rhs_from, rhs_till, onresult);
    return result;
}

fwPtr DocSetList::innerUnion() {
    std::vector<bool> result ;
    for ( DocSetList::iterator i = begin(); i < end(); i++ ) {
        DocSet* ds = pDS(*i);
        for ( DocSet::iterator d = ds->begin(); d < ds->end(); d++ ) {
            guint32 docId = *d;
            if ( docId >= result.size() ) {
                result.resize(docId + 1);
            }
            result[docId] = true;
        }
    }
    fwPtr resultDocSet = DocSet_create(0);
    for ( unsigned int i = 0; i < result.size(); i++ ) {
        if ( result[i] ) {
            pDS(resultDocSet)->push_back(i);
        }
    }
    return resultDocSet;
}

class DummyDocSet : public DocSet {
    public:
        DummyDocSet(size_t size) : DocSet(size) { }
};

double mi(int totaldocs, int lhs_size, int rhs_size, int combinedCardinality) {
    // Mutual Information (aka Information Gain)

    int N11 = combinedCardinality;
    int N10 = lhs_size - combinedCardinality;
    int N01 = rhs_size - combinedCardinality;
    int N00 = totaldocs - (lhs_size + rhs_size - combinedCardinality);

    double N = totaldocs;

    assert(N00 == N - N01 - N10 - N11);
    assert(N == N00 + N10 + N01 + N11);

    double N1_ = N10 + N11;
    double N_1 = N01 + N11;
    double N0_ = N01 + N00;
    double N_0 = N10 + N00;
    double MI = (N11 == 0 ? 0.0 : (N11/N)*log((N*N11)/(N1_*N_1))) +
                (N01 == 0 ? 0.0 : (N01/N)*log((N*N01)/(N0_*N_1))) +
                (N10 == 0 ? 0.0 : (N10/N)*log((N*N10)/(N1_*N_0))) +
                (N00 == 0 ? 0.0 : (N00/N)*log((N*N00)/(N0_*N_0)));
    return MI;
}


int min(int lhs, int rhs) {
    return lhs < rhs ? lhs : rhs;
}

CardinalityList*
DocSetList::jaccards(DocSet* docset, int minimum, int maximum, int totaldocs, int algorithm, int maxTermFreqPercentage) {
    CardinalityList* results = new CardinalityList();
    DocSetList::iterator lower = begin();
    DocSetList::iterator upper = end();
    int maxTermFreq = maxTermFreqPercentage * totaldocs / 100;
    if ( minimum > 0 ) {
        maxTermFreq = min(maxTermFreq, 100 * docset->size() / minimum);
    }
    if (maxTermFreq < totaldocs) {
        fwPtr dummyMax = DocSet_create(maxTermFreq);
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
                double MI = mi(totaldocs, docset->size(), candidate->size(), c);
                int n = int(MI * 100000.0);
                char *term = getTermForDocset(candidate);
                cardinality_t t = { term, n};
                results->push_back(t);
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

CardinalityList* DocSetList::filterByPrefix(char* prefix, guint32 maxResults) {
    CardinalityList* results = new CardinalityList();

    IntegerList* docSetFws = IntegerList_create(0);
    dictionary.valuesForPrefix(prefix, maxResults, docSetFws);

    for (IntegerList::iterator it = docSetFws->begin(); it < docSetFws->end(); it++) {
        fwPtr docset =  {0, (*it)};
        cardinality_t cardinality = {getTermForDocset(pDS(docset)), pDS(docset)->size()};
        results->push_back(cardinality);
    }
    IntegerList_delete(docSetFws);

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
void CardinalityList_sortOnCardinality(CardinalityList* vector) {
    sort(vector->begin(), vector->end(), cmpCardinalityResults);
}

/////////////// C Interface to DocSetList ////////////////

DocSetList* DocSetList_create() {
    return new DocSetList(false);
}

void DocSetList_add(DocSetList* list, fwPtr docset, char* term) {
    list->addDocSet(docset, term);
}

void DocSetList_merge(DocSetList* list, DocSetList* anotherlist) {
    list->merge(anotherlist);
}

void DocSetList_removeDoc(DocSetList* list, guint32 doc) {
    list->removeDoc(doc);
}

int DocSetList_size(DocSetList* list) {
    return list->size();
}

fwPtr DocSetList_get(DocSetList* list, int i) {
    if (i < 0 || i >= list->size()) {
        return fwNONE;
    }
    return list->at(i);
}

fwPtr DocSetList_getForTerm(DocSetList* list, char* term) {
    return list->forTerm(term);
}

int DocSetList_cardinalityForTerm(DocSetList* list, char* term) {
    return list->cardinalityForTerm(term);
}

CardinalityList* DocSetList_combinedCardinalities(DocSetList* list, fwPtr ds, guint32 maxResults, int doSort) {
    DocSet* docset = pDS(ds);
    return list->combinedCardinalities(docset, maxResults, doSort);
}

DocSetList* DocSetList_intersect(DocSetList* list, fwPtr ds) {
    return list->intersect(ds);
}

DocSetList* DocSetList_termIntersect(DocSetList* self, DocSetList* rhs) {
    return self->termIntersect(rhs);
}

fwPtr DocSetList_innerUnion(DocSetList* self) {
    return self->innerUnion();
}

CardinalityList* DocSetList_jaccards(DocSetList* list, fwPtr ds, int minimum, int maximum, int totaldocs, int algorithm, int maxTermFreq) {
    DocSet* docset = pDS(ds);
    return list->jaccards(docset, minimum, maximum, totaldocs, algorithm, maxTermFreq);
}

void DocSetList_delete(DocSetList* list) {
    delete list;
}

DocSetList* DocSetList_forField(lucene::index::IndexReader* reader, char* fieldname, IntegerList *mapping) {
    DocSetList* list = DocSetList_create();
    jstring field = JvNewStringUTF(fieldname);
    lucene::index::TermEnum* termEnum =
        reader->terms(new lucene::index::Term(field, JvNewStringUTF("")));
    lucene::index::Term* term = termEnum->term();
    if (!term || !term->field()->equals((java::lang::Object*) field)) {
        return list;
    }
    field = term->field();
    do {
        lucene::index::Term* term = termEnum->term();
        if (!term) {
            break;
        }
        if (field != term->field()) {
            break;
        }

        jstring termText = term->text();

        int jTermTextLength = termText->length();
        char* cTermText = (char*) malloc(jTermTextLength * 4 + 1);
        int w = JvGetStringUTFRegion(termText, 0, jTermTextLength, cTermText);
        cTermText[w] = '\0';

        fwPtr ds = DocSet::forTerm(reader, fieldname, cTermText, mapping);
        list->addDocSet(ds, cTermText);

        free(cTermText);
    } while (termEnum->next());
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

char* DocSetList_getTermForId(DocSetList* list, guint32 termId) {
    return list->getTermForId(termId);
}

void DocSetList_docId2terms_add(DocSetList *list, guint32 docId, fwPtr docset) {
    list->docId2terms_add(docId, docset);
}

CardinalityList* DocSetList_filterByPrefix(DocSetList* list, char* term, guint32 maxResults) {
    return list->filterByPrefix(term, maxResults);
}

int DocSetList_measure(DocSetList* list) {
    return list->measure();
}
