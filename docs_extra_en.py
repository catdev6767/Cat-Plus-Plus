# -*- coding: utf-8 -*-
"""English docs — Phase 1 additions.
Merged into docs_data_en.py by gen_docs.py.
"""

KEYWORDS_EXTRA = {
    'cast': {'cat':'Low-level','sig':'cast(type, value)','desc':'Cast a value to a given type.','detail':'Used for OS dev and type control. Supported types: i8, i16, i32, i64, u8, u16, u32, u64, ptr, int, float, bool, str.','ex':[('Cast to int','meow cast(int, "42")','42'),('Cast to str','meow cast(str, 42)','42'),('Cast pointer','paw p = cast(ptr, 0xB8000)','4096')]},
    'sizeof': {'cat':'Low-level','sig':'sizeof(x) or sizeof(type)','desc':'Size of a value or type in bytes.','detail':'For types: uses the TYPE_SIZES table. For values: measures by actual type.','ex':[('Value','meow sizeof(42)','8'),('String','meow sizeof("hello")','5'),('Type','meow sizeof(i32)','4')]},
    'struct': {'cat':'Low-level','sig':'struct <Name>\n    <field>: <type>','desc':'Define a C-layout struct.','detail':'Like a class but with no methods. Used for plain data.','ex':[('Point','struct Point\n    x: i32\n    y: i32\npaw p = Point(3, 4)\nmeow p.x','3')]},
    'volatile': {'cat':'Low-level','sig':'volatile paw <name> = <value>','desc':'Volatile variable — compiler will not optimize.','detail':'Used for memory-mapped I/O (MMIO).','ex':[('Basic','volatile paw status = 0\nmeow status','0')]},
    'asm': {'cat':'Low-level','sig':'asm("instruction")','desc':'Inline assembly.','detail':'In the interpreter it is only parsed, not executed. In Felis OS it is transpiled to __asm__ volatile().','ex':[('NOP','asm("nop")\nmeow "ok"','ok')]},
    'static': {'cat':'OOP','sig':'purr static <method>()','desc':'Static method — called on the class, no instance needed.','ex':[('Basic','cat Math\n    purr static square(n)\n        give n * n\nmeow Math.square(5)','25')]},
    'get': {'cat':'OOP','sig':'purr get <name>()','desc':'Getter — runs when the field is read.','ex':[('Basic','cat P\n    paw _x\n    purr new(v)\n        me.x = v\n    purr get x()\n        give me._x\nmeow P(42).x','42')]},
    'set': {'cat':'OOP','sig':'purr set <name>(v)','desc':'Setter — runs when the field is assigned.','ex':[('Basic','cat P\n    paw _x\n    purr set x(v)\n        me._x = v * 2\n    purr get x()\n        give me._x\npaw p = P()\np.x = 5\nmeow p.x','10')]},
    'abstract': {'cat':'OOP','sig':'cat abstract <Name>','desc':'Abstract class — cannot be instantiated.','detail':'Use `purr <method>()` with no body to declare an abstract method. Subclass must override all.','ex':[('Shape','cat abstract Shape\n    purr area()\ncat Circle kin Shape\n    paw r\n    purr new(r)\n        me.r = r\n    purr area()\n        give 3.14 * me.r * me.r\nmeow Circle(2).area()','12.56')]},
    'match': {'cat':'Control','sig':'match <expr>\n    case <value>\n        ...','desc':'Pattern matching — compares against multiple values.','detail':'Use `case _` as wildcard. Each case is a block.','ex':[('Basic','paw x = 2\nmatch x\n    case 1\n        meow "one"\n    case 2\n        meow "two"','two'),('Wildcard','paw x = 99\nmatch x\n    case 1\n        meow "one"\n    case _\n        meow "other"','other')]},
    'case': {'cat':'Control','sig':'case <value>','desc':'Branch inside match.','detail':'Only used inside a match block.','ex':[]},
    'use': {'cat':'Module','sig':'use "file.cat"','desc':'Import another Cat++ file.','detail':'Searches in examples/, current directory. Runs the whole file into the current scope.','ex':[('Import lib','use "mathlib.cat"\nmeow square(5)','25')]},
    'ptr': {'cat':'Low-level','sig':'ptr','desc':'Pointer type.','detail':'Used with cast to create a pointer from a number.','ex':[('VGA','paw vga = cast(ptr, 0xB8000)','4096')]},
    'null': {'cat':'Value','sig':'null','desc':'Null pointer — alias of hungry (0).','ex':[('Basic','meow null','0')]},
    'packed': {'cat':'Low-level','sig':'struct packed <Name>','desc':'Struct with no padding.','detail':'Used for exact binary layout.','ex':[]},
}

