from .colemak import layout as colemak
from .dvorak  import layout as dvorak
from .qwerty  import layout as qwerty
from .workman import layout as workman



def convert(key, original_layout, target_layout):
	if key in target_layout.special.keys():
		return target_layout.special[key]
	for i, row in enumerate(original_layout):
		for j, orig_key in enumerate(row):
			if orig_key == key:
				return target_layout[i][j]
	return key