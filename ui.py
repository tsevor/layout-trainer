"""UI helpers: lightweight JSON-driven scene and element system.

This module provides a minimal UI layer used by `main.py`. The
layout format is JSON (see `ui/main-menu.json` and
`ui/settings.json`) and maps element ids to element definitions.

Provided classes:
- `Scene(layout_path)`: loads a JSON layout and manages drawing and
	click dispatch for its elements.
- `Element`, `Text`, `Button`: basic drawable/clickable elements.

The module keeps a small font cache to avoid re-creating Pygame
fonts repeatedly.

JSON element schema (example fields):
{
	"type": "button" | "text",
	"text": "Label",
	"pos": [x, y],
	"size": 14,
	"font": "Arial",
	"color": "#RRGGBB",
	"bg_color": "#RRGGBB"
}
"""

import json
import pygame

pygame.font.init()

fonts = {}

# base resolution used by layouts (matches main.py initial WIDTH/HEIGHT)
BASE_WIDTH = 800
BASE_HEIGHT = 600
SCALE_X = 1.0
SCALE_Y = 1.0
SCALE_MIN = 1.0
# bump this counter whenever draw size changes; each Scene keeps
# a last-seen version so all scenes re-render when version differs.
SCALE_VERSION = 0

def set_base_resolution(w, h):
	global BASE_WIDTH, BASE_HEIGHT
	BASE_WIDTH = w
	BASE_HEIGHT = h

def set_draw_size(w, h):
	"""Set the current drawing surface size and mark scale dirty so
	Scenes re-render elements with the new scaled sizes/positions.
	"""
	global SCALE_X, SCALE_Y, SCALE_MIN, _scale_dirty
	try:
		SCALE_X = float(w) / float(BASE_WIDTH)
		SCALE_Y = float(h) / float(BASE_HEIGHT)
	except Exception:
		SCALE_X = SCALE_Y = 1.0
	SCALE_MIN = min(max(SCALE_X, 0.01), max(SCALE_Y, 0.01))
	# bump global version so all scenes know to re-render
	global SCALE_VERSION
	SCALE_VERSION += 1

def _current_scale_version():
	return SCALE_VERSION

def parse_color(color):
	if isinstance(color, str):
		color = color.lstrip('#')
		return tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
	return tuple(color)

class Element:
	def __init__(self, id, data):
		self.id = id
		self.data = data
		self.bounds = None
		self.click_callback = None
		self.orig_pos = data.get("pos", [0, 0])

	def click_at(self, pos):
		if self.bounds and self.bounds.collidepoint(pos):
			if self.click_callback:
				self.click_callback(self)
			return True
		return False

class Text(Element):
	def __init__(self, id, data):
		super().__init__(id, data)
		self.text = data["text"]
		self.font_name = data.get("font", "Arial")
		self.orig_font_size = data.get("size", 12)
		self.font_key = f"{self.font_name}_{self.orig_font_size}"
		self.color = parse_color(data.get("color", (255, 255, 255)))
		self.pos = self.orig_pos
		self.font = None
		self.render()
	
	def change_text(self, new_text):
		self.text = new_text
		self.render()
	
	def render(self):
		# compute scaled font size and position
		size = max(8, int(self.orig_font_size * SCALE_MIN))
		font_key = f"{self.font_name}_{size}"
		if font_key not in fonts:
			fonts[font_key] = pygame.font.SysFont(self.font_name, size)
		self.font = fonts[font_key]
		self.rendered_text = self.font.render(self.text, True, self.color)
		pos = (int(self.orig_pos[0] * SCALE_X), int(self.orig_pos[1] * SCALE_Y))
		self.bounds = self.rendered_text.get_rect(topleft=pos)

	def draw(self, surface):
		surface.blit(self.rendered_text, self.bounds)