BUILTINS_EXTRA = {
    'log2':   {'cat':'Math','sig':'log2(x)','desc':'Base-2 logarithm.','ex':[('8','meow log2(8)','3')]},
    'log10':  {'cat':'Math','sig':'log10(x)','desc':'Base-10 logarithm.','ex':[('100','meow log10(100)','2')]},
    'asin':   {'cat':'Math','sig':'asin(x)','desc':'Arc sine.','ex':[]},
    'acos':   {'cat':'Math','sig':'acos(x)','desc':'Arc cosine.','ex':[]},
    'atan':   {'cat':'Math','sig':'atan(x)','desc':'Arc tangent.','ex':[]},
    'atan2':  {'cat':'Math','sig':'atan2(y, x)','desc':'Two-argument arc tangent.','ex':[]},
    'sinh':   {'cat':'Math','sig':'sinh(x)','desc':'Hyperbolic sine.','ex':[]},
    'cosh':   {'cat':'Math','sig':'cosh(x)','desc':'Hyperbolic cosine.','ex':[]},
    'tanh':   {'cat':'Math','sig':'tanh(x)','desc':'Hyperbolic tangent.','ex':[]},
    'hypot':  {'cat':'Math','sig':'hypot(a, b)','desc':'sqrt(a² + b²).','ex':[('3,4','meow hypot(3, 4)','5')]},
    'degrees':{'cat':'Math','sig':'degrees(rad)','desc':'Convert radians to degrees.','ex':[]},
    'radians':{'cat':'Math','sig':'radians(deg)','desc':'Convert degrees to radians.','ex':[]},
    'pi':     {'cat':'Math','sig':'pi','desc':'Constant pi.','ex':[('Pi','meow pi','3.14159265358979')]},
    'e':      {'cat':'Math','sig':'e','desc':'Euler constant.','ex':[('E','meow e','2.718281828459045')]},
    'pad_left':  {'cat':'String','sig':'pad_left(s, n, c)','desc':'Pad a string on the left.','ex':[('Basic','meow pad_left("hi", 5, "0")','000hi')]},
    'pad_right': {'cat':'String','sig':'pad_right(s, n, c)','desc':'Pad a string on the right.','ex':[('Basic','meow pad_right("hi", 5, ".")','hi...')]},
    'substring': {'cat':'String','sig':'substring(s, a, b)','desc':'Slice string from a to b.','ex':[]},
    'char_code': {'cat':'String','sig':'char_code(c)','desc':'ASCII code of a character.','ex':[('A','meow char_code("A")','65')]},
    'char_from': {'cat':'String','sig':'char_from(n)','desc':'Character from an ASCII code.','ex':[('65','meow char_from(65)','A')]},
    'repeat':    {'cat':'String','sig':'repeat(s, n)','desc':'Repeat a string n times.','ex':[('Basic','meow repeat("ab", 3)','ababab')]},
    'reverse_str':{'cat':'String','sig':'reverse_str(s)','desc':'Reverse a string.','ex':[('Basic','meow reverse_str("hello")','olleh')]},
    'is_digit':  {'cat':'String','sig':'is_digit(s)','desc':'Check if all characters are digits.','ex':[('42','meow is_digit("42")','nod')]},
    'is_alpha':  {'cat':'String','sig':'is_alpha(s)','desc':'Check if all characters are letters.','ex':[('abc','meow is_alpha("abc")','nod')]},
    'read_file':   {'cat':'File','sig':'read_file(path)','desc':'Read the whole file as a string.','ex':[('Basic','write_file("/tmp/t.txt", "hi")\nmeow read_file("/tmp/t.txt")','hi')]},
    'write_file':  {'cat':'File','sig':'write_file(path, content)','desc':'Write file (overwrites).','ex':[('Basic','write_file("/tmp/t.txt", "hello")\nmeow exists("/tmp/t.txt")','nod')]},
    'append_file': {'cat':'File','sig':'append_file(path, content)','desc':'Append to the end of a file.','ex':[]},
    'exists':      {'cat':'File','sig':'exists(path)','desc':'Check if a file/directory exists.','ex':[('Basic','meow exists("/etc/passwd")','nod')]},
    'is_file':     {'cat':'File','sig':'is_file(path)','desc':'Check if path is a file.','ex':[]},
    'is_dir':      {'cat':'File','sig':'is_dir(path)','desc':'Check if path is a directory.','ex':[]},
    'list_dir':    {'cat':'File','sig':'list_dir(path)','desc':'List files in a directory.','ex':[('Basic','meow list_dir("/tmp")','[...]')]},
    'remove_file': {'cat':'File','sig':'remove_file(path)','desc':'Remove a file or empty directory.','ex':[]},
    'make_dir':    {'cat':'File','sig':'make_dir(path)','desc':'Create a directory.','ex':[]},
    'read_lines':  {'cat':'File','sig':'read_lines(path)','desc':'Read a file as a list of lines.','ex':[]},
    'write_lines': {'cat':'File','sig':'write_lines(path, lines)','desc':'Write a list of lines to a file.','ex':[]},
    'env':      {'cat':'System','sig':'env(key)','desc':'Read an environment variable.','ex':[('HOME','meow env("HOME")','/home/user')]},
    'cmd_args': {'cat':'System','sig':'cmd_args()','desc':'Command-line arguments.','ex':[]},
    'cwd':      {'cat':'System','sig':'cwd()','desc':'Current working directory.','ex':[]},
    'now':      {'cat':'Time','sig':'now()','desc':'Unix time (seconds, fractional).','ex':[]},
    'sleep':    {'cat':'Time','sig':'sleep(seconds)','desc':'Pause for N seconds.','ex':[('Basic','sleep(0.1)\nmeow "done"','done')]},
    'timestamp':{'cat':'Time','sig':'timestamp()','desc':'Unix timestamp (integer seconds).','ex':[]},
    'to_set':    {'cat':'Set','sig':'to_set(arr)','desc':'Convert a list to a set (deduplicated).','ex':[('Basic','meow to_set([1,1,2,3,3])','[1, 2, 3]')]},
    'union':     {'cat':'Set','sig':'union(a, b)','desc':'Union of two sets.','ex':[('Basic','meow union([1,2], [2,3])','[1, 2, 3]')]},
    'intersect': {'cat':'Set','sig':'intersect(a, b)','desc':'Intersection of two sets.','ex':[('Basic','meow intersect([1,2,3], [2,3,4])','[2, 3]')]},
    'difference':{'cat':'Set','sig':'difference(a, b)','desc':'Difference of two sets.','ex':[('Basic','meow difference([1,2,3], [2])','[1, 3]')]},
    'unique':    {'cat':'Set','sig':'unique(arr)','desc':'Remove duplicates (keeps order).','ex':[('Basic','meow unique([1,2,2,3,1])','[1, 2, 3]')]},
    'cpp': {'cat':'FFI','sig':'cpp(lib, func, ...args)','desc':'Call a C function from a dynamic library.','detail':'Loads .so via ctypes. Only supports functions taking/returning double.','ex':[('sqrt','meow cpp("m", "sqrt", 16)','4')]},
    'spawn':    {'cat':'Concurrency','sig':'spawn(fn, ...args)','desc':'Run a function in a new thread.','ex':[]},
    'wait_all': {'cat':'Concurrency','sig':'wait_all()','desc':'Wait for all threads to finish.','ex':[]},
}

