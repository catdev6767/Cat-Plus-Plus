#!/usr/bin/env python3
"""PawEditor — nano-like editor for Cat++ on Linux."""
import sys, os, curses

CATPP_KEYWORDS = {
    'asm', 'case', 'cast', 'cat', 'either', 'give', 'groom', 'hiss',
    'hungry', 'in', 'kin', 'kit', 'knead', 'leap', 'listen', 'litter',
    'match', 'me', 'meow', 'never', 'nod', 'null', 'of', 'packed', 'paw',
    'ptr', 'purr', 'shake', 'sit', 'sizeof', 'sniff', 'struct', 'swat',
    'tap', 'use', 'volatile', 'with',
}
CATPP_BUILTINS = {
    'abs_path', 'acos', 'append_file', 'asin', 'assert_eq', 'assert_false',
    'assert_true', 'atan', 'atan2', 'bolt', 'bound', 'capitalize_str',
    'char_code', 'char_from', 'chars', 'chase', 'chdir', 'chunk', 'clamp',
    'clear_list', 'cmd_args', 'collar', 'copy_shallow', 'cosh', 'count_sub',
    'cpp', 'cube', 'curl', 'cwd', 'degrees', 'dice', 'dict_get', 'dict_has',
    'difference', 'drip', 'e', 'ends_with', 'enumerate_list', 'env',
    'exists', 'factorial', 'find_all', 'flatten', 'flip', 'flop',
    'format_str', 'format_time', 'from_pairs', 'gcd', 'getenv', 'grow',
    'head', 'hunt', 'hypot', 'index_of', 'insert_at', 'intersect',
    'invert_dict', 'is_alpha', 'is_digit', 'is_dir', 'is_empty', 'is_file',
    'is_null', 'is_prime', 'join_str', 'json_parse', 'json_pretty',
    'json_stringify', 'kits', 'kitten', 'lcm', 'lerp', 'lick', 'line',
    'lion', 'list_dir', 'log10', 'log2', 'make_dir', 'match', 'melt',
    'merge_dict', 'nip', 'now', 'now_ms', 'pad_left', 'pad_right',
    'path_basename', 'path_dirname', 'path_ext', 'path_join', 'perch', 'pi',
    'pile', 'puff', 'radians', 'range_from_to', 'range_list', 'read_file',
    'read_lines', 'rear', 'remove_at', 'remove_file', 'repeat',
    'replace_all', 'reverse_str', 'round_to', 'say', 'scratch', 'seek',
    'setenv', 'shell', 'shred', 'sift', 'sign', 'sinh', 'slant', 'sleep',
    'sleep_ms', 'snatch', 'spawn', 'split_lines', 'square', 'starts_with',
    'stash', 'substring', 'swap', 'sway', 'tail', 'tally', 'tanh',
    'timestamp', 'title_case', 'to_float', 'to_int', 'to_set', 'to_str',
    'type_of', 'union', 'unique', 'wait_all', 'walk', 'wander', 'wave',
    'weave', 'write_file', 'write_lines', 'zip_lists',
}

