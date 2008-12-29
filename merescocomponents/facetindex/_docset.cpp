#include "pyjava.h"
#include "docset.h"
#include <algorithm>

extern "C" {
    #include "zipper.h"
}


DocSet* DocSet_create() {
    return new DocSet();
}
DocSet* DocSet_forTesting(int size) {
    DocSet* docset = new DocSet();
    docset->reserve(size);
    for ( int i = 0; i < size; i++ )
        docset->push_back(i);
    return docset;
}
DocSet* DocSet_fromTermDocs(PyJObject* termDocs, int freq, char* term) {
    DocSet* result = DocSet::fromTermDocs(termDocs->jobject, freq, NULL);
    result->setTerm(term);
    return result;
}
void DocSet_add(DocSet* docset, guint32 doc) {
    docset->push_back(doc);
}
void DocSet_remove(DocSet* docset, guint32 doc) {
    docset->remove(doc);
}
guint32 DocSet_get(DocSet* docset, int i) {
    return docset->at(i);
}
int DocSet_len(DocSet* docset) {
    return docset->size();
}
void DocSet_setTerm(DocSet* docset, char* term) {
    docset->setTerm(term);
}
char* DocSet_term(DocSet* docset) {
    return docset->term();
}
int DocSet_combinedCardinality(DocSet* docset, DocSet* rhs) {
    return docset->combinedCardinality(rhs);
}
DocSet* DocSet_intersect(DocSet* docset, DocSet* rhs) {
    return docset->intersect(rhs);
}
void DocSet_delete(DocSet* docset) {
    delete docset;
}


void DocSet::setTerm(char* term) {
    _term = fwString_create(term);
}

void DocSet::setTerm(JString* term) {
    char* tmp = (char*) malloc(90000);
    int w = term->writeUTF8CharsIn((char*)tmp);
    tmp[w] = '\0';
    setTerm(tmp);
    free(tmp);
}

char* DocSet::term(void) {
    if ( _term == fwStringNone )
        return NULL;
    return fwString_get(_term);
}

int DocSet::combinedCardinalitySearch(DocSet* larger) {
    std::vector<guint32>::iterator lower = larger->begin();
    std::vector<guint32>::iterator upper = larger->end();
    std::vector<guint32>::iterator from = begin();
    std::vector<guint32>::iterator till = end();
    int c = 0;
    while ( from != till ) {
        lower = lower_bound(lower, upper, *from);
        if ( *from++ == *lower ) {
            c++;
        }
        if ( till > from ) {
            upper = upper_bound(lower, upper, *--till);
            if ( *till == *upper )
                c++;
        }
    }
    return c;
}

#define SWITCHPOINT 100 // for random docsset, this is the trippoint
int DocSet::combinedCardinality(DocSet* rhs) {
    unsigned int lhsSize = size();
    unsigned int rhsSize = rhs->size();
    if ( rhsSize < lhsSize )  // redirect to shortest list works faster for both zipper and search
        return rhs->combinedCardinality(this);
    if ( rhsSize > lhsSize * SWITCHPOINT )
        return combinedCardinalitySearch(rhs);
    push_back(0xFFFFFFFF);
    rhs->push_back(0xFFFFFFFF);
    std::vector<guint32>::iterator rhsLower = lower_bound(rhs->begin(), rhs->end(), at(0));
    std::vector<guint32>::iterator myLower  = lower_bound(begin(), end(), rhs->at(0));
    int c = combinedCardinalityZipper(&(*myLower), &(*rhsLower));
    pop_back();
    rhs->pop_back();
    return c;
}

DocSet* DocSet::intersect(DocSet* rhs) {
    DocSet* result = new DocSet();
    result->resize(this->size() > rhs->size() ? size() : rhs->size());
    push_back(0xFFFFFFFF);
    rhs->push_back(0xFFFFFFFF);
    int size = intersectZipper(&this->front(), &rhs->front(), &result->front());
    pop_back();
    rhs->pop_back();
    result->resize(size);
    return result;
}

void DocSet::append(doc_t* docarray, int count) {
    reserve( size() + count );
    struct IntVectorHacker { // used to poke data in std:vector<doc_t>
        doc_t* begin;
        doc_t* end;
        doc_t* allocated;
    } *hack = (IntVectorHacker*) this;
    memcpy(hack->end, docarray, count * sizeof(doc_t));
    hack->end += count;
}

void DocSet::remove(guint32 doc) {
    std::vector<guint32>::iterator i = lower_bound(begin(), end(), doc);
    if ( *i == doc )
        erase(i);
}

/****************************************************************************
* DocSet_fromQuery() performs a Lucene query with 'search'() and gathers all
* docids in a C 0xFFFFFFFF-terminated list. It assumes PyLucene objects for
* 'searcher' and 'query', which are just unwrapped using PyJObject and passed onto 'search'().
* It uses a fake C++ hitcollector to implement the 'collect' callback. It is
* intended to be used with Python ctypes.
****************************************************************************/

class HitCollector : public JHitCollector {
    public:
        DocSet* docs;
        HitCollector() : docs( new DocSet() ) {}
        virtual void aka_collect(register jint doc, register jfloat score) { // collect
            docs->push_back(doc);
        }
};

DocSet* DocSet_fromQuery(PyJObject* psearcher, PyJObject* pquery) {
    HitCollector* resultCollector = new HitCollector();
    // Direct call of public void search(Query query, HitCollector results),
    // since there happens to be only one implementation which is not overridden
    // by any of MultiSearcher, IndexSearcher, ParallelSearche etc. Luckily!
    Searcher_search(psearcher->jobject, pquery->jobject, resultCollector);
    return resultCollector->docs;
}



/****************************************************************************
* TermDocs::read is called using fake int arrays.
* The one reason for doing so, is to lay our hands directly
* on the C/Java int[], instead of using a slow Python list of integer objects.
****************************************************************************/

#define TERMDOCS_READ_BUFF_SIZE 100000
JIntArray* documents = _Jv_NewIntArray(TERMDOCS_READ_BUFF_SIZE);
JIntArray* ignored = _Jv_NewIntArray(TERMDOCS_READ_BUFF_SIZE);

DocSet* DocSet::fromTermDocs(JObject* termDocs, int freq, JString* term) {
    // Call read() via Interface, because different implementations might be MultiTermDocs,
    // SegmentTermDocs, and the like.  Lookup only once instead of at every call. The
    // read() method is the 6th in the interface. Counting starts at 1.
    TermDocs_read read = (TermDocs_read) lookupIface(termDocs, &ITermDocs, 6);
    DocSet* docs = new DocSet();
    if ( term )
        docs->setTerm(term);
    docs->reserve(freq); // <<== this really speeds up: from 3.1/3.2 => 2.6/2.7 seconds.
    jint count = read(termDocs, documents, ignored);
    docs->append((doc_t*)documents->data, count);
    // read does not read all segments, we must check ourselves
    while ( count < freq ) {
        jint additional = read(termDocs, documents, ignored);
        if ( !additional )
            /* public final void deleteDocument(int docNum)
	         *
       	     * Deletes the document numbered docNum. Once a document is deleted it will not appear
             * in TermDocs or TermPostitions enumerations. Attempts to read its field with the
             * document(int) method will result in an error. The presence of this document may still
             * be reflected in the docFreq(org.apache.lucene.index.Term) statistic, though this will
             * be corrected eventually as the index is further modified.
             */
            break;
        docs->append((doc_t*)documents->data, additional);
        count += additional;
    }
    return docs;
}
