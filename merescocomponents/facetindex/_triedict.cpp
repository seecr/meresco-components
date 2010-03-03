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

#include "triedict.h"
#include "trie_c.h"

StringPool globalStringPool;

int TrieDict_measureall(void) {
    return globalStringPool.measure() + measureall() /* from TrieNode */;
}

TrieDict::TrieDict(int uselocalpool): termPool(&globalStringPool) {
    if (uselocalpool)
        this->termPool = new StringPool();
    termIndex = TrieNode_create(fwValueNone);
}

TrieDict::~TrieDict() {
    TrieNode_free(termIndex);
    if (termPool != &globalStringPool)
        delete termPool;
}

termid TrieDict::add(char* term, value value) {
    termid termId = this->termPool->add(term);
    TrieNode_addValue(termIndex, value, termId, this->termPool);
    return termId;
}

value TrieDict::getValue(char* term) {
    value value = TrieNode_getValue(termIndex, term, this->termPool);
    if ( value == fwValueNone )
        return 0xFFFFFFFF;
    return value;
}

void TrieDict::valuesForPrefix(char* prefix, guint32 maxResults, IntegerList* result) {
    TrieNode_getValues(termIndex, prefix, maxResults, result, this->termPool);
}

char* TrieDict::getTerm(termid termId) {
    return this->termPool->get(termId);
}

void TrieDict::printit() {
    TrieNode_printit(termIndex, 0, termPool);
}

void TrieDict::nodecount(void) {
    nodecount();
}


// ########### C Wrappers #############
guint32 TrieDict_add(TrieDict* trieDict, char* term, value value) {
    return trieDict->add(term, value);
}

value TrieDict_getValue(TrieDict* trieDict, char* term) {
    return trieDict->getValue(term);
}

TrieDict* TrieDict_create(int uselocalpool) {
    return new TrieDict(uselocalpool);
}

void TrieDict_delete(TrieDict* trieDict) {
    delete trieDict;
}

void TrieDict_valuesForPrefix(TrieDict* self, char* prefix, guint32 maxResults, IntegerList* result) {
    self->valuesForPrefix(prefix, maxResults, result);
}

void TrieDict_printit(TrieDict* trieDict) {
    trieDict->printit();
}