def hl(line, ext):
    out, i, n = [], 0, len(line)
    while i < n:
        c = line[i]
        if c == chr(35):
            out.append((line[i:], 3)); break
        if c == chr(34):
            j = i + 1
            while j < n and line[j] != chr(34):
                j += 2 if (line[j] == chr(92) and j+1 < n) else 1
            if j < n: j += 1
            out.append((line[i:j], 2)); i = j; continue
        if c.isdigit() or (c == chr(46) and i+1 < n and line[i+1].isdigit()):
            j = i
            if c == chr(48) and i+1 < n and line[i+1] in chr(120)+chr(88)+chr(98)+chr(66):
                j = i + 2
                while j < n and line[j] in chr(48)+chr(49)+chr(50)+chr(51)+chr(52)+chr(53)+chr(54)+chr(55)+chr(56)+chr(57)+chr(97)+chr(98)+chr(99)+chr(100)+chr(101)+chr(102)+chr(65)+chr(66)+chr(67)+chr(68)+chr(69)+chr(70)+chr(95): j += 1
            else:
                while j < n and (line[j].isdigit() or line[j] == chr(46)): j += 1
            out.append((line[i:j], 4)); i = j; continue
        if c.isalpha() or c == chr(95):
            j = i
            while j < n and (line[j].isalnum() or line[j] == chr(95)): j += 1
            w = line[i:j]
            if w in CATPP_KEYWORDS: out.append((w, 5))
            elif w in CATPP_BUILTINS: out.append((w, 6))
            else: out.append((w, 0))
            i = j; continue
        if c in chr(43)+chr(45)+chr(42)+chr(47)+chr(37)+chr(61)+chr(60)+chr(62)+chr(33)+chr(38)+chr(124)+chr(94)+chr(126)+chr(63)+chr(58):
            j = i
            while j < n and line[j] in chr(43)+chr(45)+chr(42)+chr(47)+chr(37)+chr(61)+chr(60)+chr(62)+chr(33)+chr(38)+chr(124)+chr(94)+chr(126)+chr(63)+chr(58): j += 1
            out.append((line[i:j], 7)); i = j; continue
        out.append((c, 0)); i += 1
    return out

