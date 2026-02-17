#!/usr/bin/env python3
"""layout-trainer — simple typing layout trainer GUI launcher.

This script is the program entrypoint. It initializes Pygame,
registers simple scene callbacks from `ui.Scene` definitions stored
as JSON in the `ui/` folder, and runs the main event loop.

Run: python3 main.py

The program depends on `pygame` and the local `ui` module.
"""

import pygame
import ui
import inputHandling

pygame.init()
pygame.font.init()

screen = pygame.display.set_mode((800, 600))
#make surface for icon.ico
icon = pygame.image.load("icon.png")
pygame.display.set_icon(icon)
pygame.display.set_caption("Layout Trainer")
clock = pygame.time.Clock()

scenes = {
	"main-menu": ui.Scene("ui/main-menu.json"),
	"training": ui.Scene("ui/training.json"),
	"settings": ui.Scene("ui/settings.json"),
	"levels": ui.Scene("ui/levels.json"),
	"level_1": ui.Scene("ui/levels/level_1.json"),
	"level_2": ui.Scene("ui/levels/level_2.json"),
}

level_difficulty = [
	[1],
	[0,1],
	[0,2],
	[0,1,2]
]

key_handler = inputHandling.keyCodeHandler({"layout": "qwerty"})
scene = "main-menu"
current_layout = "qwerty"

def on_start_training(btn=None):
	global scene
	scene = "levels"

# on_load level take a level name string and then load level callback, takes level name as argument and sets scene to that level
#try to load the keyboard element from the level scene and set its layout and key handler to match the current settings

input_text = scenes['level_1'].get_element("input_text")
def on_load_level(level_name):
	def callback(btn):
		global scene, input_text

		input_text = scenes[level_name].get_element("input_text")
		scene = level_name
		level_scene = scenes.get(level_name)

		
		if level_scene:
			kbd = level_scene.get_element("keyboard")
			if kbd:
				try:
					kbd.set_layout(current_layout)
					kbd.set_key_handler(key_handler)

				except Exception:
					pass
		
		if level_name == "level_1":
			input_text.start_level(3,current_layout,level_difficulty[0],on_start_training)
		if level_name == "level_2":
			input_text.start_level(3,current_layout,level_difficulty[1],on_start_training)
			
	return callback

	




def on_settings(btn=None):
	global scene
	scene = "settings"

def back_to_menu(btn=None):
	global scene
	scene = "main-menu"

def on_settings(btn):
	global scene
	scene = "settings"

def on_quit(btn):
	global running
	running = False

# setup callbacks

def set_layout(layout_name):
	def callback(btn):
		global current_layout
		old = current_layout
		current_layout = layout_name
		scenes["settings"].get_element("current_layout_label").change_text(f"Current Layout: {layout_name}")
		# translate existing key mappings so physical keys map to the
		# equivalent character in the new layout (preserve positions).
		try:
			key_handler.translate_layout(layout_name, from_layout=old)
		except Exception:
			# fallback to simple set_layout if translation fails
			key_handler.set_layout(layout_name)
		# if the keyboard overlay exists, update it too
		kbd = scenes["training"].get_element("keyboard")
		if kbd:
			try:
				kbd.set_layout(layout_name)
				kbd.set_key_handler(key_handler)
			except Exception:
				pass
	return callback

scenes["settings"].on_click("qwerty_button", set_layout("qwerty"))
scenes["settings"].on_click("dvorak_button", set_layout("dvorak"))
scenes["settings"].on_click("colemak_button", set_layout("colemak"))
scenes["settings"].on_click("workman_button", set_layout("workman"))
scenes["settings"].on_click("back_button", back_to_menu)

scenes["main-menu"].on_click("settings_button", on_settings)
scenes["main-menu"].on_click("start_button", on_start_training)
scenes["main-menu"].on_click("quit_button", on_quit)

scenes["levels"].on_click("level_1_btn", on_load_level("level_1"))
scenes["levels"].on_click("level_2_btn", on_load_level("level_2"))
scenes["levels"].on_click("exit_button", back_to_menu)


# training scene callbacks
scenes["training"].on_click("back_button", back_to_menu)

scenes["level_1"].on_click("back_button", back_to_menu)
scenes["level_2"].on_click("back_button", back_to_menu)


running = True
while running:
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			running = False
		elif event.type == pygame.MOUSEBUTTONDOWN:
			if event.button == 1:
				scenes[scene].click(event.pos)
		elif event.type == pygame.KEYDOWN:
			if "level" in scene :
				input_text.update_text(key_handler.translate_event(event))
			# forward key events to the input handler for pressed-state tracking
			try:
				key_handler.handle_keydown(event)
			except Exception:
				pass
		elif event.type == pygame.KEYUP:
			try:
				key_handler.handle_keyup(event)
			except Exception:
				pass

	screen.fill((40, 38, 42))
	scenes[scene].draw(screen)
	pygame.display.flip()
	clock.tick(60)

pygame.quit()