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
#include <string.h>
#include <stdio.h>
#include "fwstring.h"

fwString fwStringNone = 0xFFFFFFFF;

static char* _base;
static int   _head;
static int   _allocated;

void fwString_init() {
    _allocated = 1024;
    _head = 0;
    _base = (char*) malloc(_allocated * sizeof(char));
}

int fwString_memory() {
    return _allocated * sizeof(char);
}

fwString fwString_create(char* src) {
    int length = strlen(src) + 1;
    while (_allocated - _head < length) {
        _allocated = (int) _allocated * 1.1;
        _base = realloc(_base, _allocated * sizeof(char));
    }
    unsigned char* dst = &_base[_head];
    memcpy(dst, src, length);
    _head += length;
    return (fwString) (_head - length);
}

char* fwString_get(fwString string) {
    return &_base[string];
}

void fwString_dump() {
    int i;
    printf("fwString_dump from base %ld with length %d", (long) _base, _head);
    for (i = 0; i < _head; i++) {
        if (i % 8 == 0)
            printf("\n");
        printf("%4d %3d [%c], ", i, _base[i], _base[i]);
    }
}
