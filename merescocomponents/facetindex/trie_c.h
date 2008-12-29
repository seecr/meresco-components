#ifndef __trie__h__
#define __trie__h__

#include <glib.h>
#include "fwpool.h"
#include "fwstring.h"

#include <vector>

void trie_init(void);

typedef struct {
    void (*addValue)(fwPtr self, guint32 value, fwString term);
    guint32 (*getValue)(fwPtr self, char* term);
    void (*getValues)(fwPtr self, char *prefix, std::vector<guint32>* result,  int caseSensitive);
    void (*free)(fwPtr self);
    void (*printit)(fwPtr self, int indent);
} INode;

extern guint32 fwValueNone;
inline INode* interface(fwPtr self);

fwPtr TrieNode_create(guint32 value);
void TrieNode_free(fwPtr self);
void TrieNode_addValue(fwPtr self, guint32 value, fwString term);
guint32 TrieNode_getValue(fwPtr self, char* term);
void TrieNode_getValues(fwPtr self, char* prefix, std::vector<guint32>* result, int caseSensitive);
int TrieNode_memory(void);
void TrieNode_printit(fwPtr self, int indent);

void nodecount(void);
inline int isNone(fwPtr ptr);

#endif

