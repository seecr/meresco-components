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
#include <stdio.h>
#include <stdlib.h>
#include <glib.h>
#include <string.h>
#include <ctype.h>

#include <vector>

extern "C" {
#include "trie_c.h"
#include "fwpool.h"
#include "fwstring.h"
}

void TrieNode_init(void);
void LeafNode_init(void);
void StringNode_init(void);

void trie_init(void) {
    pool_init();
    TrieNode_init();
    LeafNode_init();
    StringNode_init();
}

guint32 fwValueNone;

extern INode ITrieNode;
extern INode ILeafNode;
extern INode IStringNode;

enum _nodetypes { TRIE, LEAF, STRING };
INode* nodeTypes[4] = { &ITrieNode, &ILeafNode, &IStringNode, 0 };

inline INode* interface(fwPtr node) {
    return nodeTypes[node.type];
}

inline int isLeaf(fwPtr ptr) {
    return ptr.type == LEAF;
}

inline int isString(fwPtr ptr) {
    return ptr.type == STRING;
}

/************************************* Trie Node *****************************/
#define ALPHABET_IN_BITS 2

typedef struct {
    guint32 value;       /* 4 bytes */
    fwPtr child[0x01<<ALPHABET_IN_BITS];
}  TrieNodeState ;

guint32 TrieNode_getValue(fwPtr self, char* term);
void TrieNode_addValue(fwPtr self, guint32 value, fwString term);
void TrieNode_getValues(fwPtr self, char *prefix, std::vector<guint32>* result, int caseSensitive);
void TrieNode_free(fwPtr self);
void TrieNode_printit(fwPtr self, int indent);

INode ITrieNode = { /* implements INode */
    TrieNode_addValue,
    TrieNode_getValue,
    TrieNode_getValues,
    TrieNode_free,
    TrieNode_printit
};

fwPool _trieNodePool;

inline TrieNodeState* TrieNode_state(fwPtr self) {
    return (TrieNodeState*) Pool_get(_trieNodePool, self);
}

void TrieNode_init() {
    _trieNodePool = Pool_create(TRIE, sizeof(TrieNodeState), 64);
    fwValueNone = 0xFFFFFFFF;
}

int TrieNode_memory(void) {
    return Pool_memory(_trieNodePool);
}

fwPtr TrieNode_create(guint32 value) {
    fwPtr newOne = Pool_new(_trieNodePool);
    TrieNodeState *node = TrieNode_state(newOne);
    int i;
    for (i=0; i< (0x01<<ALPHABET_IN_BITS); i++) {
        node->child[i] = fwNONE;
    }
    node->value = value;
    return newOne;
}

fwPtr LeafNode_create(guint32 value);
fwPtr StringNode_create(guint32 value, fwString string);
inline guint32 LeafNode_getValue(fwPtr self, char* term);
inline guint32 StringNode_getValue(fwPtr self, char* term);
inline fwString StringNode_getString(fwPtr self);

typedef struct {
    fwPtr parent;
    unsigned char letter;
    fwPtr child;
} Link;

typedef enum { DoNotCreate, Create } CreateFlag;

Link TrieNode__findLink(fwPtr parent, unsigned char character, CreateFlag create) {
    Link result = {parent, 0, fwNONE };
    unsigned char letters[8/ALPHABET_IN_BITS] = {
        character >> 6 & 0x03,
        character >> 4 & 0x03,
        character >> 2 & 0x03,
        character & 0x03
    };
    int i;
    for (i = 0; i < 8/ALPHABET_IN_BITS-1; i++) {
        result.letter = letters[i];
        result.child = TrieNode_state(result.parent)->child[result.letter];
        if (isNone(result.child)) {
            if (create) {
                result.child = TrieNode_create(fwValueNone);
                TrieNode_state(result.parent)->child[result.letter] = result.child;
            } else {
                return result;
            }
        }
        result.parent = result.child;
    }
    result.letter = letters[8/ALPHABET_IN_BITS-1];
    result.child = TrieNode_state(result.parent)->child[result.letter];
    return result;
}

guint32 TrieNode_getValue(fwPtr self, char* term) {
    if (*term == '\0') {
        return TrieNode_state(self)->value;
    }
    Link link = TrieNode__findLink(self, term[0], DoNotCreate);
    if (isNone(link.child)) {
        return fwValueNone;
    }
    return interface(link.child)->getValue(link.child, ++term);
}

