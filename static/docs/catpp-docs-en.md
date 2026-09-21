# Cat++ Documentation — English

---

## Table of Contents

1. Bài 1 — Hello Mèo
2. Bài 2 — Biến (paw)
3. Bài 3 — sniff / swat
4. Bài 4 — knead / groom
5. Bài 5 — purr / give
6. Bài 6 — Danh sách
7. Bài 7 — Chuỗi
8. Bài 8 — tap / hiss
9. Bài 9 — Thuật toán
10. Bài 10 — cat / kin / litter

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
- Ngữ pháp EBNF
- Ngữ nghĩa
- Quy ước code

---

# Tutorial

---

# Bài 1 — Hello Mèo

Chương trình đầu tiên. Bạn sẽ học cách in ra màn hình.

## In chuỗi

```
meow "Meow! Hello, Cat++!"
```

Kết quả: `Meow! Hello, Cat++!`

## In số

```
meow 42
meow 3 + 4
```

## In nhiều dòng

```
meow "Dòng 1"
meow "Dòng 2"
```

## Bài tập

In ra tên bạn 3 lần, mỗi lần một dòng.

---

# Bài 2 — Biến (paw)

Biến lưu giá trị để dùng lại. Dùng từ khóa `paw`.

## Khai báo

```
paw name = "Whiskers"
paw age = 3
meow name
meow age
```

## Gán lại

```
paw x = 10
x = x + 5
meow x
```

Kết quả: `15`

## Nối chuỗi và biến

```
paw name = "Tom"
meow "Xin chào, " + name + "!"
```

## Bài tập

Khai báo `width = 5`, `height = 3`, in ra diện tích hình chữ nhật.

---

# Bài 3 — sniff / swat

Rẽ nhánh với `sniff` / `swat`.

## Cú pháp

```
sniff dieu_kien
    code_neu_dung
swat
    code_neu_sai
```

## Ví dụ

```
paw age = 3
sniff age > 2
    meow "Mèo lớn"
swat
    meow "Mèo con"
```

## So sánh

## Bài tập

Kiểm tra `n = 8` chẵn hay lẻ.

---

# Bài 4 — knead / groom

Lặp code nhiều lần với `knead` và `groom`.

## knead — lặp có điều kiện

```
paw i = 1
knead i <= 5
    meow i
    paw i = i + 1
```

## groom — duyệt danh sách

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

## Bài tập

In các số từ 1 đến 20 chia hết cho 3.

---

# Bài 5 — purr / give

Hàm gom code để gọi lại nhiều lần.

## Định nghĩa

```
purr greet(name)
    meow "Xin chào, " + name + "!"

greet("Tom")
greet("Jerry")
```

## Trả về giá trị

```
purr add(a, b)
    give a + b

meow add(3, 4)
```

## Hàm đệ quy

```
purr fact(n)
    sniff n <= 1
        give 1
    give n * fact(n - 1)

meow fact(5)
```

## Bài tập

Viết hàm `max3(a, b, c)` trả về số lớn nhất trong ba số.

---

# Bài 6 — Danh sách

Danh sách lưu nhiều giá trị trong một biến.

## Tạo

```
paw empty = []
paw nums = [1, 2, 3]
paw mixed = [1, "hai", nod]
```

## Truy cập

```
paw cats = ["Tom", "Jerry", "Kitty"]
meow cats[0]
meow cats[2]
meow tail(cats)
```

## Thêm phần tử

```
paw arr = [1, 2]
stash(arr, 3)
meow arr
```

## Bài tập

Tính tổng các số trong `[10, 20, 30, 40]`.

---

# Bài 7 — Chuỗi

Xử lý văn bản.

## Nối

```
meow "Hello, " + "Cat!"
```

## Độ dài

```
meow tail("hello")
```

## Hoa / thường

```
meow puff("hello")
meow melt("HELLO")
```

## Cắt

```
meow nip("Hello, Cat!", 0, 5)
```

## Interpolation

```
paw name = "Tom"
meow "Xin chào, {name}!"
```

## Bài tập

