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
#include <vector>
#include "facetindex.h"
#include "integerlist.h"

extern "C" {
    #include "fwstring.h"
    #include "fwpool.h"
}

#ifndef __docset_h__
#define __docset_h__

class DocSet : public std::vector<doc_t> {
    public:
        guint32 _termOffset;
        DocSet(size_t n): std::vector<doc_t>(n, 0) {}
    public:
        DocSet(): _termOffset(0xFFFFFFFF) {};
        int     combinedCardinality      (DocSet* rhs);
        int     combinedCardinalitySearch(DocSet* longer);
        fwPtr   intersect                (DocSet* rhs);
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


#endif

