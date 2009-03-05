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

#include "integerlist.h"
#include <vector>
#include <stdio.h>
#include <errno.h>

IntegerList* IntegerList_create(int n) {
    return new IntegerList(n);
}

void IntegerList_delete(IntegerList* iList) {
    delete iList;
}

void IntegerList_append(IntegerList* iList, guint32 element) {
    iList->append(element);
}

int IntegerList_size(IntegerList *iList) {
    return iList->size();
}

guint32 IntegerList_get(IntegerList *iList, int index) {
    if (index < 0) {
        index = iList->size() + index;
    }
    return iList->at(index);
}

void IntegerList_set(IntegerList *iList, int index, guint32 value) {
    iList->at(index) = value;
}

IntegerList* IntegerList_slice(IntegerList *iList, int start, int stop, int step) {
    return iList->slice(start, stop, step);
}

void IntegerList_delitems(IntegerList* list, int start, int stop) {
    list->erase(list->begin()+start, list->begin()+stop);
}

int IntegerList_mergeFromOffset(IntegerList *iList, int offset) {
    return iList->mergeFromOffset(offset);
}

int IntegerList_save(IntegerList* list, char* filename, int offset) {
    return list->save(filename, offset);
}

int IntegerList_extendFrom(IntegerList* list, char* filename) {
    return list->extendFrom(filename);
}

int IntegerList_extendTo(IntegerList* list, char* filename) {
    return list->extendTo(filename);
}


/* ----------------------- C++ ---------------------------------------------*/

IntegerList::IntegerList(int n) : std::vector<guint32>() {
    reserve(n);
    for ( int i=0; i < n; i++ ) {
        push_back(i);
    }
}

void IntegerList::append(guint32 element) {
    push_back(element);
}

IntegerList* IntegerList::slice(int start, int stop, int step) {
    return new IntegerList(begin()+start, begin()+stop);
}

int IntegerList::mergeFromOffset(int offset) {
    for(std::vector<guint32>::iterator it=end()-1; it != begin()+offset-1; it--) {
        if (*it == 0xFFFFFFFF) {
            erase(it);
        }
    }
    return size() - offset;
}

int IntegerList::save(char* filename, int offset) {
    if ( offset < 0 || (offset >= size() && size() > 0) ) {
        return -1;
    }
    FILE* fp = fopen(filename, "wb");
    if ( !fp ) {
        return errno;
    }
    if ( size()-offset > 0 ) {
        fwrite(&at(offset), sizeof(guint32), size()-offset, fp);
    }
    fclose(fp);
    return 0;
}

int IntegerList::extendFrom(char* filename) {
    FILE* fp = fopen(filename, "r");
    if ( !fp ) {
        return errno;
    }
    while ( ! feof(fp) ) {
        guint32 i;
        if ( fread(&i, sizeof(guint32), 1, fp) == 1)
            push_back(i);
    }
    fclose(fp);
    return 0;
}

int IntegerList::extendTo(char* filename) {
    FILE* fp = fopen(filename, "a");
    if ( !fp ) {
        return errno;
    }
    if ( size() > 0 ) {
        fwrite(&at(0), sizeof(guint32), size(), fp);
    }
    fclose(fp);
    return 0;
}
