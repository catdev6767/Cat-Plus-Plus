#!/usr/bin/env python3
"""Cat++ -> C transpiler (A1+A2+A3+A4)."""
import sys, os, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from interpreter import tokenize, Parser, CatError

RUNTIME = '#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include <ctype.h>\n#include <setjmp.h>\n#include <math.h>\n\ntypedef enum { T_INT, T_DOUBLE, T_STR, T_NULL, T_BOOL, T_LIST, T_DICT } VTag;\ntypedef struct Value Value;\ntypedef struct { int len, cap; Value* items; } VList;\ntypedef struct { int len, cap; char** keys; Value* vals; } VDict;\nstruct Value { VTag t; long long i; double d; char* s; VList* list; VDict* dict; };\n\nstatic char* v_to_str(Value v);\nstatic int v_truthy(Value v);\n\n/* ═══ Error handling ═══ */\nstatic jmp_buf* __jmp_stack[64];\nstatic int __jmp_top = 0;\nstatic char __catpp_err_msg[512];\nstatic void __catpp_raise(const char* msg){\n    if (__jmp_top > 0) {\n        strncpy(__catpp_err_msg, msg, 511);\n        __catpp_err_msg[511] = 0;\n        longjmp(*__jmp_stack[__jmp_top-1], 1);\n    }\n    fprintf(stderr, "%s\\n", msg);\n    exit(1);\n}\n\n/* ═══ Value constructors ═══ */\nstatic Value V_int(long long v){ Value r; memset(&r,0,sizeof(r)); r.t=T_INT; r.i=v; return r; }\nstatic Value V_double(double v){ Value r; memset(&r,0,sizeof(r)); r.t=T_DOUBLE; r.d=v; return r; }\nstatic Value V_str(const char* v){ Value r; memset(&r,0,sizeof(r)); r.t=T_STR; r.s=strdup(v?v:""); return r; }\nstatic Value V_null(void){ Value r; memset(&r,0,sizeof(r)); r.t=T_NULL; return r; }\nstatic Value V_bool(int v){ Value r; memset(&r,0,sizeof(r)); r.t=T_BOOL; r.i=v?1:0; return r; }\nstatic Value V_list(VList* l){ Value r; memset(&r,0,sizeof(r)); r.t=T_LIST; r.list=l; return r; }\nstatic Value V_dict(VDict* d){ Value r; memset(&r,0,sizeof(r)); r.t=T_DICT; r.dict=d; return r; }\n\n/* ═══ List / Dict ═══ */\nstatic VList* list_new(void){ VList* l=malloc(sizeof(VList)); l->len=0; l->cap=4; l->items=malloc(sizeof(Value)*4); return l; }\nstatic void list_push(VList* l, Value v){ if(l->len>=l->cap){ l->cap*=2; l->items=realloc(l->items, sizeof(Value)*l->cap); } l->items[l->len++]=v; }\nstatic VDict* dict_new(void){ VDict* d=malloc(sizeof(VDict)); d->len=0; d->cap=4; d->keys=malloc(sizeof(char*)*4); d->vals=malloc(sizeof(Value)*4); return d; }\nstatic int dict_find(VDict* d, const char* k){ for(int i=0;i<d->len;i++) if(strcmp(d->keys[i],k)==0) return i; return -1; }\nstatic void dict_set(VDict* d, const char* k, Value v){ int i=dict_find(d,k); if(i>=0){ d->vals[i]=v; return; } if(d->len>=d->cap){ d->cap*=2; d->keys=realloc(d->keys,sizeof(char*)*d->cap); d->vals=realloc(d->vals,sizeof(Value)*d->cap); } d->keys[d->len]=strdup(k); d->vals[d->len]=v; d->len++; }\nstatic Value dict_get(VDict* d, const char* k){ int i=dict_find(d,k); return i>=0?d->vals[i]:V_null(); }\nstatic int dict_has(VDict* d, const char* k){ return dict_find(d,k)>=0; }\n\nstatic Value v_list_build(int n, Value* items){ VList* l=list_new(); for(int i=0;i<n;i++) list_push(l,items[i]); return V_list(l); }\nstatic Value v_list_empty(void){ return V_list(list_new()); }\nstatic Value v_dict_build(int n, Value* keys, Value* vals){ VDict* d=dict_new(); for(int i=0;i<n;i++){ char* k=v_to_str(keys[i]); dict_set(d,k,vals[i]); free(k); } return V_dict(d); }\nstatic Value v_dict_empty(void){ return V_dict(dict_new()); }\n\n/* ═══ Type checks / conversions ═══ */\nstatic int v_truthy(Value v){\n    switch(v.t){\n        case T_NULL: return 0;\n        case T_BOOL: case T_INT: return v.i!=0;\n        case T_DOUBLE: return v.d!=0.0;\n        case T_STR: return v.s && v.s[0];\n        case T_LIST: return v.list->len!=0;\n        case T_DICT: return v.dict->len!=0;\n    } return 0;\n}\nstatic double v_to_double(Value v){ if(v.t==T_INT) return (double)v.i; if(v.t==T_DOUBLE) return v.d; if(v.t==T_BOOL) return (double)v.i; return 0.0; }\nstatic long long v_to_int(Value v){ if(v.t==T_INT) return v.i; if(v.t==T_DOUBLE) return (long long)v.d; if(v.t==T_BOOL) return v.i; return 0; }\nstatic long long v_cast_int(Value v){\n    if(v.t==T_INT) return v.i;\n    if(v.t==T_DOUBLE) return (long long)v.d;\n    if(v.t==T_BOOL) return v.i;\n    if(v.t==T_STR) return (long long)atoll(v.s);\n    return 0;\n}\nstatic double v_cast_float(Value v){\n    if(v.t==T_INT) return (double)v.i;\n    if(v.t==T_DOUBLE) return v.d;\n    if(v.t==T_BOOL) return (double)v.i;\n    if(v.t==T_STR) return atof(v.s);\n    return 0.0;\n}\n\n/* ═══ to_str ═══ */\nstatic char* v_to_str(Value v){\n    char buf[64];\n    switch(v.t){\n        case T_NULL: return strdup("hungry");\n        case T_BOOL: return strdup(v.i?"nod":"shake");\n        case T_INT: sprintf(buf,"%lld",v.i); return strdup(buf);\n        case T_DOUBLE: if(v.d==(long long)v.d) sprintf(buf,"%lld",(long long)v.d); else sprintf(buf,"%g",v.d); return strdup(buf);\n        case T_STR: return strdup(v.s?v.s:"");\n        case T_LIST: {\n            int cap=256, len=0; char* out=malloc(cap); out[len++]=\'[\'; out[len]=0;\n            for(int i=0;i<v.list->len;i++){\n                if(i>0){ while(len+3>=cap){ cap*=2; out=realloc(out,cap);} out[len++]=\',\'; out[len++]=\' \'; out[len]=0; }\n                char* it=v_to_str(v.list->items[i]); int il=strlen(it);\n                while(len+il+3>=cap){ cap=cap*2+il; out=realloc(out,cap); }\n                memcpy(out+len,it,il); len+=il; out[len]=0; free(it);\n            }\n            while(len+2>=cap){ cap*=2; out=realloc(out,cap);} out[len++]=\']\'; out[len]=0; return out;\n        }\n        case T_DICT: {\n            int cap=256, len=0; char* out=malloc(cap); out[len++]=\'{\'; out[len]=0;\n            int first=1;\n            for(int i=0;i<v.dict->len;i++){\n                if(strcmp(v.dict->keys[i],"__class__")==0) continue;\n                if(!first){ while(len+3>=cap){ cap*=2; out=realloc(out,cap);} out[len++]=\',\'; out[len++]=\' \'; out[len]=0; }\n                first=0;\n                int kl=strlen(v.dict->keys[i]);\n                while(len+kl+3>=cap){ cap=cap*2+kl; out=realloc(out,cap);} memcpy(out+len,v.dict->keys[i],kl); len+=kl;\n                while(len+3>=cap){ cap*=2; out=realloc(out,cap);} out[len++]=\':\'; out[len++]=\' \'; out[len]=0;\n                char* val=v_to_str(v.dict->vals[i]); int vl=strlen(val);\n                while(len+vl+3>=cap){ cap=cap*2+vl; out=realloc(out,cap);} memcpy(out+len,val,vl); len+=vl; out[len]=0; free(val);\n            }\n            while(len+2>=cap){ cap*=2; out=realloc(out,cap);} out[len++]=\'}\'; out[len]=0; return out;\n        }\n    }\n    return strdup("?");\n}\n\n/* ═══ Operators ═══ */\nstatic Value v_add(Value a, Value b){\n    if(a.t==T_STR||b.t==T_STR){ char* sa=v_to_str(a); char* sb=v_to_str(b); char* r=malloc(strlen(sa)+strlen(sb)+1); strcpy(r,sa); strcat(r,sb); Value o=V_str(r); free(sa); free(sb); free(r); return o; }\n    if(a.t==T_LIST&&b.t==T_LIST){ VList* l=list_new(); for(int i=0;i<a.list->len;i++) list_push(l,a.list->items[i]); for(int i=0;i<b.list->len;i++) list_push(l,b.list->items[i]); return V_list(l); }\n    if(a.t==T_DOUBLE||b.t==T_DOUBLE) return V_double(v_to_double(a)+v_to_double(b));\n    return V_int(v_to_int(a)+v_to_int(b));\n}\nstatic Value v_sub(Value a, Value b){ if(a.t==T_DOUBLE||b.t==T_DOUBLE) return V_double(v_to_double(a)-v_to_double(b)); return V_int(v_to_int(a)-v_to_int(b)); }\nstatic Value v_mul(Value a, Value b){ if(a.t==T_DOUBLE||b.t==T_DOUBLE) return V_double(v_to_double(a)*v_to_double(b)); return V_int(v_to_int(a)*v_to_int(b)); }\nstatic Value v_div(Value a, Value b){ if(a.t==T_INT&&b.t==T_INT){ if(b.i==0) __catpp_raise("Chia cho 0"); if(a.i%b.i==0) return V_int(a.i/b.i);} double d=v_to_double(b); if(d==0.0) __catpp_raise("Chia cho 0"); return V_double(v_to_double(a)/d); }\nstatic Value v_mod(Value a, Value b){ long long bi=v_to_int(b); if(bi==0) __catpp_raise("Mod 0"); return V_int(v_to_int(a)%bi); }\nstatic Value v_neg(Value a){ if(a.t==T_DOUBLE) return V_double(-a.d); return V_int(-v_to_int(a)); }\nstatic Value v_not(Value a){ return V_bool(!v_truthy(a)); }\n\nstatic int v_cmp(Value a, Value b, int op){\n    if(a.t==T_STR||b.t==T_STR){ char* sa=v_to_str(a); char* sb=v_to_str(b); int r=strcmp(sa,sb); free(sa); free(sb);\n        switch(op){ case 0: return r==0; case 1: return r!=0; case 2: return r<0; case 3: return r>0; case 4: return r<=0; case 5: return r>=0; } }\n    if(a.t==T_DOUBLE||b.t==T_DOUBLE){ double x=v_to_double(a), y=v_to_double(b);\n        switch(op){ case 0: return x==y; case 1: return x!=y; case 2: return x<y; case 3: return x>y; case 4: return x<=y; case 5: return x>=y; } }\n    long long x=v_to_int(a), y=v_to_int(b);\n    switch(op){ case 0: return x==y; case 1: return x!=y; case 2: return x<y; case 3: return x>y; case 4: return x<=y; case 5: return x>=y; }\n    return 0;\n}\nstatic void v_print(Value v){ char* s=v_to_str(v); printf("%s\\n",s); free(s); }\n\nstatic Value v_index(Value obj, Value idx){\n    if(obj.t==T_LIST){ long long i=v_to_int(idx); if(i<0) i+=obj.list->len; if(i<0||i>=obj.list->len) __catpp_raise("Index out of range"); return obj.list->items[i]; }\n    if(obj.t==T_DICT){ char* k=v_to_str(idx); Value r=dict_get(obj.dict,k); free(k); return r; }\n    if(obj.t==T_STR){ long long i=v_to_int(idx); long long n=strlen(obj.s); if(i<0) i+=n; if(i<0||i>=n) __catpp_raise("Str index"); char b[2]={obj.s[i],0}; return V_str(b); }\n    return V_null();\n}\nstatic void v_index_set(Value obj, Value idx, Value val){\n    if(obj.t==T_LIST){ long long i=v_to_int(idx); if(i<0) i+=obj.list->len; if(i<0||i>=obj.list->len) __catpp_raise("Index set"); obj.list->items[i]=val; return; }\n    if(obj.t==T_DICT){ char* k=v_to_str(idx); dict_set(obj.dict,k,val); free(k); return; }\n    __catpp_raise("Cannot index-set");\n}\nstatic Value v_slice(Value obj, Value lo, Value hi, int hl, int hh){\n    if(obj.t==T_LIST){ int n=obj.list->len; int a=hl?(int)v_to_int(lo):0; int b=hh?(int)v_to_int(hi):n; if(a<0) a+=n; if(b<0) b+=n; if(a<0) a=0; if(b>n) b=n; VList* r=list_new(); for(int i=a;i<b;i++) list_push(r,obj.list->items[i]); return V_list(r); }\n    if(obj.t==T_STR){ int n=strlen(obj.s); int a=hl?(int)v_to_int(lo):0; int b=hh?(int)v_to_int(hi):n; if(a<0) a+=n; if(b<0) b+=n; if(a<0) a=0; if(b>n) b=n; int len=b-a; if(len<0) len=0; char* buf=malloc(len+1); memcpy(buf,obj.s+a,len); buf[len]=0; Value r=V_str(buf); free(buf); return r; }\n    return V_null();\n}\nstatic Value v_dot(Value obj, const char* name){ if(obj.t==T_DICT) return dict_get(obj.dict,name); return V_null(); }\nstatic void v_dot_set(Value obj, const char* name, Value val){ if(obj.t==T_DICT){ dict_set(obj.dict,name,val); return; } __catpp_raise("Cannot set field"); }\nstatic int v_in(Value nd, Value hy){\n    if(hy.t==T_LIST){ for(int i=0;i<hy.list->len;i++) if(v_cmp(hy.list->items[i],nd,0)) return 1; return 0; }\n    if(hy.t==T_DICT){ char* k=v_to_str(nd); int r=dict_has(hy.dict,k); free(k); return r; }\n    if(hy.t==T_STR){ char* n=v_to_str(nd); int r=strstr(hy.s,n)!=NULL; free(n); return r; }\n    return 0;\n}\n\n/* ═══ Struct ═══ */\nstatic Value v_struct_new(const char* name, const char** fields, int nf, Value* args, int argc){\n    VDict* d = dict_new();\n    dict_set(d, "__class__", V_str(name));\n    for(int i=0;i<nf;i++){\n        Value v = i < argc ? args[i] : V_null();\n        dict_set(d, fields[i], v);\n    }\n    return V_dict(d);\n}\nstatic long long v_sizeof_type(const char* name){\n    if(!strcmp(name,"i8")||!strcmp(name,"u8")||!strcmp(name,"bool")||!strcmp(name,"char")||!strcmp(name,"byte")) return 1;\n    if(!strcmp(name,"i16")||!strcmp(name,"u16")) return 2;\n    if(!strcmp(name,"i32")||!strcmp(name,"u32")) return 4;\n    return 8;\n}\n\n/* ═══ Classes ═══ */\ntypedef Value (*MethodFn)(Value me, Value* args, int argc);\ntypedef struct { const char* name; MethodFn fn; } MethodEntry;\ntypedef struct { const char* name; const char* parent; MethodEntry* methods; int nmeth; char** fields; int nfields; } ClassDef;\nstatic ClassDef** g_classes = NULL;\nstatic int g_nclasses = 0;\nstatic void reg_class(ClassDef* cd){ g_classes=realloc(g_classes,sizeof(ClassDef*)*(g_nclasses+1)); g_classes[g_nclasses++]=cd; }\nstatic ClassDef* find_class(const char* name){ for(int i=0;i<g_nclasses;i++) if(strcmp(g_classes[i]->name,name)==0) return g_classes[i]; return NULL; }\nstatic MethodFn find_method(ClassDef* cd, const char* name){\n    ClassDef* c = cd;\n    while(c){ for(int i=0;i<c->nmeth;i++) if(strcmp(c->methods[i].name,name)==0) return c->methods[i].fn;\n        if(!c->parent) break; c = find_class(c->parent);\n    }\n    return NULL;\n}\nstatic void collect_fields(ClassDef* cd, VDict* d){\n    if(cd->parent){ ClassDef* p=find_class(cd->parent); if(p) collect_fields(p,d); }\n    for(int i=0;i<cd->nfields;i++) if(!dict_has(d,cd->fields[i])) dict_set(d,cd->fields[i],V_null());\n}\nstatic Value v_new(const char* cls, Value* args, int argc){\n    ClassDef* cd=find_class(cls);\n    if(!cd) __catpp_raise("Class khong ton tai");\n    VDict* d=dict_new();\n    dict_set(d,"__class__",V_str(cls));\n    collect_fields(cd,d);\n    Value inst=V_dict(d);\n    MethodFn ctor=find_method(cd,"new");\n    if(ctor) ctor(inst,args,argc);\n    return inst;\n}\nstatic Value v_call_method(Value obj, const char* name, Value* args, int argc){\n    if(obj.t==T_DICT){\n        Value cls_v=dict_get(obj.dict,"__class__");\n        if(cls_v.t==T_STR){\n            ClassDef* cd=find_class(cls_v.s);\n            if(cd){ MethodFn fn=find_method(cd,name); if(fn) return fn(obj,args,argc); }\n        }\n    }\n    return V_null();\n}\n\n/* ═══ Builtins ═══ */\nstatic Value bi_tail(Value x){ if(x.t==T_LIST) return V_int(x.list->len); if(x.t==T_STR) return V_int(strlen(x.s)); if(x.t==T_DICT) return V_int(x.dict->len); return V_int(0); }\nstatic Value bi_puff(Value s){ char* c=v_to_str(s); for(char* p=c;*p;p++) *p=toupper((unsigned char)*p); Value r=V_str(c); free(c); return r; }\nstatic Value bi_melt(Value s){ char* c=v_to_str(s); for(char* p=c;*p;p++) *p=tolower((unsigned char)*p); Value r=V_str(c); free(c); return r; }\nstatic Value bi_nip(Value s, Value a, Value b){ char* c=v_to_str(s); int n=strlen(c); int i=(int)v_to_int(a), j=(int)v_to_int(b); if(i<0) i+=n; if(j<0) j+=n; if(i<0) i=0; if(j>n) j=n; int len=j-i; if(len<0) len=0; char* buf=malloc(len+1); memcpy(buf,c+i,len); buf[len]=0; Value r=V_str(buf); free(buf); free(c); return r; }\nstatic Value bi_bolt(Value x){ if(x.t==T_DOUBLE) return V_double(x.d<0?-x.d:x.d); long long v=v_to_int(x); return V_int(v<0?-v:v); }\nstatic Value bi_kitten(Value a, Value b){ return v_cmp(a,b,2)?a:b; }\nstatic Value bi_lion(Value a, Value b){ return v_cmp(a,b,3)?a:b; }\nstatic Value bi_say(Value x){ char* s=v_to_str(x); Value r=V_str(s); free(s); return r; }\nstatic Value bi_tally(Value x){ return V_int(v_to_int(x)); }\nstatic Value bi_drip(Value x){ return V_double(v_to_double(x)); }\nstatic Value bi_collar(Value d){ VList* l=list_new(); if(d.t==T_DICT) for(int i=0;i<d.dict->len;i++){ if(strcmp(d.dict->keys[i],"__class__")==0) continue; list_push(l,V_str(d.dict->keys[i])); } return V_list(l); }\nstatic Value bi_kits(Value d){ VList* l=list_new(); if(d.t==T_DICT) for(int i=0;i<d.dict->len;i++){ if(strcmp(d.dict->keys[i],"__class__")==0) continue; list_push(l,d.dict->vals[i]); } return V_list(l); }\nstatic Value bi_seek(Value d, Value k){ if(d.t!=T_DICT) return V_bool(0); char* kk=v_to_str(k); int r=dict_has(d.dict,kk); free(kk); return V_bool(r); }\nstatic Value bi_shred(Value s, Value sep){ char* str=v_to_str(s); char* sp=v_to_str(sep); VList* l=list_new(); int sl=strlen(sp); if(sl==0){ list_push(l,V_str(str)); } else { char* p=str; char* st=str; while(*p){ if(strncmp(p,sp,sl)==0){ char sv=*p; *p=0; list_push(l,V_str(st)); *p=sv; p+=sl; st=p; } else p++; } list_push(l,V_str(st)); } free(str); free(sp); return V_list(l); }\nstatic Value bi_weave(Value arr, Value sep){ if(arr.t!=T_LIST) return V_str(""); char* sp=v_to_str(sep); int cap=256, len=0; char* out=malloc(cap); out[0]=0; for(int i=0;i<arr.list->len;i++){ if(i>0){ int sl=strlen(sp); while(len+sl+3>=cap){ cap=cap*2+sl; out=realloc(out,cap);} memcpy(out+len,sp,sl); len+=sl; out[len]=0; } char* s=v_to_str(arr.list->items[i]); int sl=strlen(s); while(len+sl+3>=cap){ cap=cap*2+sl; out=realloc(out,cap);} memcpy(out+len,s,sl); len+=sl; out[len]=0; free(s); } Value r=V_str(out); free(out); free(sp); return r; }\nstatic Value bi_swap(Value s, Value a, Value b){ char* str=v_to_str(s); char* aa=v_to_str(a); char* bb=v_to_str(b); int cap=strlen(str)*2+1; char* o=malloc(cap); int ol=0; int al=strlen(aa), bl=strlen(bb); for(int i=0;str[i];){ if(strncmp(str+i,aa,al)==0){ while(ol+bl+2>=cap){ cap*=2; o=realloc(o,cap);} memcpy(o+ol,bb,bl); ol+=bl; i+=al; } else { while(ol+2>=cap){ cap*=2; o=realloc(o,cap);} o[ol++]=str[i++]; } } o[ol]=0; Value r=V_str(o); free(o); free(str); free(aa); free(bb); return r; }\nstatic Value bi_lick(Value s){ char* c=v_to_str(s); char* p=c; while(*p&&isspace((unsigned char)*p)) p++; char* e=p+strlen(p); while(e>p&&isspace((unsigned char)*(e-1))) *--e=0; Value r=V_str(p); free(c); return r; }\nstatic Value bi_hunt(Value s, Value sub){ char* c=v_to_str(s); char* n=v_to_str(sub); int r=strstr(c,n)!=NULL; free(c); free(n); return V_bool(r); }\nstatic Value bi_stash(Value a, Value v){ if(a.t==T_LIST) list_push(a.list,v); return a; }\nstatic Value bi_snatch(Value a){ if(a.t==T_LIST&&a.list->len>0) return a.list->items[--a.list->len]; return V_null(); }\nstatic Value bi_line(Value a){ if(a.t!=T_LIST) return a; VList* l=list_new(); for(int i=0;i<a.list->len;i++) list_push(l,a.list->items[i]); for(int i=1;i<l->len;i++){ Value k=l->items[i]; int j=i-1; while(j>=0&&v_cmp(l->items[j],k,3)){ l->items[j+1]=l->items[j]; j--; } l->items[j+1]=k; } return V_list(l); }\nstatic Value bi_flip(Value a){ if(a.t!=T_LIST) return a; VList* l=list_new(); for(int i=a.list->len-1;i>=0;i--) list_push(l,a.list->items[i]); return V_list(l); }\nstatic Value bi_head(Value a){ if(a.t==T_LIST&&a.list->len>0) return a.list->items[0]; return V_null(); }\nstatic Value bi_rear(Value a){ if(a.t==T_LIST&&a.list->len>0) return a.list->items[a.list->len-1]; return V_null(); }\nstatic Value bi_pile(Value a){ Value s=V_int(0); if(a.t==T_LIST) for(int i=0;i<a.list->len;i++) s=v_add(s,a.list->items[i]); return s; }\nstatic Value bi_walk(Value a, Value b){ VList* l=list_new(); long long x=v_to_int(a), y=v_to_int(b); if(x<=y) for(long long i=x;i<y;i++) list_push(l,V_int(i)); return V_list(l); }\nstatic Value bi_wander(void){ return V_double((double)rand()/RAND_MAX); }\nstatic Value bi_dice(Value a, Value b){ long long x=v_to_int(a), y=v_to_int(b); if(y<x){ long long t=x; x=y; y=t; } return V_int(x+rand()%(y-x+1)); }\nstatic Value bi_scratch(Value x){ return V_double(sqrt(v_to_double(x))); }\nstatic Value bi_flop(Value x){ return V_int((long long)floor(v_to_double(x))); }\nstatic Value bi_perch(Value x){ return V_int((long long)ceil(v_to_double(x))); }\nstatic Value bi_bound(Value a, Value b){ return V_double(pow(v_to_double(a), v_to_double(b))); }\nstatic Value bi_sway(Value x){ return V_double(sin(v_to_double(x))); }\nstatic Value bi_wave(Value x){ return V_double(cos(v_to_double(x))); }\nstatic Value bi_slant(Value x){ return V_double(tan(v_to_double(x))); }\nstatic Value bi_grow(Value x){ return V_double(log(v_to_double(x))); }\n\n/* ═══ Methods ═══ */\nstatic Value v_method(Value obj, const char* name, Value* args, int argc){\n    if(obj.t==T_STR){\n        char* s=obj.s;\n        if(!strcmp(name,"upper")){ char* o=strdup(s); for(char* p=o;*p;p++) *p=toupper((unsigned char)*p); Value r=V_str(o); free(o); return r; }\n        if(!strcmp(name,"lower")){ char* o=strdup(s); for(char* p=o;*p;p++) *p=tolower((unsigned char)*p); Value r=V_str(o); free(o); return r; }\n        if(!strcmp(name,"trim")){ char* c=strdup(s); char* p=c; while(*p&&isspace((unsigned char)*p)) p++; char* e=p+strlen(p); while(e>p&&isspace((unsigned char)*(e-1))) *--e=0; Value r=V_str(p); free(c); return r; }\n        if(!strcmp(name,"length")||!strcmp(name,"len")) return V_int(strlen(s));\n        if(!strcmp(name,"contains")){ char* n=v_to_str(args[0]); int r=strstr(s,n)!=NULL; free(n); return V_bool(r); }\n    }\n    if(obj.t==T_LIST){\n        if(!strcmp(name,"push")){ list_push(obj.list,args[0]); return obj; }\n        if(!strcmp(name,"pop")){ if(obj.list->len==0) __catpp_raise("Empty list"); return obj.list->items[--obj.list->len]; }\n        if(!strcmp(name,"length")||!strcmp(name,"len")) return V_int(obj.list->len);\n        if(!strcmp(name,"first")) return obj.list->len?obj.list->items[0]:V_null();\n        if(!strcmp(name,"last")) return obj.list->len?obj.list->items[obj.list->len-1]:V_null();\n        if(!strcmp(name,"contains")){ for(int i=0;i<obj.list->len;i++) if(v_cmp(obj.list->items[i],args[0],0)) return V_bool(1); return V_bool(0); }\n        if(!strcmp(name,"sum")){ Value s=V_int(0); for(int i=0;i<obj.list->len;i++) s=v_add(s,obj.list->items[i]); return s; }\n    }\n    if(obj.t==T_DICT){\n        if(!strcmp(name,"get")){ char* k=v_to_str(args[0]); Value r=dict_get(obj.dict,k); free(k); return r; }\n        if(!strcmp(name,"keys")){ VList* l=list_new(); for(int i=0;i<obj.dict->len;i++){ if(strcmp(obj.dict->keys[i],"__class__")==0) continue; list_push(l,V_str(obj.dict->keys[i])); } return V_list(l); }\n        if(!strcmp(name,"values")){ VList* l=list_new(); for(int i=0;i<obj.dict->len;i++){ if(strcmp(obj.dict->keys[i],"__class__")==0) continue; list_push(l,obj.dict->vals[i]); } return V_list(l); }\n        if(!strcmp(name,"has")){ char* k=v_to_str(args[0]); int r=dict_has(obj.dict,k); free(k); return V_bool(r); }\n        if(!strcmp(name,"size")||!strcmp(name,"len")) return V_int(obj.dict->len);\n    }\n    __catpp_raise("Khong co method");\n    return V_null();\n}\nstatic Value v_method_0(Value o, const char* n){ return v_method(o,n,NULL,0); }\nstatic Value v_method_n(Value o, const char* n, Value* a, int c){ return v_method(o,n,a,c); }\n\n'

