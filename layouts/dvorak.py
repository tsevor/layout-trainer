"""Dvorak layout definition used by the trainer.

See `layouts/qwerty.py` for format details. This module provides
the same top-level variables: `name`, `layout`, and `special_keys`.
"""

name = "Dvorak"

layout = [
	"',.pyfgcrl/=",
	"aoeuidhtns-",
	";qjkxbmwvz"
]

special_keys = {
	"caps": "backspace"
}

layout_shift = [
	"\"<>PYFGCRL?+",
	"AOEUIDHTNS_",
	":QJKXBMWVZ"
]