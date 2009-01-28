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
}

#ifndef __docset_h__
#define __docset_h__


class DocSet : public std::vector<doc_t> {
    public:
        fwString _term;
    protected:
        DocSet(size_t n): std::vector<doc_t>(n, 0) {}
    public:
        DocSet(): _term(fwStringNone) {};
        int     combinedCardinality      (DocSet* rhs);
        int     combinedCardinalitySearch(DocSet* longer);
        DocSet* intersect                (DocSet* rhs);
        void    append                   (doc_t* docarray, int count);
        void    setTerm                  (char* term);
        void    setTerm                  (JString* term);
        char*   term                     (void);
        void    remove                   (guint32 doc);
        void    map                      (IntegerList* mapping);
        static DocSet* fromTermDocs      (JObject* termDocs, int freq, JString* term, IntegerList* mapping);
};

extern "C" {
    DocSet* DocSet_create                    (void);
    DocSet* DocSet_forTesting                (int size);
    void    DocSet_add                       (DocSet* docset, guint32 doc);
    void    DocSet_remove                    (DocSet* docset, guint32 doc);
    guint32 DocSet_get                       (DocSet* docset, int i);
    int     DocSet_len                       (DocSet* docset);
    void    DocSet_setTerm                   (DocSet* docset, char* term);
    char*   DocSet_term                      (DocSet* docset);
    int     DocSet_combinedCardinality       (DocSet* docset, DocSet* rhs);
    int     DocSet_combinedCardinalitySearch (DocSet* docset, DocSet* rhs);
    DocSet* DocSet_intersect                 (DocSet* docset, DocSet* rhs);
    DocSet* DocSet_fromQuery                 (PyJObject* psearcher, PyJObject* pquery, IntegerList* mapping);
    DocSet* DocSet_fromTermDocs              (PyJObject* termDocs, int freq, char* term, IntegerList* mapping);
    void    DocSet_delete                    (DocSet* docset);
}


#endif

