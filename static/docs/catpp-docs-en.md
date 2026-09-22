# Cat++ Documentation — English

---

## Table of Contents

1. Lesson 1 — Hello Cat
2. Lesson 2 — Variables (paw)
3. Lesson 3 — sniff / swat
4. Lesson 4 — knead / groom
5. Lesson 5 — purr / give
6. Lesson 6 — Lists
7. Lesson 7 — Strings
8. Lesson 8 — tap / hiss
9. Lesson 9 — Algorithms
10. Lesson 10 — cat / kin / litter

### Keywords
- cat
- either
- give
- groom
- hiss
- hungry
- kin
- kit
- knead
- leap
- litter
- me
- meow
- never
- nod
- of
- paw
- purr
- shake
- sit
- sniff
- swat
- tap
- with

### Builtins
- bolt()
- bound()
- chase()
- collar()
- curl()
- dice()
- drip()
- flip()
- flop()
- grow()
- head()
- hunt()
- kits()
- kitten()
- lick()
- line()
- lion()
- melt()
- nip()
- perch()
- pile()
- puff()
- rear()
- say()
- scratch()
- seek()
- shred()
- sift()
- slant()
- snatch()
- stash()
- swap()
- sway()
- tail()
- tally()
- walk()
- wander()
- wave()
- weave()

### Specification
- EBNF Grammar
- Semantics
- Code conventions

---

# Tutorial

---

# Lesson 1 — Hello Cat

First program. You will learn how to print to screen.

## Printing strings

```
meow "Meow! Hello, Cat++!"
```

Result: `Meow! Hello, Cat++!`

## Printing numbers

```
meow 42
meow 3 + 4
```

## Print multiple lines

```
meow "Line 1"
meow "Line 2"
```

## Exercises

Print your name 3 times, each time one line.

---

# Lesson 2 — Variables (paw)

Variables store values for reuse. Use the keyword `paw`.

## Declare

```
paw name = "Whiskers"
paw age = 3
meow name
meow age
```

## Reassign

```
paw x = 10
x = x + 5
meow x
```

Result: `15`

## Concatenate strings and variables

```
paw name = "Tom"
meow "Hello, " + name + "!"
```

## Exercises

Declare `width = 5`, `height = 3`, print area rectangle.

---

# Lesson 3 — sniff / swat

Branch with `sniff` / `swat`.

## Syntax

```
sniff dieu_kien
    code_neu_dung
swat
    code_neu_sai
```

## Examples

```
paw age = 3
sniff age > 2
    meow "Big Cat"
swat
    meow "Kitten"
```

## Comparison

## Exercises

Check `n = 8`even or odd.

---

# Lesson 4 — knead / groom

Repeat code with `knead` and `groom`.

## knead

```
paw i = 1
knead i <= 5
    meow i
    paw i = i + 1
```

## groom — browse list

```
paw cats = ["Tom", "Jerry", "Kitty"]
groom c of cats
    meow c
```

## sit / leap

```
paw i = 0
knead i < 10
    paw i = i + 1
    sniff i == 3
        leap
    sniff i == 7
        sit
    meow i
```

## Exercises

Print the numbers from 1 to 20 divisible by 3.

---

# Lesson 5 — purr / give

Functions group code for reuse.

## Define

```
purr greet(name)
    meow "Hello, " + name + "!"

greet("Tom")
greet("Jerry")
```

## Return value

```
purr add(a, b)
    give a + b

meow add(3, 4)
```

## Recursive function

```
purr fact(n)
    sniff n <= 1
        give 1
    give n * fact(n - 1)

meow fact(5)
```

## Exercises

Write function`max3(a, b, c)`returns the largest number that prints three numbers.

---

# Lesson 6 — Lists

Lists store multiple values in one variable.

## Create

```
paw empty = []
paw nums = [1, 2, 3]
paw mixed = [1, "hai", nod]
```

## Access

```
paw cats = ["Tom", "Jerry", "Kitty"]
meow cats[0]
meow cats[2]
meow tail(cats)
```

## Add Section Element

```
paw arr = [1, 2]
stash(arr, 3)
meow arr
```

## Exercises

Sum of prints`[10, 20, 30, 40]`.

---

# Lesson 7 — Strings

