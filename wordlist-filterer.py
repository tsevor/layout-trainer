import os
import pygame
import random
import math
import pymunk # Ensure you have run 'pip install pymunk'

# --- CONFIG & PATHS ---
WORDLIST_PATH = os.path.join("wordlists", "top10k.txt")
OUTPUT_PATH = os.path.join("wordlists", "top10kfiltered.txt")

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_CENTER_X = SCREEN_WIDTH // 2
SCREEN_CENTER_Y = SCREEN_HEIGHT // 2

DIAGONAL_ANGLE = -30
SPACING = 220

# --- INITIALIZATION ---
pygame.init()
pygame.mixer.init()
pygame.mixer.set_num_channels(64)
pygame.key.set_repeat(200, 30)

SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
CONSOLAS_LARGE = pygame.font.SysFont("Consolas", 50, bold=True)
CONSOLAS_MED = pygame.font.SysFont("Consolas", 32)
CLOCK = pygame.time.Clock()

# --- PHYSICS WORLD SETUP ---
space = pymunk.Space()
space.gravity = (0, 1100) # Slightly heavier gravity for punchier drops

# Walls & Floor (Left, Right, Bottom)
static_lines = [
    pymunk.Segment(space.static_body, (0, SCREEN_HEIGHT - 20), (SCREEN_WIDTH, SCREEN_HEIGHT - 20), 5), # Floor
    pymunk.Segment(space.static_body, (5, 0), (5, SCREEN_HEIGHT), 5),                                # Left Wall
    pymunk.Segment(space.static_body, (SCREEN_WIDTH - 5, 0), (SCREEN_WIDTH - 5, SCREEN_HEIGHT), 5)    # Right Wall
]

for line in static_lines:
    line.elasticity = 0.75 # Bouncy walls
    line.friction = 0.5
    space.add(line)

# --- ASSETS ---
EXPLOSION_SOUNDS = []
for i in range(1, 6):
    p = f"sounds/boom{i}.wav"
    if os.path.exists(p):
        try:
            EXPLOSION_SOUNDS.append(pygame.mixer.Sound(p))
        except: pass

# --- PHYSICS CLASSES ---

class PhysicalLetter:
    def __init__(self, char, x, y):
        self.char = char
        self.surf = CONSOLAS_LARGE.render(char, True, (255, 255, 255))
        w, h = self.surf.get_size()

        # Pymunk Physics Body
        mass = 1
        moment = pymunk.moment_for_box(mass, (w, h))
        self.body = pymunk.Body(mass, moment)
        self.body.position = (x, y)
        
        # Collision Shape
        self.shape = pymunk.Poly.create_box(self.body, (w, h))
        self.shape.elasticity = 0.6
        self.shape.friction = 0.6
        space.add(self.body, self.shape)

        # Explosive Kick (Spread wider)
        angle = random.uniform(-math.pi * 0.8, -math.pi * 0.2) 
        force = random.uniform(600, 1100)
        self.body.apply_impulse_at_local_point((math.cos(angle)*force, math.sin(angle)*force))
        self.body.angular_velocity = random.uniform(-15, 15)

        self.life = 1.0
        self.decay = random.uniform(0.004, 0.008)

    def update(self):
        self.life -= self.decay
        if self.life <= 0:
            space.remove(self.body, self.shape)
            return False
        return True

    def draw(self, surf):
        angle_deg = math.degrees(-self.body.angle)
        rotated_surf = pygame.transform.rotate(self.surf, angle_deg)
        alpha = int(self.life * 255)
        rotated_surf.set_alpha(alpha)
        
        # Central glow for high-impact letters
        if self.life > 0.85:
            glow = pygame.Surface((60, 60), pygame.SRCALPHA)
            pygame.draw.circle(glow, (255, 100, 0, 100), (30, 30), 30)
            surf.blit(glow, glow.get_rect(center=self.body.position))

        rect = rotated_surf.get_rect(center=self.body.position)
        surf.blit(rotated_surf, rect.topleft)

class ParticleDebris:
    def __init__(self, x, y):
        self.x, self.y = x, y
        ang = random.uniform(0, math.pi*2)
        spd = random.uniform(5, 25)
        self.vx, self.vy = math.cos(ang)*spd, math.sin(ang)*spd
        self.life = 1.0
        self.decay = random.uniform(0.02, 0.06)
        self.size = random.randint(4, 12)
        self.color = random.choice([(255,255,255), (255,220,0), (255,60,0)])

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.3
        self.life -= self.decay
        return self.life > 0

    def draw(self, surf):
        c = [int(channel * self.life) for channel in self.color]
        pygame.draw.circle(surf, c, (int(self.x), int(self.y)), int(self.size * self.life))

# --- APP STATE ---
physical_letters = []
particles = []
shake_intensity = 0
flash_alpha = 0

