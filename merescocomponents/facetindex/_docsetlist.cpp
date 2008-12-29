#include "pyjava.h"
#include "docsetlist.h"

extern "C" {
    #include "zipper.h"
}

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
    docset->push_back(0xFFFFFFFF);
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
                sort(results->begin(), results->end(), cmpCardinalityResults);
                if ( results->size() > maxResults ) {
                    results->pop_back();
                }
                minCardinality = results->back().cardinality;
            }
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
    docset->pop_back();
    return results;
}


/////////////// C Interface to DocSetList ////////////////

void* CardinalityList_at(CardinalityList* vector, int i) {
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

void* DocSetList_combinedCardinalities(DocSetList* list, DocSet* docset, guint32 maxResults, int doSort) {
    return list->combinedCardinalities(docset, maxResults, doSort);
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

bool cmpCardinality(DocSet* lhs, DocSet* rhs) {
    return lhs->size() > rhs->size();
}
void DocSetList_sortOnCardinality(DocSetList* docsetlist) {
    sort(docsetlist->begin(), docsetlist->end(), cmpCardinality);
}