Text processing.

## Concat

```
meow "Hello, " + "Cat!"
```

## Length

```
meow tail("hello")
```

## Uppercase / Normal

```
meow puff("hello")
meow melt("HELLO")
```

## Cut

```
meow nip("Hello, Cat!", 0, 5)
```

## Interpolation

```
paw name = "Tom"
meow "Hello, {name}!"
```

## Exercises

Write reverse function string`"hello"`of living capital and gestation of the subject. `"olleh"`.

---

# Lesson 8 — tap / hiss

Not let the program crash on errors.

## Syntax

```
tap
    paw x = 1 / 0
hiss e
    meow "Error: " + e
```

## Use

```
paw nums = [10, 0, 5]
groom n of nums
    tap
        meow 100 / n
    hiss e
        meow "Skip " + say(n)
```

## Exercises

Cho `["10", "abc", "20"]`, try to shift the number, ignore the death penalty section.

---

# Lesson 9 — Algorithms

Apply cat++ ando practical math lesson.

## Foam Floating Arrangement

```
paw arr = [5, 2, 8, 1, 9]
paw n = tail(arr)

paw i = 0
knead i  arr[j + 1]
            paw tmp = arr[j]
            arr[j] = arr[j + 1]
            arr[j + 1] = tmp
        paw j = j + 1
    paw i = i + 1

groom x of arr
    meow x
```

## Binary Search

```
purr bsearch(arr, target)
    paw lo = 0
    paw hi = tail(arr) - 1
    knead lo <= hi
        paw mid = flop((lo + hi) / 2)
        sniff arr[mid] == target
            give mid
        sniff arr[mid] < target
            paw lo = mid + 1
        swat
            paw hi = mid - 1
    give -1
```

## Exercises

Write the function to check the prime number.

---

# Lesson 10 — cat / kin / litter

Classes group data and functions that operate on it.

## Define

```
cat Point
    paw x
    paw y

    purr new(a, b)
        me.x = a
        me.y = b

    purr dist()
        give scratch(me.x * me.x + me.y * me.y)

paw p = Point(3, 4)
meow p.dist()
```

## Inheritance (kin)

```
cat Animal
    paw name
    purr new(n)
        me.name = n
    purr speak()
        give "..."

cat Dog kin Animal
    purr speak()
        give me.name + " says woof!"

meow Dog("Rex").speak()
```

## Enum (litter)

```
litter Color
    red
    green
    blue

meow Color.red
```

## Exercises

Write class`Rectangle`with the method of calculating the area and perimeter.

---

# Keywords

---

# cat

**Category:** OOP  
**Syntax:** `cat <Name>`

## Description

Define a class.

Class contains paw (field) and purr (method). Method new is the constructor.

## Examples

### Class

```cat
cat Point
    paw x
    paw y
    purr new(a, b)
        me.x = a
        me.y = b
    purr info()
        give "({me.x}, {me.y})"

paw p = Point(3, 4)
meow p.info()
```

**Result:** `(3, 4)`

---

# either

**Category:** Logic  
**Syntax:** `<a> either <b>`

## Description

True when either is true.

Short-circuit evaluation.

## Examples

### Basic

```cat
meow nod either shake
```

**Result:** `nod`

---

# give

**Category:** Declaration  
**Syntax:** `give <expression>`

## Description

Return a value from function.

After give, function exits immediately. Must be inside a function.

## Examples

### Return

```cat
purr check(n)
    sniff n > 0
        give "dương"
    give "khác"
meow check(5)
```

**Result:** `dương`

---

# groom

**Category:** Control  
**Syntax:** `groom <variable> of <list>`

## Description

Iterate list.

Variable is local per iteration. Supports sit/leap.

## Examples

### Duyệt

```cat
groom c of ["a", "b"]
    meow c
```

**Result:** `a
b`

---

# hiss

**Category:** Error  
**Syntax:** `hiss <name>`

## Description

Bắt lỗi from tap.

Name is a local variable holding the message.

## Examples

### Basic

```cat
tap
    paw x = 1 / 0
hiss e
    meow "Error: " + e
```

**Result:** `Error: Chia for 0`

---

# hungry

**Category:** Value  
**Syntax:** `hungry`

## Description

Empty value (null).

