#include <vector>
#include "facetindex.h"

extern "C" {
    #include "fwstring.h"
}

#ifndef __docset_h__
#define __docset_h__


class DocSet : public std::vector<doc_t> {
    public:
        fwString _term;
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
        static DocSet*
        fromTermDocs(JObject* termDocs, int freq, JString* term);
};

extern "C" {
    DocSet* DocSet_create             (void);
    DocSet* DocSet_forTesting         (int size);
    void    DocSet_add                (DocSet* docset, guint32 doc);
    void    DocSet_remove             (DocSet* docset, guint32 doc);
    guint32 DocSet_get                (DocSet* docset, int i);
    int     DocSet_len                (DocSet* docset);
    void    DocSet_setTerm            (DocSet* docset, char* term);
    char*   DocSet_term               (DocSet* docset);
    int     DocSet_combinedCardinality(DocSet* docset, DocSet* rhs);
    DocSet* DocSet_intersect          (DocSet* docset, DocSet* rhs);
    DocSet* DocSet_fromQuery          (PyJObject* psearcher, PyJObject* pquery);
    DocSet* DocSet_fromTermDocs       (PyJObject* termDocs, int freq, char* term);
    void    DocSet_delete             (DocSet* docset);
}


#endif

