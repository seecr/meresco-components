
#include "triedict.h"
#include "trie_c.h"

TrieDict::TrieDict() {
    termIndex = TrieNode_create(fwValueNone);
}

TrieDict::~TrieDict() {
    TrieNode_free(termIndex);
}

termid TrieDict::add(char* term, value value) {
    termid termId = this->termPool.size();
    this->termPool.append(term);
    this->termPool.push_back('\0');
    TrieNode_addValue(termIndex, value, termId, &this->termPool[0]);
    return termId;
}

value TrieDict::getValue(char* term) {
    value value = TrieNode_getValue(termIndex, term, &this->termPool[0]);
    if ( value == fwValueNone )
        return 0xFFFFFFFF;
    return value;
}

char* TrieDict::getTerm(termid termId) {
    if (termId == 0xFFFFFFFF) {
        return "";
    }
    return &this->termPool[termId];
}

void TrieDict::nodecount(void) {
    nodecount();
}

TrieDict* TrieDict_create(void) {
    return new TrieDict();
}

void TrieDict_delete(TrieDict* trieDict) {
    delete trieDict;
}

