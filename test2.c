#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <setjmp.h>
#include <math.h>

typedef enum { T_INT, T_DOUBLE, T_STR, T_NULL, T_BOOL, T_LIST, T_DICT } VTag;
typedef struct Value Value;
typedef struct { int len, cap; Value* items; } VList;
typedef struct { int len, cap; char** keys; Value* vals; } VDict;
struct Value { VTag t; long long i; double d; char* s; VList* list; VDict* dict; };

static char* v_to_str(Value v);
static int v_truthy(Value v);
static Value v_method(Value obj, const char* name, Value* args, int argc);

/* ═══ Error handling ═══ */
static jmp_buf* __jmp_stack[64];
static int __jmp_top = 0;
static char __catpp_err_msg[512];
static void __catpp_raise(const char* msg){
    if (__jmp_top > 0) {
        strncpy(__catpp_err_msg, msg, 511);
        __catpp_err_msg[511] = 0;
        longjmp(*__jmp_stack[__jmp_top-1], 1);
    }
    fprintf(stderr, "%s\n", msg);
    exit(1);
}

/* ═══ Value constructors ═══ */
static Value V_int(long long v){ Value r; memset(&r,0,sizeof(r)); r.t=T_INT; r.i=v; return r; }
static Value V_double(double v){ Value r; memset(&r,0,sizeof(r)); r.t=T_DOUBLE; r.d=v; return r; }
static Value V_str(const char* v){ Value r; memset(&r,0,sizeof(r)); r.t=T_STR; r.s=strdup(v?v:""); return r; }
static Value V_null(void){ Value r; memset(&r,0,sizeof(r)); r.t=T_NULL; return r; }
static Value V_bool(int v){ Value r; memset(&r,0,sizeof(r)); r.t=T_BOOL; r.i=v?1:0; return r; }
static Value V_list(VList* l){ Value r; memset(&r,0,sizeof(r)); r.t=T_LIST; r.list=l; return r; }
static Value V_dict(VDict* d){ Value r; memset(&r,0,sizeof(r)); r.t=T_DICT; r.dict=d; return r; }

/* ═══ List / Dict ═══ */
static VList* list_new(void){ VList* l=malloc(sizeof(VList)); l->len=0; l->cap=4; l->items=malloc(sizeof(Value)*4); return l; }
static void list_push(VList* l, Value v){ if(l->len>=l->cap){ l->cap*=2; l->items=realloc(l->items, sizeof(Value)*l->cap); } l->items[l->len++]=v; }
static VDict* dict_new(void){ VDict* d=malloc(sizeof(VDict)); d->len=0; d->cap=4; d->keys=malloc(sizeof(char*)*4); d->vals=malloc(sizeof(Value)*4); return d; }
static int dict_find(VDict* d, const char* k){ for(int i=0;i<d->len;i++) if(strcmp(d->keys[i],k)==0) return i; return -1; }
static void dict_set(VDict* d, const char* k, Value v){ int i=dict_find(d,k); if(i>=0){ d->vals[i]=v; return; } if(d->len>=d->cap){ d->cap*=2; d->keys=realloc(d->keys,sizeof(char*)*d->cap); d->vals=realloc(d->vals,sizeof(Value)*d->cap); } d->keys[d->len]=strdup(k); d->vals[d->len]=v; d->len++; }
static Value dict_get(VDict* d, const char* k){ int i=dict_find(d,k); return i>=0?d->vals[i]:V_null(); }
static int dict_has(VDict* d, const char* k){ return dict_find(d,k)>=0; }

static Value v_list_build(int n, Value* items){ VList* l=list_new(); for(int i=0;i<n;i++) list_push(l,items[i]); return V_list(l); }
static Value v_list_empty(void){ return V_list(list_new()); }
static Value v_dict_build(int n, Value* keys, Value* vals){ VDict* d=dict_new(); for(int i=0;i<n;i++){ char* k=v_to_str(keys[i]); dict_set(d,k,vals[i]); free(k); } return V_dict(d); }
static Value v_dict_empty(void){ return V_dict(dict_new()); }