Functions without give return hungry.

## Examples

### Dùng

```cat
meow hungry
```

**Result:** `hungry`

---

# kin

**Category:** OOP  
**Syntax:** `cat <Name> kin <Cha>`

## Description

Kế thừa.

Child class inherits parent fields and methods.

## Examples

### Kế thừa

```cat
cat A
    paw n
    purr new(x)
        me.n = x
cat B kin A
    purr hi()
        give me.n
meow B("Bob").hi()
```

**Result:** `Bob`

---

# kit

**Category:** Function  
**Syntax:** `kit(<ts>) => <bt>`

## Description

Lambda — function ẩn danh.

Used in chase/sift/curl or assigned to a variable.

## Examples

### Lambda

```cat
paw double = kit(x) => x * 2
meow double(21)
```

**Result:** `42`

---

# knead

**Category:** Control  
**Syntax:** `knead <condition>`

## Description

Loop while condition is true.

Limit 1 million iterations. Supports sit/leap.

## Examples

### Đếm

```cat
paw i = 1
knead i <= 3
    meow i
    paw i = i + 1
```

**Result:** `1
2
3`

---

# leap

**Category:** Control  
**Syntax:** `leap`

## Description

Skip iteration hiện tại.

Does not exit the loop.

## Examples

### Bỏ 2

```cat
paw i = 0
knead i < 4
    paw i = i + 1
    sniff i == 2
        leap
    meow i
```

**Result:** `1
3
4`

---

# litter

**Category:** OOP  
**Syntax:** `litter <Name>`

## Description

Define enum.

Access via Name.thànhviên.

## Examples

### Enum

```cat
litter Color
    red
    green
    blue
meow Color.red
```

**Result:** `Color.red`

---

# me

**Category:** OOP  
**Syntax:** `me.<field>`

## Description

Tham chiếu instance hiện tại.

Equivalent to self in Python.

## Examples

### Dùng

```cat
cat P
    paw x
    purr new(a)
        me.x = a
paw p = P(5)
meow p.x
```

**Result:** `5`

---

# meow

**Category:** I/O  
**Syntax:** `meow <expression>`

## Description

Print to screen.

Auto-converts to string. nod/shake for boolean, hungry for null.

## Examples

### String

```cat
meow "Hello, Cat++!"
```

**Result:** `Hello, Cat++!`

### Number

```cat
meow 42
```

**Result:** `42`

### Expression

```cat
meow 3 + 4 * 2
```

**Result:** `11`

---

# never

**Category:** Logic  
**Syntax:** `never <a>`

## Description

Printvert boolean.

High precedence.

## Examples

### Basic

```cat
meow never nod
```

**Result:** `shake`

---

# nod

**Category:** Value  
**Syntax:** `nod`

## Description

Boolean true.

Print ra là nod.

## Examples

### Dùng

```cat
meow nod
```

**Result:** `nod`

---

# of

**Category:** Control  
**Syntax:** `groom x of <ds>`

## Description

Helper keyword for groom.

Only used in groom.

---

# paw

**Category:** Declaration  
**Syntax:** `paw <name> = <expression>`

## Description

Declare a variable.

Same scope, overrides. Different scope, new binding (shadowing).

## Examples

### Number

```cat
paw x = 10
meow x
```

**Result:** `10`

### Reassign

```cat
paw x = 10
x = x + 5
meow x
```

**Result:** `15`

### Dict

```cat
paw d = {"a": 1}
meow d["a"]
```

**Result:** `1`

---

# purr

**Category:** Declaration  
**Syntax:** `purr <name>(<parameters>)`

## Description

Define a function.

Define before calling. No give → returns hungry. Recursion up to 500 levels.

## Examples

### Basic

```cat
purr greet(name)
    meow "Hi, " + name
greet("Tom")
```

**Result:** `Hi, Tom`

### Return

```cat
purr add(a, b)
    give a + b
meow add(3, 4)
```

**Result:** `7`

### Đệ quy

```cat
purr fact(n)
    sniff n <= 1
        give 1
    give n * fact(n - 1)
meow fact(5)
```

**Result:** `120`

---

# shake

**Category:** Value  
**Syntax:** `shake`

## Description

Boolean false.

Print ra là shake.

## Examples

