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
#include "docset.h"
#include <algorithm>

extern "C" {
    #include "zipper.h"
    #include "fwpool.h"
}

fwPool _docsetPool = Pool_create(0, sizeof(DocSet), 10000);

fwPtr DocSet_create(int size=0) {
    fwPtr newOne = Pool_new(_docsetPool);
    void* p = pDS(newOne);
    if ( size > 0 ) {
        new (p) DocSet(size);
    } else {
        new (p) DocSet();
    }
    return newOne;
}
void DocSet_delete(fwPtr docset) {
    pDS(docset)->~DocSet();
    Pool_free(_docsetPool, docset);
}

fwPtr DocSet_forTesting(int size) {
    fwPtr ds = DocSet_create();
    DocSet* docset = pDS(ds);
    docset->reserve(size);
    for ( int i = 0; i < size; i++ )
        docset->push_back(i);
    return ds;
}
fwPtr DocSet_fromTermDocs(PyJObject* termDocs, int freq,  IntegerList* mapping) {
    return DocSet::fromTermDocs(termDocs->jobject, freq,  mapping);
}

int DocSet_contains(fwPtr docSet, guint32 docId) {
    return pDS(docSet)->contains(docId);
}

void DocSet_add(fwPtr docset, guint32 doc) {
    pDS(docset)->push_back(doc);
}
void DocSet_remove(fwPtr docset, guint32 doc) {
    pDS(docset)->remove(doc);
}
guint32 DocSet_get(fwPtr docset, int i) {
    return pDS(docset)->at(i);
}
int DocSet_len(fwPtr docset) {
    return pDS(docset)->size();
}

int DocSet_combinedCardinality(fwPtr docset, fwPtr rhs) {
    return pDS(docset)->combinedCardinality(pDS(rhs));
}

int DocSet_combinedCardinalitySearch(fwPtr docset, fwPtr rhs) {
    return pDS(docset)->combinedCardinalitySearch(pDS(rhs));
}

fwPtr DocSet_intersect(fwPtr docset, fwPtr rhs) {
    return pDS(docset)->intersect(pDS(rhs));
}

class CardinalityCounter : public OnResult {
    public:
        guint32 c;
        CardinalityCounter() : c(0) {};
        void operator () (guint32 docId) {
            c++;
        }
};

// ### C++ below ###

int DocSet::contains(guint32 docId) {
    return binary_search(begin(), end(), docId);
}

int DocSet::combinedCardinalitySearch(DocSet* larger) {
    CardinalityCounter counter;
    intersect_generic<DocSet::iterator>
        (begin(), end(), larger->begin(), larger->end(), counter);
    return counter.c;
}


#define SWITCHPOINT 100 // for random docsset, this is the trippoint
int DocSet::combinedCardinality(DocSet* rhs) {
    unsigned int lhsSize = size();
    unsigned int rhsSize = rhs->size();
    if ( rhsSize < lhsSize ) { // redirect to shortest list works faster for both zipper and search
        return rhs->combinedCardinality(this);
    }
    if ( rhsSize > lhsSize * SWITCHPOINT ) {
        return combinedCardinalitySearch(rhs);
    }
    push_back(0xFFFFFFFF);
    rhs->push_back(0xFFFFFFFF);
    std::vector<guint32>::iterator rhsLower = lower_bound(rhs->begin(), rhs->end(), at(0));
    std::vector<guint32>::iterator myLower  = lower_bound(begin(), end(), rhs->at(0));
    int c = combinedCardinalityZipper(&(*myLower), &(*rhsLower));
    pop_back();
    rhs->pop_back();
    return c;
}

class IntersectingDocSet : public OnResult {
    private:
        DocSet* _docset;
    public:
        IntersectingDocSet(DocSet* docset) {
            _docset = docset;
        }
    void operator () (guint32 docId) {
        _docset->push_back(docId);
    }
};

fwPtr DocSet::intersect(DocSet* rhs) {
    fwPtr result = DocSet_create();
    IntersectingDocSet onresult(pDS(result));
    intersect_generic<DocSet::iterator>(begin(), end(), rhs->begin(), rhs->end(), onresult);
    return result;
}

void DocSet::append(doc_t* docarray, int count) {
    reserve( size() + count );
    struct IntVectorHacker { // used to poke data in std:vector<doc_t>
        doc_t* begin;
        doc_t* end;
        doc_t* allocated;
    } *hack = (IntVectorHacker*) this;
    // vette hack + 100
    memcpy(hack->end, docarray, count * sizeof(doc_t));
    hack->end += count;
}

void DocSet::remove(guint32 doc) {
    std::vector<guint32>::iterator i = lower_bound(begin(), end(), doc);
    if ( i < end() && *i == doc ) {
        erase(i);
    }
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
        fwPtr docset;
        HitCollector() : docset( DocSet_create() ) {}
        virtual void aka_collect(register jint doc, register jfloat score) { // collect
            pDS(docset)->push_back(doc);
        }
};

fwPtr DocSet_fromQuery(PyJObject* psearcher, PyJObject* pquery, IntegerList* mapping) {
    HitCollector* resultCollector = new HitCollector();
    // Direct call of public void search(Query query, HitCollector results),
    // since there happens to be only one implementation which is not overridden
    // by any of MultiSearcher, IndexSearcher, ParallelSearche etc. Luckily!
    Searcher_search(psearcher->jobject, pquery->jobject, resultCollector);
    pDS(resultCollector->docset)->map(mapping);
    return resultCollector->docset;
}



/****************************************************************************
* TermDocs::read is called using fake int arrays.
* The one reason for doing so, is to lay our hands directly
* on the C/Java int[], instead of using a slow Python list of integer objects.
****************************************************************************/

#define TERMDOCS_READ_BUFF_SIZE 100000
JIntArray* documents = _Jv_NewIntArray(TERMDOCS_READ_BUFF_SIZE);
JIntArray* ignored = _Jv_NewIntArray(TERMDOCS_READ_BUFF_SIZE);

fwPtr DocSet::fromTermDocs(JObject* termDocs, int freq, IntegerList* mapping) {
    // Call read() via Interface, because different implementations might be MultiTermDocs,
    // SegmentTermDocs, and the like.  Lookup only once instead of at every call. The
    // read() method is the 6th in the interface. Counting starts at 1.
    TermDocs_read read = (TermDocs_read) lookupIface(termDocs, &ITermDocs, 6);
    fwPtr docset = DocSet_create();
    DocSet* docs = pDS(docset);
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
    docs->map(mapping);
    return docset;
}

void
DocSet::map(IntegerList* mapping) {
    if ( ! mapping ) {
        return;
    }
    for (DocSet::iterator it = begin(); it < end(); it++) {
        (*it) = (*mapping)[*it];
    }
}

void DocSet::setTermOffset(guint32 offset) {
    this->_termOffset = offset;
}
