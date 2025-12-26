# nino

A fun little terminal text editor built with Python's `curses`.

## Features (so far)

- In-memory text buffer with multi-line editing
- Arrow-key navigation
- Home/End for line start/end
- Backspace/Delete support
- Basic scrolling (vertical + horizontal)
- Status bar with cursor position and clock
- Transient status messages

## Requirements

- Python 3.10+ (uses `|` type hints)
- A terminal that supports `curses`

## Usage

Run the editor directly:

```bash
./nino.py
```

Or with Python:

```bash
python3 nino.py
```

## Key bindings

- **Ctrl+Q**: quit
- **Arrow keys**: move cursor
- **Home/End**: line start/end
- **Backspace**: delete character to the left
- **Delete**: delete character under cursor
- **Enter**: insert newline
- **Printable characters**: insert text

## Notes / limitations

- Files are not loaded or saved yet (buffer is in-memory only).
- There is no file picker or command mode yet.

## Roadmap ideas

- File open/save
- Prompt for filename on save
- Search
- Status bar hints for unsaved changes
- Basic syntax highlighting
