"""Input handling helpers for the layout trainer.

This module provides a small utility class to track keyboard state
and map Pygame keycodes to characters for the currently selected
keyboard layout (see the `layouts/` modules). The implementation
maintains a boolean array of pressed keys and a mapping from
Pygame key constants to the corresponding character for the
active layout.

Usage:
    handler = keyCodeHandler({"layout": "qwerty"})
    # in the main loop: on KEYDOWN -> handler.handle_keydown(event)
    # on KEYUP -> handler.handle_keyup(event)
    # query pressed keys via handler.keycodes or translate via
    # handler.keycode_to_char
"""

import pygame


class keyCodeHandler:
    """Track pressed keys and map keycodes to layout characters.

    Attributes:
        data (dict): configuration (expects optional "layout" key).
        layout_name (str): active layout module name.
        keycodes (list[bool]): boolean array indexed by pygame key constant.
        keycode_to_char (dict[int, str]): mapping from pygame key constants
            to the corresponding character in the active layout.
    """

    def __init__(self, data):
        """Create a handler for the specified layout.

        Args:
            data: dict-like config; uses `data.get("layout")`.
        """
        self.data = data
        self.layout_name = data.get("layout", "qwerty")
        # Use a fixed-size list to track pressed state for common keycodes.
        # Indexing beyond the list length will raise; 512 is a conservative
        # upper bound for typical pygame key constants.
        self.keycodes = [False] * 512
        self.keycode_to_char = {}
        self._load_layout()

    def _load_layout(self, layout_name=None):
        """Load the layout module and build the keycode->char map.

        The layout modules expose `layout` as a list of strings (rows).
        We iterate characters and use `pygame.key.key_code()` to map a
        character to a pygame key constant. If mapping fails for a
        particular character, it is skipped.
        """
        import importlib
        if layout_name is None:
            layout_name = self.layout_name
        try:
            mod = importlib.import_module(f"layouts.{layout_name}")
            rows = getattr(mod, "layout", [])
        except Exception:
            rows = []

        for row in rows:
            for ch in row:
                try:
                    keycode = pygame.key.key_code(ch)
                except Exception:
                    # some layout characters may not map directly to a
                    # pygame key constant (e.g. unusual symbols); skip them
                    continue
                if keycode < len(self.keycodes):
                    # record mapping from keycode -> character but do not
                    # mark the key as pressed; pressed state is managed
                    # by handle_keydown/handle_keyup and should be False
                    # by default.
                    self.keycode_to_char[keycode] = ch

        self._update_keymap()

    def set_layout(self, layout_name):
        """Public setter to change the active layout and rebuild mappings.

        Args:
            layout_name: layout module name (e.g., 'qwerty').
        """
        self.layout_name = layout_name
        # clear previous mappings
        self.keycode_to_char.clear()
        self.keycodes = [False] * len(self.keycodes)
        self._load_layout(layout_name)

    def _get_flat_layout(self, layout_name):
        """Return a flat list of characters for the given layout module.

        The returned list preserves row-major ordering used by the
        layout modules. If the module can't be imported, an empty list
        is returned.
        """
        import importlib
        try:
            mod = importlib.import_module(f"layouts.{layout_name}")
            rows = getattr(mod, "layout", [])
        except Exception:
            return []
        flat = []
        for row in rows:
            for ch in row:
                flat.append(ch)
        # include a space key at the end if layouts don't include it
        flat.append(' ')
        return flat

    def translate_layout(self, new_layout, from_layout=None):
        """Translate key mappings from one layout to another.

        This attempts to preserve physical key positions: a character
        in `from_layout` at position i will be mapped to the character
        at position i in `new_layout`. The function updates
        `keycode_to_char` so that existing pygame keycodes continue to
        refer to the corresponding character in the new layout.

        Args:
            new_layout: target layout module name.
            from_layout: optional source layout module name. If omitted
                `self.layout_name` is used.
        """
        if from_layout is None:
            from_layout = self.layout_name

        from_flat = self._get_flat_layout(from_layout)
        to_flat = self._get_flat_layout(new_layout)
        if not from_flat or not to_flat:
            # fallback to simple set_layout if layouts unavailable
            self.set_layout(new_layout)
            return

        # build char->index map for the source layout
        index_map = {}
        for i, ch in enumerate(from_flat):
            if ch not in index_map:
                index_map[ch] = i

        new_keycode_to_char = {}

        # For each known keycode in the current mapping, translate
        # the character based on its position in the source layout.
        for keycode, ch in list(self.keycode_to_char.items()):
            idx = index_map.get(ch)
            if idx is None or idx >= len(to_flat):
                # if we can't translate, keep the original char
                new_char = ch
            else:
                new_char = to_flat[idx]
            new_keycode_to_char[keycode] = new_char

        # replace mapping and update layout name
        self.keycode_to_char = new_keycode_to_char
        self.layout_name = new_layout

        # update any other derived state
        self._update_keymap()

    def handle_keydown(self, event):
        """Mark a key as pressed.

        Intended to be called with a Pygame `KEYDOWN` event.
        """
        if 0 <= event.key < len(self.keycodes):
            self.keycodes[event.key] = True

    def handle_keyup(self, event):
        """Mark a key as released.

        Intended to be called with a Pygame `KEYUP` event.
        """
        if 0 <= event.key < len(self.keycodes):
            self.keycodes[event.key] = False

    def _update_keymap(self):
        """Hook for additional state updates after loading a layout.

        This method is intentionally a no-op by default but can be
        extended to compute derived state such as home-row sets,
        shift mappings, or visual highlighting rules.
        """
        pass