### Dùng

```cat
meow shake
```

**Result:** `shake`

---

# sit

**Category:** Control  
**Syntax:** `sit`

## Description

Break loop gần nhất.

Only affects the enclosing loop.

## Examples

### Thoát

```cat
paw i = 1
knead i <= 5
    sniff i == 3
        sit
    meow i
    paw i = i + 1
```

**Result:** `1
2`

---

# sniff

**Category:** Control  
**Syntax:** `sniff <condition>`

## Description

Branch if condition is true.

Condition evaluates to nod/shake. Block indented 4 spaces.

## Examples

### Basic

```cat
sniff 5 > 3
    meow "đúng"
```

**Result:** `đúng`

### Yes swat

```cat
sniff shake
    meow "a"
swat
    meow "b"
```

**Result:** `b`

---

# swat

**Category:** Control  
**Syntax:** `swat`

## Description

Khối chạy khi sniff sai.

Must accompany sniff. No elif — use nested sniff.

## Examples

### Basic

```cat
sniff shake
    meow "a"
swat
    meow "b"
```

**Result:** `b`

---

# tap

**Category:** Error  
**Syntax:** `tap ... hiss`

## Description

Catch runtime error.

Not có hiss → lỗi bị bỏ qua.

## Examples

### Bắt lỗi

```cat
tap
    paw x = 1 / 0
hiss e
    meow e
```

**Result:** `Chia for 0`

---

# with

**Category:** Logic  
**Syntax:** `<a> with <b>`

## Description

True when both are true.

Short-circuit evaluation.

## Examples

### Basic

```cat
meow nod with shake
```

**Result:** `shake`

---

# Builtins

---

# bolt()

**Category:** Math  
**Signature:** `bolt(x)`

## Description

Absolute value.

## Examples

### Âm

```cat
meow bolt(-5)
```

**Result:** `5`

---

# bound()

**Category:** Math  
**Signature:** `bound(a, b)`

## Description

a to the power of b.

## Examples

### 2^10

```cat
meow bound(2, 10)
```

**Result:** `1024`

---

# chase()

**Category:** Higher-order  
**Signature:** `chase(ds, f)`

## Description

Apply f (map).

## Examples

### Bình phương

```cat
meow chase([1,2,3], kit(x) => x*x)
```

**Result:** `[1, 4, 9]`

---

# collar()

**Category:** Dict  
**Signature:** `collar(d)`

## Description

List of keys.

## Examples

### Basic

```cat
paw d = {"a":1,"b":2}
meow collar(d)
```

**Result:** `[a, b]`

---

# curl()

**Category:** Higher-order  
**Signature:** `curl(ds, f, init)`

## Description

Reduce.

## Examples

### Tổng

```cat
meow curl([1,2,3], kit(a,b) => a+b, 0)
```

**Result:** `6`

---

# dice()

**Category:** Random  
**Signature:** `dice(a, b)`

## Description

Random integer.

## Examples

### 1..6

```cat
paw r = dice(1, 6)
meow r
```

**Result:** `(ngẫu nhiên)`

---

# drip()

**Category:** Conversion  
**Signature:** `drip(x)`

## Description

To float.

## Examples

### String

```cat
meow drip("3.14")
```

**Result:** `3.14`

---

# flip()

**Category:** List  
**Signature:** `flip(ds)`

## Description

Reverse.

## Examples

### Basic

```cat
meow flip([1,2,3])
```

**Result:** `[3, 2, 1]`

---

# flop()

**Category:** Math  
**Signature:** `flop(x)`

## Description

Floor.

## Examples

### 3.9

```cat
meow flop(3.9)
```

**Result:** `3`

---

# grow()

**Category:** Math  
**Signature:** `grow(x)`

## Description

log tự nhiên.

## Examples

### 1

```cat
meow grow(1)
```

**Result:** `0`

---

# head()

**Category:** List  
**Signature:** `head(ds)`

## Description

First element.

## Examples

### Basic

```cat
meow head([1,2,3])
```

**Result:** `1`

---

# hunt()

**Category:** String  
**Signature:** `hunt(s, sub)`

## Description

Check substring.

## Examples

### Basic

```cat
meow hunt("hello", "ell")
```

**Result:** `nod`