BUILTIN_NAMES = {'tail','puff','melt','nip','bolt','kitten','lion','say','tally','drip',
    'collar','kits','seek','shred','weave','swap','lick','hunt','stash','snatch','line',
    'flip','head','rear','pile','walk','wander','dice','scratch','flop','perch','bound',
    'sway','wave','slant','grow'}

def c_esc(s):
    return s.replace('\\','\\\\').replace('"','\\"').replace('\n','\\n').replace('\t','\\t').replace('\r','\\r')

class CTranspiler:
    def __init__(self):
        self.out=[]; self.indent=0; self.funcs={}; self.classes={}; self.structs={}; self.tc=0
    def line(self,s=''): self.out.append('    '*self.indent+s)
    def new_tmp(self): self.tc+=1; return f'__t{self.tc}'

    def expr(self, e):
        t=e[0]
        if t=='num':
            v=e[1]
            if isinstance(v,float): return f'V_double({repr(v)})'
            return f'V_int({int(v)}LL)'
        if t=='str': return f'V_str("{c_esc(e[1])}")'
        if t=='bool': return f'V_bool({1 if e[1] else 0})'
        if t=='null': return 'V_null()'
        if t=='var': return e[1]
        if t=='neg': return f'v_neg({self.expr(e[1])})'
        if t=='not': return f'v_not({self.expr(e[1])})'
        if t=='bitnot': return f'V_int(~v_to_int({self.expr(e[1])}))'
        if t=='and': return f'V_bool(v_truthy({self.expr(e[1])}) && v_truthy({self.expr(e[2])}))'
        if t=='or': return f'V_bool(v_truthy({self.expr(e[1])}) || v_truthy({self.expr(e[2])}))'
        if t in ('+','-','*','/','%'):
            m={'+':'v_add','-':'v_sub','*':'v_mul','/':'v_div','%':'v_mod'}
            return f'{m[t]}({self.expr(e[1])}, {self.expr(e[2])})'
        if t in ('&','|','^'):
            return f'V_int(v_to_int({self.expr(e[1])}) {t} v_to_int({self.expr(e[2])}))'
        if t in ('SHL','SHR'):
            m='<<' if t=='SHL' else '>>'
            return f'V_int(v_to_int({self.expr(e[1])}) {m} v_to_int({self.expr(e[2])}))'
        if t in ('==','!=','<','>','<=','>='):
            op={'==':0,'!=':1,'<':2,'>':3,'<=':4,'>=':5}[t]
            return f'V_bool(v_cmp({self.expr(e[1])}, {self.expr(e[2])}, {op}))'
        if t=='list':
            items=e[1]
            if not items: return 'v_list_empty()'
            return f'v_list_build({len(items)}, (Value[]){{{", ".join(self.expr(x) for x in items)}}})'
        if t=='dict':
            pairs=e[1]
            if not pairs: return 'v_dict_empty()'
            ks=', '.join(self.expr(k) for k,v in pairs)
            vs=', '.join(self.expr(v) for k,v in pairs)
            return f'v_dict_build({len(pairs)}, (Value[]){{{ks}}}, (Value[]){{{vs}}})'
        if t=='index': return f'v_index({self.expr(e[1])}, {self.expr(e[2])})'
        if t=='slice':
            obj=self.expr(e[1])
            lo=self.expr(e[2]) if e[2] else 'V_null()'
            hi=self.expr(e[3]) if e[3] else 'V_null()'
            hl='1' if e[2] else '0'; hh='1' if e[3] else '0'
            return f'v_slice({obj}, {lo}, {hi}, {hl}, {hh})'
        if t=='dot': return f'v_dot({self.expr(e[1])}, "{e[2]}")'
        if t=='call':
            name=e[1]; args_list=e[2]
            args=', '.join(self.expr(a) for a in args_list)
            if name in self.structs:
                fields = self.structs[name]
                fields_c = ', '.join('"' + f + '"' for f in fields)
                if args_list:
                    return f'v_struct_new("{name}", (const char*[]){{{fields_c}}}, {len(fields)}, (Value[]){{{args}}}, {len(args_list)})'
                return f'v_struct_new("{name}", (const char*[]){{{fields_c}}}, {len(fields)}, NULL, 0)'
            if name in self.classes:
                return f'v_new("{name}", (Value[]){{{args}}}, {len(args_list)})' if args_list else f'v_new("{name}", NULL, 0)'
            if name in BUILTIN_NAMES: return f'bi_{name}({args})'
            return f'{name}({args})'
        if t=='method_call':
            obj=self.expr(e[1]); args=e[3]
            if not args: return f'v_call_method({obj}, "{e[2]}", NULL, 0)'
            inner=', '.join(self.expr(a) for a in args)
            return f'v_call_method({obj}, "{e[2]}", (Value[]){{{inner}}}, {len(args)})'
        if t=='in': return f'V_bool(v_in({self.expr(e[1])}, {self.expr(e[2])}))'
        if t=='ternary': return f'(v_truthy({self.expr(e[1])}) ? {self.expr(e[2])} : {self.expr(e[3])})'
        if t=='coalesce':
            l=self.expr(e[1])
            return f'({l}.t != T_NULL ? {l} : {self.expr(e[2])})'
        if t=='cast':
            tn=e[1].lower(); v=self.expr(e[2])
            if tn in ('i8','i16','i32','i64','int','u8','u16','u32','u64','byte','char','ptr'):
                return f'V_int(v_cast_int({v}))'
            if tn=='float': return f'V_double(v_cast_float({v}))'
            if tn=='bool': return f'V_bool(v_truthy({v}))'
            if tn=='str':
                return f'({{ char* __cs=v_to_str({v}); Value __cr=V_str(__cs); free(__cs); __cr; }})'
            return v
        if t=='sizeof': return 'V_int(8)'
        if t=='sizeof_type': return f'V_int(v_sizeof_type("{e[1]}"))'
        if t=='asm': return 'V_null()'
        if t=='addr': raise CatError("Transpiler C chua ho tro &x")
        if t=='deref': raise CatError("Transpiler C chua ho tro *p")
        if t=='lambda': raise CatError("Transpiler C chua ho tro kit (lambda)")
        raise CatError(f"Transpiler C chua ho tro expr: {t}")

    def collect_lets(self, stmts, into):
        for s in stmts:
            tt=s[0]
            if tt=='let': into.add(s[1])
            elif tt=='if':
                self.collect_lets(s[2],into)
                if s[3]: self.collect_lets(s[3],into)
            elif tt=='while': self.collect_lets(s[2],into)
            elif tt=='each': self.collect_lets(s[3],into)
            elif tt=='try':
                self.collect_lets(s[1], into)
                if s[3]: self.collect_lets(s[3], into)
            elif tt=='match':
                for pat, body in s[2]: self.collect_lets(body, into)

    def stmt(self, s):
        t=s[0]
        if t=='let': self.line(f'{s[1]} = {self.expr(s[2])};')
        elif t=='assign': self.line(f'{s[1]} = {self.expr(s[2])};')
        elif t=='assign_target':
            target=s[1]; val=self.expr(s[2])
            if target[0]=='index': self.line(f'v_index_set({self.expr(target[1])}, {self.expr(target[2])}, {val});')
            elif target[0]=='dot': self.line(f'v_dot_set({self.expr(target[1])}, "{target[2]}", {val});')
            elif target[0]=='var': self.line(f'{target[1]} = {val};')
            else: raise CatError("assign_target")
        elif t=='op_assign':
            target=s[1]; op=s[2]; rhs=s[3]
            if target[0]!='var': raise CatError("op_assign chi ho tro bien")
            name=target[1]; py_op=op[:-1]
            m={'+':'v_add','-':'v_sub','*':'v_mul','/':'v_div','%':'v_mod'}
            self.line(f'{name} = {m[py_op]}({name}, {self.expr(rhs)});')
        elif t=='print': self.line(f'v_print({self.expr(s[1])});')
        elif t=='expr': self.line(f'(void){self.expr(s[1])};')
        elif t=='return': self.line(f'return {self.expr(s[1])};')
        elif t=='if':
            self.line(f'if (v_truthy({self.expr(s[1])})) {{')
            self.indent+=1
            for x in s[2]: self.stmt(x)
            self.indent-=1
            if s[3]:
                self.line('} else {')
                self.indent+=1
                for x in s[3]: self.stmt(x)
                self.indent-=1
            self.line('}')
        elif t=='while':
            self.line(f'while (v_truthy({self.expr(s[1])})) {{')
            self.indent+=1
            for x in s[2]: self.stmt(x)
            self.indent-=1
            self.line('}')
        elif t=='each':
            name=s[1]; it=self.expr(s[2]); body=s[3]
            tmp=self.new_tmp(); idx=self.new_tmp()
            self.line(f'{{ Value {tmp} = {it};')
            self.line(f'  for (int {idx} = 0; {idx} < {tmp}.list->len; {idx}++) {{')
            self.line(f'    Value {name} = {tmp}.list->items[{idx}];')
            self.indent+=2
            for x in body: self.stmt(x)
            self.indent-=2
            self.line('  }')
            self.line('}')
        elif t=='stop': self.line('break;')
        elif t=='skip': self.line('continue;')
        elif t=='match':
            subj=self.expr(s[1]); tmp=self.new_tmp()
            self.line(f'{{ Value {tmp} = {subj};')
            self.indent+=1
            first=True
            for pat, body in s[2]:
                if pat[0]=='var' and pat[1]=='_':
                    if not first: self.line('else {')
                    else: self.line('{')
                else:
                    pv=self.expr(pat)
                    kw='if' if first else 'else if'
                    self.line(f'{kw} (v_cmp({tmp}, {pv}, 0)) {{')
                first=False
                self.indent+=1
                for x in body: self.stmt(x)
                self.indent-=1
                self.line('}')
            self.indent-=1
            self.line('}')
        elif t=='try':
            body, errname, handler = s[1], s[2], s[3]
            depth=self.new_tmp()
            self.line(f'{{ jmp_buf __jb_{depth}; int __save_{depth} = __jmp_top; __jmp_stack[__jmp_top++] = &__jb_{depth};')
            self.line(f'  if (setjmp(__jb_{depth}) == 0) {{')
            self.indent+=2
            for x in body: self.stmt(x)
            self.indent-=2
            if handler:
                self.line('  } else {')
                self.indent+=2
                if errname:
                    self.line(f'Value {errname} = V_str(__catpp_err_msg);')
                for x in handler: self.stmt(x)
                self.indent-=2
                self.line('  }')
            else:
                self.line('  }')
            self.line(f'  __jmp_top = __save_{depth};')
            self.line('}')
        else: raise CatError(f"Transpiler C chua ho tro stmt: {t}")

    def emit_func(self, s):
        name=s[1]; params=s[2]; body=s[4]
        pd=', '.join(f'Value {p}' for p in params) if params else 'void'
        self.line(f'static Value {name}({pd}) {{')
        self.indent+=1
        lets=set(); self.collect_lets(body, lets); lets-=set(params)
        for v in sorted(lets): self.line(f'Value {v};')
        for x in body: self.stmt(x)
        self.line('return V_null();')
        self.indent-=1
        self.line('}')

    def emit_method(self, cidx, midx, params, body):
        fname=f'__meth_{cidx}_{midx}'
        self.line(f'static Value {fname}(Value me, Value* __args, int __argc) {{')
        self.indent+=1
        for i,p in enumerate(params):
            self.line(f'Value {p} = __argc > {i} ? __args[{i}] : V_null();')
        lets=set(); self.collect_lets(body, lets); lets-=set(params)
        for v in sorted(lets): self.line(f'Value {v};')
        for x in body: self.stmt(x)
        self.line('return V_null();')
        self.indent-=1
        self.line('}')
        return fname

    def emit_class(self, s, cidx):
        name=s[1]; parent=s[2]; fields=s[3]; methods=s[4]
        mnames=[]
        for mi,(mname,(params,body)) in enumerate(methods.items()):
            fname=f'__meth_{cidx}_{mi}'
            self.line(f'static Value {fname}(Value me, Value* __args, int __argc);')
            mnames.append((mname,fname))
        self.out.append('')
        for mi,(mname,(params,body)) in enumerate(methods.items()):
            self.emit_method(cidx, mi, params, body)
            self.line('')
        tbl=f'__methods_{cidx}'
        self.line(f'static MethodEntry {tbl}[] = {{')
        self.indent+=1
        for mname,fname in mnames:
            self.line(f'{{ "{mname}", {fname} }},')
        if not mnames: self.line('{ "", NULL },')
        self.indent-=1
        self.line('};')
        ftbl=f'__fields_{cidx}'
        self.line(f'static char* {ftbl}[] = {{')
        self.indent+=1
        for f in fields:
            self.line(f'"{f}",')
        if not fields: self.line('NULL,')
        self.indent-=1
        self.line('};')
        par=f'"{parent}"' if parent else 'NULL'
        self.line(f'static ClassDef __clsd_{cidx} = {{ "{name}", {par}, {tbl}, {len(mnames)}, {ftbl}, {len(fields)} }};')
        self.line('')

    def compile(self, ast):
        cidx=0
        for s in ast:
            if s[0]=='struct': self.structs[s[1]]=s[2]
        for s in ast:
            if s[0]=='func': self.funcs[s[1]]=(s[2],s[4])
            elif s[0]=='class': self.classes[s[1]]=cidx; cidx+=1

        self.out.append(RUNTIME)
        self.out.append('')

        for name,(params,_) in self.funcs.items():
            pd=', '.join(f'Value {p}' for p in params) if params else 'void'
            self.line(f'static Value {name}({pd});')
        self.out.append('')

        for s in ast:
            if s[0]=='class':
                self.emit_class(s, self.classes[s[1]])
        for s in ast:
            if s[0]=='func':
                self.emit_func(s); self.line('')

        self.line('int main(void) {')
        self.indent+=1
        for s in ast:
            if s[0]=='class':
                self.line(f'reg_class(&__clsd_{self.classes[s[1]]});')
        top=[s for s in ast if s[0] not in ('func','class','struct')]
        lets=set(); self.collect_lets(top, lets)
        for v in sorted(lets): self.line(f'Value {v};')
        for s in top: self.stmt(s)
        self.line('return 0;')
        self.indent-=1
        self.line('}')
        return '\n'.join(self.out)


