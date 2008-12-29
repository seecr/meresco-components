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
