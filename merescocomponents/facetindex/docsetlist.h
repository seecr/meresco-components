#include <Python.h>
#include <vector>
#include "facetindex.h"
#include "docset.h"
extern "C" {
    #include "trie_c.h"
}

#ifndef __docsetlist_h__
#define __docsetlist_h__



/**************** C++ implementation of DocSetList****************************/
typedef struct {
    char*   term;
    guint32 cardinality;
} cardinality_t;

typedef std::vector<cardinality_t> CardinalityList;

class DocSetList : public std::vector<DocSet*> {
    private:
        fwPtr termIndex2;
    public:
        DocSetList();
        ~DocSetList();
        void                 addDocSet(DocSet* docset);
        CardinalityList* combinedCardinalities(DocSet* docset, guint32 maxResults, int doSort);
        DocSet*              forTerm(char* term);
        void                 removeDoc(guint32 doc);
};

/**************** C-interface for DocSetList ****************************/
extern "C" {
    DocSetList*    DocSetList_create               (void);
    void           DocSetList_add                  (DocSetList* list, DocSet* docset);
    void           DocSetList_removeDoc            (DocSetList* list, guint32 doc);
    int            DocSetList_size                 (DocSetList* list);
    DocSet*        DocSetList_get                  (DocSetList* list, int i);
    DocSet*        DocSetList_getForTerm           (DocSetList* list, char* term);
    void* DocSetList_combinedCardinalities(DocSetList* list, DocSet* docset, guint32 maxResults, int doSort);
    void           DocSetList_delete               (DocSetList* list);
    void           DocSetList_sortOnCardinality    (DocSetList* list);
    DocSetList*    DocSetList_fromTermEnum         (PyJObject* termEnum, PyJObject* termDocs);
    void*          CardinalityList_at              (CardinalityList* vector, int i);
    int            CardinalityList_size            (CardinalityList* vector);
    void           CardinalityList_free            (CardinalityList* vector);
}

#endif