void TrieNode_getValues(fwPtr self, char* prefix, std::vector<guint32>* result, int caseSensitive) {
    char character;
    if (*prefix == '\0') {
        guint32 value = TrieNode_state(self)->value;
        if (value != fwValueNone) {
            result->push_back(value);
        }
        int i;
        fwPtr child;
        for (i = 0; i < 0x01<<ALPHABET_IN_BITS; i++) {
            child = TrieNode_state(self)->child[i];
            if (! isNone(child)) {
                interface(child)->getValues(child, prefix, result, caseSensitive);
            }
        }
        return;
    }

    character = prefix[0];
    Link link = TrieNode__findLink(self, character, DoNotCreate);

    prefix++;

    if (! isNone(link.child)) {
        interface(link.child)->getValues(link.child, prefix, result, caseSensitive);
    }

    if (! caseSensitive  && isalpha(character)) {
        if (islower(character)) {
            character = toupper(character);
        } else {
            character = tolower(character);
        }
        link = TrieNode__findLink(self, character, DoNotCreate);

        if (! isNone(link.child)) {
            interface(link.child)->getValues(link.child, prefix, result, caseSensitive);
        }
    }

}

void TrieNode_addValue(fwPtr self, guint32 value, fwString term) {
    if (*fwString_get(term) == '\0') {
        TrieNode_state(self)->value = value;
        return;
    }

    Link link = TrieNode__findLink(self, fwString_get(term)[0], Create);

    /********** Code to decide about what node type to create is ONLY here *******************/
    fwPtr child = link.child;
    if (isNone(child)) {
        if (fwString_get(term)[1] == '\0') {
            child = LeafNode_create(value);
        } else {
            child = StringNode_create(fwValueNone, term);
        }
        TrieNode_state(link.parent)->child[link.letter] = child;
    } else {
        if (isLeaf(child)) {
            guint32 value = LeafNode_getValue(child, (char*) "");
            interface(child)->free(child);
            child = TrieNode_create(value);
            TrieNode_state(link.parent)->child[link.letter] = child;
        } else if (isString(child)) {
            fwString string = StringNode_getString(child);
            guint32 value = StringNode_getValue(child, fwString_get(string));
            interface(child)->free(child);
            child = TrieNode_create(fwValueNone);
            TrieNode_addValue(child, value, string);
            TrieNode_state(link.parent)->child[link.letter] = child;
        }
    }
    /*************************************************************************************************/

    interface(child)->addValue(child, value, ++term); /* ++term?!? dit gaat wel heel toevallig goed !!!
    het moet zijn: fwString_strdup(term, 1) of zo iets */

}

void TrieNode_free(fwPtr self) {
    //printf("TrieNode_free - Not yet implemented!\n");
}

void TrieNode_printit(fwPtr self, int indent) {
    TrieNodeState* me = TrieNode_state(self);
    int i;
    fwPtr child;

    for(i=0; i<indent; i++) {
        printf(" ");
    }
    if ( me->value == fwValueNone )
        printf("%u: -\n", self.ptr);
    else
        printf("%u %u\n", self.ptr, me->value);
    for(i=0; i<0x01<<ALPHABET_IN_BITS; i++) {
        child = me->child[i];
        if (!isNone(child)) {
            interface(child)->printit(child, indent + 1);
        }
    }
}




/*************************************************** LeafNodeState ************/

typedef struct {
    guint32 value;       /* 4 bytes */
} LeafNodeState;

guint32 LeafNode_getValue(fwPtr self, char* term);
void LeafNode_getValues(fwPtr self, char *prefix, std::vector<guint32>* result, int caseSensitive);
inline void LeafNode_addValue(fwPtr self, guint32 value, fwString term);
void LeafNode_free(fwPtr self);
void LeafNode_printit(fwPtr self, int indent);

INode ILeafNode = {
    LeafNode_addValue,
    LeafNode_getValue,
    LeafNode_getValues,
    LeafNode_free,
    LeafNode_printit
};

fwPool _leafNodePool;

inline LeafNodeState* LeafNode_state(fwPtr self) {
    return (LeafNodeState*) Pool_get(_leafNodePool, self);
}
void LeafNode_init() {
    _leafNodePool = Pool_create(LEAF, sizeof(LeafNodeState), 64);
}

int LeafNode_memory(void) {
    return Pool_memory(_leafNodePool);
}

