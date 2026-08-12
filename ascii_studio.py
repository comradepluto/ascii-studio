#!/usr/bin/env python3
"""ASCII Studio — a terminal tool for ASCII art.

Turn an image into ASCII art, or render plain text as big ASCII lettering.

Usage:
    python3 ascii_studio.py                     (guided wizard)
    python3 ascii_studio.py <image-file> [opts] (quick convert)
    python3 ascii_studio.py image <img> [opts]
    python3 ascii_studio.py text "message" [opts]
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys

from figlet_fonts import FIGLET_FONTS

__version__ = "2.3.0"

DEFAULT_WIDTH = 100
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tif", ".tiff"}

TEXT_STYLES = ("Block", "Shadow", "Mini", "Slant", "Bold", "Bubble", "Framed")

CHAR_SETS = {
    "Standard": "@%#*+=-:. ",
    "Short": "@#*+;:, '",
    "Simple": "#. ",
    "Binary": "10",
    "Blocks": "█▓▒░ ",
    "Faint": " .:-=+*#%@",
}

# --------------------------------------------------------------------------
# Text -> ASCII lettering
# --------------------------------------------------------------------------

# Each style is a real FIGlet font, so it has its own native symbols and look.
_FIGLET_STYLES = {
    "Block": "standard",
    "Shadow": "shadow",
    "Mini": "mini",
    "Slant": "slant",
    "Bold": "big",
    "Bubble": "bubble",
}

_SHADOW_INK = {"\\"}


def _scale_lines(raw: list[str], scale: int) -> list[str]:
    scale = max(1, scale)
    if scale == 1:
        return raw
    out: list[str] = []
    for ln in raw:
        expanded = "".join(c * scale for c in ln)
        out.extend([expanded] * scale)
    return out


def _figlet_lines(text: str, font_name: str, spacing: int = 0,
                  scale: int = 1) -> list[str]:
    """Render ``text`` with a FIGlet ``font_name`` as a list of lines.

    Each glyph's rows are padded to the glyph's own width, so letters keep
    a consistent box and line up across rows.
    """
    height, glyphs = FIGLET_FONTS[font_name]
    blank = ("",) * height
    gap = " " * max(0, spacing)
    cells: list[list[str]] = [[] for _ in range(height)]
    for ch in text:
        glyph = glyphs.get(ch, glyphs.get(ch.upper(), blank))
        gw = max((len(r) for r in glyph), default=0)
        for row in range(height):
            cells[row].append(glyph[row].ljust(gw))
    out = [gap.join(cols).rstrip() for cols in cells]
    return _scale_lines(out, scale)


_figlet_figlet = None


def _figlet_engine():
    """Return the ``pyfiglet.Figlet`` class, or ``False`` if unavailable."""
    global _figlet_figlet
    if _figlet_figlet is None:
        try:
            from pyfiglet import Figlet
        except Exception:
            _figlet_figlet = False
        else:
            _figlet_figlet = Figlet
    return _figlet_figlet


def _figlet_render(text: str, font_name: str, spacing: int = 0,
                   scale: int = 1) -> list[str]:
    """Render ``text`` with the real FIGlet engine when pyfiglet is installed.

    Falls back to the bundled font data when it isn't.
    """
    engine = _figlet_engine()
    if engine is not False:
        try:
            if spacing:
                gap = " " * spacing
                cells = []
                for ch in text:
                    rows = engine(font=font_name, width=1000).renderText(ch).splitlines()
                    cells.append(_strip_blank_rows(rows))
                height = max((len(c) for c in cells), default=0)
                out: list[str] = []
                for row in range(height):
                    parts = []
                    for c in cells:
                        cw = max((len(r) for r in c), default=0)
                        parts.append(c[row] if row < len(c) else " " * cw)
                    out.append(gap.join(parts).rstrip())
                return _scale_lines(out, scale)
            rows = engine(font=font_name, width=1000).renderText(text).splitlines()
            return _scale_lines(_strip_blank_rows(rows), scale)
        except Exception:
            pass
    if font_name not in FIGLET_FONTS:
        font_name = "standard"
    return _figlet_lines(text, font_name, spacing, scale)


def _strip_blank_rows(rows: list[str]) -> list[str]:
    """Drop all-blank rows from the top and bottom of a glyph block."""
    while rows and not rows[0].strip():
        rows.pop(0)
    while rows and not rows[-1].strip():
        rows.pop()
    return rows


def _trim_left_margin(rows: list[str]) -> list[str]:
    """Trim the common leading margin so a word's rows share one left edge."""
    nonblank = [r for r in rows if r.strip()]
    if not nonblank:
        return rows
    lead = min(len(r) - len(r.lstrip(" ")) for r in nonblank)
    return [r[lead:] for r in rows]


