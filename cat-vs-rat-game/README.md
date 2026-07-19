# Cat vs Rat Game

A simple pygame game where a cat chases a rat across the screen. The objective is to collide with the rat to increase the score.

## Requirements

- Python 3.11+
- uv

## Setup

From the project directory, create and activate a virtual environment:

```bash
cd /Users/simonmandy/Desktop/vscode/python_work-branch/cat-vs-rat-game
uv venv
source .venv/bin/activate
```

Install dependencies:

```bash
uv sync
```

## Run the game

Run the game directly with Python:

```bash
python src/game.py
```

Or with uv:

```bash
uv run python src/game.py
```

## Unit tests

```bash
pytest
```

## Build a macOS app bundle

To build a standalone macOS application bundle:

```bash
uv run pyinstaller --clean --windowed --name cat-vs-rat-game src/game.py
```

To build a standalone Windows executable:

```bash
uv run pyinstaller --clean --onefile --windowed --name cat-vs-rat-game src/game.py
```

The output will be created in:

```bash
dist/cat-vs-rat-game.app
dist/cat-vs-rat-game.app.exe
```

You can launch it with:

```bash
open dist/cat-vs-rat-game.app
launch dist/cat-vs-rat-game.app.exe
```

## Controls

- Arrow keys: move the cat

## Notes

- The app bundle is intended for macOS GUI use and should launch without opening a Terminal window.
- If you want to build again from scratch, remove previous build output first:

```bash
rm -rf dist build *.spec
```