class Button(Element):
	def __init__(self, id, data):
		super().__init__(id, data)
		self.text = data["text"]
		self.font_name = data.get("font", "Arial")
		self.orig_font_size = data.get("size", 12)
		self.font = None
		self.color = parse_color(data.get("color", (255, 255, 255)))
		self.bg_color = parse_color(data.get("bg_color", (100, 100, 100)))
		self.border_color = parse_color(data.get("border_color", (150, 150, 150)))
		self.border_width = data.get("border_width", 1)
		self.border_radius = data.get("border_radius", 8)
		self.centered = data.get("centered", False)
		self.pos = self.orig_pos
		self.orig_padding = data.get("padding", 10)
		self.orig_border_radius = self.border_radius
		self.orig_border_width = self.border_width
		self.render()
	
	def change_text(self, new_text):
		self.text = new_text
		self.render()
	
	def render(self):
		# compute scaled font size, padding and border
		size = max(8, int(self.orig_font_size * SCALE_MIN))
		font_key = f"{self.font_name}_{size}"
		if font_key not in fonts:
			fonts[font_key] = pygame.font.SysFont(self.font_name, size)
		self.font = fonts[font_key]
		text_surface = self.font.render(self.text, True, self.color)
		padding = int(self.orig_padding * SCALE_MIN)
		w = text_surface.get_width() + padding * 2
		h = text_surface.get_height() + padding * 2
		px = int(self.orig_pos[0] * SCALE_X)
		py = int(self.orig_pos[1] * SCALE_Y)
		if self.centered:
			self.bounds = pygame.Rect(px - w // 2, py - h // 2, w, h)
		else:
			self.bounds = pygame.Rect(px, py, w, h)
		self.text_surface = text_surface
		if self.centered:
			self.text_pos = (px - w // 2 + padding, py - h // 2 + padding)
		else:
			self.text_pos = (px + padding, py + padding)
	
	def draw(self, surface):
		pygame.draw.rect(surface, self.bg_color, self.bounds, border_radius=self.border_radius)
		pygame.draw.rect(surface, self.border_color, self.bounds, self.border_width, border_radius=self.border_radius)
		surface.blit(self.text_surface, self.text_pos)


class KeyboardOverlay(Element):
	def __init__(self, id, data):
		super().__init__(id, data)
		import importlib
		self.data = data
		self.rowsShown = data.get("rows_shown", [0, 1, 2])  # default to showing all rows
		self.hideLabels = False
		self.layout_name = data.get("layout", "qwerty")
		self.orig_pos = data.get("pos", [20, 200])
		self.orig_key_width = data.get("key_width", 48)
		self.orig_key_height = data.get("key_height", 48)
		self.orig_spacing = data.get("spacing", 6)
		self.orig_font_size = data.get("font_size", 18)
		self.font = None
		self.highlight = set(data.get("highlight", []))
		self.key_handler = None
		self.char_to_keycode = {}
		self._load_layout(importlib)

	def _load_layout(self, importlib_module):
		try:
			mod = importlib_module.import_module(f"layouts.{self.layout_name}")
			rows = getattr(mod, "layout", [])
			self.shift_rows = getattr(mod, "layout_shift", None)
		except Exception:
			rows = []
		self.rows = rows
		self._render_keys()

	def render(self):
		# re-generate key rects using current scale
		self._render_keys()

	def _render_keys(self):
		# store keys with their row/col positions so we can lookup shifted
		# labels at draw time when Shift is held
		self.keys = []
		x0 = int(self.orig_pos[0] * SCALE_X)
		y0 = int(self.orig_pos[1] * SCALE_Y)
		key_w = int(self.orig_key_width * SCALE_MIN)
		key_h = int(self.orig_key_height * SCALE_MIN)
		spacing = int(self.orig_spacing * SCALE_MIN)
		y = y0
		for row_idx, row in enumerate(self.rows):
			x = x0 + int(row_idx * (self.orig_key_width * SCALE_MIN) / 2)
			for col_idx, ch in enumerate(row):
				rect = pygame.Rect(x, y, key_w, key_h)
				self.keys.append((ch, rect, row_idx, col_idx))
				x += key_w + spacing
			y += key_h + spacing

		# render spacebar (store with sentinel row/col)
		rect = pygame.Rect(x0 + int(self.orig_key_width * 4 * SCALE_MIN), y, key_w * 5, key_h)
		self.keys.append((" ", rect, -1, -1))

	def set_key_handler(self, handler):
		"""Attach an input handler instance for live pressed-key highlighting.

		The handler is expected to be an instance of `inputHandling.keyCodeHandler`.
		We build a reverse map from characters to pygame keycodes to efficiently
		check pressed state in `draw()`.
		"""
		self.key_handler = handler
		self.char_to_keycode = {}
		if handler is None:
			return
		for k, v in handler.keycode_to_char.items():
			# store both the exact and lowercase character for lookups
			self.char_to_keycode[v] = k
			self.char_to_keycode.setdefault(v.lower(), k)
		# also build reverse mapping for shifted characters if present
		if hasattr(self, 'shift_rows') and self.shift_rows:
			for r_idx, row in enumerate(self.shift_rows):
				for c_idx, ch in enumerate(row):
					# map shifted char to same keycode as the base char at that position
					try:
						base = self.rows[r_idx][c_idx]
					except Exception:
						base = None
					if base is not None:
						kc = self.char_to_keycode.get(base) or self.char_to_keycode.get(base.lower())
						if kc:
							self.char_to_keycode[ch] = kc
							self.char_to_keycode.setdefault(ch.lower(), kc)

	def set_layout(self, layout_name):
		import importlib
		self.layout_name = layout_name
		self._load_layout(importlib)

	def draw(self, surface):
		# determine if Shift is held via the key handler
		shift_held = False
		if self.key_handler:
			try:
				l = pygame.K_LSHIFT
				r = pygame.K_RSHIFT
				if 0 <= l < len(self.key_handler.keycodes) and self.key_handler.keycodes[l]:
					shift_held = True
				if 0 <= r < len(self.key_handler.keycodes) and self.key_handler.keycodes[r]:
					shift_held = True
			except Exception:
				shift_held = False

		for base_ch, rect, row_idx, col_idx in self.keys:
			# choose label: shifted if shift held and mapping available
			if row_idx in self.rowsShown and not self.hideLabels:
				label = base_ch
			else :
				label = ""
			
			if shift_held and hasattr(self, 'shift_rows') and self.shift_rows:
				if 0 <= row_idx < len(self.shift_rows):
					row = self.shift_rows[row_idx]
					if 0 <= col_idx < len(row):
						label = row[col_idx]
			
				

			# detect pressed state via the base (unshifted) character
			pressed = False
			if self.key_handler:
				keycode = self.char_to_keycode.get(base_ch) or self.char_to_keycode.get(base_ch.lower())
				if keycode is None:
					try:
						keycode = pygame.key.key_code(base_ch)
					except Exception:
						keycode = None
				if keycode is not None and 0 <= keycode < len(self.key_handler.keycodes):
					pressed = bool(self.key_handler.keycodes[keycode])
			#------------------------------------------------------------------------------- set color ----------------
			
			color = (200, 100, 60) if (pressed or base_ch.lower() in self.highlight) else (80, 80, 120)
			if (row_idx == 1 and (col_idx == 3 or col_idx == 6) and not (pressed or base_ch.lower() in self.highlight)):
				color =  (103, 103, 163)

			pygame.draw.rect(surface, color, rect, border_radius=max(1, int(6 * SCALE_MIN)))
			pygame.draw.rect(surface, (120, 120, 160), rect, max(1, int(2 * SCALE_MIN)), border_radius=max(1, int(6 * SCALE_MIN)))
			# render label fresh so shifted labels show when Shift is pressed
			font_size = max(8, int(self.orig_font_size * SCALE_MIN))
			font_key = f"kbd_{font_size}"
			if font_key not in fonts:
				fonts[font_key] = pygame.font.SysFont(None, font_size)
			self.font = fonts[font_key]
			surf = self.font.render(label, True, (255, 255, 255))
			text_pos = surf.get_rect(center=rect.center)
			surface.blit(surf, text_pos)

#copy of text goal is to have a cursor and a incorrect and correct font color per character might need multiple surfaces to acheive that result
#needs to be able to get the keys and be able to check. also needs to be able to switch modes between burst type and 
class Text_box(Element):
	def __init__(self, id, data):
		super().__init__(id, data)
		import importlib
		self.text = data["text"]
		self.font_name = data.get("font", "Arial")
		self.orig_font_size = data.get("size", 12)
		self.layout_name = data.get("layout_name", "qwerty")
		self.rounds = data.get("rounds", 3) - 1 
		self.level_over_callback = None
		
		# defer font creation until render with scaled size
		self.font = None
		self.color = parse_color(data.get("color", (255, 255, 255)))
		self.pos = self.orig_pos

		self.current_rows = data.get("difficulty")
	
	def change_text(self, new_text):
		self.text = new_text
		self.render()
	
	def update_text(self, key): 
		if key == self.text[0]: 
			self.change_text(self.text[1:])
		if self.text == '':
			if self.rounds == 0 and self.level_over_callback: 
				self.level_over_callback()
				return
			self.generate_words(self.layout_name, self.current_rows)
			self.rounds -= 1
				
	#load layout
	def _load_layout(self, importlib_module):
		try:
			mod = importlib_module.import_module(f"layouts.{self.layout_name}")
			
			self.shift_rows = getattr(mod, "layout_shift", None)
		except Exception:
			print(" loading layout failed")
				
	def set_layout(self, layout_name):
		import importlib
		self.layout_name = layout_name
		self._load_layout(importlib)

	def render(self):
		size = max(8, int(self.orig_font_size * SCALE_MIN))
		font_key = f"{self.font_name}_{size}"
		if font_key not in fonts:
			fonts[font_key] = pygame.font.SysFont(self.font_name, size)
		self.font = fonts[font_key]
		self.rendered_text = self.font.render(self.text, True, self.color)
		pos = (int(self.orig_pos[0] * SCALE_X), int(self.orig_pos[1] * SCALE_Y))
		self.bounds = self.rendered_text.get_rect(topleft=pos)

	def draw(self, surface):
		surface.blit(self.rendered_text, self.bounds)

	def generate_words(self, layout, rows):
		import word_generator
		words_object = word_generator.Wordlist(layout,rows)
		sentence = ""
		for word in words_object.random(10):
			sentence += word + " "
		
		sentence = sentence[:len(sentence)-1] # deletes trailing space
		self.change_text(sentence)

	def start_level(self, layout, level_over_callback=None):
		self.layout_name = layout
		self.level_over_callback = level_over_callback
		self.generate_words(self.layout_name, self.current_rows)

class Scene:
	def __init__(self, layout_path):
		with open(layout_path) as f:
			self.layout = json.load(f)
		self.elements = []
		self._last_scale_version = -1
		for el_id, el_data in self.layout.items():
			if el_data["type"] == "text":
				self.elements.append(Text(el_id, el_data))
			elif el_data["type"] == "button":
				self.elements.append(Button(el_id, el_data))
			elif el_data["type"] == "keyboard_overlay":
				self.elements.append(KeyboardOverlay(el_id, el_data))
			elif el_data["type"] == "text_box":
				self.elements.append(Text_box(el_id, el_data))
	
	def draw(self, surface):
		# if global scale version changed since this scene last rendered,
		# re-render all elements so they pick up new scaled sizes/positions.
		cur = _current_scale_version()
		if self._last_scale_version != cur:
			for el in self.elements:
				try:
					el.render()
				except Exception:
					pass
			self._last_scale_version = cur

		for el in self.elements:
			el.draw(surface)
	
	def click(self, pos):
		# check in reverse order (topmost element first)
		for el in reversed(self.elements):
			if el.click_at(pos):
				return el.id
		return None
	
	def on_click(self, element_id, callback):
		for el in self.elements:
			if el.id == element_id:
				el.click_callback = callback
				break
	
	def get_element(self, element_id):
		for el in self.elements:
			if el.id == element_id:
				return el
		return None
	
