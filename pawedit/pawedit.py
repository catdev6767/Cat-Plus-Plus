#!/usr/bin/env python3
"""PawEditor — nano-like editor for Cat++ on Linux."""
import sys, os, curses

CATPP_KEYWORDS = {
    'meow','paw','purr','give','sniff','swat','knead','groom','sit','leap',
    'tap','hiss','nod','shake','hungry','with','either','never','cat','kin',
    'me','kit','litter','use','match','case','in','cast','sizeof','asm','ptr',
    'null','packed','struct','volatile','of','static','get','set','abstract',
}
CATPP_BUILTINS = {
    'tail','puff','melt','nip','bolt','kitten','lion','say','tally','drip',
    'collar','kits','seek','shred','weave','swap','lick','hunt','stash','snatch',
    'line','flip','head','rear','pile','walk','chase','sift','curl',
    'scratch','flop','perch','bound','sway','wave','slant','grow',
    'read_file','write_file','exists','env','cwd','now','sleep','unique',
}

def hl(line, ext):
    if ext != '.cat':
        return [(line, 0)]
    out, i, n = [], 0, len(line)
    while i < n:
        c = line[i]
        if c == '#':
            out.append((line[i:], 3)); break
        if c == '"':
            j = i + 1
            while j < n and line[j] != '"':
                j += 2 if (line[j] == '\\' and j+1 < n) else 1
            if j < n: j += 1
            out.append((line[i:j], 2)); i = j; continue
        if c.isdigit():
            j = i
            while j < n and (line[j].isdigit() or line[j] == '.'): j += 1
            out.append((line[i:j], 4)); i = j; continue
        if c.isalpha() or c == '_':
            j = i
            while j < n and (line[j].isalnum() or line[j] == '_'): j += 1
            w = line[i:j]
            if w in CATPP_KEYWORDS: out.append((w, 5))
            elif w in CATPP_BUILTINS: out.append((w, 6))
            else: out.append((w, 0))
            i = j; continue
        if c in '+-*/%=<>!&|^~?:':
            j = i
            while j < n and line[j] in '+-*/%=<>!&|^~?:': j += 1
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