/* ═══ Type checks / conversions ═══ */
static int v_truthy(Value v){
    switch(v.t){
        case T_NULL: return 0;
        case T_BOOL: case T_INT: return v.i!=0;
        case T_DOUBLE: return v.d!=0.0;
        case T_STR: return v.s && v.s[0];
        case T_LIST: return v.list->len!=0;
        case T_DICT: return v.dict->len!=0;
    } return 0;
}
static double v_to_double(Value v){ if(v.t==T_INT) return (double)v.i; if(v.t==T_DOUBLE) return v.d; if(v.t==T_BOOL) return (double)v.i; return 0.0; }
static long long v_to_int(Value v){ if(v.t==T_INT) return v.i; if(v.t==T_DOUBLE) return (long long)v.d; if(v.t==T_BOOL) return v.i; return 0; }
static long long v_cast_int(Value v){
    if(v.t==T_INT) return v.i;
    if(v.t==T_DOUBLE) return (long long)v.d;
    if(v.t==T_BOOL) return v.i;
    if(v.t==T_STR) return (long long)atoll(v.s);
    return 0;
}
static double v_cast_float(Value v){
    if(v.t==T_INT) return (double)v.i;
    if(v.t==T_DOUBLE) return v.d;
    if(v.t==T_BOOL) return (double)v.i;
    if(v.t==T_STR) return atof(v.s);
    return 0.0;
}

/* ═══ to_str ═══ */
static char* v_to_str(Value v){
    char buf[64];
    switch(v.t){
        case T_NULL: return strdup("hungry");
        case T_BOOL: return strdup(v.i?"nod":"shake");
        case T_INT: sprintf(buf,"%lld",v.i); return strdup(buf);
        case T_DOUBLE: if(v.d==(long long)v.d) sprintf(buf,"%lld",(long long)v.d); else sprintf(buf,"%g",v.d); return strdup(buf);
        case T_STR: return strdup(v.s?v.s:"");
        case T_LIST: {
            int cap=256, len=0; char* out=malloc(cap); out[len++]='['; out[len]=0;
            for(int i=0;i<v.list->len;i++){
                if(i>0){ while(len+3>=cap){ cap*=2; out=realloc(out,cap);} out[len++]=','; out[len++]=' '; out[len]=0; }
                char* it=v_to_str(v.list->items[i]); int il=strlen(it);
                while(len+il+3>=cap){ cap=cap*2+il; out=realloc(out,cap); }
                memcpy(out+len,it,il); len+=il; out[len]=0; free(it);
            }
            while(len+2>=cap){ cap*=2; out=realloc(out,cap);} out[len++]=']'; out[len]=0; return out;
        }
        case T_DICT: {
            int cap=256, len=0; char* out=malloc(cap); out[len++]='{'; out[len]=0;
            int first=1;
            for(int i=0;i<v.dict->len;i++){
                if(strcmp(v.dict->keys[i],"__class__")==0) continue;
                if(!first){ while(len+3>=cap){ cap*=2; out=realloc(out,cap);} out[len++]=','; out[len++]=' '; out[len]=0; }
                first=0;
                int kl=strlen(v.dict->keys[i]);
                while(len+kl+3>=cap){ cap=cap*2+kl; out=realloc(out,cap);} memcpy(out+len,v.dict->keys[i],kl); len+=kl;
                while(len+3>=cap){ cap*=2; out=realloc(out,cap);} out[len++]=':'; out[len++]=' '; out[len]=0;
                char* val=v_to_str(v.dict->vals[i]); int vl=strlen(val);
                while(len+vl+3>=cap){ cap=cap*2+vl; out=realloc(out,cap);} memcpy(out+len,val,vl); len+=vl; out[len]=0; free(val);
            }
            while(len+2>=cap){ cap*=2; out=realloc(out,cap);} out[len++]='}'; out[len]=0; return out;
        }
    }
    return strdup("?");
}

