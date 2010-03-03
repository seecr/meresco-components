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

#ifndef __triedict_h__
#define __triedict_h__

#include <string>
#include <glib.h>
#include "stringpool.h"
#include "integerlist.h"

extern "C" {
    #include "fwpool.h"
}

typedef guint32 termid;
typedef guint32 value;

class TrieDict {
    private:
        fwPtr termIndex;
        StringPool* termPool;
    public:
        TrieDict(int uselocalpool = 0);
        ~TrieDict(void);
        int                measure(void) {
            return sizeof(this); // excluding global termPool and TrieNodes, use TrieNode_measureall()
        }
        termid             add(char* term, value value);
        value              getValue(char* term);
        void               valuesForPrefix(char* prefix, guint32 maxResults, IntegerList* result);
        char*              getTerm(termid termId);
        void               printit();
        void               nodecount(void);
};
extern "C" {
    termid                 TrieDict_add(TrieDict*, char* term, value value);
    value                  TrieDict_getValue(TrieDict*, char* term);
    TrieDict*              TrieDict_create(int uselocalpool = 0);
    void                   TrieDict_delete(TrieDict*);
    void                   TrieDict_valuesForPrefix(TrieDict* self, char* prefix, guint32 maxResults, IntegerList* result);
    int                    TrieDict_measureall(void);
    void                   TrieDict_printit(TrieDict*);
}
#endif