def _graffiti_word(text: str) -> list[str]:
    """Render one logo word in graffiti lettering, exactly as figlet draws it.

    Keeps the font's real spacing (letters stay readable and aligned) and
    drops the font's sparse bottom swoosh row, which only reads as debris.
    """
    rows = _strip_blank_rows(_figlet_render(text, "graffiti"))
    rows = rows[:-1]
    return _trim_left_margin(rows)


def _replace_ink(art: str, fill: str) -> str:
    """Swap every non-space glyph character for a single ``fill`` char."""
    fill = fill[:1]
    if not fill:
        return art
    return "".join(fill if c != " " else " " for c in art)


def _framed_box(inner: list[str], border: str) -> str:
    width = max((len(ln) for ln in inner), default=0)
    edge = border * (width + 2)
    body = [border + ln.ljust(width) + border for ln in inner]
    return "\n".join([edge, *body, edge])


def render_text(
    text: str,
    style: str = "Block",
    fill_char: str | None = None,
    shadow_char: str | None = None,
    spacing: int = 0,
    scale: int = 1,
) -> str:
    """Render ``text`` as ASCII lettering in the given ``style``.

    Styles: Block, Shadow, Mini, Slant, Bold, Bubble, Framed.
    The letterforms come from real FIGlet fonts, so every style has its own
    symbols (``/ \\ _ |`` and friends) instead of a flat hash grid.  A blank
    ``fill_char`` keeps the font's native symbols; supplying one recolors the
    whole glyph.  For the Shadow style, ``shadow_char`` recolors the echo.
    """
    style = (style or "Block").title()
    if style == "Framed":
        inner = _figlet_render(text, "standard", spacing, scale)
        if fill_char:
            return _framed_box(inner, fill_char[:1])
        width = max((len(ln) for ln in inner), default=0)
        top = "+" + "-" * (width + 2) + "+"
        body = ["| " + ln.ljust(width) + " |" for ln in inner]
        return "\n".join([top, *body, top])
    art = "\n".join(_figlet_render(text, _FIGLET_STYLES.get(style, "standard"),
                                   spacing, scale))
    if style == "Shadow" and shadow_char and shadow_char not in _SHADOW_INK:
        art = art.replace("\\", shadow_char[:1])
    return _replace_ink(art, fill_char or "")


# --------------------------------------------------------------------------
# Image -> ASCII art
# --------------------------------------------------------------------------

# (distro group) -> index into the install-hints table
_DISTRO_GROUPS = {
    "arch": 0, "manjaro": 0, "endeavouros": 0, "garuda": 0, "cachyos": 0,
    "debian": 1, "ubuntu": 1, "linuxmint": 1, "pop": 1, "elementary": 1,
    "raspbian": 1, "kali": 1,
    "fedora": 2, "rhel": 2, "centos": 2, "rocky": 2, "almalinux": 2,
    "nobara": 2,
    "opensuse": 3, "opensuse-tumbleweed": 3, "suse": 3,
}

_INSTALL_TABLE = [
    ("Arch / Manjaro",            "sudo pacman -S",  ["python-pillow",   "python-colorama"]),
    ("Debian / Ubuntu / Mint",    "sudo apt install", ["python3-pil",     "python3-colorama"]),
    ("Fedora / RHEL / CentOS",    "sudo dnf install", ["python3-pillow",  "python3-colorama"]),
    ("openSUSE",                  "sudo zypper install", ["python3-Pillow", "python3-colorama"]),
    ("Any distro (Python pip)",   "python3 -m pip install", ["Pillow", "colorama"]),
]


