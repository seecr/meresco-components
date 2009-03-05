
#ifndef __triedict_h__
#define __triedict_h__

#include <string>
#include <glib.h>

extern "C" {
    #include "fwpool.h"
}

typedef guint32 termid;
typedef guint32 value;

class TrieDict {
    private:
        fwPtr termIndex;
        std::string termPool;
    public:
        TrieDict(void);
        ~TrieDict(void);
        termid             add(char* term, value value);
        value              getValue(char* term);
        char*              getTerm(termid termId);
        void               nodecount(void);
};
extern "C" {
    TrieDict*              TrieDict_create(void);
    void                   TrieDict_delete(TrieDict*);
}
#endif
