"""Colemak layout definition used by the trainer.

See `layouts/qwerty.py` for format details. Provide `name`,
`layout` and optional `special_keys` variables.
"""

name = "Colemak"

layout = [
	"`1234567890-=",
	"qwfpgjluy;[]\\",
	"arstdhneio'",
	"zxcvbkm,./"
]

special_keys = {
	"caps": "backspace"
}