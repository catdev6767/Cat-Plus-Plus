# -*- coding: utf-8 -*-
# English version — placeholder (chưa dịch)
# Sửa trực tiếp file này để dịch sang tiếng Anh.

# -*- coding: utf-8 -*-
import os

def _load(path):
    with open(os.path.join('content', path), encoding='utf-8') as f:
        return f.read()

KEYWORDS = {
  'meow': {'cat':'I/O','sig':'meow <biểu thức>','desc':'In ra màn hình.','detail':'Tự động chuyển sang chuỗi. nod/shake cho boolean, hungry cho rỗng.','ex':[('Chuỗi','meow "Hello, Cat++!"','Hello, Cat++!'),('Số','meow 42','42'),('Biểu thức','meow 3 + 4 * 2','11')]},
  'paw': {'cat':'Khai báo','sig':'paw <tên> = <biểu thức>','desc':'Khai báo biến.','detail':'Trong cùng scope, ghi đè. Khác scope, tạo biến mới (shadowing).','ex':[('Số','paw x = 10\nmeow x','10'),('Gán lại','paw x = 10\nx = x + 5\nmeow x','15'),('Dict','paw d = {"a": 1}\nmeow d["a"]','1')]},
  'purr': {'cat':'Khai báo','sig':'purr <tên>(<tham số>)','desc':'Định nghĩa hàm.','detail':'Định nghĩa trước khi gọi. Không give → trả về hungry. Đệ quy tối đa 500 tầng.','ex':[('Cơ bản','purr greet(name)\n    meow "Hi, " + name\ngreet("Tom")','Hi, Tom'),('Trả về','purr add(a, b)\n    give a + b\nmeow add(3, 4)','7'),('Đệ quy','purr fact(n)\n    sniff n <= 1\n        give 1\n    give n * fact(n - 1)\nmeow fact(5)','120')]},
  'give': {'cat':'Khai báo','sig':'give <biểu thức>','desc':'Trả về giá trị từ hàm.','detail':'Sau give, hàm thoát ngay. Phải nằm trong hàm.','ex':[('Trả về','purr check(n)\n    sniff n > 0\n        give "dương"\n    give "khác"\nmeow check(5)','dương')]},
  'sniff': {'cat':'Điều khiển','sig':'sniff <điều kiện>','desc':'Rẽ nhánh khi điều kiện đúng.','detail':'Điều kiện đánh giá là nod/shake. Block thụt lề 4 spaces.','ex':[('Cơ bản','sniff 5 > 3\n    meow "đúng"','đúng'),('Có swat','sniff shake\n    meow "a"\nswat\n    meow "b"','b')]},
  'swat': {'cat':'Điều khiển','sig':'swat','desc':'Khối chạy khi sniff sai.','detail':'Phải đi kèm sniff. Không có elif — dùng sniff lồng nhau.','ex':[('Cơ bản','sniff shake\n    meow "a"\nswat\n    meow "b"','b')]},
  'knead': {'cat':'Điều khiển','sig':'knead <điều kiện>','desc':'Lặp khi điều kiện còn đúng.','detail':'Giới hạn 1 triệu lần. Hỗ trợ sit/leap.','ex':[('Đếm','paw i = 1\nknead i <= 3\n    meow i\n    paw i = i + 1','1\n2\n3')]},
  'groom': {'cat':'Điều khiển','sig':'groom <biến> of <danh sách>','desc':'Duyệt danh sách.','detail':'Biến là local trong mỗi lần lặp. Hỗ trợ sit/leap.','ex':[('Duyệt','groom c of ["a", "b"]\n    meow c','a\nb')]},
  'of': {'cat':'Điều khiển','sig':'groom x of <ds>','desc':'Từ khóa phụ trợ cho groom.','detail':'Chỉ dùng trong groom.','ex':[]},
  'sit': {'cat':'Điều khiển','sig':'sit','desc':'Thoát vòng lặp gần nhất.','detail':'Chỉ ảnh hưởng vòng lặp bao quanh.','ex':[('Thoát','paw i = 1\nknead i <= 5\n    sniff i == 3\n        sit\n    meow i\n    paw i = i + 1','1\n2')]},
  'leap': {'cat':'Điều khiển','sig':'leap','desc':'Bỏ qua lần lặp hiện tại.','detail':'Không thoát vòng lặp.','ex':[('Bỏ 2','paw i = 0\nknead i < 4\n    paw i = i + 1\n    sniff i == 2\n        leap\n    meow i','1\n3\n4')]},
  'tap': {'cat':'Lỗi','sig':'tap ... hiss','desc':'Bắt lỗi runtime.','detail':'Không có hiss → lỗi bị bỏ qua.','ex':[('Bắt lỗi','tap\n    paw x = 1 / 0\nhiss e\n    meow e','Chia cho 0')]},
  'hiss': {'cat':'Lỗi','sig':'hiss <tên>','desc':'Bắt lỗi từ tap.','detail':'Tên là biến local chứa thông báo.','ex':[('Cơ bản','tap\n    paw x = 1 / 0\nhiss e\n    meow "Lỗi: " + e','Lỗi: Chia cho 0')]},
  'nod': {'cat':'Giá trị','sig':'nod','desc':'Boolean đúng.','detail':'In ra là nod.','ex':[('Dùng','meow nod','nod')]},
  'shake': {'cat':'Giá trị','sig':'shake','desc':'Boolean sai.','detail':'In ra là shake.','ex':[('Dùng','meow shake','shake')]},
  'hungry': {'cat':'Giá trị','sig':'hungry','desc':'Giá trị rỗng (null).','detail':'Hàm không give trả về hungry.','ex':[('Dùng','meow hungry','hungry')]},
  'with': {'cat':'Logic','sig':'<a> with <b>','desc':'Đúng khi cả hai đúng.','detail':'Đánh giá ngắn mạch.','ex':[('Cơ bản','meow nod with shake','shake')]},
  'either': {'cat':'Logic','sig':'<a> either <b>','desc':'Đúng khi một trong hai đúng.','detail':'Đánh giá ngắn mạch.','ex':[('Cơ bản','meow nod either shake','nod')]},
  'never': {'cat':'Logic','sig':'never <a>','desc':'Đảo ngược boolean.','detail':'Độ ưu tiên cao.','ex':[('Cơ bản','meow never nod','shake')]},
  'cat': {'cat':'OOP','sig':'cat <Tên>','desc':'Định nghĩa class.','detail':'Class chứa paw (field) và purr (method). Method new là constructor.','ex':[('Class','cat Point\n    paw x\n    paw y\n    purr new(a, b)\n        me.x = a\n        me.y = b\n    purr info()\n        give "({me.x}, {me.y})"\n\npaw p = Point(3, 4)\nmeow p.info()','(3, 4)')]},
  'me': {'cat':'OOP','sig':'me.<field>','desc':'Tham chiếu instance hiện tại.','detail':'Tương đương self trong Python.','ex':[('Dùng','cat P\n    paw x\n    purr new(a)\n        me.x = a\npaw p = P(5)\nmeow p.x','5')]},
  'kin': {'cat':'OOP','sig':'cat <Tên> kin <Cha>','desc':'Kế thừa.','detail':'Class con kế thừa field và method của cha.','ex':[('Kế thừa','cat A\n    paw n\n    purr new(x)\n        me.n = x\ncat B kin A\n    purr hi()\n        give me.n\nmeow B("Bob").hi()','Bob')]},
  'litter': {'cat':'OOP','sig':'litter <Tên>','desc':'Định nghĩa enum.','detail':'Truy cập bằng Tên.thànhviên.','ex':[('Enum','litter Color\n    red\n    green\n    blue\nmeow Color.red','Color.red')]},
  'kit': {'cat':'Hàm','sig':'kit(<ts>) => <bt>','desc':'Lambda — hàm ẩn danh.','detail':'Dùng trong chase/sift/curl hoặc gán vào biến.','ex':[('Lambda','paw double = kit(x) => x * 2\nmeow double(21)','42')]},
}

