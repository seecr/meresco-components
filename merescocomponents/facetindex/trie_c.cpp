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
}

void TrieNode_init(void);
void LeafNode_init(void);
void StringNode_init(void);
void ListNode_init(void);

void trie_init(void) {
    pool_init();
    TrieNode_init();
    LeafNode_init();
    StringNode_init();
    ListNode_init();
}

guint32 fwValueNone;

extern INode ITrieNode;
extern INode ILeafNode;
extern INode IStringNode;
extern INode IListNode;

enum _nodetypes { TRIE, LEAF, STRING, LIST };
INode* nodeTypes[4] = { &ITrieNode, &ILeafNode, &IStringNode, &IListNode};

inline INode* interface(fwPtr node) {
    return nodeTypes[node.type];
}

inline int isLeaf(fwPtr ptr) {
    return ptr.type == LEAF;
}

inline int isString(fwPtr ptr) {
    return ptr.type == STRING;
}

inline int isList(fwPtr ptr) {
    return ptr.type == LIST;
}

/************** LISTNode ******************************/
inline void ListNode_addValue(fwPtr node, guint32 value, fwString term, char* (*getString)(fwString));
inline guint32 ListNode_getValue(fwPtr node, char* term, char* (*getString)(fwString));
void ListNode_getValues(fwPtr node, char* prefix, std::vector<guint32>* result, int caseSensitive);
void ListNode_free(fwPtr node);
void ListNode_printit(fwPtr node, int indent, char* (*getString)(fwString));

INode IListNode = {
    ListNode_addValue,
    ListNode_getValue,
    ListNode_getValues,
    ListNode_free,
    ListNode_printit
};

const unsigned int LISTSIZE = 100;
/*
LEAF+STRING+LIST+TRIE (NO move-to-front optimization on LISTNode)
LISTSIZE:  MEMORY: TIME inserts/getterm/getvalue (98568 words)
    1000: 1.15 MB: 1.5/0.5/1.4 s
     500: 1.18 MB: 1.3/0.5/1.1 s
     200: 1.23 MB: 1.1/0.6/0.9 s
     100: 1.30 MB: 1.0/0.5/0.7 s  <== seems to be an optimum
      50: 1.43 MB: 1.1/0.5/0.7 s
      20: 1.77 MB: 1.0/0.5/0.7 s
      10: 2.30 MB: 1.0/0.5/0.7 s

Improvement memory usages over raw Trie without ListNodes: 14.12/1.30 = 11x
*/

typedef struct {
    guint32 value;
    fwString aString;
    fwPtr next;
} ListItem;

typedef struct {
    guint32 value;
    guint32 size;
    fwPtr first;
} ListNodeState;

fwPool _listNodePool;
fwPool _listItemPool;

inline ListNodeState* ListNode_state(fwPtr self) {
    return (ListNodeState*) Pool_get(_listNodePool, self);
}

inline ListItem* ListItem_state(fwPtr self) {
    return (ListItem*) Pool_get(_listItemPool, self);
}

void ListNode_init() {
    _listNodePool = Pool_create(LIST, sizeof(ListNodeState),  5000);
    _listItemPool = Pool_create(0 /*NA*/, sizeof(ListItem), 100000);
}

fwPtr ListItem_create(guint32 value, fwString term) {
    fwPtr newOne = Pool_new(_listItemPool);
    ListItem* listitem = ListItem_state(newOne);
    listitem->value = value;
    listitem->aString = term;
    listitem->next = fwNONE;
    return newOne;
}

fwPtr ListNode_create(guint32 value) {
    fwPtr newOne = Pool_new(_listNodePool);
    ListNodeState* node = ListNode_state(newOne);
    node->value = value;
    node->size = 0;
    node->first = fwNONE;
    return newOne;
}