def list_words(path):
    if not os.path.exists(path): return []
    with open(path, "r", encoding="utf-8") as f:
        return [w.strip() for w in f if w.strip()]

def save_words(blocks):
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(blocks))

blocks = list_words(OUTPUT_PATH) if os.path.exists(OUTPUT_PATH) else list_words(WORDLIST_PATH)
target_index = 0
display_index = 0.0
last_del = []

# --- MAIN LOOP ---
while True:
    dt = CLOCK.tick(60) / 1000.0
    space.step(dt)
    
    # SHAKE FADE (Reduced from 0.9 to 0.8 for faster stabilization)
    if shake_intensity > 0: 
        shake_intensity *= 0.8
        if shake_intensity < 0.5: shake_intensity = 0
        
    if flash_alpha > 0: 
        flash_alpha -= 20 # Faster flash fade too

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            save_words(blocks)
            pygame.quit(); quit()
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT: target_index = (target_index - 1) % len(blocks) if blocks else 0
            elif event.key == pygame.K_RIGHT: target_index = (target_index + 1) % len(blocks) if blocks else 0
            
            # Letter Jump
            elif hasattr(event, 'unicode') and event.unicode.isalpha():
                ch = event.unicode.lower()
                if blocks:
                    for i in range(len(blocks)):
                        idx = (target_index + 1 + i) % len(blocks)
                        if blocks[idx].lower().startswith(ch):
                            target_index = idx; break

            # DELETE
            elif event.key == pygame.K_DELETE and blocks:
                idx = int(round(display_index)) % len(blocks)
                word = blocks.pop(idx)
                last_del.append((idx, word))
                
                for i, char in enumerate(word):
                    spawn_x = SCREEN_CENTER_X + (i - len(word)/2) * 35
                    physical_letters.append(PhysicalLetter(char, spawn_x, SCREEN_CENTER_Y))
                
                for _ in range(80):
                    particles.append(ParticleDebris(SCREEN_CENTER_X, SCREEN_CENTER_Y))

                if EXPLOSION_SOUNDS: random.choice(EXPLOSION_SOUNDS).play()
                shake_intensity = 45 # High initial shake
                flash_alpha = 220
                save_words(blocks)
                if blocks: target_index %= len(blocks)

            elif event.key == pygame.K_z and last_del:
                i, w = last_del.pop()
                blocks.insert(min(i, len(blocks)), w)
                save_words(blocks)

    # UI Physics
    display_index += (target_index - display_index) * 0.22
    
    physical_letters = [l for l in physical_letters if l.update()]
    particles = [p for p in particles if p.update()]

    # --- RENDERING ---
    off_x = random.uniform(-shake_intensity, shake_intensity)
    off_y = random.uniform(-shake_intensity, shake_intensity)
    SCREEN.fill((10, 8, 20))
    
    # Word List
    if blocks:
        c_idx = int(round(display_index))
        for i in range(c_idx - 8, c_idx + 9):
            idx = i % len(blocks)
            x = SCREEN_CENTER_X + (i - display_index) * SPACING
            dist = abs(SCREEN_CENTER_X - x)
            if dist > SCREEN_WIDTH: continue
            
            scale = max(1, 4.2 * (1 - dist/SCREEN_CENTER_X))
            font = pygame.font.SysFont("Inconsolata", int(32 * scale))
            
            # Color jitter during high shake
            color = (255, 255, 255)
            if shake_intensity > 10:
                color = (255, random.randint(150, 255), 150)
            
            txt = font.render(blocks[idx], True, color)
            txt = pygame.transform.rotate(txt, DIAGONAL_ANGLE)
            rect = txt.get_rect(center=(int(x + off_x), int(SCREEN_CENTER_Y + off_y)))
            SCREEN.blit(txt, rect)

    # Physical Letters (behind particles, on top of list)
    for l in physical_letters:
        l.draw(SCREEN)

    for p in particles:
        p.draw(SCREEN)

    # Impact Flash
    if flash_alpha > 0:
        f_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        f_surf.fill((255, 255, 255))
        f_surf.set_alpha(flash_alpha)
        SCREEN.blit(f_surf, (0,0))

    # Center Pointer UI
    ptr_color = (255, 0, 0) if shake_intensity > 10 else (255, 255, 255)
    pygame.draw.polygon(SCREEN, ptr_color, 
                        [(SCREEN_CENTER_X + p[0], SCREEN_CENTER_Y + p[1]) for p in [(0, -90), (-25, -120), (25, -120)]])

    if blocks:
        cur = blocks[int(round(display_index)) % len(blocks)]
        info = CONSOLAS_MED.render(f"Remaining: {len(blocks)} | Target: {cur}", True, (120, 120, 160))
        SCREEN.blit(info, (20, SCREEN_HEIGHT - 45))

    pygame.display.flip()