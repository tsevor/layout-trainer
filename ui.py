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
		self.font_size = data.get("size", 12)
		self.font_key = f"{self.font_name}_{self.font_size}"
		if self.font_key not in fonts:
			fonts[self.font_key] = pygame.font.SysFont(self.font_name, self.font_size)
		self.font = fonts[self.font_key]
		self.color = parse_color(data.get("color", (255, 255, 255)))
		self.pos = data.get("pos", [0, 0])
		
		self.render()
	
	def change_text(self, new_text):
		self.text = new_text
		self.render()
	
	def render(self):
		self.rendered_text = self.font.render(self.text, True, self.color)
		self.bounds = self.rendered_text.get_rect(topleft=self.pos)

	def draw(self, surface):
		surface.blit(self.rendered_text, self.bounds)

class Button(Element):
	def __init__(self, id, data):
		super().__init__(id, data)
		self.text = data["text"]
		self.font_name = data.get("font", "Arial")
		self.font_size = data.get("size", 12)
		self.font_key = f"{self.font_name}_{self.font_size}"
		if self.font_key not in fonts:
			fonts[self.font_key] = pygame.font.SysFont(self.font_name, self.font_size)
		self.font = fonts[self.font_key]
		self.color = parse_color(data.get("color", (255, 255, 255)))
		self.bg_color = parse_color(data.get("bg_color", (100, 100, 100)))
		self.border_color = parse_color(data.get("border_color", (150, 150, 150)))
		self.border_width = data.get("border_width", 1)
		self.border_radius = data.get("border_radius", 8)
		self.centered = data.get("centered", False)
		self.pos = data.get("pos", [0, 0])
		
		self.padding = data.get("padding", 10)
		
		
		self.render()
	
	def change_text(self, new_text):
		self.text = new_text
		self.render()
	
	def render(self):
		text_surface = self.font.render(self.text, True, self.color)
		w = text_surface.get_width() + self.padding * 2
		h = text_surface.get_height() + self.padding * 2
		if self.centered:
			self.bounds = pygame.Rect(self.pos[0] - w/2, self.pos[1] - h/2, w, h)
		else:
			self.bounds = pygame.Rect(self.pos[0], self.pos[1], w, h)
		self.text_surface = text_surface
		if self.centered:
			self.text_pos = (self.pos[0] - w/2 + self.padding, self.pos[1] - h/2 + self.padding)
		else:
			self.text_pos = (self.pos[0] + self.padding, self.pos[1] + self.padding)
	
	def draw(self, surface):
		pygame.draw.rect(surface, self.bg_color, self.bounds, border_radius=self.border_radius)
		pygame.draw.rect(surface, self.border_color, self.bounds, self.border_width, border_radius=self.border_radius)
		surface.blit(self.text_surface, self.text_pos)


class KeyboardOverlay(Element):
	def __init__(self, id, data):
		super().__init__(id, data)
		import importlib
		self.data = data
		self.rowsShown = [1]  # default to showing all rows
		self.hideLabels = False
		self.layout_name = data.get("layout", "qwerty")
		self.pos = data.get("pos", [20, 200])
		self.key_width = data.get("key_width", 48)
		self.key_height = data.get("key_height", 48)
		self.spacing = data.get("spacing", 6)
		self.font_size = data.get("font_size", 18)
		self.font_key = f"kbd_{self.font_size}"
		if self.font_key not in fonts:
			fonts[self.font_key] = pygame.font.SysFont(None, self.font_size)
		self.font = fonts[self.font_key]
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

	def _render_keys(self):
		# store keys with their row/col positions so we can lookup shifted
		# labels at draw time when Shift is held
		self.keys = []
		x0, y0 = self.pos
		y = y0
		for row_idx, row in enumerate(self.rows):
			x = x0 + (row_idx * self.key_width / 2)
			for col_idx, ch in enumerate(row):
				rect = pygame.Rect(x, y, self.key_width, self.key_height)
				self.keys.append((ch, rect, row_idx, col_idx))
				x += self.key_width + self.spacing
			y += self.key_height + self.spacing

		# render spacebar (store with sentinel row/col)
		rect = pygame.Rect(x0 + self.key_width * 4, y, self.key_width * 5, self.key_height)
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

			color = (200, 100, 60) if (pressed or base_ch.lower() in self.highlight) else (80, 80, 120)
			pygame.draw.rect(surface, color, rect, border_radius=6)
			pygame.draw.rect(surface, (120, 120, 160), rect, 2, border_radius=6)
			# render label fresh so shifted labels show when Shift is pressed
			surf = self.font.render(label, True, (255, 255, 255))
			text_pos = surf.get_rect(center=rect.center)
			surface.blit(surf, text_pos)

class Scene:
	def __init__(self, layout_path):
		with open(layout_path) as f:
			self.layout = json.load(f)
		self.elements = []
		for el_id, el_data in self.layout.items():
			if el_data["type"] == "text":
				self.elements.append(Text(el_id, el_data))
			elif el_data["type"] == "button":
				self.elements.append(Button(el_id, el_data))
			elif el_data["type"] == "keyboard_overlay":
				self.elements.append(KeyboardOverlay(el_id, el_data))
	
	def draw(self, surface):
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