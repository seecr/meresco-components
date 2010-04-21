/* begin license *
 *
 *     Meresco Components are components to build searchengines, repositories
 *     and archives, based on Meresco Core.
 *     Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
 *     Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
 *        http://www.kennisnetictopschool.nl
 *     Copyright (C) 2009 Delft University of Technology http://www.tudelft.nl
 *     Copyright (C) 2009 Tilburg University http://www.uvt.nl
 *     Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
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

#include "stringpool.h"
#include "trie_c.h"

StringPool::StringPool() {
    trie_init();
    termIndex = TrieNode_create(fwValueNone);
}

StringPool::~StringPool() {
    TrieNode_free(termIndex);
}

termid StringPool::add(char* term) {
    termid termId = TrieNode_getValue(termIndex, term, this);
    if ( termId == fwValueNone ) {
        termId = this->allterms.size();
        this->allterms.append(term);
        this->allterms.push_back('\0');
        TrieNode_addValue(termIndex, termId, termId, this);
    }
    return termId;
}

char* StringPool::get(termid termId) {
    if (termId == 0xFFFFFFFF) {
        return "";
    }
    return &this->allterms[termId];
}
