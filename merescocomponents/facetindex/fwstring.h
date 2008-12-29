#ifndef __fwstring_h__
#define __fwstring_h__

#include <glib.h>

// Flyweight Strings:
//  - packs 0-terminated strings in one big buffer
//  - returns small 32 bits 'pointers' (fwString)
//  - delete string is not supported

typedef guint32 fwString;
extern fwString fwStringNone;

void     fwString_init  (void);
int      fwString_memory(void);
fwString fwString_create(char*);
char*    fwString_get   (fwString);
void     fwString_dump  (void);


#endif
