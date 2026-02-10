"""Workman layout definition used by the trainer.

See `layouts/qwerty.py` for format details. Provide `name`,
`layout` and optional `special_keys` variables.
"""

name = "Workman"

layout = [
	"`1234567890-=",
	"qdrwbjfup;[]\\",
	"ashtgneio'",
	"zxcvkm,./"
]

special_keys = {
	"caps": "backspace"
}