Viết hàm đảo ngược chuỗi `"hello"` thành `"olleh"`.

---

# Bài 8 — tap / hiss

Không để chương trình dừng khi có lỗi.

## Cú pháp

```
tap
    paw x = 1 / 0
hiss e
    meow "Lỗi: " + e
```

## Ứng dụng

```
paw nums = [10, 0, 5]
groom n of nums
    tap
        meow 100 / n
    hiss e
        meow "Bỏ qua " + say(n)
```

## Bài tập

Cho `["10", "abc", "20"]`, thử chuyển sang số, bỏ qua phần tử lỗi.

---

# Bài 9 — Thuật toán

Áp dụng Cat++ vào bài toán thực tế.

## Sắp xếp nổi bọt

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

## Tìm kiếm nhị phân

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

## Bài tập

Viết hàm kiểm tra số nguyên tố.

---

# Bài 10 — cat / kin / litter

Class gom dữ liệu và hàm xử lý dữ liệu đó.

## Định nghĩa

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

## Kế thừa (kin)

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

## Bài tập

Viết class `Rectangle` với phương thức tính diện tích và chu vi.

---

# Keywords

---

# cat

**Category:** OOP  
**Syntax:** `cat <Tên>`

## Description

Định nghĩa class.

Class chứa paw (field) và purr (method). Method new là constructor.

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

Đúng khi một trong hai đúng.

Đánh giá ngắn mạch.

## Examples

### Cơ bản

```cat
meow nod either shake
```

**Result:** `nod`

---

# give

**Category:** Khai báo  
**Syntax:** `give <biểu thức>`

## Description

Trả về giá trị từ hàm.

Sau give, hàm thoát ngay. Phải nằm trong hàm.

## Examples

### Trả về

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

**Category:** Điều khiển  
**Syntax:** `groom <biến> of <danh sách>`

## Description

Duyệt danh sách.

Biến là local trong mỗi lần lặp. Hỗ trợ sit/leap.

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

**Category:** Lỗi  
**Syntax:** `hiss <tên>`

## Description

Bắt lỗi từ tap.

Tên là biến local chứa thông báo.

## Examples

### Cơ bản

```cat
tap
    paw x = 1 / 0
hiss e
    meow "Lỗi: " + e
```

**Result:** `Lỗi: Chia cho 0`

---

# hungry

**Category:** Giá trị  
**Syntax:** `hungry`

## Description

Giá trị rỗng (null).

Hàm không give trả về hungry.

## Examples

### Dùng

```cat
meow hungry
```

**Result:** `hungry`

---

# kin

**Category:** OOP  
**Syntax:** `cat <Tên> kin <Cha>`

## Description

Kế thừa.

Class con kế thừa field và method của cha.

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

**Category:** Hàm  
**Syntax:** `kit(<ts>) => <bt>`

## Description

Lambda — hàm ẩn danh.

Dùng trong chase/sift/curl hoặc gán vào biến.

## Examples

### Lambda

```cat
paw double = kit(x) => x * 2
meow double(21)
```

**Result:** `42`

---

# knead

**Category:** Điều khiển  
**Syntax:** `knead <điều kiện>`

## Description

Lặp khi điều kiện còn đúng.

Giới hạn 1 triệu lần. Hỗ trợ sit/leap.

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

**Category:** Điều khiển  
**Syntax:** `leap`

## Description

Bỏ qua lần lặp hiện tại.

Không thoát vòng lặp.

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
**Syntax:** `litter <Tên>`

## Description

Định nghĩa enum.

Truy cập bằng Tên.thànhviên.

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

Tương đương self trong Python.

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
**Syntax:** `meow <biểu thức>`

## Description

In ra màn hình.

Tự động chuyển sang chuỗi. nod/shake cho boolean, hungry cho rỗng.

## Examples

### Chuỗi

```cat
meow "Hello, Cat++!"
```

**Result:** `Hello, Cat++!`

### Số

```cat
meow 42
```

**Result:** `42`

### Biểu thức

```cat
meow 3 + 4 * 2
```

**Result:** `11`

