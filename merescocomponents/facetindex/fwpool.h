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
