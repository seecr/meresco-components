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
#ifndef __trie__h__
#define __trie__h__

#include <glib.h>
#include "fwpool.h"
#include "stringpool.h"

#include <vector>

typedef guint32 stringNr;


typedef struct {
    void (*addValue)(fwPtr self, guint32 value, stringNr term, StringPool* pool);
    guint32 (*getValue)(fwPtr self, char* term, StringPool* pool);
    void (*getValues)(fwPtr self, char *prefix, std::vector<guint32>* result,  int caseSensitive);
    void (*free)(fwPtr self);
    void (*printit)(fwPtr self, int indent, StringPool* pool);
} INode;

extern guint32 fwValueNone;
inline INode* interface(fwPtr self);

extern "C" {
    void trie_init(void);
    fwPtr TrieNode_create(guint32 value);
    void TrieNode_free(fwPtr self);
    void TrieNode_addValue(fwPtr self, guint32 value, stringNr term, StringPool* pool);
    guint32 TrieNode_getValue(fwPtr self, char* term, StringPool* pool);
    void TrieNode_getValues(fwPtr self, char* prefix, std::vector<guint32>* result, int caseSensitive);
    int TrieNode_memory(void);
    void TrieNode_printit(fwPtr self, int indent, StringPool* pool);
    int measureall(void);
    void nodecount(void);
    inline int isNone(fwPtr ptr) { return ptr.ptr == fwNONE.ptr; }
}

#endif

