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
#include <Python.h>
#include <glib.h>

#ifndef __pyjava_h__
#define __pyjava_h__

typedef gint32   jint;
typedef gfloat   jfloat;
typedef gboolean jboolean;

// See http://www.cse.wustl.edu/~mdeters/seminar/fall2005/notes1114.html

struct JVTable {
    public:
        // Java vtable layout, do not change.
        jint    topoffset;
        void*   typeinfo;
    public:
        // This is where C++ vtable pointers point to
        void*   vtable[0];
};

class JObject {
    public:
        // this is how Java Objects lay in memory, do not change!
        void** vtable;
};

class PyJObject : PyObject {
    public:
        // This points to the wrapped Java object acc. to PyLucene
        JObject *jobject;
};

class JIntArray : public JObject {
    // this is how Java int arrays lay in memory, do not change!
    private:
        jint length;
    public:
        jint data[0];
};

// Fake HitCollector to create a suitable vtable for Java
class JHitCollector : JObject {
    // This is how the java::lang::Object vtable lays in memory, do not change
    virtual void _NA_1_() { assert(0); } // class pointer
    virtual void _NA_2_() { assert(0); } // GC bitmap
    virtual void _NA_3_() { assert(0); } // finalize
    virtual void _NA_4_() { assert(0); } // hashCode
    virtual void _NA_5_() { assert(0); } // equals
    virtual void _NA_6_() { assert(0); } // toString
    virtual void _NA_7_() { assert(0); } // clone
};


#define JINTTYPE 10
extern "C" void* _Jv_NewArray(jint type, jint size);
inline JIntArray* _Jv_NewIntArray(jint size) {
    return (JIntArray*)_Jv_NewArray(JINTTYPE, size);
}

class JString;
extern "C" jint _Jv_GetStringUTFRegion (JString* jstring, jint, jint, char *);

class JString : public JObject {
    private:
        // This is how Java String lays in memory, do not change
        char* data;
        jint boffset;
        jint _length;
        jint _NA_count;
    public:
        int writeUTF8CharsIn(char* dst) {
            return _Jv_GetStringUTFRegion(this, 0, this->_length, dst);
        }
        inline jint length(void) { return _length; }
};

extern "C" void*
_Jv_LookupInterfaceMethodIdx (void* klass, JObject* iface, int meth_idx);

inline void*
lookupIface(JObject* object, JObject* iface, int methodIndex) {
    return _Jv_LookupInterfaceMethodIdx(object->vtable[0], iface, methodIndex);
}

inline void*
lookupMethod(JObject* object, int methodIndex) {
    return object->vtable[methodIndex];
}


// interface of Searcher (of which is only one impl, so use direct method link)
#define Searcher_search _ZN3org6apache6lucene6search8Searcher6searchEPNS2_5QueryEPNS2_12HitCollectorE
extern "C" void
Searcher_search(JObject* searcher, JObject* query, JHitCollector* collector);

// interface of Term (is a class, with no virtual methods, so direct method link)
#define Term_field _ZN3org6apache6lucene5index4Term5fieldEv
extern "C" JString* Term_field (JObject* term);
#define Term_text  _ZN3org6apache6lucene5index4Term4textEv
extern "C" JString* Term_text  (JObject* term);

// interface of TermDocs (is a real interface, so define the itable as ITermDocs)
#define ITermDocs _ZN3org6apache6lucene5index8TermDocs6class$E
extern JObject ITermDocs;
typedef jint (*TermDocs_read)(JObject* termDocs, JIntArray* docs, JIntArray* freqs);
typedef void (*TermDocs_seek)(JObject* termDocs, JObject* termEnum);

// interface of TermEnumtop (is a class with virtual methods, so use vtable)
typedef jboolean (*TermEnum_next)   (JObject* termEnum);
typedef JObject* (*TermEnum_term)   (JObject* termEnum);
typedef jint     (*TermEnum_docFreq)(JObject* termEnum);


#endif
