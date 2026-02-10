# layout-trainer

A minimal typing-layout training GUI built with Pygame.

Overview
- `main.py`: program entrypoint and scene wiring.
- `ui.py`: lightweight JSON-driven UI system (Scene, Button, Text).
- `layouts/`: various keyboard layout modules (each exports `name`, `layout`, `special_keys`).
- `ui/*.json`: scene definitions used by `ui.Scene`.
- `wordlists/`: sample word lists for training exercises.

Quick start

1. Create a Python virtualenv and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pygame
```

2. Run the app:

```bash
python3 main.py
```

Documentation
- UI layout JSON format: `docs/ui-config.md`.
- Layout modules: `layouts/*.py` — each exposes a `layout` list and a `name`.

License
- This repository does not include a license file. Use at your own discretion.
