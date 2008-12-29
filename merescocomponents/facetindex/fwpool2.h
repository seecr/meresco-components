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