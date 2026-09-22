/* FelisOS kernel (Kitty) — Mini Cat++ interpreter.
   Support: paw, meow, purr/give, sniff/swat, knead, sit/leap,
   nod/shake/hungry, expr, call.
   Builtin: say, tally, tail, bolt, exec, exec_cmd, readline,
            read_file, write_file, exists, mkdir */
#include "catpp_rt.h"

#define MAX_VARS    64
#define MAX_FUNCS   32
#define MAX_PARAMS  8
#define MAX_BLOCK   64
#define MAX_STR     256
#define MAX_LINE    512

/* ═══ Value ═══ */
typedef struct {
    int type;      /* 0=num, 1=str, 2=null */
    long num;
    char str[MAX_STR];
} Value;

static Value mk_num(long n){ Value v; v.type=0; v.num=n; v.str[0]=0; return v; }
static Value mk_null(void){ Value v; v.type=2; v.num=0; v.str[0]=0; return v; }
static Value mk_str(const char* s){
    Value v; v.type=1; v.num=0;
    int i=0; while(s[i]&&i<MAX_STR-1){v.str[i]=s[i];i++;} v.str[i]=0;
    return v;
}

/* ═══ Env ═══ */
typedef struct { char name[32]; Value val; } Var;
typedef struct {
    Var vars[MAX_VARS];
    int var_count;
} Env;

static Env g_global;
static Env* g_env = &g_global;

static int str_eq(const char* a, const char* b){
    while(*a && *a==*b){a++;b++;} return *a==*b;
}
static int s_len(const char* s){int n=0;while(s[n])n++;return n;}
static void s_cpy(char* d,const char* s,int max){
    int i=0;while(s[i]&&i<max-1){d[i]=s[i];i++;}d[i]=0;
}

static Value* env_find(const char* name){
    for(int i=0;i<g_env->var_count;i++)
        if(str_eq(g_env->vars[i].name,name)) return &g_env->vars[i].val;
    return 0;
}
static void env_def(const char* name, Value v){
    Value* e = env_find(name);
    if(e){ *e = v; return; }
    if(g_env->var_count >= MAX_VARS) return;
    s_cpy(g_env->vars[g_env->var_count].name, name, 32);
    g_env->vars[g_env->var_count].val = v;
    g_env->var_count++;
}

/* ═══ Function table ═══ */
typedef struct {
    char name[32];
    char params[MAX_PARAMS][32];
    int nparams;
    char body[1024];
} Func;

static Func g_funcs[MAX_FUNCS];
static int g_func_count = 0;

static Func* func_find(const char* name){
    for(int i=0;i<g_func_count;i++)
        if(str_eq(g_funcs[i].name,name)) return &g_funcs[i];
    return 0;
}

/* ═══ Return exception ═══ */
typedef struct { int is_return; Value val; } ReturnEx;
static ReturnEx g_return;
static int g_break = 0;
static int g_continue = 0;
static int g_depth = 0;

/* ═══ Output helpers ═══ */
extern void catpp_putc(char c);
extern void catpp_print_str(const char* s);
extern int fs_write(const char* name, const char* data, int size);
extern int fs_append(const char* name, const char* data, int size);
extern const char* fs_read(const char* name, int* size_out);
extern int fs_resolve(int cwd, const char* path);
extern int fs_create_at(int parent, const char* name, int is_dir);
extern int fs_list_children(int parent, int* out, int max);
extern const char* fs_get_name(int i);
extern int fs_is_dir(int i);
extern int fs_file_size(int i);
extern void fs_path_of(int idx, char* out, int max);
extern int shell_execute(char* cmdline);
extern char keyboard_getchar(void);