/* ═══ Operators ═══ */
static Value v_add(Value a, Value b){
    if(a.t==T_STR||b.t==T_STR){ char* sa=v_to_str(a); char* sb=v_to_str(b); char* r=malloc(strlen(sa)+strlen(sb)+1); strcpy(r,sa); strcat(r,sb); Value o=V_str(r); free(sa); free(sb); free(r); return o; }
    if(a.t==T_LIST&&b.t==T_LIST){ VList* l=list_new(); for(int i=0;i<a.list->len;i++) list_push(l,a.list->items[i]); for(int i=0;i<b.list->len;i++) list_push(l,b.list->items[i]); return V_list(l); }
    if(a.t==T_DOUBLE||b.t==T_DOUBLE) return V_double(v_to_double(a)+v_to_double(b));
    return V_int(v_to_int(a)+v_to_int(b));
}
static Value v_sub(Value a, Value b){ if(a.t==T_DOUBLE||b.t==T_DOUBLE) return V_double(v_to_double(a)-v_to_double(b)); return V_int(v_to_int(a)-v_to_int(b)); }
static Value v_mul(Value a, Value b){ if(a.t==T_DOUBLE||b.t==T_DOUBLE) return V_double(v_to_double(a)*v_to_double(b)); return V_int(v_to_int(a)*v_to_int(b)); }
static Value v_div(Value a, Value b){ if(a.t==T_INT&&b.t==T_INT){ if(b.i==0) __catpp_raise("Chia cho 0"); if(a.i%b.i==0) return V_int(a.i/b.i);} double d=v_to_double(b); if(d==0.0) __catpp_raise("Chia cho 0"); return V_double(v_to_double(a)/d); }
static Value v_mod(Value a, Value b){ long long bi=v_to_int(b); if(bi==0) __catpp_raise("Mod 0"); return V_int(v_to_int(a)%bi); }
static Value v_neg(Value a){ if(a.t==T_DOUBLE) return V_double(-a.d); return V_int(-v_to_int(a)); }
static Value v_not(Value a){ return V_bool(!v_truthy(a)); }

static int v_cmp(Value a, Value b, int op){
    if(a.t==T_STR||b.t==T_STR){ char* sa=v_to_str(a); char* sb=v_to_str(b); int r=strcmp(sa,sb); free(sa); free(sb);
        switch(op){ case 0: return r==0; case 1: return r!=0; case 2: return r<0; case 3: return r>0; case 4: return r<=0; case 5: return r>=0; } }
    if(a.t==T_DOUBLE||b.t==T_DOUBLE){ double x=v_to_double(a), y=v_to_double(b);
        switch(op){ case 0: return x==y; case 1: return x!=y; case 2: return x<y; case 3: return x>y; case 4: return x<=y; case 5: return x>=y; } }
    long long x=v_to_int(a), y=v_to_int(b);
    switch(op){ case 0: return x==y; case 1: return x!=y; case 2: return x<y; case 3: return x>y; case 4: return x<=y; case 5: return x>=y; }
    return 0;
}
static void v_print(Value v){ char* s=v_to_str(v); printf("%s\n",s); free(s); }