---

# never

**Category:** Logic  
**Syntax:** `never <a>`

## Description

Đảo ngược boolean.

Độ ưu tiên cao.

## Examples

### Cơ bản

```cat
meow never nod
```

**Result:** `shake`

---

# nod

**Category:** Giá trị  
**Syntax:** `nod`

## Description

Boolean đúng.

In ra là nod.

## Examples

### Dùng

```cat
meow nod
```

**Result:** `nod`

---

# of

**Category:** Điều khiển  
**Syntax:** `groom x of <ds>`

## Description

Từ khóa phụ trợ cho groom.

Chỉ dùng trong groom.

---

# paw

**Category:** Khai báo  
**Syntax:** `paw <tên> = <biểu thức>`

## Description

Khai báo biến.

Trong cùng scope, ghi đè. Khác scope, tạo biến mới (shadowing).

## Examples

### Số

```cat
paw x = 10
meow x
```

**Result:** `10`

### Gán lại

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

**Category:** Khai báo  
**Syntax:** `purr <tên>(<tham số>)`

## Description

Định nghĩa hàm.

Định nghĩa trước khi gọi. Không give → trả về hungry. Đệ quy tối đa 500 tầng.

## Examples

### Cơ bản

```cat
purr greet(name)
    meow "Hi, " + name
greet("Tom")
```

**Result:** `Hi, Tom`

### Trả về

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

**Category:** Giá trị  
**Syntax:** `shake`

## Description

Boolean sai.

In ra là shake.

## Examples

### Dùng

```cat
meow shake
```

**Result:** `shake`

---

# sit

**Category:** Điều khiển  
**Syntax:** `sit`

## Description

Thoát vòng lặp gần nhất.

Chỉ ảnh hưởng vòng lặp bao quanh.

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

**Category:** Điều khiển  
**Syntax:** `sniff <điều kiện>`

## Description

Rẽ nhánh khi điều kiện đúng.

Điều kiện đánh giá là nod/shake. Block thụt lề 4 spaces.

## Examples

### Cơ bản

```cat
sniff 5 > 3
    meow "đúng"
```

**Result:** `đúng`

### Có swat

```cat
sniff shake
    meow "a"
swat
    meow "b"
```

**Result:** `b`

---

# swat

**Category:** Điều khiển  
**Syntax:** `swat`

## Description

Khối chạy khi sniff sai.

Phải đi kèm sniff. Không có elif — dùng sniff lồng nhau.

## Examples

### Cơ bản

```cat
sniff shake
    meow "a"
swat
    meow "b"
```

**Result:** `b`

---

# tap

**Category:** Lỗi  
**Syntax:** `tap ... hiss`

## Description

Bắt lỗi runtime.

Không có hiss → lỗi bị bỏ qua.

## Examples

### Bắt lỗi

```cat
tap
    paw x = 1 / 0
hiss e
    meow e
```

**Result:** `Chia cho 0`

---

# with

**Category:** Logic  
**Syntax:** `<a> with <b>`

## Description

Đúng khi cả hai đúng.

Đánh giá ngắn mạch.

## Examples

### Cơ bản

```cat
meow nod with shake
```

**Result:** `shake`

---

# Builtins

---

# bolt()

**Category:** Toán  
**Signature:** `bolt(x)`

## Description

Trị tuyệt đối.

## Examples

### Âm

```cat
meow bolt(-5)
```

**Result:** `5`

---

# bound()

**Category:** Toán  
**Signature:** `bound(a, b)`

## Description

a lũy thừa b.

## Examples

### 2^10

```cat
meow bound(2, 10)
```

**Result:** `1024`

---

# chase()

**Category:** Bậc cao  
**Signature:** `chase(ds, f)`

## Description

Áp dụng f (map).

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

Danh sách key.

## Examples

### Cơ bản

```cat
paw d = {"a":1,"b":2}
meow collar(d)
```

**Result:** `[a, b]`

---

# curl()

**Category:** Bậc cao  
**Signature:** `curl(ds, f, init)`

## Description

Gộp (reduce).

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