/* ═══ Print value ═══ */
static void print_value(Value v){
    if(v.type == 0){
        char buf[32];
        long n = (long)v.num;
        int neg = 0;
        if(n<0){neg=1;n=-n;}
        int i=30; buf[31]=0;
        if(n==0) buf[--i]='0';
        while(n>0){buf[--i]='0'+(n%10);n/=10;}
        if(neg) buf[--i]='-';
        catpp_print_str(&buf[i]);
    } else if(v.type == 1){
        catpp_print_str(v.str);
    } else {
        catpp_print_str("hungry");
    }
}

/* ═══ Number to string ═══ */
static void num_to_str(double x, char* out){
    long n = (long)x;
    int neg = 0;
    if(n<0){neg=1;n=-n;}
    char buf[32]; int i=30; buf[31]=0;
    if(n==0) buf[--i]='0';
    while(n>0){buf[--i]='0'+(n%10);n/=10;}
    if(neg) buf[--i]='-';
    s_cpy(out, &buf[i], 32);
}

/* ═══ Value to string ═══ */
static void val_to_str(Value v, char* out){
    if(v.type == 0) num_to_str(v.num, out);
    else if(v.type == 1) s_cpy(out, v.str, MAX_STR);
    else s_cpy(out, "hungry", 8);
}

/* ═══ Lexer — từng dòng ═══ */
enum {
    T_EOF, T_NUM, T_STR, T_IDENT,
    T_PLUS, T_MINUS, T_STAR, T_SLASH, T_PERCENT,
    T_EQ, T_NEQ, T_LT, T_GT, T_LTE, T_GTE,
    T_LP, T_RP, T_COMMA, T_ASSIGN,
    T_MEOW, T_PAW, T_PURR, T_GIVE, T_SNIFF, T_SWAT,
    T_KNEAD, T_SIT, T_LEAP, T_NOD, T_SHAKE, T_HUNGRY,
};

typedef struct { int type; long num; char str[MAX_STR]; } Token;
typedef struct { const char* src; int pos; } Lexer;

static int is_digit(char c){return c>='0'&&c<='9';}
static int is_alpha(char c){return (c>='a'&&c<='z')||(c>='A'&&c<='Z')||c=='_';}
static int is_alnum(char c){return is_alpha(c)||is_digit(c);}

static Token next_token(Lexer* lx){
    Token t; t.type=T_EOF; t.num=0; t.str[0]=0;
    while(lx->src[lx->pos]==' ') lx->pos++;
    char c = lx->src[lx->pos];
    if(!c) return t;
    if(is_digit(c)){
        long n=0;
        while(is_digit(lx->src[lx->pos])){n=n*10+(lx->src[lx->pos]-'0');lx->pos++;}
        if(lx->src[lx->pos]=='.'){
            lx->pos++;
            while(is_digit(lx->src[lx->pos])) lx->pos++;
        }
        t.type=T_NUM; t.num=n; return t;
    }
    if(c=='"'){
        lx->pos++;
        int i=0;
        while(lx->src[lx->pos] && lx->src[lx->pos]!='"' && i<MAX_STR-1)
            t.str[i++]=lx->src[lx->pos++];
        t.str[i]=0;
        if(lx->src[lx->pos]=='"') lx->pos++;
        t.type=T_STR; return t;
    }
    if(is_alpha(c)){
        int i=0;
        while(is_alnum(lx->src[lx->pos]) && i<31) t.str[i++]=lx->src[lx->pos++];
        t.str[i]=0;
        if(str_eq(t.str,"meow"))  {t.type=T_MEOW;  return t;}
        if(str_eq(t.str,"paw"))   {t.type=T_PAW;   return t;}
        if(str_eq(t.str,"purr"))  {t.type=T_PURR;  return t;}
        if(str_eq(t.str,"give"))  {t.type=T_GIVE;  return t;}
        if(str_eq(t.str,"sniff")) {t.type=T_SNIFF; return t;}
        if(str_eq(t.str,"swat"))  {t.type=T_SWAT;  return t;}
        if(str_eq(t.str,"knead")) {t.type=T_KNEAD; return t;}
        if(str_eq(t.str,"sit"))   {t.type=T_SIT;   return t;}
        if(str_eq(t.str,"leap"))  {t.type=T_LEAP;  return t;}
        if(str_eq(t.str,"nod"))   {t.type=T_NOD;   return t;}
        if(str_eq(t.str,"shake")) {t.type=T_SHAKE; return t;}
        if(str_eq(t.str,"hungry")){t.type=T_HUNGRY;return t;}
        t.type=T_IDENT; return t;
    }
    char c2 = lx->src[lx->pos+1];
    if(c=='=' && c2=='='){lx->pos+=2;t.type=T_EQ;return t;}
    if(c=='!' && c2=='='){lx->pos+=2;t.type=T_NEQ;return t;}
    if(c=='<' && c2=='='){lx->pos+=2;t.type=T_LTE;return t;}
    if(c=='>' && c2=='='){lx->pos+=2;t.type=T_GTE;return t;}
    lx->pos++;
    switch(c){
        case '+':t.type=T_PLUS;return t;
        case '-':t.type=T_MINUS;return t;
        case '*':t.type=T_STAR;return t;
        case '/':t.type=T_SLASH;return t;
        case '%':t.type=T_PERCENT;return t;
        case '<':t.type=T_LT;return t;
        case '>':t.type=T_GT;return t;
        case '(':t.type=T_LP;return t;
        case ')':t.type=T_RP;return t;
        case ',':t.type=T_COMMA;return t;
        case '=':t.type=T_ASSIGN;return t;
    }
    return t;
}