inline void ListNode_addValue(fwPtr self, guint32 value, fwString term, char* (*getString)(fwString)) {
    ListNodeState* me = ListNode_state(self);
    if ( me->size > LISTSIZE ) {
        printf("ListNode_addValue(): Ignoring new string '%s'\n", getString(term));
        return;
    }
    if ( isNone( me->first ) ) {
        me->first = ListItem_create(value, term);
        me->size++;
        return;
    }
    fwPtr last = me->first;
    fwPtr prev = last;
    while ( ! isNone(last) ) {
        prev = last;
        last = ListItem_state(last)->next;
    }
    fwPtr item = prev;
    fwPtr tmp =
        ListItem_create(
            value,
            term
        );
    ListItem_state(item)->next = tmp;
    me->size++;
}

inline guint32 ListNode_getValue(fwPtr self, char* term, char* (*getString)(fwString)) {
    ListNodeState* me = ListNode_state(self);
    if ( *term == '\0' ) {
        return me->value;
    }
    fwPtr last = me->first;
    while ( ! isNone(last) ) {
        ListItem* plast = ListItem_state(last);
        char* string = getString(plast->aString);
        if ( strcmp(term, string) == 0 ) {
            return plast->value;
        }
        last = plast->next;
    }
    return fwValueNone;
}

bool ListNode_hasRoom(fwPtr self) {
    return ListNode_state(self)->size < LISTSIZE;
}

void ListNode_addTo(fwPtr self, fwPtr other, char* (*getString)(fwString)) {
    ListNodeState* me = ListNode_state(self);
    fwPtr last = me->first;
    while ( ! isNone(last) ) {
        ListItem* plast = ListItem_state(last);
        interface(other)->addValue(other, plast->value, plast->aString, getString);
        last = ListItem_state(last)->next;
    }
}

void ListNode_getValues(fwPtr self, char *prefix, std::vector<guint32>* result, int caseSensitive) {
/*
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
*/
}

void ListNode_free(fwPtr self) {
    ListNodeState* me = ListNode_state(self);
    fwPtr last = me->first;
    fwPtr prev = last;
    while ( ! isNone(last) ) {
        prev = last;
        last = ListItem_state(last)->next;
        Pool_free(_listItemPool, prev);
    }
    Pool_free(_listNodePool, self);
}

void ListNode_printit(fwPtr self, int indent, char* (*getString)(fwString)) {
    ListNodeState* me = ListNode_state(self);
    for(int i=0;i<indent; i++) printf(" ");
    printf("%u List: %d elements.\n", self.ptr, me->size);
    fwPtr last = me->first;
    while ( ! isNone(last) ) {
        ListItem* plast = ListItem_state(last);
        for(int i=0;i<indent; i++) printf(" ");
        printf("  %s:%d\n", getString(plast->aString), plast->value);
        last = ListItem_state(last)->next;
    }
}


/************************************* Trie Node *****************************/
#define ALPHABET_IN_BITS 2

typedef struct {
    guint32 value;       /* 4 bytes */
    fwPtr child[0x01<<ALPHABET_IN_BITS];
}  TrieNodeState ;

guint32 TrieNode_getValue(fwPtr self, char* term);
void TrieNode_addValue(fwPtr self, guint32 value, fwString term, char* (*getString)(fwString));
void TrieNode_getValues(fwPtr self, char *prefix, std::vector<guint32>* result, int caseSensitive);
void TrieNode_free(fwPtr self);
void TrieNode_printit(fwPtr self, int indent, char* (*getString)(fwString));

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
    _trieNodePool = Pool_create(TRIE, sizeof(TrieNodeState), 5000);
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
inline guint32 LeafNode_getValue(fwPtr self, char* term, char* (*getString)(fwString));
inline guint32 StringNode_getValue(fwPtr self, char* term, char* (*getString)(fwString));
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