---

# kits()

**Category:** Dict  
**Signature:** `kits(d)`

## Description

List of values.

## Examples

### Basic

```cat
paw d = {"a":1,"b":2}
meow kits(d)
```

**Result:** `[1, 2]`

---

# kitten()

**Category:** Math  
**Signature:** `kitten(a, b)`

## Description

Smaller.

## Examples

### Basic

```cat
meow kitten(3, 7)
```

**Result:** `3`

---

# lick()

**Category:** String  
**Signature:** `lick(s)`

## Description

Trim whitespace.

## Examples

### Basic

```cat
meow lick("  hi  ")
```

**Result:** `hi`

---

# line()

**Category:** List  
**Signature:** `line(ds)`

## Description

Sort.

## Examples

### Basic

```cat
meow line([3,1,2])
```

**Result:** `[1, 2, 3]`

---

# lion()

**Category:** Math  
**Signature:** `lion(a, b)`

## Description

Larger.

## Examples

### Basic

```cat
meow lion(3, 7)
```

**Result:** `7`

---

# melt()

**Category:** String  
**Signature:** `melt(s)`

## Description

Lowercase.

## Examples

### Basic

```cat
meow melt("HELLO")
```

**Result:** `hello`

---

# nip()

**Category:** String  
**Signature:** `nip(s, a, b)`

## Description

Slice from a to b-1.

## Examples

### Đầu

```cat
meow nip("Hello, Cat!", 0, 5)
```

**Result:** `Hello`

---

# perch()

**Category:** Math  
**Signature:** `perch(x)`

## Description

Ceiling.

## Examples

### 3.1

```cat
meow perch(3.1)
```

**Result:** `4`

---

# pile()

**Category:** List  
**Signature:** `pile(ds)`

## Description

Sum of list.

## Examples

### Basic

```cat
meow pile([1,2,3,4])
```

**Result:** `10`

---

# puff()

**Category:** String  
**Signature:** `puff(s)`

## Description

Uppercase.

## Examples

### Basic

```cat
meow puff("hello")
```

**Result:** `HELLO`

---

# rear()

**Category:** List  
**Signature:** `rear(ds)`

## Description

Last element.

## Examples

### Basic

```cat
meow rear([1,2,3])
```

**Result:** `3`

---

# say()

**Category:** Conversion  
**Signature:** `say(x)`

## Description

To string.

## Examples

### Number

```cat
meow say(42)
```

**Result:** `42`

---

# scratch()

**Category:** Math  
**Signature:** `scratch(x)`

## Description

Square root.

## Examples

### 16

```cat
meow scratch(16)
```

**Result:** `4`

---

# seek()

**Category:** Dict  
**Signature:** `seek(d, k)`

## Description

Check key.

## Examples

### Basic

```cat
paw d = {"a":1}
meow seek(d, "a")
```

**Result:** `nod`

---

# shred()

**Category:** String  
**Signature:** `shred(s, sep)`

## Description

Split string.

## Examples

### Basic

```cat
meow shred("a,b,c", ",")
```

**Result:** `[a, b, c]`

---

# sift()

**Category:** Higher-order  
**Signature:** `sift(ds, f)`

## Description

Filter.

## Examples

### Chẵn

```cat
meow sift([1,2,3,4], kit(x) => x%2==0)
```

**Result:** `[2, 4]`

---

# slant()

**Category:** Math  
**Signature:** `slant(x)`

## Description

tan(x).

## Examples

### 0

```cat
meow slant(0)
```

**Result:** `0`

---

# snatch()

**Category:** List  
**Signature:** `snatch(ds)`

## Description

Get last element.

## Examples

### Basic

```cat
paw a = [1,2,3]
meow snatch(a)
```

**Result:** `3`

---

# stash()

**Category:** List  
**Signature:** `stash(ds, v)`

## Description

Append element.

## Examples

### Basic

```cat
paw a = [1,2]
stash(a, 3)
meow a
```

**Result:** `[1, 2, 3]`

---

# swap()

**Category:** String  
**Signature:** `swap(s, a, b)`

## Description

Replace.

## Examples

### Basic

```cat
meow swap("hello", "l", "L")
```

**Result:** `heLLo`

---

# sway()