/* ═══ Parser ═══ */
typedef struct { Lexer lx; Token cur; int error; } Parser;
static void advance(Parser* p){ p->cur = next_token(&p->lx); }

static Value parse_expr(Parser* p);
static Value parse_or(Parser* p);
static Value parse_and(Parser* p);
static Value parse_cmp(Parser* p);
static Value parse_add(Parser* p);
static Value parse_mul(Parser* p);
static Value parse_unary(Parser* p);
static Value parse_primary(Parser* p);
static void run_line(const char* line);
static void run_block(const char* body);

/* Builtin functions */
static int is_builtin(const char* name){
    const char* names[] = {"say","tally","tail","bolt","exec","exec_cmd",
                           "readline","read_file","write_file","exists",
                           "mkdir","ls","abs","max","min",0};
    for(int i=0;names[i];i++) if(str_eq(name,names[i])) return 1;
    return 0;
}

static Value call_builtin(const char* name, Value* args, int argc);

static Value parse_primary(Parser* p){
    Token t = p->cur;
    if(t.type == T_NUM){ advance(p); return mk_num(t.num); }
    if(t.type == T_STR){ advance(p); return mk_str(t.str); }
    if(t.type == T_NOD){ advance(p); return mk_num(1); }
    if(t.type == T_SHAKE){ advance(p); return mk_num(0); }
    if(t.type == T_HUNGRY){ advance(p); return mk_null(); }
    if(t.type == T_LP){
        advance(p);
        Value v = parse_expr(p);
        if(p->cur.type == T_RP) advance(p);
        return v;
    }
    if(t.type == T_IDENT){
        advance(p);
        /* Function call */
        if(p->cur.type == T_LP){
            advance(p);
            Value args[MAX_PARAMS];
            int argc = 0;
            if(p->cur.type != T_RP){
                args[argc++] = parse_expr(p);
                while(p->cur.type == T_COMMA && argc < MAX_PARAMS){
                    advance(p);
                    args[argc++] = parse_expr(p);
                }
            }
            if(p->cur.type == T_RP) advance(p);
            /* Builtin */
            if(is_builtin(t.str)) return call_builtin(t.str, args, argc);
            /* User function */
            Func* f = func_find(t.str);
            if(f){
                if(g_depth > 50){ p->error=1; return mk_null(); }
                g_depth++;
                /* Save env */
                Env saved = *g_env;
                Env local; local.var_count = 0;
                g_env = &local;
                for(int i=0;i<f->nparams && i<argc;i++)
                    env_def(f->params[i], args[i]);
                g_return.is_return = 0;
                run_block(f->body);
                Value ret = g_return.is_return ? g_return.val : mk_null();
                *g_env = saved;
                g_depth--;
                return ret;
            }
            return mk_null();
        }
        Value* v = env_find(t.str);
        if(v) return *v;
        return mk_num(0);
    }
    p->error = 1;
    return mk_null();
}

