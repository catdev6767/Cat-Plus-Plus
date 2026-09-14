/* Felis OS — Mini Cat++ evaluator.
   Hỗ trợ: số, chuỗi, biến, + - * / %, == != < > <= >=,
           meow, paw, sniff/swat, knead, stop, skip */
#include <stdint.h>
#include "utils.h"

#define MAX_VARS 32
#define MAX_STR  256
#define MAX_TOK  512

/* ═══ Giá trị ═══ */
typedef struct {
    int type;      /* 0=num, 1=str, 2=null */
    double num;
    char str[MAX_STR];
} Value;

static Value mk_num(double n) { Value v; v.type=0; v.num=n; v.str[0]=0; return v; }
static Value mk_str(const char* s) {
    Value v; v.type=1; v.num=0;
    int i=0; while (s[i] && i<MAX_STR-1) { v.str[i]=s[i]; i++; } v.str[i]=0;
    return v;
}
static Value mk_null(void) { Value v; v.type=2; v.num=0; v.str[0]=0; return v; }

/* ═══ Biến ═══ */
typedef struct { char name[32]; Value val; } Var;
static Var g_vars[MAX_VARS];
static int g_var_count = 0;

extern void catpp_putc(char c);
extern void catpp_print_str(const char* s);

static Value* find_var(const char* name) {
    for (int i = 0; i < g_var_count; i++)
        if (str_eq(g_vars[i].name, name)) return &g_vars[i].val;
    return 0;
}
static void define_var(const char* name, Value v) {
    Value* e = find_var(name);
    if (e) { *e = v; return; }
    if (g_var_count >= MAX_VARS) return;
    int i=0; while (name[i] && i<31) { g_vars[g_var_count].name[i]=name[i]; i++; }
    g_vars[g_var_count].name[i]=0;
    g_vars[g_var_count].val=v;
    g_var_count++;
}

/* ═══ In giá trị ═══ */
static void print_value(Value v) {
    if (v.type == 0) {
        /* Số */
        char buf[32];
        long n = (long)v.num;
        int neg = 0;
        if (n < 0) { neg = 1; n = -n; }
        int i = 30; buf[31] = 0;
        if (n == 0) buf[--i] = '0';
        while (n > 0) { buf[--i] = '0' + (n % 10); n /= 10; }
        if (neg) buf[--i] = '-';
        catpp_print_str(&buf[i]);
    } else if (v.type == 1) {
        catpp_print_str(v.str);
    } else {
        catpp_print_str("hungry");
    }
}

/* ═══ Lexer ═══ */
enum {
    T_EOF, T_NUM, T_STR, T_IDENT,
    T_PLUS, T_MINUS, T_STAR, T_SLASH, T_PERCENT,
    T_EQ, T_NEQ, T_LT, T_GT, T_LTE, T_GTE,
    T_LP, T_RP, T_ASSIGN,
    T_MEOW, T_PAW, T_SNIFF, T_SWAT, T_KNEAD, T_SIT, T_LEAP,
};

typedef struct {
    int type;
    double num;
    char str[MAX_STR];
} Token;

typedef struct {
    const char* src;
    int pos;
} Lexer;

static int is_digit(char c) { return c >= '0' && c <= '9'; }
static int is_alpha(char c) { return (c>='a'&&c<='z') || (c>='A'&&c<='Z') || c=='_'; }
static int is_alnum(char c) { return is_alpha(c) || is_digit(c); }