**Category:** Math  
**Signature:** `sway(x)`

## Description

sin(x).

## Examples

### 0

```cat
meow sway(0)
```

**Result:** `0`

---

# tail()

**Category:** Basic  
**Signature:** `tail(x)`

## Description

Length of string or list.

## Examples

### String

```cat
meow tail("hello")
```

**Result:** `5`

### List

```cat
meow tail([1,2,3])
```

**Result:** `3`

---

# tally()

**Category:** Conversion  
**Signature:** `tally(x)`

## Description

To integer.

## Examples

### String

```cat
meow tally("42")
```

**Result:** `42`

---

# walk()

**Category:** List  
**Signature:** `walk(a, b)`

## Description

Create number range.

## Examples

### Basic

```cat
meow walk(1, 5)
```

**Result:** `[1, 2, 3, 4]`

---

# wander()

**Category:** Random  
**Signature:** `wander()`

## Description

Random number 0..1.

---

# wave()

**Category:** Math  
**Signature:** `wave(x)`

## Description

cos(x).

## Examples

### 0

```cat
meow wave(0)
```

**Result:** `1`

---

# weave()

**Category:** String  
**Signature:** `weave(ds, sep)`

## Description

Join list.

## Examples

### Basic

```cat
meow weave(["a","b"], "-")
```

**Result:** `a-b`

---

# Specification

---

# EBNF Grammar

## Program

```
program    = { statement } ;
statement  = let_stmt | assign_stmt | print_stmt | listen_stmt
           | fn_stmt | return_stmt | if_stmt | while_stmt
           | each_stmt | try_stmt | stop_stmt | skip_stmt
           | class_stmt | enum_stmt | expr_stmt ;

let_stmt   = "paw" IDENT "=" expr NEWLINE ;
print_stmt = "meow" expr NEWLINE ;
fn_stmt    = "purr" IDENT [ params ] NEWLINE INDENT { stmt } DEDENT ;
if_stmt    = "sniff" expr NEWLINE INDENT { stmt } DEDENT
             [ "swat" NEWLINE INDENT { stmt } DEDENT ] ;
while_stmt = "knead" expr NEWLINE INDENT { stmt } DEDENT ;
each_stmt  = "groom" IDENT "of" expr NEWLINE INDENT { stmt } DEDENT ;
try_stmt   = "tap" NEWLINE INDENT { stmt } DEDENT
             [ "hiss" [ IDENT ] NEWLINE INDENT { stmt } DEDENT ] ;
class_stmt = "cat" IDENT [ "kin" IDENT ] NEWLINE INDENT { member } DEDENT ;
enum_stmt  = "litter" IDENT NEWLINE INDENT { IDENT NEWLINE } DEDENT ;
```

## Expression

```
expr     = or_expr ;
or_expr  = and_expr { "either" and_expr } ;
and_expr = not_expr { "with" not_expr } ;
not_expr = "never" not_expr | cmp_expr ;
cmp_expr = add_expr { cmp_op add_expr } ;
add_expr = mul_expr { ("+" | "-") mul_expr } ;
mul_expr = unary { ("*" | "/" | "%") unary } ;
primary  = NUMBER | STRING | "nod" | "shake" | "hungry"
         | IDENT | "me" | "(" expr ")" | list_lit
         | dict_lit | lambda ;
lambda   = "kit" "(" [ params ] ")" "=>" expr ;
```

---

# Semantics

## Expression evaluation

Left to right, respecting precedence:

- ()

- never, negative sign

- * / %

- + -

- < > <= >=

- == !=

- with

- either

## Short-circuit assessment

```
a with b    # a false → not evaluated b
a either b  # a → right to evaluate b
```

## Ép type

- + with string → press the remaining part to string

- Other permissions require both to be numeric

- Comparison not pressed: 42 == "42" is shake

## Truthiness

- nod → right, shake → wrong

- Non-zero number → true

- Other String/DS is empty → correctly

- hungry → sai

## Scope

- Each function has its own scope

- Variable in function sees variable outside (lexical scope)

- None keyword global

---

# Code conventions

## Naming

## Indent

4 spaces, no tabs, no mixing.

## Line length

Maximum 80 characters.

## Comment

Explanation **why does the**, must not**What u do for earnings**.

---