Số nguyên ngẫu nhiên.

## Examples

### 1..6

```cat
paw r = dice(1, 6)
meow r
```

**Result:** `(ngẫu nhiên)`

---

# drip()

**Category:** Chuyển kiểu  
**Signature:** `drip(x)`

## Description

Sang số thực.

## Examples

### Chuỗi

```cat
meow drip("3.14")
```

**Result:** `3.14`

---

# flip()

**Category:** Danh sách  
**Signature:** `flip(ds)`

## Description

Đảo ngược.

## Examples

### Cơ bản

```cat
meow flip([1,2,3])
```

**Result:** `[3, 2, 1]`

---

# flop()

**Category:** Toán  
**Signature:** `flop(x)`

## Description

Làm tròn xuống.

## Examples

### 3.9

```cat
meow flop(3.9)
```

**Result:** `3`

---

# grow()

**Category:** Toán  
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

**Category:** Danh sách  
**Signature:** `head(ds)`

## Description

Phần tử đầu.

## Examples

### Cơ bản

```cat
meow head([1,2,3])
```

**Result:** `1`

---

# hunt()

**Category:** Chuỗi  
**Signature:** `hunt(s, sub)`

## Description

Kiểm tra chuỗi con.

## Examples

### Cơ bản

```cat
meow hunt("hello", "ell")
```

**Result:** `nod`

---

# kits()

**Category:** Dict  
**Signature:** `kits(d)`

## Description

Danh sách value.

## Examples

### Cơ bản

```cat
paw d = {"a":1,"b":2}
meow kits(d)
```

**Result:** `[1, 2]`

---

# kitten()

**Category:** Toán  
**Signature:** `kitten(a, b)`

## Description

Nhỏ hơn.

## Examples

### Cơ bản

```cat
meow kitten(3, 7)
```

**Result:** `3`

---

# lick()

**Category:** Chuỗi  
**Signature:** `lick(s)`

## Description

Cắt khoảng trắng.

## Examples

### Cơ bản

```cat
meow lick("  hi  ")
```

**Result:** `hi`

---

# line()

**Category:** Danh sách  
**Signature:** `line(ds)`

## Description

Sắp xếp.

## Examples

### Cơ bản

```cat
meow line([3,1,2])
```

**Result:** `[1, 2, 3]`

---

# lion()

**Category:** Toán  
**Signature:** `lion(a, b)`

## Description

Lớn hơn.

## Examples

### Cơ bản

```cat
meow lion(3, 7)
```

**Result:** `7`

---

# melt()

**Category:** Chuỗi  
**Signature:** `melt(s)`

## Description

Chữ thường.

## Examples

### Cơ bản

```cat
meow melt("HELLO")
```

**Result:** `hello`

---

# nip()

**Category:** Chuỗi  
**Signature:** `nip(s, a, b)`

## Description

Cắt từ a đến b-1.

## Examples

### Đầu

```cat
meow nip("Hello, Cat!", 0, 5)
```

**Result:** `Hello`

---

# perch()

**Category:** Toán  
**Signature:** `perch(x)`

## Description

Làm tròn lên.

## Examples

### 3.1

```cat
meow perch(3.1)
```

**Result:** `4`

---

# pile()

**Category:** Danh sách  
**Signature:** `pile(ds)`

## Description

Tổng danh sách.

## Examples

### Cơ bản

```cat
meow pile([1,2,3,4])
```

**Result:** `10`

---

# puff()

**Category:** Chuỗi  
**Signature:** `puff(s)`

## Description

Chữ hoa.

## Examples

### Cơ bản

```cat
meow puff("hello")
```

**Result:** `HELLO`

---

# rear()

**Category:** Danh sách  
**Signature:** `rear(ds)`

## Description

Phần tử cuối.

## Examples

### Cơ bản

```cat
meow rear([1,2,3])
```

**Result:** `3`

---

# say()

**Category:** Chuyển kiểu  
**Signature:** `say(x)`

## Description

Sang chuỗi.

## Examples

### Số

```cat
meow say(42)
```

