"""QWERTY layout definition used by the trainer.

Each layout module exposes these top-level variables:
- `name` (str): human-readable layout name
- `layout` (list[str]): rows of keys from top to bottom
- `special_keys` (dict): optional mapping for special-key names

The `layout` rows are simple strings where each character
represents a physical key. Escape sequences like `\\` are used
for backslash characters.
"""

name = "QWERTY"

layout = [
	"`1234567890-=",
	"qwertyuiop[]\\",
	"asdfghjkl;'",
	"zxcvbnm,./"
]

special_keys = {}  # no changes, default