static Value v_index(Value obj, Value idx){
    if(obj.t==T_LIST){ long long i=v_to_int(idx); if(i<0) i+=obj.list->len; if(i<0||i>=obj.list->len) __catpp_raise("Index out of range"); return obj.list->items[i]; }
    if(obj.t==T_DICT){ char* k=v_to_str(idx); Value r=dict_get(obj.dict,k); free(k); return r; }
    if(obj.t==T_STR){ long long i=v_to_int(idx); long long n=strlen(obj.s); if(i<0) i+=n; if(i<0||i>=n) __catpp_raise("Str index"); char b[2]={obj.s[i],0}; return V_str(b); }
    return V_null();
}
static void v_index_set(Value obj, Value idx, Value val){
    if(obj.t==T_LIST){ long long i=v_to_int(idx); if(i<0) i+=obj.list->len; if(i<0||i>=obj.list->len) __catpp_raise("Index set"); obj.list->items[i]=val; return; }
    if(obj.t==T_DICT){ char* k=v_to_str(idx); dict_set(obj.dict,k,val); free(k); return; }
    __catpp_raise("Cannot index-set");
}
static Value v_slice(Value obj, Value lo, Value hi, int hl, int hh){
    if(obj.t==T_LIST){ int n=obj.list->len; int a=hl?(int)v_to_int(lo):0; int b=hh?(int)v_to_int(hi):n; if(a<0) a+=n; if(b<0) b+=n; if(a<0) a=0; if(b>n) b=n; VList* r=list_new(); for(int i=a;i<b;i++) list_push(r,obj.list->items[i]); return V_list(r); }
    if(obj.t==T_STR){ int n=strlen(obj.s); int a=hl?(int)v_to_int(lo):0; int b=hh?(int)v_to_int(hi):n; if(a<0) a+=n; if(b<0) b+=n; if(a<0) a=0; if(b>n) b=n; int len=b-a; if(len<0) len=0; char* buf=malloc(len+1); memcpy(buf,obj.s+a,len); buf[len]=0; Value r=V_str(buf); free(buf); return r; }
    return V_null();
}
static Value v_dot(Value obj, const char* name){ if(obj.t==T_DICT) return dict_get(obj.dict,name); return V_null(); }
static void v_dot_set(Value obj, const char* name, Value val){ if(obj.t==T_DICT){ dict_set(obj.dict,name,val); return; } __catpp_raise("Cannot set field"); }
static int v_in(Value nd, Value hy){
    if(hy.t==T_LIST){ for(int i=0;i<hy.list->len;i++) if(v_cmp(hy.list->items[i],nd,0)) return 1; return 0; }
    if(hy.t==T_DICT){ char* k=v_to_str(nd); int r=dict_has(hy.dict,k); free(k); return r; }
    if(hy.t==T_STR){ char* n=v_to_str(nd); int r=strstr(hy.s,n)!=NULL; free(n); return r; }
    return 0;
}

/* ═══ Struct ═══ */
static Value v_struct_new(const char* name, const char** fields, int nf, Value* args, int argc){
    VDict* d = dict_new();
    dict_set(d, "__class__", V_str(name));
    for(int i=0;i<nf;i++){
        Value v = i < argc ? args[i] : V_null();
        dict_set(d, fields[i], v);
    }
    return V_dict(d);
}
static long long v_sizeof_type(const char* name){
    if(!strcmp(name,"i8")||!strcmp(name,"u8")||!strcmp(name,"bool")||!strcmp(name,"char")||!strcmp(name,"byte")) return 1;
    if(!strcmp(name,"i16")||!strcmp(name,"u16")) return 2;
    if(!strcmp(name,"i32")||!strcmp(name,"u32")) return 4;
    return 8;
}

/* ═══ Classes ═══ */
typedef Value (*MethodFn)(Value me, Value* args, int argc);
typedef struct { const char* name; MethodFn fn; } MethodEntry;
typedef struct { const char* name; const char* parent; MethodEntry* methods; int nmeth; char** fields; int nfields; } ClassDef;
static ClassDef** g_classes = NULL;
static int g_nclasses = 0;
static void reg_class(ClassDef* cd){ g_classes=realloc(g_classes,sizeof(ClassDef*)*(g_nclasses+1)); g_classes[g_nclasses++]=cd; }
static ClassDef* find_class(const char* name){ for(int i=0;i<g_nclasses;i++) if(strcmp(g_classes[i]->name,name)==0) return g_classes[i]; return NULL; }
static MethodFn find_method(ClassDef* cd, const char* name){
    ClassDef* c = cd;
    while(c){ for(int i=0;i<c->nmeth;i++) if(strcmp(c->methods[i].name,name)==0) return c->methods[i].fn;
        if(!c->parent) break; c = find_class(c->parent);
    }
    return NULL;
}
static void collect_fields(ClassDef* cd, VDict* d){
    if(cd->parent){ ClassDef* p=find_class(cd->parent); if(p) collect_fields(p,d); }
    for(int i=0;i<cd->nfields;i++) if(!dict_has(d,cd->fields[i])) dict_set(d,cd->fields[i],V_null());
}
static Value v_new(const char* cls, Value* args, int argc){
    ClassDef* cd=find_class(cls);
    if(!cd) __catpp_raise("Class khong ton tai");
    VDict* d=dict_new();
    dict_set(d,"__class__",V_str(cls));
    collect_fields(cd,d);
    Value inst=V_dict(d);
    MethodFn ctor=find_method(cd,"new");
    if(ctor) ctor(inst,args,argc);
    return inst;
}
static Value v_call_method(Value obj, const char* name, Value* args, int argc){
    if(obj.t==T_DICT){
        Value cls_v=dict_get(obj.dict,"__class__");
        if(cls_v.t==T_STR){
            ClassDef* cd=find_class(cls_v.s);
            if(cd){ MethodFn fn=find_method(cd,name); if(fn) return fn(obj,args,argc); }
        }
    }
    return v_method(obj, name, args, argc);
}

