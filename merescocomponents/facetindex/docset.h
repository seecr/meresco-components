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
#include <vector>
#include <iterator>
#include "facetindex.h"
#include "integerlist.h"

#include <gcj/cni.h>
#include "org/apache/lucene/search/Query.h"
#include "org/apache/lucene/search/IndexSearcher.h"
#include "org/apache/lucene/index/IndexReader.h"

using namespace org::apache;

extern "C" {
    #include "fwpool.h"
}

#ifndef __docset_h__
#define __docset_h__

class OnResult {
    public:
        virtual void operator () (guint32 docId) = 0;
        virtual ~OnResult() {};
};

class DocSet : public std::vector<doc_t> {
    public:
        guint32 _termOffset;
        DocSet(size_t n): std::vector<doc_t>(n, 0) {}
        DocSet(): _termOffset(0xFFFFFFFF) {};
        int     measure                  (void) {
            return sizeof(this) + size() * sizeof(doc_t);
        }
        int     contains                 (guint32 docId);
        int     combinedCardinality      (DocSet* rhs);
        int     combinedCardinalitySearch(DocSet* longer);
        fwPtr   intersect                (fwPtr rhs);
        void    append                   (doc_t* docarray, int count);
        void    merge                    (DocSet* docSet);
        void    remove                   (guint32 doc);
        void    map                      (IntegerList* mapping);
        static  fwPtr forTerm            (lucene::index::IndexReader *reader, char* fieldname, char* term, IntegerList* mapping);
        void    setTermOffset            (guint32 offset);
};

static int x = pool_init();
extern fwPool _docsetPool;

inline DocSet* pDS(fwPtr ds) {
    return (DocSet*) Pool_get(_docsetPool, ds);
}

extern "C" {
    fwPtr   DocSet_create                    (int size);
    DocSet* DocSet_create2                   (void);
    DocSet* DocSet_from_param                (fwPtr docset);
    fwPtr   DocSet_forTesting                (int size);
    int     DocSet_measure                   (fwPtr docSet);
    int     DocSet_contains                  (fwPtr docSet, guint32 docId);
    void    DocSet_add                       (fwPtr docSet, guint32 doc);
    void    DocSet_merge                     (fwPtr docSet, fwPtr anotherDocSet);
    void    DocSet_remove                    (fwPtr docSet, guint32 doc);
    guint32 DocSet_get                       (fwPtr docSet, int i);
    int     DocSet_len                       (fwPtr docSet);
    int     DocSet_combinedCardinality       (fwPtr docSet, fwPtr rhs);
    int     DocSet_combinedCardinalitySearch (fwPtr docSet, fwPtr rhs);
    fwPtr   DocSet_intersect                 (fwPtr docSet, fwPtr rhs);
    fwPtr   DocSet_fromQuery                 (lucene::search::Searcher* searcher, lucene::search::Query* query, IntegerList* mapping);
    fwPtr   DocSet_forTerm                   (lucene::index::IndexReader*, char* fieldname, char* term, IntegerList* mapping);
    void    DocSet_delete                    (fwPtr docSet);
}



#define SWITCHPOINT 200 // for random docsset, this is the trippoint, experimentally

template <class ForwardIterator, class OutputIterator>
void intersect_generic(
        ForwardIterator lhs_from, ForwardIterator lhs_till,
        ForwardIterator rhs_from, ForwardIterator rhs_till,
        OutputIterator& result) {
    if ( lhs_till <= lhs_from || rhs_till <= rhs_from )
       return;
    while ( 1 ) {
        // Lowerbound pruning
        rhs_from = lower_bound(rhs_from, rhs_till, *lhs_from);
        if ( rhs_from >= rhs_till )
            return;
        lhs_from = lower_bound(lhs_from, lhs_till, *rhs_from);
        if ( lhs_from >= lhs_till )
            return;
        if ( *lhs_from == *rhs_from ) {
            *result++ = *lhs_from;
            lhs_from++;
            rhs_from++;
        }
        // Upperbound pruning optimization
        rhs_till = upper_bound(rhs_from, rhs_till, *(lhs_till-1));
        if ( rhs_till <= rhs_from )
            return;
        lhs_till = upper_bound(lhs_from, lhs_till, *(rhs_till-1));
        if ( lhs_till <= lhs_from )
            return;
        if ( *(lhs_till-1) == *(rhs_till-1) ) {
            *result++ = *(lhs_till-1);
            lhs_till--;
            rhs_till--;
        }
        // Switch to Zipper, optimization
        size_t lhs_size = lhs_till - lhs_from;
        size_t rhs_size = rhs_till - rhs_from;
        if ( (lhs_size <= rhs_size * SWITCHPOINT) && (rhs_size <= lhs_size * SWITCHPOINT) ) {
            ForwardIterator lhs = lhs_from; // Reassign slow iterator to faster one (pointer)
            ForwardIterator rhs = rhs_from;
            while ( 1 ) {
                while ( rhs < rhs_till && *rhs < *lhs ) rhs++;
                if ( rhs >= rhs_till )
                    return;
                while ( lhs < lhs_till && *lhs < *rhs ) lhs++;
                if ( lhs >= lhs_till )
                    return;
                if ( *lhs == *rhs ) {
                    *result++ = *lhs;
                    lhs++;
                    rhs++;
                }
            }
        }
    }
}

#endif