def _os_id() -> str:
    try:
        with open("/etc/os-release", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("ID="):
                    return line.split("=", 1)[1].strip().strip('"')
    except OSError:
        pass
    return ""


def print_install_hints() -> None:
    """Show per-distro commands for installing the missing dependencies."""
    detected = _DISTRO_GROUPS.get(_os_id(), -1)
    print("\n  Install the missing dependency with one of these:", file=sys.stderr)
    for i, (label, cmd, pkgs) in enumerate(_INSTALL_TABLE):
        marker = "  >>>" if i == detected else "    "
        print(f"{marker}{label}:", file=sys.stderr)
        print(f"       {cmd} {' '.join(pkgs)}", file=sys.stderr)
    print("\n  Or run the bundled installer:  ./install.sh", file=sys.stderr)
    print("  Full instructions:             see INSTALL.md", file=sys.stderr)


def _load_pillow():
    try:
        from PIL import Image, ImageOps

        return Image, ImageOps
    except ImportError:
        print("\n  Pillow is required for image mode.", file=sys.stderr)
        print_install_hints()
        raise SystemExit(1) from None


def _resolve_charset(charset: str) -> str:
    return CHAR_SETS.get(charset, charset)


def _build_lookup(charset: str, invert: bool) -> list[str]:
    ramp = list(_resolve_charset(charset)) or list(CHAR_SETS["Standard"])
    if invert:
        ramp = list(reversed(ramp))
    n = len(ramp)
    if n > 256:
        ramp = ramp[:256]
        n = 256
    return [ramp[min(n - 1, int(i * n / 256))] for i in range(256)]


def image_to_ascii(
    path: str,
    width: int = DEFAULT_WIDTH,
    charset: str = "Standard",
    invert: bool = False,
    half_height: bool = True,
) -> tuple[str, list[list[tuple[int, int, int]]]]:
    """Turn an image file into ASCII art.

    Returns ``(text, colors)`` where ``colors`` is a parallel matrix of
    (r, g, b) tuples for every output character.
    """
    Image, ImageOps = _load_pillow()

    img = Image.open(path)
    img = ImageOps.exif_transpose(img)
    img = img.convert("RGB")

    w = max(1, min(int(width), 2000))
    aspect = img.height / img.width
    h = int(round(w * aspect))
    if half_height:
        h = int(round(h * 0.5))
    h = max(1, h)

    img = img.resize((w, h), Image.LANCZOS)
    px = img.load()
    lookup = _build_lookup(charset, invert)

    lines: list[str] = []
    colors: list[list[tuple[int, int, int]]] = []
    for y in range(h):
        line = []
        row = []
        for x in range(w):
            r, g, b = px[x, y]
            lum = int(0.2126 * r + 0.7152 * g + 0.0722 * b)
            line.append(lookup[lum])
            row.append((r, g, b))
        lines.append("".join(line))
        colors.append(row)

    while lines and not lines[0].strip():
        lines.pop(0)
        colors.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
        colors.pop()

    out_lines: list[str] = []
    out_colors: list[list[tuple[int, int, int]]] = []
    for ln, row in zip(lines, colors):
        ln = ln.rstrip()
        out_lines.append(ln)
        out_colors.append(row[: len(ln)])
    return "\n".join(out_lines), out_colors


# --------------------------------------------------------------------------
# Output helpers
# --------------------------------------------------------------------------

def colorize(text: str, colors: list[list[tuple[int, int, int]]]) -> str:
    """Return ``text`` with truecolor ANSI escapes per character."""
    out: list[str] = []
    for ln, row in zip(text.split("\n"), colors):
        if not ln:
            out.append("")
            continue
        n = min(len(ln), len(row))
        buf: list[str] = []
        c = 0
        while c < n:
            r, g, b = row[c]
            j = c
            while j < n and row[j] == (r, g, b):
                j += 1
            buf.append(f"\x1b[38;2;{r};{g};{b}m{ln[c:j]}")
            c = j
        buf.append("\x1b[0m")
        out.append("".join(buf))
    return "\n".join(out)


def to_html(text: str, colors: list[list[tuple[int, int, int]]]) -> str:
    lines = text.split("\n")
    parts = [
        '<!doctype html><html><head><meta charset="utf-8">',
        "<style>body{background:#fff}pre{font:12px/1.2 monospace;"
        "white-space:pre;}</style></head><body><pre>",
    ]
    for ln, row in zip(lines, colors):
        esc = ln.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if row:
            c = 0
            n = min(len(esc), len(row))
            while c < n:
                r, g, b = row[c]
                j = c
                while j < n and row[j] == (r, g, b):
                    j += 1
                parts.append(
                    f'<span style="color:#{r:02x}{g:02x}{b:02x}">{esc[c:j]}</span>'
                )
                c = j
        else:
            parts.append(esc)
        parts.append("\n")
    parts.append("</pre></body></html>")
    return "".join(parts)


# --------------------------------------------------------------------------
# Colors (colorama)
# --------------------------------------------------------------------------

def _colors():
    """Return (Fore, Style) from colorama, or (None, None) if unavailable."""
    try:
        from colorama import Fore, Style, init

        init()
        return Fore, Style
    except ImportError:
        return None, None


def _paint(text: str, color) -> str:
    Fore, Style = _colors()
    if Fore is None:
        return text
    return color + text + Style.RESET_ALL


def print_logo() -> None:
    Fore, _ = _colors()
    has_color = Fore is not None

    ascii_art = _graffiti_word("ASCII")
    studio_art = _graffiti_word("STUDIO")

    warm = Fore.LIGHTYELLOW_EX if has_color else None
    cool = Fore.LIGHTCYAN_EX if has_color else None

    tagline_raw = f"v{__version__}  ·  terminal ascii art"

    print()
    for word, color in ((ascii_art, warm), (studio_art, cool)):
        for ln in word:
            out = _paint(ln, color) if has_color else ln
            print(out)
    print(tagline_raw)
    print()


STYLE_PALETTES: dict[str, list[tuple[int, int, int]]] = {
    "Block": [(255, 85, 85), (255, 200, 90), (255, 90, 180)],
    "Shadow": [(120, 135, 160), (90, 200, 220)],
    "Mini": [(110, 220, 160)],
    "Slant": [(90, 200, 220)],
    "Bold": [(255, 170, 60), (255, 90, 90)],
    "Bubble": [(90, 220, 190), (90, 160, 255)],
    "Framed": [(170, 120, 255), (90, 160, 255)],
}


def text_colors(lines: list[str],
                palette: list[tuple[int, int, int]]) -> list[list[tuple[int, int, int]]]:
    """Per-character RGB colors for ASCII lettering (cycled by column)."""
    rows: list[list[tuple[int, int, int]]] = []
    for ln in lines:
        rows.append([palette[i % len(palette)] for i in range(len(ln))])
    return rows


def banner(text: str) -> None:
    Fore, Style = _colors()
    width = 58
    if Fore is None:
        print(f"\n{'─' * width}\n  {text}\n{'─' * width}")
    else:
        print("\n" + Fore.LIGHTCYAN_EX + "─" * width + Style.RESET_ALL)
        print(Fore.LIGHTCYAN_EX + "  " + text + Style.RESET_ALL)
        print(Fore.LIGHTCYAN_EX + "─" * width + Style.RESET_ALL)


# --------------------------------------------------------------------------
# Interactive prompts
# --------------------------------------------------------------------------

def ask(prompt: str, default: str | None = None) -> str:
    label = f" [{default}]" if default is not None else ""
    val = input(f"{prompt}{label}: ").strip()
    return val or (default or "")


def ask_int(prompt: str, default: int) -> int:
    while True:
        val = input(f"{prompt} [{default}]: ").strip()
        if not val:
            return default
        try:
            return max(0, int(val))
        except ValueError:
            print("  Please enter a whole number.")


def ask_choice(prompt: str, choices: list[str], default: str) -> str:
    while True:
        val = input(f"{prompt} ({'/'.join(choices)}) [{default}]: ").strip() or default
        for choice in choices:
            if val.lower() == choice.lower():
                return choice
        print(f"  Please choose one of: {', '.join(choices)}")


def ask_bool(prompt: str, default: bool = False) -> bool:
    label = "Y/n" if default else "y/N"
    val = input(f"{prompt} [{label}]: ").strip().lower()
    if not val:
        return default
    return val in ("y", "yes")


# --------------------------------------------------------------------------
# Non-interactive commands
# --------------------------------------------------------------------------

def cmd_image(path: str, args: argparse.Namespace) -> int:
    if not os.path.exists(path):
        print(f"No such file or directory: {path}", file=sys.stderr)
        return 1

    if os.path.isdir(path):
        return _convert_directory(path, args)

    width = args.width or (DEFAULT_WIDTH if not sys.stdout.isatty() else _term_width())
    charset = args.charset or "Standard"
    try:
        text, colors = image_to_ascii(
            path, width=width, charset=charset,
            invert=args.invert, half_height=not args.full_height,
        )
    except OSError as exc:
        print(f"Could not read image: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Conversion failed: {exc}", file=sys.stderr)
        return 1

    rows = text.count("\n") + 1
    cols = len(text.splitlines()[0]) if text else 0
    print(f"{os.path.basename(path)}  ->  {cols}x{rows}", file=sys.stderr)

    if args.html:
        if not _write_file(args.html, to_html(text, colors), "HTML"):
            return 1
    if args.save:
        if not _write_file(args.save, text + "\n", "art"):
            return 1

    print(colorize(text, colors) if args.color and colors else text)
    return 0


def _convert_directory(path: str, args: argparse.Namespace) -> int:
    files = sorted(
        f for f in os.listdir(path)
        if os.path.splitext(f)[1].lower() in IMAGE_EXTS
    )
    if not files:
        print(f"No images found in {path}", file=sys.stderr)
        return 1
    width = max(10, args.width) if args.width else DEFAULT_WIDTH
    ok = True
    for name in files:
        full = os.path.join(path, name)
        out = os.path.join(path, os.path.splitext(name)[0] + ".txt")
        try:
            text, _ = image_to_ascii(
                full, width=width, charset=args.charset or "Standard",
                invert=args.invert, half_height=not args.full_height,
            )
            with open(out, "w", encoding="utf-8") as fh:
                fh.write(text + "\n")
            rows = text.count("\n") + 1
            cols = len(text.splitlines()[0]) if text else 0
            print(f"{name}  ->  {os.path.basename(out)}  ({cols}x{rows})")
        except Exception as exc:
            ok = False
            print(f"{name}  FAILED: {exc}", file=sys.stderr)
    return 0 if ok else 1


def cmd_text(args: argparse.Namespace) -> int:
    msg = args.path
    if not msg:
        print('No text provided. Usage: ascii_studio.py text "message"',
              file=sys.stderr)
        return 1
    style = (args.style or "Block").title()
    if style not in TEXT_STYLES:
        print(f"Unknown style '{args.style}'. Choose one of: "
              f"{', '.join(TEXT_STYLES)}", file=sys.stderr)
        return 1
    fill = args.fill or None
    spacing = max(0, args.spacing) if args.spacing is not None else 0
    scale = max(1, args.scale) if args.scale is not None else 1
    shadow = args.shadow or None
    art = render_text(msg, style=style, fill_char=fill, shadow_char=shadow,
                      spacing=spacing, scale=scale)
    colors = text_colors(art.split("\n"), STYLE_PALETTES[style])
    if args.save:
        _write_file(args.save, art + "\n", "art")
    if args.html:
        _write_file(args.html, to_html(art, colors), "HTML")
    print(art)
    return 0


def _write_file(path: str, content: str, what: str) -> bool:
    try:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        print(f"Saved {what} to {path}", file=sys.stderr)
        return True
    except OSError as exc:
        print(f"Could not write file: {exc}", file=sys.stderr)
        return False


def _term_width() -> int:
    return min(max(shutil.get_terminal_size().columns - 2, 30), 120)


# --------------------------------------------------------------------------
# Guided wizard
# --------------------------------------------------------------------------

def _preview_height(px_w: int, px_h: int, width: int, half: bool) -> int:
    h = round(width * px_h / px_w)
    if half:
        h = round(h * 0.5)
    return max(1, h)


def choose_charset() -> str:
    names = list(CHAR_SETS)
    print("  Character set (darkest -> lightest):")
    for i, name in enumerate(names, 1):
        print(f"    {i}. {name:<10}  {CHAR_SETS[name]}")
    val = ask("  Choose (1-{n}, or 'c' for custom)".format(n=len(names)), "1")
    if val.lower() in ("c", "custom"):
        return ask("  Type your ramp", "@%#*+=-:. ")
    try:
        return names[max(0, min(int(val) - 1, len(names) - 1))]
    except ValueError:
        return names[0]


def _pick_image_from_dir(path: str) -> str:
    files = sorted(
        f for f in os.listdir(path)
        if os.path.splitext(f)[1].lower() in IMAGE_EXTS
    )
    if not files:
        print(f"  No images found in {path}", file=sys.stderr)
        return ""
    print(f"  Images in {path}:")
    for i, name in enumerate(files, 1):
        print(f"    {i}. {name}")
    val = ask("  Which one (1-{n})".format(n=len(files)), "1").strip().lower()
    if val == "a":
        print("  Converting all images to .txt...")
        _convert_directory(path, argparse.Namespace(
            width=None, charset=None, invert=False, full_height=False,
        ))
        input("  Done. Press Enter to return to the menu.")
        return ""
    try:
        idx = int(val)
        return os.path.join(path, files[max(0, min(idx - 1, len(files) - 1))])
    except ValueError:
        return os.path.join(path, files[0])


def _post_menu(art: str, colors, default_name: str):
    """Offer reconvert/save/back/quit.  Returns 'again' or 'menu'."""
    while True:
        print("\n  [r] Reconvert   [s] Save .txt   [h] Save .html   "
              "[m] Main menu   [q] Quit")
        val = input("  Choose: ").strip().lower()
        if val in ("r", "reconvert"):
            return "again"
        if val in ("s", "save"):
            name = ask("  Output file", default_name + ".txt")
            if name:
                _write_file(name, art + "\n", "art")
        elif val in ("h", "html"):
            name = ask("  Output HTML file", default_name + ".html")
            if name:
                _write_file(name, to_html(art, colors), "HTML")
        elif val in ("m", "menu"):
            return "menu"
        elif val in ("q", "quit", "exit"):
            raise SystemExit(0)
        else:
            print("  Not a valid choice.")


def guide_image(initial_path: str | None, args: argparse.Namespace) -> None:
    path = initial_path
    while True:
        if path is None:
            path = ask("Drag & drop or type an image path")
        if not path:
            return
        if os.path.isdir(path):
            picked = _pick_image_from_dir(path)
            if not picked:
                return
            path = picked
        if not os.path.exists(path):
            print(f"  Not found: {path}", file=sys.stderr)
            if ask_bool("  Try a different path", default=True):
                path = None
                continue
            return

        try:
            Image, ImageOps = _load_pillow()
            with Image.open(path) as im:
                im = ImageOps.exif_transpose(im)
                px_w, px_h = im.size
        except Exception as exc:
            print(f"  Could not open image: {exc}", file=sys.stderr)
            return

        banner(f"IMAGE MODE — {os.path.basename(path)}  ({px_w} x {px_h} px)")

        cols = shutil.get_terminal_size().columns
        recommended = min(px_w, max(cols - 2, 20))
        h_half = _preview_height(px_w, px_h, recommended, half=True)
        h_full = _preview_height(px_w, px_h, recommended, half=False)
        print("  Terminal is", cols, "columns wide.")
        print(f"  Suggested width: {recommended} characters  "
              f"(1 character = 1 pixel, capped to fit)")
        print(f"    with 2:1 height correction  ->  about {recommended} x {h_half}")
        print(f"    at full resolution          ->  about {recommended} x {h_full}")

        width = args.width if args.width else ask_int("  Output width", recommended)
        charset = args.charset if args.charset else choose_charset()
        invert = args.invert if args.invert else ask_bool(
            "  Invert (light becomes dark)", default=False)
        half = (not args.full_height) if args.full_height else ask_bool(
            "  Use 2:1 height correction (recommended)", default=True)
        color = ask_bool("  Color output in the terminal", default=False)

        try:
            text, colors = image_to_ascii(
                path, width=width, charset=charset, invert=invert,
                half_height=half,
            )
        except Exception as exc:
            print(f"  Conversion failed: {exc}", file=sys.stderr)
            if ask_bool("  Try again", default=True):
                continue
            return

        rows = text.count("\n") + 1
        cols_out = len(text.splitlines()[0]) if text else 0
        print(f"\n  Converted: {cols_out} x {rows} characters\n")
        print(colorize(text, colors) if color else text)

        if _post_menu(text, colors, os.path.splitext(path)[0]) == "again":
            path = initial_path
            continue
        return


def guide_text(args: argparse.Namespace) -> None:
    while True:
        banner("TEXT MODE — big ASCII lettering")
        msg = ask("  Message (e.g. 'Hello World')", args.path)
        if not msg:
            return

        print("\n  Available styles (each uses its own FIGlet symbols):")
        for style in TEXT_STYLES:
            sample = render_text("Hi", style=style)
            for i, ln in enumerate(sample.splitlines()):
                prefix = f"  {style:<7}" if i == 0 else "         "
                print(prefix + "  " + ln)
            print()

        if args.style:
            style = args.style
        else:
            style = ask_choice("  Style", list(TEXT_STYLES), "Block")
        fill = args.fill or ask("  Ink character (blank = font's own)", "")
        spacing = args.spacing if args.spacing is not None else ask_int(
            "  Letter spacing (0-4)", 0)
        scale = args.scale if args.scale is not None else ask_int(
            "  Letter size (1-5)", 1)
        shadow = None
        if style == "Shadow":
            shadow = args.shadow or ask("  Shadow character (blank = font's own)", "")

        art = render_text(msg, style=style, fill_char=fill,
                          shadow_char=shadow, spacing=spacing, scale=scale)
        print("\n" + art)
        colors = text_colors(art.split("\n"), STYLE_PALETTES[style])
        if _post_menu(art, colors, "ascii_art") == "again":
            continue
        return


def guide(args: argparse.Namespace) -> int:
    try:
        while True:
            print("\n")
            print_logo()
            print("\n  What would you like to do?")
            print("    1. Image mode   — turn a photo into ASCII art")
            print("    2. Text mode    — turn a message into big ASCII lettering")
            print("    q. Quit")
            val = input("\n  Choice: ").strip().lower()
            if val in ("q", "quit", "exit"):
                break
            if val in ("1", "image", "img", "i"):
                guide_image(None, args)
            elif val in ("2", "text", "txt", "t"):
                guide_text(args)
            else:
                print("  Not a valid choice.")
    except (EOFError, KeyboardInterrupt):
        pass
    print("\n  Thanks for using ASCII Studio!\n")
    return 0


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ascii_studio",
        description="Turn an image into ASCII art, or render text as big "
                    "ASCII lettering.",
        epilog=(
            "Examples:\n"
            '  python3 ascii_studio.py                    (guided wizard)\n'
            '  python3 ascii_studio.py photo.png\n'
            '  python3 ascii_studio.py photo.png --color --save art.txt\n'
            '  python3 ascii_studio.py images/            (convert a folder)\n'
            '  python3 ascii_studio.py text "Hello 2026" --style Shadow\n'
            '  python3 ascii_studio.py text "Rave" --style Mini --fill @\n'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "target", nargs="?",
        help="'text', 'image', or a path to an image file or folder",
    )
    p.add_argument(
        "path", nargs="?",
        help="image path (after 'image') or the message (after 'text')",
    )
    p.add_argument("-V", "--version", action="version",
                   version=f"%(prog)s {__version__}")

    img = p.add_argument_group("image options")
    img.add_argument("-w", "--width", type=int,
                     help="output width in characters (default: fits your "
                          "terminal)")
    img.add_argument("-c", "--charset", metavar="RAMP",
                     help="preset name (Standard, Short, Simple, Binary, Blocks, "
                          "Faint) or a custom ramp string, e.g. ' .:-=+*#%%@'")
    img.add_argument("-i", "--invert", action="store_true",
                     help="light pixels become dark characters")
    img.add_argument("--full-height", action="store_true",
                     help="use true pixel aspect ratio (no 2:1 correction)")
    img.add_argument("--color", action="store_true",
                     help="print truecolor ANSI art in the terminal")

    out = p.add_argument_group("output options")
    out.add_argument("--save", metavar="FILE", help="also save plain-text art to FILE")
    out.add_argument("--html", metavar="FILE", help="also save a colored HTML version")

    txt = p.add_argument_group("text options")
    txt.add_argument("--style", choices=list(TEXT_STYLES),
                     help="lettering style: " + ", ".join(TEXT_STYLES))
    txt.add_argument("--fill", metavar="CHAR",
                     help="recolor every glyph symbol with CHAR "
                          "(blank keeps the font's own symbols)")
    txt.add_argument("--shadow", metavar="CHAR",
                     help="Shadow style: recolor the echo with CHAR "
                          "(blank keeps the font's own)")
    txt.add_argument("--spacing", type=int, help="extra spaces between letters")
    txt.add_argument("--scale", type=int, help="multiply the size of each letter")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    target = args.target
    tty = sys.stdin.isatty()

    if target is None:
        if not tty:
            print("ASCII Studio — run it interactively, or see --help for "
                  "one-shot commands.", file=sys.stderr)
            return 0
        return guide(args)

    if target.lower() == "text":
        if tty:
            return guide_text(args) or 0
        return cmd_text(args)

    if target.lower() == "image":
        if not args.path:
            print("Usage: ascii_studio.py image <image-file>", file=sys.stderr)
            return 1
        if tty:
            guide_image(args.path, args)
            return 0
        return cmd_image(args.path, args)

    # First positional looks like a path.
    if tty:
        guide_image(target, args)
        return 0
    return cmd_image(target, args)


if __name__ == "__main__":
    raise SystemExit(main())
