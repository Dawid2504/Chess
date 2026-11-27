# Plan for cleaning and improving the Chess project

## Overview
The project consists of three main modules:
- `main.py` – game loop and UI rendering
- `figuren.py` – creation of piece graphics
- `engine.py` – chess engine implementation

The goal is to bring the codebase up to modern Python standards, improve readability, enforce consistent naming, add type hints and docstrings, and extract shared constants to a dedicated module.

## Steps
1. **Create `constants.py`** (already created) with geometry, colors, piece values and start counts.
2. **Update imports** in `main.py` to import values from `constants` instead of defining them locally.
3. **Remove duplicate color definitions** in `constants.py` (there were many repeated `FARBE_TEXT_GEDIMMT`).
4. **Add type hints and docstrings** to public functions in all modules.
5. **Rename German identifiers** to English where feasible while keeping the public API unchanged (e.g., `FELD_GROESSE` → `SQUARE_SIZE`).
6. **Add `if __name__ == "__main__":` guard** to `main.py`.
7. **Run a quick lint check** (via `python -m pycodestyle .`).
8. **Commit changes** and verify that the project still runs.

## Expected Outcome
- Consistent constant definitions in a single place.
- Cleaner, PEP‑8 compliant code with proper documentation.
- Easier future maintenance and potential feature extensions.