**Result:** `42`

---

# scratch()

**Category:** Toán  
**Signature:** `scratch(x)`

## Description

Căn bậc 2.

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

Kiểm tra key.

## Examples

### Cơ bản

```cat
paw d = {"a":1}
meow seek(d, "a")
```

**Result:** `nod`

---

# shred()

**Category:** Chuỗi  
**Signature:** `shred(s, sep)`

## Description

Tách chuỗi.

## Examples

### Cơ bản

```cat
meow shred("a,b,c", ",")
```

**Result:** `[a, b, c]`

---

# sift()

**Category:** Bậc cao  
**Signature:** `sift(ds, f)`

## Description

Lọc (filter).

## Examples

### Chẵn

```cat
meow sift([1,2,3,4], kit(x) => x%2==0)
```

**Result:** `[2, 4]`

---

# slant()

**Category:** Toán  
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

**Category:** Danh sách  
**Signature:** `snatch(ds)`

## Description

Lấy phần tử cuối.

## Examples

### Cơ bản

```cat
paw a = [1,2,3]
meow snatch(a)
```

**Result:** `3`

---

# stash()

**Category:** Danh sách  
**Signature:** `stash(ds, v)`

## Description

Thêm phần tử.

## Examples

### Cơ bản

```cat
paw a = [1,2]
stash(a, 3)
meow a
```

**Result:** `[1, 2, 3]`

---

# swap()

**Category:** Chuỗi  
**Signature:** `swap(s, a, b)`

## Description

Thay thế.

## Examples

### Cơ bản

```cat
meow swap("hello", "l", "L")
```

**Result:** `heLLo`

---

# sway()

**Category:** Toán  
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

**Category:** Cơ bản  
**Signature:** `tail(x)`

## Description

Độ dài chuỗi hoặc danh sách.

## Examples

### Chuỗi

```cat
meow tail("hello")
```

**Result:** `5`

### DS

```cat
meow tail([1,2,3])
```

**Result:** `3`

---

# tally()

**Category:** Chuyển kiểu  
**Signature:** `tally(x)`

## Description

Sang số nguyên.

## Examples

### Chuỗi

```cat
meow tally("42")
```

**Result:** `42`

---

# walk()

**Category:** Danh sách  
**Signature:** `walk(a, b)`

## Description

Tạo danh sách số.

## Examples

### Cơ bản

```cat
meow walk(1, 5)
```

**Result:** `[1, 2, 3, 4]`

---

# wander()

**Category:** Random  
**Signature:** `wander()`

## Description

Số ngẫu nhiên 0..1.

---

# wave()

**Category:** Toán  
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

**Category:** Chuỗi  
**Signature:** `weave(ds, sep)`

## Description

Nối danh sách.

## Examples

### Cơ bản

```cat
meow weave(["a","b"], "-")
```

**Result:** `a-b`

---

# Specification

---

# Ngữ pháp EBNF

## Chương trình

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

## Biểu thức

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

# Ngữ nghĩa

## Đánh giá biểu thức

Trái sang phải, tôn trọng độ ưu tiên:

- ()

- never, dấu âm

- * / %

- + -

- < > <= >=

- == !=

- with

- either

## Đánh giá ngắn mạch

```
a with b    # a sai → không đánh giá b
a either b  # a đúng → không đánh giá b
```

## Ép kiểu

- + với chuỗi → ép vế còn lại thành chuỗi

- Các phép khác yêu cầu cả hai là số

- So sánh không ép: 42 == "42" là shake

## Truthiness

- nod → đúng, shake → sai

- Số khác 0 → đúng

- Chuỗi/DS khác rỗng → đúng

- hungry → sai

## Scope

- Mỗi hàm có scope riêng

- Biến trong hàm nhìn thấy biến ngoài (lexical scope)

- Không có từ khóa global

---

# Quy ước code

## Đặt tên

## Thụt lề

4 spaces, không tab, không trộn.

## Độ dài dòng

Tối đa 80 ký tự.

## Comment

Giải thích **tại sao**, không phải **làm gì**.

---