guint32 TrieNode_getValue(fwPtr self, char* term, char* (*getString)(fwString)) {

    if ( ! getString ) { getString = fwString_get; }

    if (*term == '\0') {
        return TrieNode_state(self)->value;
    }
    Link link = TrieNode__findLink(self, term[0], DoNotCreate);
    if (isNone(link.child)) {
        return fwValueNone;
    }
    return interface(link.child)->getValue(link.child, ++term, getString);
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

void TrieNode_addValue(fwPtr self, guint32 value, fwString term, char* (*getString)(fwString)) {
    if ( ! getString ) { getString = fwString_get; }

    if (*getString(term) == '\0') {
        TrieNode_state(self)->value = value;
        return;
    }

    Link link = TrieNode__findLink(self, getString(term)[0], Create);

    /********** Code to decide about what node type to create is ONLY here *******************/
    fwPtr child = link.child;
    if (isNone(child)) {
        if (getString(term)[1] == '\0') {
            child = LeafNode_create(value);
        } else {
            child = StringNode_create(fwValueNone, term);
        }
    } else {
        if (isLeaf(child)) {
            guint32 value = interface(child)->getValue(child, (char*) "", getString);
            interface(child)->free(child);
            child = ListNode_create(value);
        } else if (isString(child)) {
            fwString string = StringNode_getString(child);
            guint32 value = interface(child)->getValue(child, getString(string), getString);
            interface(child)->free(child);
            child = ListNode_create(fwValueNone);
            ListNode_addValue(child, value, string, getString);
        }
        else if (isList(child)) {
            if ( ! ListNode_hasRoom(child) ) {
                guint32 value = ListNode_getValue(child, (char*) "", getString);
                fwPtr newNode = TrieNode_create(value);
                ListNode_addTo(child, newNode, getString);
                interface(child)->free(child);
                child = newNode;
            }
        }
    }
    /*************************************************************************************************/

    TrieNode_state(link.parent)->child[link.letter] = child;
    interface(child)->addValue(child, value, ++term, getString); /* ++term?!? dit gaat wel heel toevallig goed !!!
    het moet zijn: fwString_strdup(term, 1) of zo iets */

}

void TrieNode_free(fwPtr self) {
    TrieNodeState* me = TrieNode_state(self);
    for( int i = 0; i < 0x01<<ALPHABET_IN_BITS; i++ ) {
        fwPtr child = me->child[i];
        if ( ! isNone(child) ) {
            interface(child)->free(child);
        }
    }
    Pool_free(_trieNodePool, self);
}

void TrieNode_printit(fwPtr self, int indent, char* (*getString)(fwString)) {

    if ( ! getString ) getString = fwString_get;

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
            interface(child)->printit(child, indent + 1, getString);
        }
    }
}




/*************************************************** LeafNodeState ************/

typedef struct {
    guint32 value;       /* 4 bytes */
} LeafNodeState;

guint32 LeafNode_getValue(fwPtr self, char* term, char* (*getString)(fwString));
void LeafNode_getValues(fwPtr self, char *prefix, std::vector<guint32>* result, int caseSensitive);
inline void LeafNode_addValue(fwPtr self, guint32 value, fwString term, char* (*getString)(fwString));
void LeafNode_free(fwPtr self);
void LeafNode_printit(fwPtr self, int indent, char* (*getString)(fwString));

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

inline void LeafNode_addValue(fwPtr self, guint32 value, fwString term, char* (*getString)(fwString)) {
    /*if (*term != '\0')
        printf("LeafNodeState: term not zero: %s.\n", term);*/
    LeafNode_state(self)->value = value;
}