def _resolve_uses(ast, base_dir):
    result = []
    for s in ast:
        if s[0] == 'use':
            fname = s[1]
            candidates = [os.path.join(base_dir, fname), os.path.join(base_dir,'examples',fname), fname]
            found = None
            for p in candidates:
                if os.path.exists(p):
                    found = p; break
            if not found:
                raise CatError(f"Khong tim thay file '{fname}'")
            with open(found, encoding='utf-8') as f:
                lib_src = f.read()
            lib_ast = Parser(tokenize(lib_src)).parse()
            result.extend(_resolve_uses(lib_ast, os.path.dirname(found) or base_dir))
        else:
            result.append(s)
    return result


def transpile(source, base_dir='.'):
    ast = Parser(tokenize(source)).parse()
    ast = _resolve_uses(ast, base_dir)
    return CTranspiler().compile(ast)


def main():
    if len(sys.argv)<2:
        print(__doc__); return 1
    src=sys.argv[1]
    with open(src, encoding='utf-8') as f: source=f.read()
    try: c_code=transpile(source, base_dir=os.path.dirname(os.path.abspath(src)))
    except CatError as e: print(f'X {e}'); return 1
    out=src.rsplit('.',1)[0]+'.c'
    if '-o' in sys.argv: out=sys.argv[sys.argv.index('-o')+1]
    with open(out,'w',encoding='utf-8') as f: f.write(c_code)
    print(f'OK {out}')
    if '--run' in sys.argv:
        binp=out.rsplit('.',1)[0]
        r=subprocess.run(['gcc','-O2','-lm','-o',binp,out], capture_output=True, text=True)
        if r.returncode!=0: print('gcc fail:'); print(r.stderr); return 1
        r=subprocess.run([binp], capture_output=True, text=True)
        print('--- Output ---'); print(r.stdout, end='')
        if r.stderr: print(r.stderr, end='')
    return 0

if __name__=='__main__': sys.exit(main())
