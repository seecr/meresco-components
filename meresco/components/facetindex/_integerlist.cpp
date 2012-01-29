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
 * Copyright (C) 2011 Stichting Kennisnet http://www.kennisnet.nl
 * Copyright (C) 2012 Seecr (Seek You Too B.V.) http://seecr.nl
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


/* ----------------------- C++ ---------------------------------------------*/


template <typename T>
class TypedIntegerList : public IntegerList {
    private:
        std::vector<T>* v;
    public:
        TypedIntegerList(int n) {
            v = new std::vector<T>();
            v->reserve(n);
            for (int i=0; i < n; i++) {
                v->push_back(i);
            }
        }
        TypedIntegerList(TypedIntegerList<T>* integerList, int start, int stop) {
            if (start < 0 || stop > integerList->size() || stop <= start) {
                v = new std::vector<T>();
            }
            else {
                v = new std::vector<T>(integerList->v->begin() + start, integerList->v->begin() + stop);
            }
        }
        virtual ~TypedIntegerList() { delete v; }
        virtual int size() { return v->size(); }
        virtual uint64_t get(int index) {
            if (index < 0) {
                index = size() + index;
            }
            if (!use64bits()) {
                return (signed) v->at(index);
            }
            return v->at(index);
        }
        virtual void append(uint64_t element) {
            v->push_back((T) element);
        }
        virtual void set(int index, uint64_t element) { v->at(index) = (T) element; }
        virtual IntegerList* slice(int start, int stop, int step) {
            return new TypedIntegerList<T>(this, start, stop);
        }
        virtual void delitems(int start, int stop) {
            if (start >= 0 && stop <= v->size() && stop > start) {
                v->erase(v->begin() + start, v->begin() + stop);
            }
        }
        virtual int mergeFromOffset(int offset) {
            for (typename std::vector<T>::iterator it=v->end()-1; it != v->begin()+offset-1; it--) {
                if ((int) *it < 0) {
                    v->erase(it);
                }
            }
            return size() - offset;
        }
        virtual int save(char* filename, int offset, bool append) {
            if (offset < 0 || (offset >= size() && size() > 0)) {
                return -1;
            }
            FILE* fp = fopen(filename, append ? "ab" : "wb");
            if (!fp) {
                return errno;
            }
            if (size()-offset > 0) {
                fwrite(&(v->at(offset)), sizeof(T), size() - offset, fp);
            }
            fclose(fp);
            return 0;
        }
        virtual int extendFrom(char* filename) {
            FILE* fp = fopen(filename, "r");
            if (!fp) {
                return errno;
            }
            while (!feof(fp)) {
                T i;
                if (fread(&i, sizeof(T), 1, fp) == 1) {
                    v->push_back(i);
                }
            }
            fclose(fp);
            return 0;
        }
        bool use64bits() { return sizeof(T) == sizeof(uint64_t); }
};


/* ----------------------- C -----------------------------------------------*/


IntegerList* IntegerList_create(int n, bool use64bits) {
    return use64bits ? (IntegerList*) new TypedIntegerList<uint64_t>(n) : (IntegerList*) new TypedIntegerList<uint32_t>(n);
}

void IntegerList_delete(IntegerList* iList) {
    delete iList;
}

void IntegerList_append(IntegerList* iList, uint64_t element) {
    iList->append(element);
}

int IntegerList_size(IntegerList *iList) {
    return iList->size();
}

uint64_t IntegerList_get(IntegerList *iList, int index) {
    return iList->get(index);
}

void IntegerList_set(IntegerList *iList, int index, uint64_t value) {
    iList->set(index, value);
}

IntegerList* IntegerList_slice(IntegerList *iList, int start, int stop, int step) {
    return iList->slice(start, stop, step);
}

void IntegerList_delitems(IntegerList* iList, int start, int stop) {
    iList->delitems(start, stop);
}

int IntegerList_mergeFromOffset(IntegerList *iList, int offset) {
    return iList->mergeFromOffset(offset);
}

int IntegerList_save(IntegerList* iList, char* filename, int offset, bool append) {
    return iList->save(filename, offset, append);
}

int IntegerList_extendFrom(IntegerList* iList, char* filename) {
    return iList->extendFrom(filename);
}