static Value parse_unary(Parser* p){
    if(p->cur.type == T_MINUS){
        advance(p);
        Value v = parse_unary(p);
        return mk_num(-v.num);
    }
    return parse_primary(p);
}

static Value parse_mul(Parser* p){
    Value l = parse_unary(p);
    while(p->cur.type==T_STAR || p->cur.type==T_SLASH || p->cur.type==T_PERCENT){
        int op = p->cur.type; advance(p);
        Value r = parse_unary(p);
        long res = 0;
        if(op==T_STAR) res = l.num * r.num;
        else if(op==T_SLASH){ if(r.num!=0) res = l.num / r.num; }
        else if(op==T_PERCENT){ if(r.num!=0) res = l.num % r.num; }
        l = mk_num(res);
    }
    return l;
}

static Value parse_add(Parser* p){
    Value l = parse_mul(p);
    while(p->cur.type==T_PLUS || p->cur.type==T_MINUS){
        int op = p->cur.type; advance(p);
        Value r = parse_mul(p);
        if(op==T_PLUS && (l.type==1 || r.type==1)){
            char ls[MAX_STR]; val_to_str(l, ls);
            char rs[MAX_STR]; val_to_str(r, rs);
            Value s = mk_str(ls);
            int len = s_len(s.str);
            int i=0;
            while(rs[i] && len<MAX_STR-1) s.str[len++] = rs[i++];
            s.str[len]=0;
            l = s;
        } else {
            l = mk_num(op==T_PLUS ? l.num+r.num : l.num-r.num);
        }
    }
    return l;
}

static Value parse_cmp(Parser* p){
    Value l = parse_add(p);
    while(p->cur.type>=T_EQ && p->cur.type<=T_GTE){
        int op = p->cur.type; advance(p);
        Value r = parse_add(p);
        int res = 0;
        if(l.type==1 && r.type==1){
            res = str_eq(l.str, r.str);
            if(op==T_NEQ) res = !res;
        } else {
            switch(op){
                case T_EQ: res=(l.num==r.num); break;
                case T_NEQ:res=(l.num!=r.num); break;
                case T_LT: res=(l.num<r.num);  break;
                case T_GT: res=(l.num>r.num);  break;
                case T_LTE:res=(l.num<=r.num); break;
                case T_GTE:res=(l.num>=r.num); break;
            }
        }
        l = mk_num(res);
    }
    return l;
}

static Value parse_and(Parser* p){ return parse_cmp(p); }
static Value parse_or(Parser* p){ return parse_and(p); }
static Value parse_expr(Parser* p){ return parse_or(p); }

