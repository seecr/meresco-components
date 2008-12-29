#ifndef __fwpool_h__
#define __fwpool_h__

typedef struct {
    unsigned int type:2;
    unsigned int ptr:30;
} fwPtr;


typedef struct {
    int     _headElement;
    int     _allocatedElements;

    int     _freed_head;
    int     _freed_allocated;

    char*    pool;
    fwPtr*   freed;
    short   _elementType;
    short   _elementSize;
} PoolState;


extern fwPtr fwNONE;
extern PoolState* _pools;

typedef int fwPool;

inline PoolState* P(fwPool pool) {
    return &_pools[pool];
}
fwPool Pool_create(short elementType, size_t elementSize, int initialSize);
fwPtr Pool_new(fwPool self);
void Pool_free(fwPool self, fwPtr ptr);
inline void* Pool_get(fwPool self, fwPtr ptr) {
    return P(self)->pool + (ptr.ptr * P(self)->_elementSize);
}
int Pool_memory(fwPool self);
int Pool_count(fwPool self);
void pool_init(void);

inline int isNone(fwPtr ptr);

#endif
