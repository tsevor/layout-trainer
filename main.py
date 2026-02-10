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

pygame.init()
pygame.font.init()

screen = pygame.display.set_mode((800, 600))
#make surface for icon.ico
icon = pygame.image.load("icon.ico")
pygame.display.set_icon(icon)
pygame.display.set_caption("Layout Trainer")
clock = pygame.time.Clock()

scenes = {
	"main-menu": ui.Scene("ui/main-menu.json"),
	"training": ui.Scene("ui/training.json"),
	"settings": ui.Scene("ui/settings.json")
}


scene = "main-menu"
current_layout = "qwerty"

def on_start_training(btn):
	global scene
	# ensure keyboard overlay reflects current layout
	kbd = scenes["training"].get_element("keyboard")
	if kbd:
		try:
			kbd.set_layout(current_layout)
		except Exception:
			pass
	scene = "training"

def on_settings(btn):
	global scene
	scene = "settings"

def back_to_menu(btn):
	global scene
	scene = "main-menu"

def on_settings(btn):
	global scene
	scene = "settings"

def on_quit(btn):
	global running
	running = False

def back_to_menu(btn):
	global scene
	scene = "main-menu"


# setup callbacks

def set_layout(layout_name):
	def callback(btn):
		global current_layout
		current_layout = layout_name
		scenes["settings"].get_element("current_layout_label").change_text(f"Current Layout: {layout_name}")
	return callback

scenes["settings"].on_click("qwerty_button", set_layout("qwerty"))
scenes["settings"].on_click("dvorak_button", set_layout("dvorak"))
scenes["settings"].on_click("colemak_button", set_layout("colemak"))
scenes["settings"].on_click("workman_button", set_layout("workman"))
scenes["settings"].on_click("back_button", back_to_menu)

scenes["main-menu"].on_click("settings_button", on_settings)
scenes["main-menu"].on_click("start_button", on_start_training)
scenes["main-menu"].on_click("quit_button", on_quit)

# training scene callbacks
scenes["training"].on_click("back_button", back_to_menu)


running = True
while running:
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			running = False
		elif event.type == pygame.MOUSEBUTTONDOWN:
			if event.button == 1:
				scenes[scene].click(event.pos)

	screen.fill((40, 38, 42))
	scenes[scene].draw(screen)
	pygame.display.flip()
	clock.tick(60)

pygame.quit()