static Token next_token(Lexer* lx) {
    Token t; t.type=T_EOF; t.num=0; t.str[0]=0;
    while (lx->src[lx->pos] == ' ') lx->pos++;
    char c = lx->src[lx->pos];
    if (!c) return t;

    /* Số */
    if (is_digit(c)) {
        double n = 0;
        while (is_digit(lx->src[lx->pos])) { n = n*10 + (lx->src[lx->pos]-'0'); lx->pos++; }
        t.type = T_NUM; t.num = n; return t;
    }

    /* Chuỗi */
    if (c == '"') {
        lx->pos++;
        int i = 0;
        while (lx->src[lx->pos] && lx->src[lx->pos] != '"' && i < MAX_STR-1) {
            t.str[i++] = lx->src[lx->pos++];
        }
        t.str[i] = 0;
        if (lx->src[lx->pos] == '"') lx->pos++;
        t.type = T_STR; return t;
    }

    /* Định danh / từ khóa */
    if (is_alpha(c)) {
        int i = 0;
        while (is_alnum(lx->src[lx->pos]) && i < 31) t.str[i++] = lx->src[lx->pos++];
        t.str[i] = 0;
        if (str_eq(t.str, "meow"))  { t.type = T_MEOW;  return t; }
        if (str_eq(t.str, "paw"))   { t.type = T_PAW;   return t; }
        if (str_eq(t.str, "sniff")) { t.type = T_SNIFF; return t; }
        if (str_eq(t.str, "swat"))  { t.type = T_SWAT;  return t; }
        if (str_eq(t.str, "knead")) { t.type = T_KNEAD; return t; }
        if (str_eq(t.str, "sit"))   { t.type = T_SIT;   return t; }
        if (str_eq(t.str, "leap"))  { t.type = T_LEAP;  return t; }
        t.type = T_IDENT; return t;
    }

    /* Toán tử */
    char c2 = lx->src[lx->pos+1];
    if (c == '=' && c2 == '=') { lx->pos+=2; t.type=T_EQ; return t; }
    if (c == '!' && c2 == '=') { lx->pos+=2; t.type=T_NEQ; return t; }
    if (c == '<' && c2 == '=') { lx->pos+=2; t.type=T_LTE; return t; }
    if (c == '>' && c2 == '=') { lx->pos+=2; t.type=T_GTE; return t; }
    lx->pos++;
    switch (c) {
        case '+': t.type = T_PLUS; return t;
        case '-': t.type = T_MINUS; return t;
        case '*': t.type = T_STAR; return t;
        case '/': t.type = T_SLASH; return t;
        case '%': t.type = T_PERCENT; return t;
        case '<': t.type = T_LT; return t;
        case '>': t.type = T_GT; return t;
        case '(': t.type = T_LP; return t;
        case ')': t.type = T_RP; return t;
        case '=': t.type = T_ASSIGN; return t;
    }
    return t;
}

/* ═══ Parser / Evaluator ═══ */
typedef struct {
    Lexer lx;
    Token cur;
    int error;
} Parser;

static void advance(Parser* p) { p->cur = next_token(&p->lx); }

static Value parse_expr(Parser* p);
static Value parse_or(Parser* p);
static Value parse_and(Parser* p);
static Value parse_cmp(Parser* p);
static Value parse_add(Parser* p);
static Value parse_mul(Parser* p);
static Value parse_unary(Parser* p);
static Value parse_primary(Parser* p);

static Value parse_primary(Parser* p) {
    Token t = p->cur;
    if (t.type == T_NUM)  { advance(p); return mk_num(t.num); }
    if (t.type == T_STR)  { advance(p); return mk_str(t.str); }
    if (t.type == T_LP)   { advance(p); Value v = parse_expr(p);
                            if (p->cur.type == T_RP) advance(p); return v; }
    if (t.type == T_IDENT) {
        advance(p);
        Value* v = find_var(t.str);
        if (v) return *v;
        return mk_num(0);
    }
    p->error = 1;
    return mk_null();
}

static Value parse_unary(Parser* p) {
    if (p->cur.type == T_MINUS) {
        advance(p);
        Value v = parse_unary(p);
        return mk_num(-v.num);
    }
    return parse_primary(p);
}

