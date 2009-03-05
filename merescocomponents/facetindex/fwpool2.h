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
#ifndef __fwpool2_h__
#define __fwpool2_h__

#include <assert.h>
#include <vector>
#include <stdio.h>
#include <string.h>
#include <exception>


template <class T> class fwPtr;

template <class T> class fwPoolBase : public std::vector<T> {
    protected:
        std::vector<int> released;
    friend class fwPtr<T>;
};

void* types[8] = {0, 0, 0, 0, 0, 0, 0, 0}; // see int type:3 below

template <class T, int type> class fwPool : public fwPoolBase<T>  {
    public:
        fwPool() {
            if ( type >= 8 )
                throw "invalid type: use 0-7 for types";
            if ( types[type] != NULL )
                throw "duplicate type";
            types[type] = this;
        }
        fwPtr<T> create() {
            int ptr = -1;
            if ( this->released.size() > 0 ) {
                ptr = this->released.back();
                this->released.pop_back();
            } else {
                ptr = this->size();
                push_back(T());
            }
            return fwPtr<T>(ptr, type);
        }
};


template <class T> class fwPtr {
    private:
        int ptr: 29;
        int type: 3;  // see types[8] above
    public:
        fwPtr( int ptr, int type ) : ptr(ptr), type(type) {}
        inline T& operator*() {
            return ((std::vector<T>**)types)[type]->at(ptr);
        }
        inline void release(void) {
            ((fwPoolBase<T>**)types)[type]->released.push_back(ptr);
        }
};

#endif
