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
#include <stdlib.h>
#include <stdio.h>
#include "fwpool.h"

fwPtr fwNONE = {0, 0x3FFFFFFF};

int _head = 0;
int _allocated = 5;
PoolState *_pools = 0;

void pool_init() {
    if (_pools == 0) {
        _pools = (PoolState *) calloc(_allocated, sizeof(PoolState));
    }
}

fwPool Pool_create(short elementType, size_t elementSize, int initialSize) {
    if (_head >= _allocated) {
        _allocated = (int) _allocated * 2;
        _pools = (PoolState*) realloc(_pools, _allocated * sizeof(PoolState));
    }
    P(_head)->pool = calloc(initialSize, elementSize);

    P(_head)->freed = calloc(initialSize, sizeof(fwPtr));
    P(_head)->_allocatedElements = initialSize;
    P(_head)->_freed_allocated = initialSize;
    P(_head)->_headElement = 0;
    P(_head)->_freed_head = 0;
    P(_head)->_elementType = elementType;
    P(_head)->_elementSize = elementSize;
    return _head++;
}


fwPtr Pool__pop_free(fwPool self) {
    if (P(self)->_freed_head == 0) {
        printf("illegal call on Pool_pop_free");
    }
    return P(self)->freed[--P(self)->_freed_head];
}

fwPtr Pool_new(fwPool self) {
    fwPtr newOne = fwNONE;
    newOne.type = P(self)->_elementType;
    if (P(self)->_freed_head) {
        newOne.ptr = Pool__pop_free(self).ptr;
    } else {
        if (P(self)->_headElement >= P(self)->_allocatedElements) {
            P(self)->_allocatedElements = (int) P(self)->_allocatedElements * 1.5;
            P(self)->pool = realloc(P(self)->pool, P(self)->_allocatedElements * P(self)->_elementSize);
        }
        newOne.ptr = P(self)->_headElement++;
    }
   return newOne;
}

void Pool_free(fwPool self, fwPtr ptr) {
    if (P(self)->_freed_head >= P(self)->_freed_allocated) {
        P(self)->_freed_allocated = (int) P(self)->_freed_allocated * 1.5;
        P(self)->freed = (fwPtr*) realloc(P(self)->freed, P(self)->_freed_allocated * sizeof(fwPtr));
    }
    P(self)->freed[P(self)->_freed_head++] = ptr;
}


int Pool_memory(fwPool self) {
    return P(self)->_allocatedElements * P(self)->_elementSize;
}

int Pool_count(fwPool self) {
    return P(self)->_headElement + 1;
}

inline int isNone(fwPtr ptr) {
    return ptr.ptr == fwNONE.ptr;
}
