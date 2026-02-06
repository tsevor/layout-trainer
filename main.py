#!/usr/bin/env python3

import pygame

import layouts
import time

pygame.init()
pygame.font.init()

SCREEN = pygame.display.set_mode((800, 600))


while True:
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			pygame.quit()
			exit()

	SCREEN.fill((0, 0, 0))

	layouts.draw(SCREEN, layouts.qwerty)

	pygame.display.flip()
	time.sleep(0.01)