static Value parse_mul(Parser* p) {
    Value l = parse_unary(p);
    while (p->cur.type == T_STAR || p->cur.type == T_SLASH || p->cur.type == T_PERCENT) {
        int op = p->cur.type; advance(p);
        Value r = parse_unary(p);
        double res = 0;
        if (op == T_STAR)      res = l.num * r.num;
        else if (op == T_SLASH) { if (r.num != 0) res = l.num / r.num; }
        else if (op == T_PERCENT) { if ((long)r.num != 0) res = (long)l.num % (long)r.num; }
        l = mk_num(res);
    }
    return l;
}

static Value parse_add(Parser* p) {
    Value l = parse_mul(p);
    while (p->cur.type == T_PLUS || p->cur.type == T_MINUS) {
        int op = p->cur.type; advance(p);
        Value r = parse_mul(p);
        if (op == T_PLUS && (l.type == 1 || r.type == 1)) {
            /* Nối chuỗi */
            Value s = mk_str(l.type==1 ? l.str : "");
            int len = 0; while (s.str[len]) len++;
            int i = 0;
            if (r.type == 1) { while (r.str[i] && len < MAX_STR-1) s.str[len++] = r.str[i++]; }
            else {
                char buf[32]; long n = (long)r.num;
                int neg = 0; if (n<0){neg=1;n=-n;}
                int j=30; buf[31]=0;
                if (n==0) buf[--j]='0';
                while (n>0){buf[--j]='0'+(n%10);n/=10;}
                if (neg) buf[--j]='-';
                while (buf[j] && len < MAX_STR-1) s.str[len++] = buf[j++];
            }
            s.str[len] = 0;
            l = s;
        } else {
            l = mk_num(op == T_PLUS ? l.num + r.num : l.num - r.num);
        }
    }
    return l;
}

static Value parse_cmp(Parser* p) {
    Value l = parse_add(p);
    while (p->cur.type >= T_EQ && p->cur.type <= T_GTE) {
        int op = p->cur.type; advance(p);
        Value r = parse_add(p);
        int res = 0;
        if (l.type == 1 && r.type == 1) {
            res = str_eq(l.str, r.str);
            if (op == T_NEQ) res = !res;
        } else {
            switch (op) {
                case T_EQ:  res = (l.num == r.num); break;
                case T_NEQ: res = (l.num != r.num); break;
                case T_LT:  res = (l.num <  r.num); break;
                case T_GT:  res = (l.num >  r.num); break;
                case T_LTE: res = (l.num <= r.num); break;
                case T_GTE: res = (l.num >= r.num); break;
            }
        }
        l = mk_num(res);
    }
    return l;
}

static Value parse_and(Parser* p) { return parse_cmp(p); }
static Value parse_or(Parser* p)  { return parse_and(p); }
static Value parse_expr(Parser* p) { return parse_or(p); }

/* ═══ Chạy 1 dòng lệnh ═══ */
void catpp_mini_eval(const char* line) {
    Parser p;
    p.lx.src = line; p.lx.pos = 0;
    p.error = 0;
    advance(&p);

    /* paw x = expr */
    if (p.cur.type == T_PAW) {
        advance(&p);
        if (p.cur.type != T_IDENT) { catpp_print_str("Loi: paw can ten bien"); return; }
        char name[32]; int i=0;
        while (p.cur.str[i] && i<31) { name[i]=p.cur.str[i]; i++; }
        name[i]=0;
        advance(&p);
        if (p.cur.type != T_ASSIGN) { catpp_print_str("Loi: thieu ="); return; }
        advance(&p);
        Value v = parse_expr(&p);
        define_var(name, v);
        return;
    }

    /* meow expr */
    if (p.cur.type == T_MEOW) {
        advance(&p);
        Value v = parse_expr(&p);
        print_value(v);
        return;
    }

    /* Biểu thức trực tiếp */
    Value v = parse_expr(&p);
    if (!p.error) print_value(v);
    else catpp_print_str("Loi cu phap");
}