/* ═══ Builtins ═══ */
static Value bi_tail(Value x){ if(x.t==T_LIST) return V_int(x.list->len); if(x.t==T_STR) return V_int(strlen(x.s)); if(x.t==T_DICT) return V_int(x.dict->len); return V_int(0); }
static Value bi_puff(Value s){ char* c=v_to_str(s); for(char* p=c;*p;p++) *p=toupper((unsigned char)*p); Value r=V_str(c); free(c); return r; }
static Value bi_melt(Value s){ char* c=v_to_str(s); for(char* p=c;*p;p++) *p=tolower((unsigned char)*p); Value r=V_str(c); free(c); return r; }
static Value bi_nip(Value s, Value a, Value b){ char* c=v_to_str(s); int n=strlen(c); int i=(int)v_to_int(a), j=(int)v_to_int(b); if(i<0) i+=n; if(j<0) j+=n; if(i<0) i=0; if(j>n) j=n; int len=j-i; if(len<0) len=0; char* buf=malloc(len+1); memcpy(buf,c+i,len); buf[len]=0; Value r=V_str(buf); free(buf); free(c); return r; }
static Value bi_bolt(Value x){ if(x.t==T_DOUBLE) return V_double(x.d<0?-x.d:x.d); long long v=v_to_int(x); return V_int(v<0?-v:v); }
static Value bi_kitten(Value a, Value b){ return v_cmp(a,b,2)?a:b; }
static Value bi_lion(Value a, Value b){ return v_cmp(a,b,3)?a:b; }
static Value bi_say(Value x){ char* s=v_to_str(x); Value r=V_str(s); free(s); return r; }
static Value bi_tally(Value x){ return V_int(v_to_int(x)); }
static Value bi_drip(Value x){ return V_double(v_to_double(x)); }
static Value bi_collar(Value d){ VList* l=list_new(); if(d.t==T_DICT) for(int i=0;i<d.dict->len;i++){ if(strcmp(d.dict->keys[i],"__class__")==0) continue; list_push(l,V_str(d.dict->keys[i])); } return V_list(l); }
static Value bi_kits(Value d){ VList* l=list_new(); if(d.t==T_DICT) for(int i=0;i<d.dict->len;i++){ if(strcmp(d.dict->keys[i],"__class__")==0) continue; list_push(l,d.dict->vals[i]); } return V_list(l); }
static Value bi_seek(Value d, Value k){ if(d.t!=T_DICT) return V_bool(0); char* kk=v_to_str(k); int r=dict_has(d.dict,kk); free(kk); return V_bool(r); }
static Value bi_shred(Value s, Value sep){ char* str=v_to_str(s); char* sp=v_to_str(sep); VList* l=list_new(); int sl=strlen(sp); if(sl==0){ list_push(l,V_str(str)); } else { char* p=str; char* st=str; while(*p){ if(strncmp(p,sp,sl)==0){ char sv=*p; *p=0; list_push(l,V_str(st)); *p=sv; p+=sl; st=p; } else p++; } list_push(l,V_str(st)); } free(str); free(sp); return V_list(l); }
static Value bi_weave(Value arr, Value sep){ if(arr.t!=T_LIST) return V_str(""); char* sp=v_to_str(sep); int cap=256, len=0; char* out=malloc(cap); out[0]=0; for(int i=0;i<arr.list->len;i++){ if(i>0){ int sl=strlen(sp); while(len+sl+3>=cap){ cap=cap*2+sl; out=realloc(out,cap);} memcpy(out+len,sp,sl); len+=sl; out[len]=0; } char* s=v_to_str(arr.list->items[i]); int sl=strlen(s); while(len+sl+3>=cap){ cap=cap*2+sl; out=realloc(out,cap);} memcpy(out+len,s,sl); len+=sl; out[len]=0; free(s); } Value r=V_str(out); free(out); free(sp); return r; }
static Value bi_swap(Value s, Value a, Value b){ char* str=v_to_str(s); char* aa=v_to_str(a); char* bb=v_to_str(b); int cap=strlen(str)*2+1; char* o=malloc(cap); int ol=0; int al=strlen(aa), bl=strlen(bb); for(int i=0;str[i];){ if(strncmp(str+i,aa,al)==0){ while(ol+bl+2>=cap){ cap*=2; o=realloc(o,cap);} memcpy(o+ol,bb,bl); ol+=bl; i+=al; } else { while(ol+2>=cap){ cap*=2; o=realloc(o,cap);} o[ol++]=str[i++]; } } o[ol]=0; Value r=V_str(o); free(o); free(str); free(aa); free(bb); return r; }
static Value bi_lick(Value s){ char* c=v_to_str(s); char* p=c; while(*p&&isspace((unsigned char)*p)) p++; char* e=p+strlen(p); while(e>p&&isspace((unsigned char)*(e-1))) *--e=0; Value r=V_str(p); free(c); return r; }
static Value bi_hunt(Value s, Value sub){ char* c=v_to_str(s); char* n=v_to_str(sub); int r=strstr(c,n)!=NULL; free(c); free(n); return V_bool(r); }
static Value bi_stash(Value a, Value v){ if(a.t==T_LIST) list_push(a.list,v); return a; }
static Value bi_snatch(Value a){ if(a.t==T_LIST&&a.list->len>0) return a.list->items[--a.list->len]; return V_null(); }
static Value bi_line(Value a){ if(a.t!=T_LIST) return a; VList* l=list_new(); for(int i=0;i<a.list->len;i++) list_push(l,a.list->items[i]); for(int i=1;i<l->len;i++){ Value k=l->items[i]; int j=i-1; while(j>=0&&v_cmp(l->items[j],k,3)){ l->items[j+1]=l->items[j]; j--; } l->items[j+1]=k; } return V_list(l); }
static Value bi_flip(Value a){ if(a.t!=T_LIST) return a; VList* l=list_new(); for(int i=a.list->len-1;i>=0;i--) list_push(l,a.list->items[i]); return V_list(l); }
static Value bi_head(Value a){ if(a.t==T_LIST&&a.list->len>0) return a.list->items[0]; return V_null(); }
static Value bi_rear(Value a){ if(a.t==T_LIST&&a.list->len>0) return a.list->items[a.list->len-1]; return V_null(); }
static Value bi_pile(Value a){ Value s=V_int(0); if(a.t==T_LIST) for(int i=0;i<a.list->len;i++) s=v_add(s,a.list->items[i]); return s; }
static Value bi_walk(Value a, Value b){ VList* l=list_new(); long long x=v_to_int(a), y=v_to_int(b); if(x<=y) for(long long i=x;i<y;i++) list_push(l,V_int(i)); return V_list(l); }
static Value bi_wander(void){ return V_double((double)rand()/RAND_MAX); }
static Value bi_dice(Value a, Value b){ long long x=v_to_int(a), y=v_to_int(b); if(y<x){ long long t=x; x=y; y=t; } return V_int(x+rand()%(y-x+1)); }
static Value bi_scratch(Value x){ return V_double(sqrt(v_to_double(x))); }
static Value bi_flop(Value x){ return V_int((long long)floor(v_to_double(x))); }
static Value bi_perch(Value x){ return V_int((long long)ceil(v_to_double(x))); }
static Value bi_bound(Value a, Value b){ return V_double(pow(v_to_double(a), v_to_double(b))); }
static Value bi_sway(Value x){ return V_double(sin(v_to_double(x))); }
static Value bi_wave(Value x){ return V_double(cos(v_to_double(x))); }
static Value bi_slant(Value x){ return V_double(tan(v_to_double(x))); }
static Value bi_grow(Value x){ return V_double(log(v_to_double(x))); }