/* ═══ Builtins ═══ */
static Value call_builtin(const char* name, Value* args, int argc){
    if(str_eq(name,"say")){
        if(argc>=1){ char b[MAX_STR]; val_to_str(args[0],b); return mk_str(b); }
        return mk_str("");
    }
    if(str_eq(name,"tally")){
        if(argc>=1) return mk_num(args[0].num);
        return mk_num(0);
    }
    if(str_eq(name,"bolt")){
        if(argc>=1){ long x=args[0].num; return mk_num(x<0?-x:x); }
        return mk_num(0);
    }
    if(str_eq(name,"max")){
        if(argc>=2) return mk_num(args[0].num>args[1].num?args[0].num:args[1].num);
        return mk_num(0);
    }
    if(str_eq(name,"min")){
        if(argc>=2) return mk_num(args[0].num<args[1].num?args[0].num:args[1].num);
        return mk_num(0);
    }
    if(str_eq(name,"tail")){
        if(argc>=1){
            if(args[0].type==1) return mk_num(s_len(args[0].str));
            return mk_num(0);
        }
        return mk_num(0);
    }
    if(str_eq(name,"readline")){
        if(argc>=1 && args[0].type==1) catpp_print_str(args[0].str);
        char buf[MAX_LINE]; int i=0;
        while(1){
            char c = keyboard_getchar();
            if(c=='\n'){ catpp_putc('\n'); break; }
            if(c=='\b'){ if(i>0){ i--; catpp_print_str("\b \b"); } continue; }
            if(c>=32 && c<127 && i<MAX_LINE-1){ buf[i++]=c; catpp_putc(c); }
        }
        buf[i]=0;
        return mk_str(buf);
    }
    if(str_eq(name,"exec")){
        if(argc>=1 && args[0].type==1){
            char* cmd = args[0].str;
            shell_execute(cmd);
        }
        return mk_null();
    }
    if(str_eq(name,"exec_cmd")){
        if(argc>=1 && args[0].type==1){
            char* cmd = args[0].str;
            shell_execute(cmd);
        }
        return mk_null();
    }
    if(str_eq(name,"exists")){
        if(argc>=1 && args[0].type==1){
            int idx = fs_resolve(-1, args[0].str);
            return mk_num(idx >= 0 ? 1 : 0);
        }
        return mk_num(0);
    }
    if(str_eq(name,"mkdir")){
        if(argc>=1 && args[0].type==1){
            fs_create_at(-1, args[0].str, 1);
        }
        return mk_null();
    }
    if(str_eq(name,"write_file")){
        if(argc>=2 && args[0].type==1 && args[1].type==1){
            fs_write(args[0].str, args[1].str, s_len(args[1].str));
        }
        return mk_null();
    }
    if(str_eq(name,"read_file")){
        if(argc>=1 && args[0].type==1){
            int sz;
            const char* d = fs_read(args[0].str, &sz);
            if(d) return mk_str(d);
        }
        return mk_str("");
    }
    if(str_eq(name,"ls")){
        int children[64];
        int n = fs_list_children(-1, children, 64);
        for(int i=0;i<n;i++){
            const char* name = fs_get_name(children[i]);
            if(name) catpp_print_str(name);
        }
        return mk_null();
    }
    return mk_null();
}

/* ═══ Run one line ═══ */
static void run_line(const char* line){
    Parser p;
    p.lx.src = line; p.lx.pos = 0; p.error = 0;
    advance(&p);

    /* paw x = expr */
    if(p.cur.type == T_PAW){
        advance(&p);
        if(p.cur.type != T_IDENT){ p.error=1; return; }
        char name[32]; s_cpy(name, p.cur.str, 32);
        advance(&p);
        if(p.cur.type != T_ASSIGN){ p.error=1; return; }
        advance(&p);
        Value v = parse_expr(&p);
        env_def(name, v);
        return;
    }
    /* meow expr */
    if(p.cur.type == T_MEOW){
        advance(&p);
        Value v = parse_expr(&p);
        if(!p.error) print_value(v);
        return;
    }
    /* give expr */
    if(p.cur.type == T_GIVE){
        advance(&p);
        Value v = parse_expr(&p);
        g_return.is_return = 1;
        g_return.val = v;
        return;
    }
    /* sit / leap */
    if(p.cur.type == T_SIT){ g_break = 1; return; }
    if(p.cur.type == T_LEAP){ g_continue = 1; return; }
    /* expr */
    parse_expr(&p);
}

/* ═══ Indent ═══ */
static int line_indent(const char* line){
    int n=0;
    while(*line==' '){n++;line++;}
    return n;
}

