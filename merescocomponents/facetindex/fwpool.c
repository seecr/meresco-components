/* begin license *
 *
 *     Meresco Components are components to build searchengines, repositories
 *     and archives, based on Meresco Core.
 *     Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
 *     Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
 *        http://www.kennisnetictopschool.nl
 *     Copyright (C) 2009 Delft University of Technology http://www.tudelft.nl
 *     Copyright (C) 2009 Tilburg University http://www.uvt.nl
 *     Copyright (C) 2007-2009 Seek You Too (CQ2) http://www.cq2.nl
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
#include <assert.h>
#include "fwpool.h"

#define FACTOR 1.1
#define POOLFACTOR 2

fwPtr fwNONE = {0, 0x3FFFFFFF};

int _head = 0;
int _allocated = 5;
PoolState *_pools = 0;

int pool_init() {
    if (_pools == 0) {
        _pools = (PoolState *) calloc(_allocated, sizeof(PoolState));
    }
    return 1;
}

fwPool Pool_create(short elementType, size_t elementSize, int initialSize) {
    if ( (int)(initialSize * FACTOR) == initialSize ) {
        printf("initialSize of pool too small: %d\n", initialSize);
        exit(1);
    }
    if ( (int)(_allocated * POOLFACTOR) == _allocated ) {
        printf("_allocated nr of pools too small: %d\n", _allocated);
        exit(1);
    }
    if (_head >= _allocated) {
        _allocated = (int) _allocated * POOLFACTOR;
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
            P(self)->_allocatedElements = (int) P(self)->_allocatedElements * FACTOR;
            P(self)->pool = realloc(P(self)->pool, P(self)->_allocatedElements * P(self)->_elementSize);
        }
        newOne.ptr = P(self)->_headElement++;
    }
    return newOne;
}

void Pool_free(fwPool self, fwPtr ptr) {
    if (P(self)->_freed_head >= P(self)->_freed_allocated) {
        P(self)->_freed_allocated = (int) P(self)->_freed_allocated * FACTOR;
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