fwPtr LeafNode_create(guint32 value) {
    fwPtr newOne = Pool_new(_leafNodePool);
    LeafNodeState *node = LeafNode_state(newOne);
    node->value = value;
    return newOne;
}

inline void LeafNode_addValue(fwPtr self, guint32 value, fwString term) {
    /*if (*term != '\0')
        printf("LeafNodeState: term not zero: %s.\n", term);*/
    LeafNode_state(self)->value = value;
}

inline guint32 LeafNode_getValue(fwPtr self, char* term) {
    if (*term == '\0')
        return LeafNode_state(self)->value;
    return fwValueNone;
}

void LeafNode_getValues(fwPtr self, char *prefix, std::vector<guint32>* result, int caseSensitive) {
    if (*prefix == '\0') {
        result->push_back(LeafNode_state(self)->value);
    }
}

void LeafNode_free(fwPtr self) {
    Pool_free(_leafNodePool, self);
}

void LeafNode_printit(fwPtr self, int indent) {
    int i;
    for(i=0;i<indent; i++) {
        printf(" ");
    }
    printf("%u Leaf %d\n", self.ptr, LeafNode_state(self)->value);
}

/************************************************* StringNodeState ************/

inline void StringNode_addValue(fwPtr node, guint32 value, fwString term);
inline guint32 StringNode_getValue(fwPtr node, char* term);
void StringNode_getValues(fwPtr node, char* prefix, std::vector<guint32>* result, int caseSensitive);
void StringNode_free(fwPtr node);
void StringNode_printit(fwPtr node, int indent);

INode IStringNode = {
    StringNode_addValue,
    StringNode_getValue,
    StringNode_getValues,
    StringNode_free,
    StringNode_printit};

typedef struct {
    guint32 value;
    fwString aString;
} StringNodeState;

fwPool _stringNodePool;

inline StringNodeState* StringNode_state(fwPtr self) {
    return (StringNodeState*) Pool_get(_stringNodePool, self);
}

void StringNode_init() {
    _stringNodePool = Pool_create(STRING, sizeof(StringNodeState), 64);
}

fwPtr StringNode_create(guint32 value, fwString string) {
    fwPtr newOne = Pool_new(_stringNodePool);
    StringNodeState* node = StringNode_state(newOne);
    node->value = value;
    node->aString = string;
    return newOne;
}

inline void StringNode_addValue(fwPtr self, guint32 value, fwString term) {
    StringNode_state(self)->value = value;
    StringNode_state(self)->aString = term;
}

inline guint32 StringNode_getValue(fwPtr self, char* term) {
    char* string = fwString_get(StringNode_state(self)->aString);
    if (strcmp((char*) term, (char *)string) == 0) {
        return StringNode_state(self)->value;
    }
    return fwValueNone;
}

void StringNode_getValues(fwPtr self, char *prefix, std::vector<guint32>* result, int caseSensitive) {
    char *aString = fwString_get(StringNode_state(self)->aString);
    if (caseSensitive) {
        while (*aString != '\0' && *prefix != '\0' && *aString++ == *prefix++)
            ;
    } else {
        while (*aString != '\0' && *prefix != '\0' && tolower(*aString++) == tolower(*prefix++))
            ;
    }

    if (*prefix == '\0') {
        result->push_back(StringNode_state(self)->value);
    }
}

void StringNode_free(fwPtr self) {
    Pool_free(_stringNodePool, self);
}

inline fwString StringNode_getString(fwPtr self) {
    return StringNode_state(self)->aString;
}

void StringNode_printit(fwPtr self, int indent) {
    int i;
    for(i=0;i<indent; i++) {
        printf(" ");
    }
    printf("%u String: %d: %s\n", self.ptr, StringNode_state(self)->value, fwString_get(StringNode_state(self)->aString));
}

/************** fwTrie ******************/


void nodecount() {
    printf("Trie node memory (%d elements) = %.2f MB\n", Pool_count(_trieNodePool), Pool_memory(_trieNodePool)/1024.0/1024.0);
    printf("Leaf node memory (%d elements) = %.2f MB\n", Pool_count(_leafNodePool), Pool_memory(_leafNodePool)/1024.0/1024.0);
    printf("String node memory (%d elements) = %.2f MB\n", Pool_count(_stringNodePool), Pool_memory(_stringNodePool)/1024.0/1024.0);
}