static const char* line_skip_ws(const char* line){
    while(*line==' ') line++;
    return line;
}

/* ═══ run_block — parse block with indent ═══ */
static void run_block(const char* body){
    /* Copy và tách dòng */
    char buf[2048];
    s_cpy(buf, body, sizeof(buf));

    char* lines[64];
    int line_count = 0;
    char* p = buf;
    while(*p && line_count<64){
        lines[line_count++] = p;
        while(*p && *p!='\n') p++;
        if(*p=='\n'){ *p=0; p++; }
    }

    int i = 0;
    int base_indent = -1;
    while(i < line_count){
        const char* ln = line_skip_ws(lines[i]);
        if(!*ln){ i++; continue; }
        int ind = line_indent(lines[i]);
        if(base_indent < 0) base_indent = ind;
        if(ind < base_indent){ i++; continue; }

        /* sniff */
        if(ln[0]=='s' && str_eq(ln, "sniff")==0 && ln[4]==' '){
            Parser pp; pp.lx.src = ln+5; pp.lx.pos=0; pp.error=0;
            advance(&pp);
            Value cond = parse_expr(&pp);
            /* Tìm block then (dòng tiếp cùng indent + 4) */
            int j = i+1;
            int then_start = j;
            while(j<line_count){
                if(!*lines[j] || line_indent(lines[j])<=ind) break;
                j++;
            }
            if(cond.num != 0){
                /* Ghép các dòng then */
                char then_body[1024]; then_body[0]=0;
                for(int k=then_start;k<j;k++){
                    int len = s_len(then_body);
                    s_cpy(then_body+len, lines[k], 1024-len);
                    len = s_len(then_body);
                    if(len < 1023){ then_body[len]='\n'; then_body[len+1]=0; }
                }
                run_block(then_body);
            }
            i = j;
            /* swat */
            if(i<line_count){
                const char* sw = line_skip_ws(lines[i]);
                if(sw[0]=='s' && str_eq(sw, "swat")==0 && (sw[4]==0||sw[4]==' ')){
                    int k = i+1;
                    int swat_start = k;
                    while(k<line_count){
                        if(!*lines[k] || line_indent(lines[k])<=ind) break;
                        k++;
                    }
                    if(cond.num == 0){
                        char sb[1024]; sb[0]=0;
                        for(int m=swat_start;m<k;m++){
                            int len = s_len(sb);
                            s_cpy(sb+len, lines[m], 1024-len);
                            len = s_len(sb);
                            if(len<1023){ sb[len]='\n'; sb[len+1]=0; }
                        }
                        run_block(sb);
                    }
                    i = k;
                }
            }
            if(g_return.is_return || g_break || g_continue) return;
            continue;
        }

        /* knead */
        if(ln[0]=='k' && ln[5]==' ' && s_len(ln)>6 && ln[0]=='k' && ln[1]=='n' && ln[2]=='e' && ln[3]=='a' && ln[4]=='d'){
            Parser pp; pp.lx.src = ln+6; pp.lx.pos=0; pp.error=0;
            advance(&pp);
            /* Parse condition once — nhưng cần re-eval mỗi vòng */
            char cond_src[256]; s_cpy(cond_src, ln+6, sizeof(cond_src));
            int j = i+1;
            int body_start = j;
            while(j<line_count){
                if(!*lines[j] || line_indent(lines[j])<=ind) break;
                j++;
            }
            /* Ghép body */
            char wb[1024]; wb[0]=0;
            for(int k=body_start;k<j;k++){
                int len = s_len(wb);
                s_cpy(wb+len, lines[k], 1024-len);
                len = s_len(wb);
                if(len<1023){ wb[len]='\n'; wb[len+1]=0; }
            }
            int iter = 0;
            while(iter < 10000){
                Parser p2; p2.lx.src = cond_src; p2.lx.pos=0; p2.error=0;
                advance(&p2);
                Value c = parse_expr(&p2);
                if(c.num == 0) break;
                g_break = 0; g_continue = 0;
                run_block(wb);
                if(g_return.is_return) return;
                if(g_break){ g_break=0; break; }
                iter++;
            }
            i = j;
            continue;
        }

        /* Dòng thường — chạy trực tiếp */
        {
            Parser pp; pp.lx.src = ln; pp.lx.pos=0; pp.error=0;
            advance(&pp);
            run_line(ln);
            if(g_return.is_return || g_break || g_continue) return;
        }
        i++;
    }
}

