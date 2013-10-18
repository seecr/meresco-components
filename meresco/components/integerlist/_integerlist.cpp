/* begin license *
 *
 * "Meresco Components" are components to build searchengines, repositories
 * and archives, based on "Meresco Core".
 *
 * Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
 * Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
 * Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
 * Copyright (C) 2009 Delft University of Technology http://www.tudelft.nl
 * Copyright (C) 2009 Tilburg University http://www.uvt.nl
 * Copyright (C) 2011-2013 Seecr (Seek You Too B.V.) http://seecr.nl
 * Copyright (C) 2011 Stichting Kennisnet http://www.kennisnet.nl
 *
 * This file is part of "Meresco Components"
 *
 * "Meresco Components" is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * "Meresco Components" is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with "Meresco Components"; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 *
 * end license */

#include "integerlist.h"
#include <vector>
#include <errno.h>
#include <limits.h>
#include <algorithm>

/* ----------------------- C++ ---------------------------------------------*/

IntegerList::IntegerList(int n) {
    v = new std::vector<uint64_t>();
    v->reserve(n);
    for (int i=0; i < n; i++) {
        v->push_back(i);
    }
    deletes = new std::vector<int>();
    DELETE_MARK = LONG_MAX;
}
IntegerList::IntegerList(IntegerList* integerList, int start, int stop, int size) {
    deletes = new std::vector<int>();
    if (start < 0 || stop > size || stop <= start) {
        v = new std::vector<uint64_t>();
    }
    else {
        v = new std::vector<uint64_t>(integerList->v->begin() + start, integerList->v->begin() + stop);
        for (std::vector<int>::iterator it=integerList->deletes->begin(); it != integerList->deletes->end(); ++it)
        {
            int index = *it;
            if (index > start && index < stop) {
                deletes->push_back(index-start);
            }
        }
    }
    DELETE_MARK = integerList->DELETE_MARK;
}
IntegerList::~IntegerList() {
    delete v;
    delete deletes;
}
int IntegerList::size() {
    return v->size() - deletes->size();
}
uint64_t IntegerList::get(int index) {
    if (index < 0) {
        index = size() + index;
    }
    return v->at(indexFor(index));
}
int IntegerList::append(uint64_t element) {
    if (element == DELETE_MARK) {
        return -1;
    }
    v->push_back(element);
    return 0;
}
int IntegerList::set(int index, uint64_t element) {
    if (element == DELETE_MARK) {
        return -1;
    }
    v->at(indexFor(index)) = element;
    return 0;
}
IntegerList* IntegerList::slice(int start, int stop) {
    return new IntegerList(this, indexFor(start), indexFor(stop), v->size());
}
void IntegerList::delitems(int start, int stop) {
    if (start >= 0 && stop <= int(size()) && stop > start) {
        for (int i = stop-1; i >= start; i--) {
            int index = indexFor(i);
            v->at(index) = DELETE_MARK;
            deletes->insert(lower_bound(deletes->begin(), deletes->end(), index), index);
        }
    }    
}
int IntegerList::save(char* filename, int offset, bool append) {
    if (offset < 0 || (offset >= size() && size() > 0)) {
        return -1;
    }
    offset = indexFor(offset);
    FILE* fp = fopen(filename, append ? "ab" : "wb");
    if (!fp) {
        return errno;
    }
    if (v->size()-offset > 0) {
        fwrite(&(v->at(offset)), sizeof(uint64_t), v->size() - offset, fp);
    }
    fclose(fp);
    return 0;
}
int IntegerList::extendFrom(char* filename) {
    FILE* fp = fopen(filename, "r");
    if (!fp) {
        return errno;
    }
    while (!feof(fp)) {
        uint64_t i;
        if (fread(&i, sizeof(uint64_t), 1, fp) == 1) {
            if (i != DELETE_MARK) {
                v->push_back(i);
            }
        }
    }
    fclose(fp);
    return 0;
}
int IntegerList::indexFor(int index) {
    for (std::vector<int>::iterator it=deletes->begin(); it < deletes->end(); it++) {
        if (*it > index) {
            break;
        }
        index++;
    }
    return index;
}


/* ----------------------- C -----------------------------------------------*/


IntegerList* IntegerList_create(int n) {
    return new IntegerList(n);
}

void IntegerList_delete(IntegerList* iList) {
    delete iList;
}

int IntegerList_append(IntegerList* iList, uint64_t element) {
    return iList->append(element);
}

int IntegerList_size(IntegerList *iList) {
    return iList->size();
}

uint64_t IntegerList_get(IntegerList *iList, int index) {
    return iList->get(index);
}

int IntegerList_set(IntegerList *iList, int index, uint64_t value) {
    return iList->set(index, value);
}

IntegerList* IntegerList_slice(IntegerList *iList, int start, int stop) {
    return iList->slice(start, stop);
}

void IntegerList_delitems(IntegerList* iList, int start, int stop) {
    iList->delitems(start, stop);
}

int IntegerList_save(IntegerList* iList, char* filename, int offset, bool append) {
    return iList->save(filename, offset, append);
}

int IntegerList_extendFrom(IntegerList* iList, char* filename) {
    return iList->extendFrom(filename);
}