import os as _os

def _load_tut(name):
    path = _os.path.join('content', 'tut', name)
    if _os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            return f.read()
    return '<p>(no content yet)</p>'

TUTORIAL_EXTRA = [
    ('11-oop',   'Lesson 11 — Advanced OOP',            _load_tut('11-oop.html')),
    ('12-regex', 'Lesson 12 — Regex',                   _load_tut('12-regex.html')),
    ('13-match', 'Lesson 13 — match/case',              _load_tut('13-match.html')),
    ('14-file',  'Lesson 14 — File I/O',                _load_tut('14-file.html')),
    ('15-catos', 'Lesson 15 — CatOS (legacy)',          _load_tut('15-catos.html')),
    ('16-vm',    'Lesson 16 — Bytecode VM',             _load_tut('16-vm.html')),
    ('17-pycompiler', 'Lesson 17 — PyCompiler',         _load_tut('17-pycompiler.html')),
    ('18-felis-intro', 'Lesson 18 — Felis OS intro',    _load_tut('18-felis-intro.html')),
    ('19-felis-cmds', 'Lesson 19 — Felis OS commands',  _load_tut('19-felis-cmds.html')),
    ('20-felis-fs', 'Lesson 20 — Felis OS filesystem',  _load_tut('20-felis-fs.html')),
    ('21-felis-editor', 'Lesson 21 — Felis OS line editor', _load_tut('21-felis-editor.html')),
    ('22-felis-keyboard', 'Lesson 22 — Keyboard driver', _load_tut('22-felis-keyboard.html')),
    ('23-felis-idt', 'Lesson 23 — IDT and Interrupts',  _load_tut('23-felis-idt.html')),
    ('24-felis-build', 'Lesson 24 — Build system',      _load_tut('24-felis-build.html')),
    ('25-felis-iso', 'Lesson 25 — Create bootable USB ISO', _load_tut('25-felis-iso.html')),
    ('26-felis-vga', 'Lesson 26 — VGA driver',          _load_tut('26-felis-vga.html')),
    ('27-felis-serial', 'Lesson 27 — Serial port',      _load_tut('27-felis-serial.html')),
    ('28-felis-memory', 'Lesson 28 — Memory management', _load_tut('28-felis-memory.html')),
    ('29-felis-newcmd', 'Lesson 29 — Adding a new command', _load_tut('29-felis-newcmd.html')),
    ('30-felis-project', 'Lesson 30 — Final project',   _load_tut('30-felis-project.html')),
]

def _load_file(path):
    if _os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            return f.read()
    return '<p>(no content)</p>'

COOKBOOK_EXTRA = [
    ('file',      'File I/O',   _load_file('content/cookbook/file.html')),
    ('string',    'Strings',    _load_file('content/cookbook/string.html')),
    ('list',      'Lists',      _load_file('content/cookbook/list.html')),
    ('algorithm', 'Algorithms', _load_file('content/cookbook/algorithm.html')),
]

ERRORS_EXTRA = [
    ('syntax',  'Syntax errors',  _load_file('content/errors/syntax.html')),
    ('runtime', 'Runtime errors', _load_file('content/errors/runtime.html')),
    ('oop',     'OOP errors',     _load_file('content/errors/oop.html')),
]

GUIDE_EXTRA = [
    ('felis',          'Felis OS — Guide',        _load_file('content/guide/felis.html')),
    ('best-practices', 'Best Practices',          _load_file('content/guide/best-practices.html')),
    ('internals',      'Internals — How it runs', _load_file('content/guide/internals.html')),
    ('performance',    'Performance Guide',       _load_file('content/guide/performance.html')),
]