/* ═══ Public API ═══ */
void catpp_mini_eval(const char* line){
    g_return.is_return = 0;
    run_line(line);
}

/* Chạy file .cat nhiều dòng */
int catpp_run(const char* source){
    g_global.var_count = 0;
    g_func_count = 0;
    g_depth = 0;

    /* Pre-scan functions (purr name(params)) */
    char buf[4096];
    s_cpy(buf, source, sizeof(buf));

    char* lines[128];
    int line_count = 0;
    char* p = buf;
    while(*p && line_count<128){
        lines[line_count++] = p;
        while(*p && *p!='\n') p++;
        if(*p=='\n'){ *p=0; p++; }
    }

    /* Detect functions */
    for(int i=0;i<line_count;i++){
        const char* ln = line_skip_ws(lines[i]);
        if(s_len(ln)<5 || ln[0]!='p' || ln[1]!='u' || ln[2]!='r' || ln[3]!='r') continue;
        if(ln[4]!=' ') continue;

        const char* name_p = ln+5;
        int ni=0;
        while(*name_p && *name_p!='(' && ni<31) g_funcs[g_func_count].name[ni++] = *name_p++;
        g_funcs[g_func_count].name[ni]=0;
        if(*name_p=='('){
            name_p++;
            int np=0;
            while(*name_p && *name_p!=')' && np<MAX_PARAMS){
                while(*name_p==' ') name_p++;
                int pi=0;
                while(*name_p && *name_p!=',' && *name_p!=')' && pi<31)
                    g_funcs[g_func_count].params[np][pi++] = *name_p++;
                g_funcs[g_func_count].params[np][pi]=0;
                np++;
                while(*name_p==' ') name_p++;
                if(*name_p==',') name_p++;
            }
            g_funcs[g_func_count].nparams = np;
        }
        /* Body = các dòng tiếp cùng indent + 4 */
        int ind = line_indent(lines[i]);
        int j = i+1;
        g_funcs[g_func_count].body[0]=0;
        while(j<line_count){
            if(!*lines[j]){ j++; continue; }
            if(line_indent(lines[j])<=ind) break;
            int len = s_len(g_funcs[g_func_count].body);
            s_cpy(g_funcs[g_func_count].body+len, lines[j], 1024-len);
            len = s_len(g_funcs[g_func_count].body);
            if(len<1023){ g_funcs[g_func_count].body[len]='\n'; g_funcs[g_func_count].body[len+1]=0; }
            j++;
        }
        g_func_count++;
        if(g_func_count >= MAX_FUNCS) break;
    }

    /* Run main body — skip function defs */
    for(int i=0;i<line_count;i++){
        const char* ln = line_skip_ws(lines[i]);
        if(!*ln) continue;
        if(ln[0]=='#' ) continue;
        /* Skip function definition */
        if(s_len(ln)>5 && ln[0]=='p' && ln[1]=='u' && ln[2]=='r' && ln[3]=='r' && ln[4]==' '){
            int ind = line_indent(lines[i]);
            int j = i+1;
            while(j<line_count){
                if(!*lines[j]){ j++; continue; }
                if(line_indent(lines[j])<=ind) break;
                j++;
            }
            i = j-1;
            continue;
        }
        g_return.is_return = 0;
        g_break = 0; g_continue = 0;
        run_line(ln);
    }
    return 0;
}
