# ASCII Studio

ASCII Studio turns a photo into ASCII art, or renders a message as big
ASCII lettering. You can run it as a guided wizard, or fire off quick
one-shot commands.

## What you need

- Python 3.9 or newer
- [Pillow](https://pypi.org/project/Pillow/) (for image conversion)
- [colorama](https://pypi.org/project/colorama/) (helps colored output on Windows)
- [pyfiglet](https://pypi.org/project/pyfiglet/) (for text lettering)

Pillow and pyfiglet are the two that matter. pyfiglet is the engine behind
the big lettering and the logo; without it, ASCII Studio falls back to the
font data bundled inside the project, so text still works either way.
colorama is only really needed on Windows so that colored terminal output
shows up correctly there. If you never plan to convert images, you can even
skip Pillow entirely, the text lettering works without it.

## The easy way (Linux)

There is a little installer script bundled with the project. It figures out
which distro you are running, installs everything through your package
manager, and falls back to pip if that does not work out:

```sh
./install.sh
```

Want to skip the package manager and just use pip? You can force it:

```sh
./install.sh --pip
```

## Doing it by hand, per distro

Prefer to install manually? These are the commands for each distro.

### Arch / Manjaro / EndeavourOS / Garuda
```sh
sudo pacman -S python-pillow python-colorama python-pyfiglet
```

### Debian / Ubuntu / Mint / Pop!_OS / elementary / Kali / Raspberry Pi OS
```sh
sudo apt-get update
sudo apt-get install python3-pil python3-colorama python3-pyfiglet
```

### Fedora / RHEL / CentOS / Rocky / AlmaLinux
```sh
sudo dnf install python3-pillow python3-colorama python3-pyfiglet
```

### openSUSE
```sh
sudo zypper install python3-Pillow python3-colorama python3-pyfiglet
```

### macOS
```sh
brew install python-pillow python-colorama
pip3 install pyfiglet
```

### Windows
```sh
py -m pip install -r requirements.txt
```

### No package manager handy? (any OS)
```sh
python3 -m pip install --user -r requirements.txt
```

## Quick sanity check

Run these two commands. If both print something nice, you are ready to go:

```sh
python3 ascii_studio.py --version
python3 ascii_studio.py text "Hi there" --style Block
```

## What you can do with it

```sh
python3 ascii_studio.py                 # guided wizard
python3 ascii_studio.py photo.png       # convert an image
python3 ascii_studio.py photo.png --color --save art.txt
python3 ascii_studio.py images/         # convert every image in a folder
python3 ascii_studio.py text "Hello"    # big ASCII lettering
python3 ascii_studio.py text "Hello" --style Shadow --fill # --scale 2
```

Seven lettering styles to pick from: `Block`, `Shadow`, `Mini`, `Slant`,
`Bold`, `Bubble`, and `Framed`. Every style uses a real FIGlet font with its
own symbols, so each one has a distinct look out of the box.

`python3 ascii_studio.py --help` lists every option if you want to dig in.
