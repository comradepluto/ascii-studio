# ASCII Studio

Turn a photo into ASCII art, or render a message as big ASCII lettering,
right in your terminal. Run it as a guided wizard, or fire off quick
one-shot commands.

```
   _____     __________________  .___ .___
  /  _  \   /   _____/\_   ___ \ |   ||   |
 /  /_\  \  \_____  \ /    \  \/ |   ||   |
/    |    \ /        \\     \____|   ||   |
\____|__  //_______  / \______  /|___||___|
  ____________________ ____ ___ ________   .___ ________
 /   _____/\__    ___/|    |   \\______ \  |   |\_____  \
 \_____  \   |    |   |    |   / |    |  \ |   | /   |   \
 /        \  |    |   |    |  /  |    `   \|   |/    |    \
/_______  /  |____|   |______/  /_______  /|___|\_______  /
             v2.3.0  ·  terminal ascii art
```

## Features

- Interactive wizard for guided use, plus one-shot commands
- Photo to ASCII art as plain text, truecolor ANSI, or colored HTML
- Seven lettering styles, each with a real FIGlet font and its own symbols
- Letter spacing, scaling, custom fill/shadow characters
- Works with or without `pyfiglet` installed (fonts are bundled)
- Python 3.9+, no heavy dependencies

## Installation

Full step-by-step instructions, including per-distro package commands, live
in [INSTALL.md](INSTALL.md). The short version:

### Linux (easy)

```sh
git clone https://github.com/YOUR_USERNAME/ascii-studio.git
cd ascii-studio
./install.sh
```

The installer detects your distro, installs `Pillow`, `colorama`, and
`pyfiglet` through your package manager, and falls back to pip. Force pip
with `./install.sh --pip`.

### Any OS, with pip

```sh
git clone https://github.com/YOUR_USERNAME/ascii-studio.git
cd ascii-studio
python3 -m pip install --user -r requirements.txt
```

### Directly from GitHub

```sh
python3 -m pip install --user git+https://github.com/YOUR_USERNAME/ascii-studio.git
```

## Quick start

```sh
python3 ascii_studio.py                    # guided wizard
python3 ascii_studio.py photo.png          # convert an image
python3 ascii_studio.py photo.png --color  # truecolor ANSI art
python3 ascii_studio.py images/            # convert every image in a folder
python3 ascii_studio.py text "Hello"       # big ASCII lettering
python3 ascii_studio.py text "Rave" --style Shadow --fill @
```

Sanity check:

```sh
python3 ascii_studio.py --version
python3 ascii_studio.py text "Hi there" --style Block
```

## Options

| Option | Description |
| --- | --- |
| `target` | `text`, `image`, or a path to an image file or folder |
| `path` | the message (after `text`) or image path (after `image`) |
| `-w, --width WIDTH` | output width in characters (default: fits your terminal) |
| `-c, --charset RAMP` | preset name or a custom ramp like `' .:-=+*#%@'` |
| `-i, --invert` | light pixels become dark characters |
| `--full-height` | use true pixel aspect ratio (no 2:1 correction) |
| `--color` | print truecolor ANSI art in the terminal |
| `--save FILE` | also save plain-text art to FILE |
| `--html FILE` | also save a colored HTML version |
| `--style NAME` | lettering style: Block, Shadow, Mini, Slant, Bold, Bubble, Framed |
| `--fill CHAR` | recolor every glyph symbol with CHAR |
| `--shadow CHAR` | Shadow style: recolor the echo with CHAR |
| `--spacing N` | extra spaces between letters |
| `--scale N` | multiply the size of each letter |
| `-V, --version` | show the version |

Run `python3 ascii_studio.py --help` for full examples.

## Project layout

```
ascii_studio.py    the whole application (CLI, wizard, rendering)
figlet_fonts.py    bundled FIGlet font data used when pyfiglet is missing
install.sh         distro-aware dependency installer (Linux)
INSTALL.md         step-by-step installation guide
requirements.txt   Python dependencies (Pillow, colorama, pyfiglet)
```

## Notes

- `pyfiglet` is the lettering engine. If it is not installed, ASCII Studio
  falls back to the fonts bundled in `figlet_fonts.py`, so text still works.
- `colorama` is only needed on Windows for colored terminal output.
- Text lettering works without `Pillow`; it is only required for images.

## License

Pick a license (for example MIT) and add a `LICENSE` file, or leave this
section out if the project is for personal use.