BUILTINS = {
  'tail': {'cat':'Cơ bản','sig':'tail(x)','desc':'Độ dài chuỗi hoặc danh sách.','ex':[('Chuỗi','meow tail("hello")','5'),('DS','meow tail([1,2,3])','3')]},
  'puff': {'cat':'Chuỗi','sig':'puff(s)','desc':'Chữ hoa.','ex':[('Cơ bản','meow puff("hello")','HELLO')]},
  'melt': {'cat':'Chuỗi','sig':'melt(s)','desc':'Chữ thường.','ex':[('Cơ bản','meow melt("HELLO")','hello')]},
  'nip': {'cat':'Chuỗi','sig':'nip(s, a, b)','desc':'Cắt từ a đến b-1.','ex':[('Đầu','meow nip("Hello, Cat!", 0, 5)','Hello')]},
  'bolt': {'cat':'Toán','sig':'bolt(x)','desc':'Trị tuyệt đối.','ex':[('Âm','meow bolt(-5)','5')]},
  'scratch': {'cat':'Toán','sig':'scratch(x)','desc':'Căn bậc 2.','ex':[('16','meow scratch(16)','4')]},
  'flop': {'cat':'Toán','sig':'flop(x)','desc':'Làm tròn xuống.','ex':[('3.9','meow flop(3.9)','3')]},
  'perch': {'cat':'Toán','sig':'perch(x)','desc':'Làm tròn lên.','ex':[('3.1','meow perch(3.1)','4')]},
  'kitten': {'cat':'Toán','sig':'kitten(a, b)','desc':'Nhỏ hơn.','ex':[('Cơ bản','meow kitten(3, 7)','3')]},
  'lion': {'cat':'Toán','sig':'lion(a, b)','desc':'Lớn hơn.','ex':[('Cơ bản','meow lion(3, 7)','7')]},
  'say': {'cat':'Chuyển kiểu','sig':'say(x)','desc':'Sang chuỗi.','ex':[('Số','meow say(42)','42')]},
  'tally': {'cat':'Chuyển kiểu','sig':'tally(x)','desc':'Sang số nguyên.','ex':[('Chuỗi','meow tally("42")','42')]},
  'drip': {'cat':'Chuyển kiểu','sig':'drip(x)','desc':'Sang số thực.','ex':[('Chuỗi','meow drip("3.14")','3.14')]},
  'collar': {'cat':'Dict','sig':'collar(d)','desc':'Danh sách key.','ex':[('Cơ bản','paw d = {"a":1,"b":2}\nmeow collar(d)','[a, b]')]},
  'kits': {'cat':'Dict','sig':'kits(d)','desc':'Danh sách value.','ex':[('Cơ bản','paw d = {"a":1,"b":2}\nmeow kits(d)','[1, 2]')]},
  'seek': {'cat':'Dict','sig':'seek(d, k)','desc':'Kiểm tra key.','ex':[('Cơ bản','paw d = {"a":1}\nmeow seek(d, "a")','nod')]},
  'shred': {'cat':'Chuỗi','sig':'shred(s, sep)','desc':'Tách chuỗi.','ex':[('Cơ bản','meow shred("a,b,c", ",")','[a, b, c]')]},
  'weave': {'cat':'Chuỗi','sig':'weave(ds, sep)','desc':'Nối danh sách.','ex':[('Cơ bản','meow weave(["a","b"], "-")','a-b')]},
  'swap': {'cat':'Chuỗi','sig':'swap(s, a, b)','desc':'Thay thế.','ex':[('Cơ bản','meow swap("hello", "l", "L")','heLLo')]},
  'lick': {'cat':'Chuỗi','sig':'lick(s)','desc':'Cắt khoảng trắng.','ex':[('Cơ bản','meow lick("  hi  ")','hi')]},
  'hunt': {'cat':'Chuỗi','sig':'hunt(s, sub)','desc':'Kiểm tra chuỗi con.','ex':[('Cơ bản','meow hunt("hello", "ell")','nod')]},
  'stash': {'cat':'Danh sách','sig':'stash(ds, v)','desc':'Thêm phần tử.','ex':[('Cơ bản','paw a = [1,2]\nstash(a, 3)\nmeow a','[1, 2, 3]')]},
  'snatch': {'cat':'Danh sách','sig':'snatch(ds)','desc':'Lấy phần tử cuối.','ex':[('Cơ bản','paw a = [1,2,3]\nmeow snatch(a)','3')]},
  'line': {'cat':'Danh sách','sig':'line(ds)','desc':'Sắp xếp.','ex':[('Cơ bản','meow line([3,1,2])','[1, 2, 3]')]},
  'flip': {'cat':'Danh sách','sig':'flip(ds)','desc':'Đảo ngược.','ex':[('Cơ bản','meow flip([1,2,3])','[3, 2, 1]')]},
  'head': {'cat':'Danh sách','sig':'head(ds)','desc':'Phần tử đầu.','ex':[('Cơ bản','meow head([1,2,3])','1')]},
  'rear': {'cat':'Danh sách','sig':'rear(ds)','desc':'Phần tử cuối.','ex':[('Cơ bản','meow rear([1,2,3])','3')]},
  'pile': {'cat':'Danh sách','sig':'pile(ds)','desc':'Tổng danh sách.','ex':[('Cơ bản','meow pile([1,2,3,4])','10')]},
  'walk': {'cat':'Danh sách','sig':'walk(a, b)','desc':'Tạo danh sách số.','ex':[('Cơ bản','meow walk(1, 5)','[1, 2, 3, 4]')]},
  'chase': {'cat':'Bậc cao','sig':'chase(ds, f)','desc':'Áp dụng f (map).','ex':[('Bình phương','meow chase([1,2,3], kit(x) => x*x)','[1, 4, 9]')]},
  'sift': {'cat':'Bậc cao','sig':'sift(ds, f)','desc':'Lọc (filter).','ex':[('Chẵn','meow sift([1,2,3,4], kit(x) => x%2==0)','[2, 4]')]},
  'curl': {'cat':'Bậc cao','sig':'curl(ds, f, init)','desc':'Gộp (reduce).','ex':[('Tổng','meow curl([1,2,3], kit(a,b) => a+b, 0)','6')]},
  'sway': {'cat':'Toán','sig':'sway(x)','desc':'sin(x).','ex':[('0','meow sway(0)','0')]},
  'wave': {'cat':'Toán','sig':'wave(x)','desc':'cos(x).','ex':[('0','meow wave(0)','1')]},
  'slant': {'cat':'Toán','sig':'slant(x)','desc':'tan(x).','ex':[('0','meow slant(0)','0')]},
  'grow': {'cat':'Toán','sig':'grow(x)','desc':'log tự nhiên.','ex':[('1','meow grow(1)','0')]},
  'bound': {'cat':'Toán','sig':'bound(a, b)','desc':'a lũy thừa b.','ex':[('2^10','meow bound(2, 10)','1024')]},
  'wander': {'cat':'Random','sig':'wander()','desc':'Số ngẫu nhiên 0..1.','ex':[]},
  'dice': {'cat':'Random','sig':'dice(a, b)','desc':'Số nguyên ngẫu nhiên.','ex':[('1..6','paw r = dice(1, 6)\nmeow r','(ngẫu nhiên)')]},
}