/* ═══ Methods ═══ */
static Value v_method(Value obj, const char* name, Value* args, int argc){
    if(obj.t==T_STR){
        char* s=obj.s;
        if(!strcmp(name,"upper")){ char* o=strdup(s); for(char* p=o;*p;p++) *p=toupper((unsigned char)*p); Value r=V_str(o); free(o); return r; }
        if(!strcmp(name,"lower")){ char* o=strdup(s); for(char* p=o;*p;p++) *p=tolower((unsigned char)*p); Value r=V_str(o); free(o); return r; }
        if(!strcmp(name,"trim")){ char* c=strdup(s); char* p=c; while(*p&&isspace((unsigned char)*p)) p++; char* e=p+strlen(p); while(e>p&&isspace((unsigned char)*(e-1))) *--e=0; Value r=V_str(p); free(c); return r; }
        if(!strcmp(name,"length")||!strcmp(name,"len")) return V_int(strlen(s));
        if(!strcmp(name,"contains")){ char* n=v_to_str(args[0]); int r=strstr(s,n)!=NULL; free(n); return V_bool(r); }
    }
    if(obj.t==T_LIST){
        if(!strcmp(name,"push")){ list_push(obj.list,args[0]); return obj; }
        if(!strcmp(name,"pop")){ if(obj.list->len==0) __catpp_raise("Empty list"); return obj.list->items[--obj.list->len]; }
        if(!strcmp(name,"length")||!strcmp(name,"len")) return V_int(obj.list->len);
        if(!strcmp(name,"first")) return obj.list->len?obj.list->items[0]:V_null();
        if(!strcmp(name,"last")) return obj.list->len?obj.list->items[obj.list->len-1]:V_null();
        if(!strcmp(name,"contains")){ for(int i=0;i<obj.list->len;i++) if(v_cmp(obj.list->items[i],args[0],0)) return V_bool(1); return V_bool(0); }
        if(!strcmp(name,"sum")){ Value s=V_int(0); for(int i=0;i<obj.list->len;i++) s=v_add(s,obj.list->items[i]); return s; }
    }
    if(obj.t==T_DICT){
        if(!strcmp(name,"get")){ char* k=v_to_str(args[0]); Value r=dict_get(obj.dict,k); free(k); return r; }
        if(!strcmp(name,"keys")){ VList* l=list_new(); for(int i=0;i<obj.dict->len;i++){ if(strcmp(obj.dict->keys[i],"__class__")==0) continue; list_push(l,V_str(obj.dict->keys[i])); } return V_list(l); }
        if(!strcmp(name,"values")){ VList* l=list_new(); for(int i=0;i<obj.dict->len;i++){ if(strcmp(obj.dict->keys[i],"__class__")==0) continue; list_push(l,obj.dict->vals[i]); } return V_list(l); }
        if(!strcmp(name,"has")){ char* k=v_to_str(args[0]); int r=dict_has(obj.dict,k); free(k); return V_bool(r); }
        if(!strcmp(name,"size")||!strcmp(name,"len")) return V_int(obj.dict->len);
    }
    __catpp_raise("Khong co method");
    return V_null();
}
static Value v_method_0(Value o, const char* n){ return v_method(o,n,NULL,0); }
static Value v_method_n(Value o, const char* n, Value* a, int c){ return v_method(o,n,a,c); }




int main(void) {
    Value a;
    Value d;
    Value s;
    s = V_str("Hello");
    v_print(v_call_method(s, "upper", NULL, 0));
    v_print(v_call_method(s, "lower", NULL, 0));
    v_print(bi_tail(s));
    d = v_dict_build(2, (Value[]){V_str("name"), V_str("age")}, (Value[]){V_str("Tom"), V_int(5LL)});
    v_print(v_index(d, V_str("name")));
    v_index_set(d, V_str("age"), V_int(6LL));
    v_print(v_index(d, V_str("age")));
    v_print(v_call_method(d, "keys", NULL, 0));
    v_print(v_call_method(d, "has", (Value[]){V_str("name")}, 1));
    a = v_list_build(3, (Value[]){V_int(1LL), V_int(2LL), V_int(3LL)});
    v_print(bi_head(a));
    v_print(bi_rear(a));
    v_print(bi_pile(a));
    v_print(bi_tail(a));
    return 0;
}