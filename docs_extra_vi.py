# -*- coding: utf-8 -*-
"""Nội dung docs bổ sung — Phase 1.
Sẽ được merge vào docs_data_vi.py bởi gen_docs.py.
"""

KEYWORDS_EXTRA = {
    'cast': {'cat':'Low-level','sig':'cast(type, value)','desc':'Ép kiểu giá trị sang type.','detail':'Dùng cho OS dev và kiểm soát kiểu. Các type hỗ trợ: i8, i16, i32, i64, u8, u16, u32, u64, ptr, int, float, bool, str.','ex':[('Cast sang int','meow cast(int, "42")','42'),('Cast sang str','meow cast(str, 42)','42'),('Cast pointer','paw p = cast(ptr, 0xB8000)','4096')]},
    'sizeof': {'cat':'Low-level','sig':'sizeof(x) hoặc sizeof(type)','desc':'Kích thước của giá trị hoặc kiểu trong byte.','detail':'Với type: dùng bảng TYPE_SIZES. Với value: đo theo kiểu thực tế.','ex':[('Value','meow sizeof(42)','8'),('String','meow sizeof("hello")','5'),('Type','meow sizeof(i32)','4')]},
    'struct': {'cat':'Low-level','sig':'struct <Tên>\n    <field>: <type>','desc':'Định nghĩa struct C-layout.','detail':'Giống class nhưng không có method. Dùng cho dữ liệu thuần.','ex':[('Point','struct Point\n    x: i32\n    y: i32\npaw p = Point(3, 4)\nmeow p.x','3')]},
    'volatile': {'cat':'Low-level','sig':'volatile paw <name> = <value>','desc':'Biến volatile — compiler không tối ưu.','detail':'Dùng cho memory-mapped I/O (MMIO).','ex':[('Cơ bản','volatile paw status = 0\nmeow status','0')]},
    'asm': {'cat':'Low-level','sig':'asm("instruction")','desc':'Inline assembly.','detail':'Trong interpreter chỉ parse, không chạy. Trong CatOS transpile thành __asm__ volatile().','ex':[('NOP','asm("nop")\nmeow "ok"','ok')]},
    'static': {'cat':'OOP','sig':'purr static <method>()','desc':'Static method — gọi qua class, không cần instance.','ex':[('Cơ bản','cat Math\n    purr static square(n)\n        give n * n\nmeow Math.square(5)','25')]},
    'get': {'cat':'OOP','sig':'purr get <name>()','desc':'Getter — chạy khi đọc field.','ex':[('Cơ bản','cat P\n    paw _x\n    purr new(v)\n        me.x = v\n    purr get x()\n        give me._x\nmeow P(42).x','42')]},
    'set': {'cat':'OOP','sig':'purr set <name>(v)','desc':'Setter — chạy khi gán field.','ex':[('Cơ bản','cat P\n    paw _x\n    purr set x(v)\n        me._x = v * 2\n    purr get x()\n        give me._x\npaw p = P()\np.x = 5\nmeow p.x','10')]},
    'abstract': {'cat':'OOP','sig':'cat abstract <Tên>','desc':'Abstract class — không tạo instance được.','detail':'Dùng với `purr <method>()` không có body để định nghĩa method abstract. Class con phải override hết.','ex':[('Shape','cat abstract Shape\n    purr area()\ncat Circle kin Shape\n    paw r\n    purr new(r)\n        me.r = r\n    purr area()\n        give 3.14 * me.r * me.r\nmeow Circle(2).area()','12.56')]},
    'match': {'cat':'Điều khiển','sig':'match <expr>\n    case <value>\n        ...','desc':'Pattern matching — so sánh với nhiều giá trị.','detail':'Dùng `case _` làm wildcard. Mỗi case là 1 block.','ex':[('Cơ bản','paw x = 2\nmatch x\n    case 1\n        meow "one"\n    case 2\n        meow "two"','two'),('Wildcard','paw x = 99\nmatch x\n    case 1\n        meow "one"\n    case _\n        meow "other"','other')]},
    'case': {'cat':'Điều khiển','sig':'case <value>','desc':'Nhánh trong match.','detail':'Chỉ dùng trong block match.','ex':[]},
    'use': {'cat':'Module','sig':'use "file.cat"','desc':'Import file Cat++ khác.','detail':'Tìm trong examples/, thư mục hiện tại. Chạy toàn bộ file vào scope hiện tại.','ex':[('Import lib','use "mathlib.cat"\nmeow square(5)','25')]},
    'ptr': {'cat':'Low-level','sig':'ptr','desc':'Kiểu con trỏ.','detail':'Dùng với cast để tạo pointer từ số.','ex':[('VGA','paw vga = cast(ptr, 0xB8000)','4096')]},
    'null': {'cat':'Giá trị','sig':'null','desc':'Con trỏ null — alias của hungry (0).','ex':[('Cơ bản','meow null','0')]},
    'packed': {'cat':'Low-level','sig':'struct packed <Tên>','desc':'Struct không padding.','detail':'Dùng cho binary layout chính xác.','ex':[]},
}