inline guint32 LeafNode_getValue(fwPtr self, char* term, char* (*getString)(fwString)) {
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

void LeafNode_printit(fwPtr self, int indent, char* (*getString)(fwString)) {
    int i;
    for(i=0;i<indent; i++) {
        printf(" ");
    }
    printf("%u Leaf %d\n", self.ptr, LeafNode_state(self)->value);
}

/************************************************* StringNodeState ************/

inline void StringNode_addValue(fwPtr node, guint32 value, fwString term, char* (*getString)(fwString));
inline guint32 StringNode_getValue(fwPtr node, char* term, char* (*getString)(fwString));
void StringNode_getValues(fwPtr node, char* prefix, std::vector<guint32>* result, int caseSensitive);
void StringNode_free(fwPtr node);
void StringNode_printit(fwPtr node, int indent, char* (*getString)(fwString));

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

inline void StringNode_addValue(fwPtr self, guint32 value, fwString term, char* (*getString)(fwString)) {
    StringNode_state(self)->value = value;
    StringNode_state(self)->aString = term;
}

inline guint32 StringNode_getValue(fwPtr self, char* term, char* (*getString)(fwString)) {
    char* string = getString(StringNode_state(self)->aString);
    if (strcmp((char*) term, (char *)string) == 0) {
        return StringNode_state(self)->value;
    }
    return fwValueNone;
}

void StringNode_getValues(fwPtr self, char *prefix, std::vector<guint32>* result, int caseSensitive) {
/*    char *aString = fwString_get(StringNode_state(self)->aString);
    if (caseSensitive) {
        while (*aString != '\0' && *prefix != '\0' && *aString++ == *prefix++)
            ;
    } else {
        while (*aString != '\0' && *prefix != '\0' && tolower(*aString++) == tolower(*prefix++))
            ;
    }

    if (*prefix == '\0') {
        result->push_back(StringNode_state(self)->value);
    }*/
}

void StringNode_free(fwPtr self) {
    Pool_free(_stringNodePool, self);
}

inline fwString StringNode_getString(fwPtr self) {
    return StringNode_state(self)->aString;
}

void StringNode_printit(fwPtr self, int indent, char* (*getString)(fwString)) {
    int i;
    for(i=0;i<indent; i++) {
        printf(" ");
    }
    printf("%u String: %d: %s\n", self.ptr, StringNode_state(self)->value, getString(StringNode_state(self)->aString));
}


/************** fwTrie ******************/


void nodecount() {
    int trieMemory = Pool_memory(_trieNodePool);
    int leafMemory = Pool_memory(_leafNodePool);
    int stringMemory = Pool_memory(_stringNodePool);
    int listMemory = Pool_memory(_listNodePool);
    int listItemMemory = Pool_memory(_listItemPool);
    int totalMemory = trieMemory+leafMemory+stringMemory+listMemory+listItemMemory;
    int trieCount = Pool_count(_trieNodePool);
    int leafCount = Pool_count(_leafNodePool);
    int stringCount = Pool_count(_stringNodePool);
    int listCount = Pool_count(_listNodePool);
    int listItemCount = Pool_count(_listItemPool);
    printf("===== Summary of Memory Used by Trie ======\n");
    printf("Maximum ListSize used: %d\n", LISTSIZE);
    printf("%d Trie nodes take %.2f MB (%d bytes/node).\n", trieCount, trieMemory/1024.0/1024.0, trieMemory/trieCount);
    printf("%d Leaf nodes take %.2f MB (%d bytes/node).\n", leafCount, leafMemory/1024.0/1024.0, leafMemory/leafCount);
    printf("%d String nodes take %.2f MB (%d bytes/node).\n", stringCount, stringMemory/1024.0/1024.0, stringMemory/stringCount);
    printf("%d List nodes take %.2f MB (%d bytes/node).\n", listCount, listMemory/1024.0/1024.0, listMemory/listCount);
    printf("%d ListItems take %.2f MB (%d bytes/item).\n", listItemCount, listItemMemory/1024.0/1024.0, listItemMemory/listItemCount);
    printf("Total memory used: %.2f MB.\n", totalMemory/1024.0/1024.0);
}


/*
LISTSIZE=16, ALPHABET_IN_BITS=2
Time for 98568 inserts: 1.0295009613 ( 832898 total length) ( 0.0104445759405 ms per insert)
30962 Trie nodes take 0.80 MB: 27 bytes/node
794 Leaf nodes take 0.00 MB: 5 bytes/node
1732 String nodes take 0.02 MB: 11 bytes/node
15351 List nodes take 2.42 MB: 165 bytes/node
48839 total nodes take 3.24 MB: 69 bytes/node

20
Time for 98568 inserts: 1.27293586731 ( 832898 total length) ( 0.0129142913249 ms per insert)
24316 Trie nodes take 0.53 MB: 23 bytes/node
549 Leaf nodes take 0.00 MB: 5 bytes/node
1289 String nodes take 0.01 MB: 10 bytes/node
13635 List nodes take 2.99 MB: 229 bytes/node
39789 total nodes take 3.54 MB: 93 bytes/node

22
Time for 98568 inserts: 1.13807606697 ( 832898 total length) ( 0.0115461008336 ms per insert)
22076 Trie nodes take 0.53 MB: 25 bytes/node
475 Leaf nodes take 0.00 MB: 4 bytes/node
1151 String nodes take 0.01 MB: 11 bytes/node
12966 List nodes take 3.27 MB: 264 bytes/node
36668 total nodes take 3.82 MB: 109 bytes/node

23
Time for 98568 inserts: 1.02449226379 ( 832898 total length) ( 0.0103937612998 ms per insert)
21128 Trie nodes take 0.53 MB: 26 bytes/node
441 Leaf nodes take 0.00 MB: 4 bytes/node
1094 String nodes take 0.01 MB: 7 bytes/node
12668 List nodes take 3.42 MB: 282 bytes/node
35331 total nodes take 3.96 MB: 117 bytes/node

24
Time for 98568 inserts: 0.915761709213 ( 832898 total length) ( 0.00929065933379 ms per insert)
20217 Trie nodes take 0.53 MB: 27 bytes/node
409 Leaf nodes take 0.00 MB: 4 bytes/node
1038 String nodes take 0.01 MB: 8 bytes/node
12390 List nodes take 2.37 MB: 200 bytes/node
34054 total nodes take 2.92 MB: 89 bytes/node

25
Time for 98568 inserts: 1.71824574471 ( 832898 total length) ( 0.0174320849029 ms per insert)
19321 Trie nodes take 0.53 MB: 28 bytes/node
385 Leaf nodes take 0.00 MB: 5 bytes/node
982 String nodes take 0.01 MB: 8 bytes/node
12104 List nodes take 2.47 MB: 213 bytes/node
32792 total nodes take 3.01 MB: 96 bytes/node


26
18599 Trie nodes take 0.36 MB: 20 bytes/node
365 Leaf nodes take 0.00 MB: 5 bytes/node
946 String nodes take 0.01 MB: 9 bytes/node
11873 List nodes take 2.56 MB: 226 bytes/node
31783 total nodes take 2.93 MB: 96 bytes/node


28
Time for 98568 inserts: 1.02911114693 ( 832898 total length) ( 0.0104406211643 ms per insert)
17573 Trie nodes take 0.36 MB: 21 bytes/node
340 Leaf nodes take 0.00 MB: 5 bytes/node
892 String nodes take 0.01 MB: 9 bytes/node
11506 List nodes take 2.75 MB: 250 bytes/node
30311 total nodes take 3.12 MB: 107 bytes/node


32
Time for 98568 inserts: 0.938856840134 ( 832898 total length) ( 0.00952496591321 ms per insert)
15630 Trie nodes take 0.36 MB: 23 bytes/node
292 Leaf nodes take 0.00 MB: 4 bytes/node
772 String nodes take 0.01 MB: 11 bytes/node
10739 List nodes take 3.13 MB: 305 bytes/node
27433 total nodes take 3.50 MB: 133 bytes/node


LISTSIZE=8, ALPHABET_IN_BITS=2 ==> NO ListNodes
Time for 98568 inserts: 1.17398691177 ( 832898 total length) ( 0.0119104264241 ms per insert)
525934 Trie nodes take 13.68 MB: 27 bytes/node
24243 Leaf nodes take 0.11 MB: 4 bytes/node
41175 String nodes take 0.32 MB: 8 bytes/node
1 List nodes take 0.00 MB: 4352 bytes/node
591353 total nodes take 14.12 MB: 25 bytes/node


*/