class PawEditor:
    def __init__(self, stdscr, filename=None):
        self.stdscr = stdscr
        self.filename = filename
        self.lines = ['']
        self.row = self.col = self.top = 0
        self.dirty = False
        self.msg = ''
        self.mode = 'edit'
        self.p_label = ''
        self.p_text = ''
        if filename and os.path.exists(filename):
            try:
                with open(filename, encoding='utf-8') as f:
                    c = f.read()
                self.lines = c.split('\n')
                if self.lines and self.lines[-1] == '':
                    self.lines.pop()
                if not self.lines: self.lines = ['']
            except Exception as e:
                self.msg = f'Error: {e}'

    def cur(self): return self.lines[self.row] if 0 <= self.row < len(self.lines) else ''

    def draw(self):
        self.stdscr.erase()
        h, w = self.stdscr.getmaxyx()
        th = h - 3
        name = self.filename or '[No Name]'
        st = f'  {name}'
        if self.dirty: st += ' *'
        st += f'   {self.row+1},{self.col+1}'
        self.stdscr.addstr(0, 0, st.ljust(w-1)[:w-1], curses.A_REVERSE)

        ext = os.path.splitext(self.filename or '')[1].lower()
        for i in range(th):
            li = self.top + i
            if li >= len(self.lines): break
            try:
                self.stdscr.addstr(i+1, 0, f'{li+1:>4} ', curses.color_pair(1))
            except curses.error: pass
            x = 5
            for txt, col in hl(self.lines[li], ext):
                if x >= w-1: break
                try:
                    self.stdscr.addstr(i+1, x, txt[:w-1-x], curses.color_pair(col))
                except curses.error: pass
                x += len(txt)

        if self.mode == 'prompt':
            p = f'{self.p_label}{self.p_text}'
            try: self.stdscr.addstr(h-2, 0, p.ljust(w-1)[:w-1], curses.A_REVERSE)
            except curses.error: pass
        else:
            try: self.stdscr.addstr(h-2, 0, self.msg.ljust(w-1)[:w-1], curses.color_pair(3))
            except curses.error: pass

        menu = '^S Save  ^O Save-As  ^K Cut  ^X Exit'
        try: self.stdscr.addstr(h-1, 0, menu.ljust(w-1)[:w-1], curses.A_REVERSE)
        except curses.error: pass

        try: self.stdscr.move(self.row - self.top + 1, self.col + 5)
        except curses.error: pass
        self.stdscr.refresh()

    def save(self, fn=None):
        fn = fn or self.filename
        if not fn:
            self.mode = 'prompt'
            self.p_label = 'Save as: '
            self.p_text = ''
            return
        try:
            with open(fn, 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.lines))
            self.filename = fn
            self.dirty = False
            self.msg = f'Saved: {fn}'
        except Exception as e:
            self.msg = f'Save error: {e}'

    def ins(self, c):
        line = self.cur()
        self.lines[self.row] = line[:self.col] + c + line[self.col:]
        self.col += 1
        self.dirty = True

    def bs(self):
        if self.col > 0:
            line = self.cur()
            self.lines[self.row] = line[:self.col-1] + line[self.col:]
            self.col -= 1
            self.dirty = True
        elif self.row > 0:
            prev = self.lines[self.row-1]
            cur = self.cur()
            self.col = len(prev)
            self.lines[self.row-1] = prev + cur
            del self.lines[self.row]
            self.row -= 1
            self.dirty = True

    def enter(self):
        line = self.cur()
        self.lines[self.row] = line[:self.col]
        self.lines.insert(self.row+1, line[self.col:])
        self.row += 1
        self.col = 0
        self.dirty = True

    def run(self):
        curses.curs_set(1)
        self.stdscr.keypad(True)
        while True:
            self.draw()
            ch = self.stdscr.getch()

            if self.mode == 'prompt':
                if ch == 27:
                    self.mode = 'edit'
                elif ch in (10, 13, curses.KEY_ENTER):
                    self.mode = 'edit'
                    if self.p_label.startswith('Save'):
                        self.save(self.p_text)
                    else:
                        try:
                            n = int(self.p_text) - 1
                            if 0 <= n < len(self.lines):
                                self.row = n; self.col = 0
                        except ValueError: pass
                elif ch in (curses.KEY_BACKSPACE, 127, 8):
                    self.p_text = self.p_text[:-1]
                elif 32 <= ch < 127:
                    self.p_text += chr(ch)
                continue

            if ch == 24:
                if self.dirty:
                    self.msg = 'Unsaved changes. Ctrl+X again to force exit.'
                    self.dirty = False
                else:
                    break
            elif ch == 19: self.save()
            elif ch == 15:
                self.mode = 'prompt'
                self.p_label = 'Save as: '
                self.p_text = self.filename or ''
            elif ch == 7:
                self.mode = 'prompt'
                self.p_label = 'Go to line: '
                self.p_text = ''
            elif ch == 11:
                if len(self.lines) > 1:
                    del self.lines[self.row]
                    if self.row >= len(self.lines): self.row = len(self.lines)-1
                    self.dirty = True
            elif ch == curses.KEY_UP:
                if self.row > 0:
                    self.row -= 1
                    self.col = min(self.col, len(self.cur()))
            elif ch == curses.KEY_DOWN:
                if self.row < len(self.lines)-1:
                    self.row += 1
                    self.col = min(self.col, len(self.cur()))
            elif ch == curses.KEY_LEFT:
                if self.col > 0: self.col -= 1
                elif self.row > 0:
                    self.row -= 1; self.col = len(self.cur())
            elif ch == curses.KEY_RIGHT:
                if self.col < len(self.cur()): self.col += 1
                elif self.row < len(self.lines)-1:
                    self.row += 1; self.col = 0
            elif ch == curses.KEY_HOME: self.col = 0
            elif ch == curses.KEY_END: self.col = len(self.cur())
            elif ch in (curses.KEY_BACKSPACE, 127, 8): self.bs()
            elif ch in (10, 13, curses.KEY_ENTER): self.enter()
            elif ch == 9:
                for _ in range(4): self.ins(' ')
            elif 32 <= ch < 127:
                self.ins(chr(ch))

            if self.row < self.top: self.top = self.row
            if self.row >= self.top + (h:=self.stdscr.getmaxyx()[0]-3):
                self.top = self.row - h + 1


def main(stdscr):
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN, -1)
    curses.init_pair(2, curses.COLOR_GREEN, -1)
    curses.init_pair(3, curses.COLOR_YELLOW, -1)
    curses.init_pair(4, curses.COLOR_MAGENTA, -1)
    curses.init_pair(5, curses.COLOR_BLUE, -1)
    curses.init_pair(6, curses.COLOR_RED, -1)
    curses.init_pair(7, curses.COLOR_WHITE, -1)
    fname = sys.argv[1] if len(sys.argv) > 1 else None
    ed = PawEditor(stdscr, fname)
    try: ed.run()
    except SystemExit: pass


if __name__ == '__main__':
    try: curses.wrapper(main)
    except KeyboardInterrupt: pass
