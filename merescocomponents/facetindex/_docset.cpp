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

#include "assert.h"

#include "org/apache/lucene/search/MatchAllDocsQuery.h"
#include "org/apache/lucene/search/HitCollector.h"
#include "org/apache/lucene/index/TermEnum.h"
#include "org/apache/lucene/index/TermDocs.h"
#include "org/apache/lucene/index/Term.h"
#include "java/lang/Throwable.h"
#include "docset.h"
#include <algorithm>

using namespace org::apache;


extern "C" {
    #include "zipper.h"
    #include "fwpool.h"
}

fwPool _docsetPool = Pool_create(0, sizeof(DocSet), 10000);

DocSet* DocSet_create2(void) {
    return new DocSet();
}

DocSet* DocSet_from_param(fwPtr docset) {
    return pDS(docset);
}

fwPtr DocSet_create(int size=0) {
    fwPtr newOne = Pool_new(_docsetPool);
    DocSet* p = pDS(newOne);
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

int DocSet_measure(fwPtr docset) {
    return pDS(docset)->measure();
}

fwPtr DocSet_forTesting(int size) {
    fwPtr ds = DocSet_create();
    DocSet* docset = pDS(ds);
    docset->reserve(size);
    for ( int i = 0; i < size; i++ )
        docset->push_back(i);
    return ds;
}

fwPtr DocSet_forTerm(lucene::index::IndexReader *reader, char* fieldname, char* term, IntegerList* mapping) {
    return DocSet::forTerm(reader, fieldname, term, mapping);
}

int DocSet_contains(fwPtr docSet, guint32 docId) {
    return pDS(docSet)->contains(docId);
}

void DocSet_add(fwPtr docset, guint32 doc) {
    pDS(docset)->push_back(doc);
}

void DocSet_merge(fwPtr docSet, fwPtr anotherDocSet) {
    pDS(docSet)->merge(pDS(anotherDocSet));
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
    return pDS(docset)->intersect(rhs);
}

// ### C++ below ###
int DocSet::contains(guint32 docId) {
    return binary_search(begin(), end(), docId);
}

class CardinalityCounter {
    public:
        int count;
        CardinalityCounter() : count( 0 ) {};
        CardinalityCounter& operator++ (int i) { return *this; }
        CardinalityCounter& operator* () { return *this; }
        CardinalityCounter& operator= (guint32 termId) { count++; return *this; }
};

int DocSet::combinedCardinalitySearch(DocSet* larger) {
    CardinalityCounter counter;
    intersect_generic<DocSet::iterator, CardinalityCounter>
        (begin(), end(), larger->begin(), larger->end(), counter);
    return counter.count;
}


int DocSet::combinedCardinality(DocSet* rhs) {
    return combinedCardinalitySearch(rhs);
}

fwPtr DocSet::intersect(fwPtr rhs) {
    DocSet::iterator a = begin();
    DocSet::iterator b = end();
    DocSet::iterator c = pDS(rhs)->begin();
    DocSet::iterator d = pDS(rhs)->end();
    fwPtr result = DocSet_create();
    pDS(result)->resize(std::min(size(), pDS(rhs)->size()));
    guint32* result_feeder = &(pDS(result)->front());
    guint32* start = result_feeder;
    intersect_generic<DocSet::iterator, guint32*>(a, b, c, d, result_feeder);
    pDS(result)->resize(result_feeder - start);
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


void DocSet::merge(DocSet* docSet) {
    DocSet::iterator thisIterator = begin();
    for (DocSet::iterator it = docSet->begin(); it < docSet->end(); it++) {
        while (thisIterator < end() && *it > *thisIterator) {
            thisIterator++;
        }
        if (thisIterator >= end() || *it != *thisIterator) {
            thisIterator = insert(thisIterator, *it);
        }
    }
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

class DocSetHitCollector {
    private:
        DocSet* docset;
    public:
        DocSetHitCollector(DocSet* docset) {
            this->docset = docset;
        }
        // This uses the Java/CNI ABI to perform callbacks. Collect is in slot 9.
        virtual void vtable_slot1() {}
        virtual void vtable_slot2() {}
        virtual void vtable_slot3() {}
        virtual void vtable_slot4() {}
        virtual void vtable_slot5() {}
        virtual void vtable_slot6() {}
        virtual void vtable_slot7() {}
        virtual void vtable_slot8() {}
        virtual void aka_collect(jint luceneId, jfloat score) {
            this->docset->push_back(luceneId);
        }
        virtual ~DocSetHitCollector() {}
};

extern "C"
fwPtr DocSet_fromQuery(lucene::search::Searcher* searcher, lucene::search::Query* query, IntegerList* mapping) {
    fwPtr docset = DocSet_create();
    DocSetHitCollector resultCollector(pDS(docset));
    searcher->search(query, (lucene::search::HitCollector*) &resultCollector);
    pDS(docset)->map(mapping);
    return docset;
}



/****************************************************************************
* TermDocs::read is called using fake int arrays.
* The one reason for doing so, is to lay our hands directly
* on the C/Java int[], instead of using a slow Python list of integer objects.
****************************************************************************/

#define TERMDOCS_READ_BUFF_SIZE 32

fwPtr DocSet::forTerm(lucene::index::IndexReader *reader, char* fieldname, char* term, IntegerList* mapping) {
    jintArray documents = JvNewIntArray(TERMDOCS_READ_BUFF_SIZE);
    jintArray ignored = JvNewIntArray(TERMDOCS_READ_BUFF_SIZE);
    fwPtr docset = DocSet_create();
    DocSet* docs = pDS(docset);
    lucene::index::TermEnum *termEnum = reader->terms(
        new lucene::index::Term(JvNewStringUTF(fieldname), JvNewStringUTF(term)));
    int freq = termEnum->docFreq();
    docs->reserve(freq); // <<== this really speeds up: from 3.1/3.2 => 2.6/2.7 seconds.
    lucene::index::TermDocs *termDocs = reader->termDocs();
    termDocs->seek(termEnum);
    int count = 0;
    count = termDocs->read(documents, ignored);
    docs->append((doc_t*) elements(documents), count);
    // read does not read all segments, we must check ourselves
    while (count < freq) {
        int additional = termDocs->read(documents, ignored);
        if (!additional)
            break;
        docs->append((doc_t*) elements(documents), additional);
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
