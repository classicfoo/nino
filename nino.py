#!/usr/bin/env python3
import curses
import time
from dataclasses import dataclass, field

CTRL_Q = 17  # Ctrl+Q


@dataclass
class Editor:
    filename: str | None = None
    lines: list[str] = field(default_factory=lambda: [""])
    cx: int = 0  # cursor x in line (col)
    cy: int = 0  # cursor y in buffer (row)

    rowoff: int = 0  # vertical scroll offset
    coloff: int = 0  # horizontal scroll offset

    dirty: bool = False
    status_msg: str = "Ctrl+Q quit | (save later)"
    status_time: float = field(default_factory=time.time)

    def set_status(self, msg: str):
        self.status_msg = msg
        self.status_time = time.time()

    def current_line(self) -> str:
        return self.lines[self.cy]

    def clamp_cursor(self):
        # Keep cy in bounds
        if self.cy < 0:
            self.cy = 0
        if self.cy >= len(self.lines):
            self.cy = len(self.lines) - 1

        # Keep cx in bounds for current line
        line_len = len(self.lines[self.cy])
        if self.cx < 0:
            self.cx = 0
        if self.cx > line_len:
            self.cx = line_len

    def scroll_into_view(self, screen_h: int, screen_w: int):
        # Text area excludes last line (status bar)
        text_h = max(1, screen_h - 1)
        text_w = max(1, screen_w)

        # Vertical scroll
        if self.cy < self.rowoff:
            self.rowoff = self.cy
        elif self.cy >= self.rowoff + text_h:
            self.rowoff = self.cy - text_h + 1

        # Horizontal scroll
        if self.cx < self.coloff:
            self.coloff = self.cx
        elif self.cx >= self.coloff + text_w:
            self.coloff = self.cx - text_w + 1

    def insert_char(self, ch: str):
        line = self.lines[self.cy]
        self.lines[self.cy] = line[:self.cx] + ch + line[self.cx:]
        self.cx += 1
        self.dirty = True

    def insert_newline(self):
        line = self.lines[self.cy]
        left = line[:self.cx]
        right = line[self.cx:]
        self.lines[self.cy] = left
        self.lines.insert(self.cy + 1, right)
        self.cy += 1
        self.cx = 0
        self.dirty = True

    def backspace(self):
        if self.cx > 0:
            line = self.lines[self.cy]
            self.lines[self.cy] = line[: self.cx - 1] + line[self.cx :]
            self.cx -= 1
            self.dirty = True
        elif self.cy > 0:
            # Join with previous line
            prev = self.lines[self.cy - 1]
            cur = self.lines[self.cy]
            new_cx = len(prev)
            self.lines[self.cy - 1] = prev + cur
            del self.lines[self.cy]
            self.cy -= 1
            self.cx = new_cx
            self.dirty = True

    def delete(self):
        line = self.lines[self.cy]
        if self.cx < len(line):
            self.lines[self.cy] = line[: self.cx] + line[self.cx + 1 :]
            self.dirty = True
        elif self.cy < len(self.lines) - 1:
            # Join with next line
            self.lines[self.cy] = line + self.lines[self.cy + 1]
            del self.lines[self.cy + 1]
            self.dirty = True

    def move_left(self):
        if self.cx > 0:
            self.cx -= 1
        elif self.cy > 0:
            self.cy -= 1
            self.cx = len(self.lines[self.cy])

    def move_right(self):
        line_len = len(self.lines[self.cy])
        if self.cx < line_len:
            self.cx += 1
        elif self.cy < len(self.lines) - 1:
            self.cy += 1
            self.cx = 0

    def move_up(self):
        if self.cy > 0:
            self.cy -= 1

    def move_down(self):
        if self.cy < len(self.lines) - 1:
            self.cy += 1

    def move_home(self):
        self.cx = 0

    def move_end(self):
        self.cx = len(self.lines[self.cy])


def draw_status(stdscr, ed: Editor, h: int, w: int):
    left = f" nino  {'(UNSAVED)' if ed.dirty else '(SAVED)'} "
    right = f"Ln {ed.cy+1}, Col {ed.cx+1}  {time.strftime('%H:%M:%S')}"
    bar = left[: max(0, w - 1)].ljust(max(0, w - 1))
    r = right[: max(0, w - 1)]
    if len(r) < w - 1:
        bar = bar[: (w - 1 - len(r))] + r

    stdscr.attron(curses.A_REVERSE)
    stdscr.addstr(h - 1, 0, bar)
    stdscr.attroff(curses.A_REVERSE)


def draw_message(stdscr, ed: Editor, h: int, w: int):
    # Show status message for ~5 seconds
    if time.time() - ed.status_time > 5:
        return
    msg = ed.status_msg[: max(0, w - 1)]
    stdscr.addstr(h - 1, 0, msg.ljust(max(0, w - 1)), curses.A_REVERSE)


def refresh_screen(stdscr, ed: Editor):
    stdscr.erase()
    h, w = stdscr.getmaxyx()
    text_h = max(1, h - 1)

    # Draw buffer lines within viewport
    for screen_y in range(text_h):
        file_y = ed.rowoff + screen_y
        if file_y >= len(ed.lines):
            # Tilde like vim, empty area
            stdscr.addstr(screen_y, 0, "~")
            continue

        line = ed.lines[file_y]
        # Apply horizontal scroll
        visible = line[ed.coloff : ed.coloff + max(0, w - 1)]
        stdscr.addstr(screen_y, 0, visible)

    # Status bar
    draw_status(stdscr, ed, h, w)
    draw_message(stdscr, ed, h, w)

    # Place cursor on screen
    ed.clamp_cursor()
    ed.scroll_into_view(h, w)
    screen_x = ed.cx - ed.coloff
    screen_y = ed.cy - ed.rowoff
    if 0 <= screen_y < text_h and 0 <= screen_x < w:
        stdscr.move(screen_y, screen_x)
    else:
        stdscr.move(0, 0)

    stdscr.refresh()


def process_key(stdscr, ed: Editor, ch: int):
    if ch == CTRL_Q:
        raise SystemExit

    if ch in (curses.KEY_LEFT,):
        ed.move_left()
    elif ch in (curses.KEY_RIGHT,):
        ed.move_right()
    elif ch in (curses.KEY_UP,):
        ed.move_up()
    elif ch in (curses.KEY_DOWN,):
        ed.move_down()
    elif ch in (curses.KEY_HOME,):
        ed.move_home()
    elif ch in (curses.KEY_END,):
        ed.move_end()
    elif ch in (curses.KEY_BACKSPACE, 127, 8):
        ed.backspace()
    elif ch == curses.KEY_DC:  # Delete key
        ed.delete()
    elif ch in (10, 13):  # Enter
        ed.insert_newline()
    elif 32 <= ch <= 126:  # printable ASCII
        ed.insert_char(chr(ch))
    # ignore everything else


def main(stdscr):
    curses.curs_set(1)
    stdscr.keypad(True)
    curses.noecho()
    curses.cbreak()

    stdscr.timeout(50)  # keep UI responsive

    ed = Editor()
    ed.set_status("Ctrl+Q quit | arrows move | type to edit")

    while True:
        refresh_screen(stdscr, ed)
        ch = stdscr.getch()
        if ch == -1:
            continue
        try:
            process_key(stdscr, ed, ch)
        except SystemExit:
            break


if __name__ == "__main__":
    curses.wrapper(main)