BUILTINS_EXTRA = {
    # Math mới
    'log2':   {'cat':'Toán','sig':'log2(x)','desc':'Logarit cơ số 2.','ex':[('8','meow log2(8)','3')]},
    'log10':  {'cat':'Toán','sig':'log10(x)','desc':'Logarit cơ số 10.','ex':[('100','meow log10(100)','2')]},
    'asin':   {'cat':'Toán','sig':'asin(x)','desc':'Arcsin.','ex':[]},
    'acos':   {'cat':'Toán','sig':'acos(x)','desc':'Arccos.','ex':[]},
    'atan':   {'cat':'Toán','sig':'atan(x)','desc':'Arctan.','ex':[]},
    'atan2':  {'cat':'Toán','sig':'atan2(y, x)','desc':'Arctan 2 tham số.','ex':[]},
    'sinh':   {'cat':'Toán','sig':'sinh(x)','desc':'Sin hyperbolic.','ex':[]},
    'cosh':   {'cat':'Toán','sig':'cosh(x)','desc':'Cos hyperbolic.','ex':[]},
    'tanh':   {'cat':'Toán','sig':'tanh(x)','desc':'Tan hyperbolic.','ex':[]},
    'hypot':  {'cat':'Toán','sig':'hypot(a, b)','desc':'sqrt(a² + b²).','ex':[('3,4','meow hypot(3, 4)','5')]},
    'degrees':{'cat':'Toán','sig':'degrees(rad)','desc':'Đổi radian sang độ.','ex':[]},
    'radians':{'cat':'Toán','sig':'radians(deg)','desc':'Đổi độ sang radian.','ex':[]},
    'pi':     {'cat':'Toán','sig':'pi','desc':'Hằng số π.','ex':[('Pi','meow pi','3.14159265358979')]},
    'e':      {'cat':'Toán','sig':'e','desc':'Hằng số Euler.','ex':[('E','meow e','2.718281828459045')]},

    # String mới
    'pad_left':  {'cat':'Chuỗi','sig':'pad_left(s, n, c)','desc':'Thêm ký tự vào bên trái.','ex':[('Cơ bản','meow pad_left("hi", 5, "0")','000hi')]},
    'pad_right': {'cat':'Chuỗi','sig':'pad_right(s, n, c)','desc':'Thêm ký tự vào bên phải.','ex':[('Cơ bản','meow pad_right("hi", 5, ".")','hi...')]},
    'substring': {'cat':'Chuỗi','sig':'substring(s, a, b)','desc':'Cắt chuỗi từ a đến b.','ex':[]},
    'char_code': {'cat':'Chuỗi','sig':'char_code(c)','desc':'Mã ASCII của ký tự.','ex':[('A','meow char_code("A")','65')]},
    'char_from': {'cat':'Chuỗi','sig':'char_from(n)','desc':'Ký tự từ mã ASCII.','ex':[('65','meow char_from(65)','A')]},
    'repeat':    {'cat':'Chuỗi','sig':'repeat(s, n)','desc':'Lặp chuỗi n lần.','ex':[('Cơ bản','meow repeat("ab", 3)','ababab')]},
    'reverse_str':{'cat':'Chuỗi','sig':'reverse_str(s)','desc':'Đảo ngược chuỗi.','ex':[('Cơ bản','meow reverse_str("hello")','olleh')]},
    'is_digit':  {'cat':'Chuỗi','sig':'is_digit(s)','desc':'Kiểm tra toàn chữ số.','ex':[('42','meow is_digit("42")','nod')]},
    'is_alpha':  {'cat':'Chuỗi','sig':'is_alpha(s)','desc':'Kiểm tra toàn chữ cái.','ex':[('abc','meow is_alpha("abc")','nod')]},

    # File I/O
    'read_file':   {'cat':'File','sig':'read_file(path)','desc':'Đọc toàn bộ file thành chuỗi.','ex':[('Cơ bản','write_file("/tmp/t.txt", "hi")\nmeow read_file("/tmp/t.txt")','hi')]},
    'write_file':  {'cat':'File','sig':'write_file(path, content)','desc':'Ghi file (ghi đè).','ex':[('Cơ bản','write_file("/tmp/t.txt", "hello")\nmeow exists("/tmp/t.txt")','nod')]},
    'append_file': {'cat':'File','sig':'append_file(path, content)','desc':'Ghi thêm vào cuối file.','ex':[]},
    'exists':      {'cat':'File','sig':'exists(path)','desc':'Kiểm tra file/thư mục tồn tại.','ex':[('Cơ bản','meow exists("/etc/passwd")','nod')]},
    'is_file':     {'cat':'File','sig':'is_file(path)','desc':'Kiểm tra là file.','ex':[]},
    'is_dir':      {'cat':'File','sig':'is_dir(path)','desc':'Kiểm tra là thư mục.','ex':[]},
    'list_dir':    {'cat':'File','sig':'list_dir(path)','desc':'Danh sách file trong thư mục.','ex':[('Cơ bản','meow list_dir("/tmp")','[...]')]},
    'remove_file': {'cat':'File','sig':'remove_file(path)','desc':'Xóa file hoặc thư mục rỗng.','ex':[]},
    'make_dir':    {'cat':'File','sig':'make_dir(path)','desc':'Tạo thư mục.','ex':[]},
    'read_lines':  {'cat':'File','sig':'read_lines(path)','desc':'Đọc file thành danh sách dòng.','ex':[]},
    'write_lines': {'cat':'File','sig':'write_lines(path, lines)','desc':'Ghi danh sách dòng vào file.','ex':[]},

    # System
    'env':      {'cat':'Hệ thống','sig':'env(key)','desc':'Đọc biến môi trường.','ex':[('HOME','meow env("HOME")','/home/user')]},
    'cmd_args': {'cat':'Hệ thống','sig':'cmd_args()','desc':'Tham số dòng lệnh.','ex':[]},
    'cwd':      {'cat':'Hệ thống','sig':'cwd()','desc':'Thư mục làm việc hiện tại.','ex':[]},
    'now':      {'cat':'Thời gian','sig':'now()','desc':'Thời gian Unix (giây, có phần thập phân).','ex':[]},
    'sleep':    {'cat':'Thời gian','sig':'sleep(seconds)','desc':'Tạm dừng N giây.','ex':[('Cơ bản','sleep(0.1)\nmeow "done"','done')]},
    'timestamp':{'cat':'Thời gian','sig':'timestamp()','desc':'Timestamp Unix (giây nguyên).','ex':[]},

    # Set
    'to_set':    {'cat':'Set','sig':'to_set(arr)','desc':'Chuyển list thành set (loại trùng).','ex':[('Cơ bản','meow to_set([1,1,2,3,3])','[1, 2, 3]')]},
    'union':     {'cat':'Set','sig':'union(a, b)','desc':'Hợp hai tập.','ex':[('Cơ bản','meow union([1,2], [2,3])','[1, 2, 3]')]},
    'intersect': {'cat':'Set','sig':'intersect(a, b)','desc':'Giao hai tập.','ex':[('Cơ bản','meow intersect([1,2,3], [2,3,4])','[2, 3]')]},
    'difference':{'cat':'Set','sig':'difference(a, b)','desc':'Hiệu hai tập.','ex':[('Cơ bản','meow difference([1,2,3], [2])','[1, 3]')]},
    'unique':    {'cat':'Set','sig':'unique(arr)','desc':'Loại phần tử trùng (giữ thứ tự).','ex':[('Cơ bản','meow unique([1,2,2,3,1])','[1, 2, 3]')]},

    # FFI
    'cpp': {'cat':'FFI','sig':'cpp(lib, func, ...args)','desc':'Gọi hàm C từ thư viện động.','detail':'Load .so bằng ctypes. Chỉ hỗ trợ hàm nhận/trả double.','ex':[('sqrt','meow cpp("m", "sqrt", 16)','4')]},

    # Concurrency
    'spawn':    {'cat':'Đa luồng','sig':'spawn(fn, ...args)','desc':'Chạy hàm ở thread mới.','ex':[]},
    'wait_all': {'cat':'Đa luồng','sig':'wait_all()','desc':'Chờ tất cả thread kết thúc.','ex':[]},
}

# ═══ Tutorial mới ═══
import os as _os

def _load_tut(name):
    path = _os.path.join('content', 'tut', name)
    if _os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            return f.read()
    return '<p>(chưa có nội dung)</p>'

TUTORIAL_EXTRA = [
    ('11-oop',   'Bài 11 — OOP nâng cao',       _load_tut('11-oop.html')),
    ('12-regex', 'Bài 12 — Regex',               _load_tut('12-regex.html')),
    ('13-match', 'Bài 13 — match/case',          _load_tut('13-match.html')),
    ('14-file',  'Bài 14 — File I/O',            _load_tut('14-file.html')),
    ('15-catos', 'Bài 15 — CatOS',               _load_tut('15-catos.html')),
]