TUTORIAL = [
  ('01-hello',     'Bài 1 — Hello Mèo',         _load('tut/01-hello.html')),
  ('02-bien',      'Bài 2 — Biến (paw)',         _load('tut/02-bien.html')),
  ('03-dieu-kien', 'Bài 3 — sniff / swat',       _load('tut/03-dieu-kien.html')),
  ('04-vong-lap',  'Bài 4 — knead / groom',      _load('tut/04-vong-lap.html')),
  ('05-ham',       'Bài 5 — purr / give',        _load('tut/05-ham.html')),
  ('06-danh-sach', 'Bài 6 — Danh sách',          _load('tut/06-danh-sach.html')),
  ('07-chuoi',     'Bài 7 — Chuỗi',              _load('tut/07-chuoi.html')),
  ('08-loi',       'Bài 8 — tap / hiss',         _load('tut/08-loi.html')),
  ('09-thuat-toan','Bài 9 — Thuật toán',         _load('tut/09-thuat-toan.html')),
  ('10-class',     'Bài 10 — cat / kin / litter',_load('tut/10-class.html')),
]

SPEC = [
  ('grammar',     'Ngữ pháp EBNF', _load('spec/grammar.html')),
  ('semantics',   'Ngữ nghĩa',     _load('spec/semantics.html')),
  ('conventions', 'Quy ước code',  _load('spec/conventions.html')),
]
