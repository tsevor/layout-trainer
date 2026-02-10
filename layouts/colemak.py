"""Colemak layout definition used by the trainer.

See `layouts/qwerty.py` for format details. Provide `name`,
`layout` and optional `special_keys` variables.
"""

name = "Colemak"

layout = [
	"qwfpgjluy;[]\\",
	"arstdhneio'",
	"zxcvbkm,./"
]

special_keys = {
	"caps": "backspace"
}

layout_shift = [
	"QWFPGJLUY:{}|",
	"ARSTDHNEIO\"",
	"ZXCVBKM<>?"
]