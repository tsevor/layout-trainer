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
		self.bounds = pygame.Rect(self.pos[0], self.pos[1], w, h)
		self.text_surface = text_surface
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
		self._load_layout(importlib)

	def _load_layout(self, importlib_module):
		try:
			mod = importlib_module.import_module(f"layouts.{self.layout_name}")
			rows = getattr(mod, "layout", [])
		except Exception:
			rows = []
		self.rows = rows
		self._render_keys()

	def _render_keys(self):
		self.keys = []
		x0, y0 = self.pos
		y = y0
		rownum = 0
		for row in self.rows:
			x = x0 + ( rownum* self.key_width /2)
			rownum += 1
			for ch in row:
				color = (80, 80, 120)
				#detect if the key is pressed and change color if so
				if ch.lower() in self.highlight:
					color = (200, 100, 60)
					self.highlight.remove(ch.lower())
					self.highlight.remove(ch.upper())
				else:
					color = (80, 80, 120)
					self.highlight.discard(ch.lower())
					self.highlight.discard(ch.upper())
				rect = pygame.Rect(x, y, self.key_width, self.key_height)
				label = ch
				surf = self.font.render(label, True, color)
				text_pos = surf.get_rect(center=rect.center)
				self.keys.append((ch, rect, surf, text_pos))
				x += self.key_width + self.spacing
			y += self.key_height + self.spacing
		#render spacebar
		rect = pygame.Rect(x0 + self.key_width*4, y, self.key_width * 5, self.key_height)
		surf = self.font.render(" ", True, (255, 255, 255))
		text_pos = surf.get_rect(center=rect.center)
		self.keys.append((" ", rect, surf, text_pos))

	def set_layout(self, layout_name):
		import importlib
		self.layout_name = layout_name
		self._load_layout(importlib)

	def draw(self, surface):
		for ch, rect, surf, text_pos in self.keys:
			color = (80, 80, 120)
			if ch.lower() in self.highlight:
				color = (200, 100, 60)
			pygame.draw.rect(surface, color, rect, border_radius=6)
			pygame.draw.rect(surface, (120, 120, 160), rect, 2, border_radius=6)
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