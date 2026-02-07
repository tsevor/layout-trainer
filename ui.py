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