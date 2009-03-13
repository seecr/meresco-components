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

extern "C" {
    #include "fwpool.h"
}

#ifndef __docset_h__
#define __docset_h__

class OnResult {
    public:
        virtual void operator () (guint32 docId) = 0;
};

class DocSet : public std::vector<doc_t> {
    public:
        guint32 _termOffset;
        DocSet(size_t n): std::vector<doc_t>(n, 0) {}
    public:
        DocSet(): _termOffset(0xFFFFFFFF) {};
        int     contains                 (guint32 docId);
        int     combinedCardinality      (DocSet* rhs);
        int     combinedCardinalitySearch(DocSet* longer);
        fwPtr   intersect                (fwPtr rhs);
        void    append                   (doc_t* docarray, int count);
        void    remove                   (guint32 doc);
        void    map                      (IntegerList* mapping);
        static  fwPtr fromTermDocs       (JObject* termDocs, int freq, IntegerList* mapping);
        void    setTermOffset            (guint32 offset);
};

static int x = pool_init();
extern fwPool _docsetPool;

inline DocSet* pDS(fwPtr ds) {
    void* p = Pool_get(_docsetPool, ds);
    return (DocSet*) p;
}

extern "C" {
    fwPtr   DocSet_create                    (int size);
    fwPtr   DocSet_forTesting                (int size);
    int     DocSet_contains                  (fwPtr docSet, guint32 docId);
    void    DocSet_add                       (fwPtr docset, guint32 doc);
    void    DocSet_remove                    (fwPtr docset, guint32 doc);
    guint32 DocSet_get                       (fwPtr docset, int i);
    int     DocSet_len                       (fwPtr docset);
    int     DocSet_combinedCardinality       (fwPtr docset, fwPtr rhs);
    int     DocSet_combinedCardinalitySearch (fwPtr docset, fwPtr rhs);
    fwPtr   DocSet_intersect                 (fwPtr docset, fwPtr rhs);
    fwPtr   DocSet_fromQuery                 (PyJObject* psearcher, PyJObject* pquery, IntegerList* mapping);
    fwPtr   DocSet_fromTermDocs              (PyJObject* termDocs, int freq, IntegerList* mapping);
    void    DocSet_delete                    (fwPtr docset);
}

#define SWITCHPOINT 10 // for random docsset, this is the trippoint

template <class ForwardIterator>
void intersect_generic(
        ForwardIterator lhs_from, ForwardIterator lhs_till,
        ForwardIterator rhs_from, ForwardIterator rhs_till,
        OnResult& onresult) {
    if ( lhs_till - lhs_from == 0 )
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
            onresult(*lhs_from);
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
            onresult(*(lhs_till-1));
            lhs_till--;
            rhs_till--;
        }
        // Switch to Zipper, optimization
        size_t lhs_size = lhs_till - lhs_from;
        size_t rhs_size = rhs_till - rhs_from;
        if ( (lhs_size < rhs_size * SWITCHPOINT) && (rhs_size < lhs_size * SWITCHPOINT) ) {
            ForwardIterator lhs = lhs_from; // Reassign slow iterator to faster one (pointer)
            ForwardIterator rhs = rhs_from;
            guint32 old_lhs = *lhs_till; // save old values before poking, jekkerdedekkie!
            guint32 old_rhs = *rhs_till;
            *lhs_till = 0xFFFFFFFF; // jekkerdedekkie!
            *rhs_till = 0xFFFFFFFF;
            while ( *lhs < 0xFFFFFFFF && *rhs < 0xFFFFFFFF ) {
                if ( *lhs == *rhs ) onresult(*lhs);
                while ( *++rhs < *lhs );
                if ( *lhs == *rhs ) onresult(*rhs);
                while ( *++lhs < *rhs );
            }
            *lhs_till = old_lhs; // restore old values, jekkerdedekkie!
            *rhs_till = old_rhs;
            return;
        }
    }
}

#endif
