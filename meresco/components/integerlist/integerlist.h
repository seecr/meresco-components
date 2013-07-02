/* begin license *
 *
 * "Meresco Components" are components to build searchengines, repositories
 * and archives, based on "Meresco Core".
 *
 * Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
 * Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
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

#include <vector>
#include <stdio.h>
#include <stdint.h>

#ifndef __integerlist_h__
#define __integerlist_h__

class IntegerList {
    private:
        std::vector<uint64_t>* v;
        std::vector<int>* deletes;
        uint64_t DELETE_MARK;
    public:
        IntegerList(int n);
        IntegerList(IntegerList* integerList, int start, int stop, int size);
        virtual ~IntegerList();
        int size();
        uint64_t get(int index);
        int append(uint64_t element);
        int set(int index, uint64_t value);
        IntegerList* slice(int start, int stop);
        void delitems(int start, int stop);
        int save(char* filename, int offset, bool append);
        int extendFrom(char* filename);
        int indexFor(int index);
};

extern "C" {
    IntegerList*    IntegerList_create               (int n);
    void            IntegerList_delete               (IntegerList*);
    int             IntegerList_append               (IntegerList*, uint64_t);
    int             IntegerList_size                 (IntegerList*);
    uint64_t        IntegerList_get                  (IntegerList*, int);
    int             IntegerList_set                  (IntegerList*, int, uint64_t);
    IntegerList*    IntegerList_slice                (IntegerList*, int, int);
    void            IntegerList_delitems             (IntegerList* list, int start, int stop);
    int             IntegerList_save                 (IntegerList* list, char* filename, int offset, bool append);
    int             IntegerList_extendFrom           (IntegerList* list, char* filename);
}

#endif


