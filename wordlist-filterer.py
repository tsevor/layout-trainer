import os
import pygame
import random
import math
import pymunk

# --- CONFIG ---
WORDLIST_PATH = os.path.join("wordlists", "top10k.txt")
OUTPUT_PATH = os.path.join("wordlists", "top10kfiltered.txt")
SOUNDS_DIR = "sounds"
SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 700 
SCREEN_CENTER = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

# --- THEMES ---
THEMES = [
    {"bg": (5, 5, 10), "text": (255, 255, 255), "grid": (20, 30, 40), "accent": (0, 255, 200)}, # Cyber
    {"bg": (20, 10, 10), "text": (255, 200, 150), "grid": (40, 20, 20), "accent": (255, 80, 0)}, # Mars
    {"bg": (0, 0, 0), "text": (50, 255, 50), "grid": (0, 30, 0), "accent": (0, 255, 0)},       # Matrix
]
current_theme_idx = 0

# --- INITIALIZATION ---
pygame.init()
pygame.mixer.init()
pygame.mixer.set_num_channels(64)
pygame.key.set_repeat(300, 50)

SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("WORD KILLER // REGEN V2")
FONT_XL = pygame.font.SysFont("Consolas", 80, bold=True)
FONT_L = pygame.font.SysFont("Consolas", 60, bold=True)
FONT_M = pygame.font.SysFont("Consolas", 32)
FONT_S = pygame.font.SysFont("Consolas", 18)
CLOCK = pygame.time.Clock()

# --- SOUNDS ---
BOOMS = []
REGEN_SOUND = None
try:
    if os.path.exists(SOUNDS_DIR):
        for i in range(1, 6):
            p = os.path.join(SOUNDS_DIR, f"boom{i}.wav")
            if os.path.exists(p):
                s = pygame.mixer.Sound(p)
                s.set_volume(0.6)
                BOOMS.append(s)
        
        r_p = os.path.join(SOUNDS_DIR, "regen.mp3")
        if os.path.exists(r_p):
            REGEN_SOUND = pygame.mixer.Sound(r_p)
            REGEN_SOUND.set_volume(0.8)
except Exception as e:
    print(f"Audio Error: {e}")

# --- PHYSICS ---
space = pymunk.Space()
space.gravity = (0, 1500)
static_lines = [
    pymunk.Segment(space.static_body, (0, SCREEN_HEIGHT-20), (SCREEN_WIDTH, SCREEN_HEIGHT-20), 10),
    pymunk.Segment(space.static_body, (-10, 0), (-10, SCREEN_HEIGHT), 10),
    pymunk.Segment(space.static_body, (SCREEN_WIDTH+10, 0), (SCREEN_WIDTH+10, SCREEN_HEIGHT), 10)
]
for line in static_lines:
    line.elasticity, line.friction = 0.6, 0.5
    space.add(line)

# --- CLASSES ---

class Particle:
    def __init__(self, x, y, p_type="spark", color=None, speed_mult=1.0):
        self.x, self.y = x, y
        ang = random.uniform(0, math.pi*2)
        spd = random.uniform(3, 22) * speed_mult
        self.vx, self.vy = math.cos(ang)*spd, math.sin(ang)*spd
        self.life = 1.0
        self.type = p_type
        self.decay = random.uniform(0.015, 0.04)
        self.size = random.randint(2, 6)
        if p_type == "smoke": self.size = random.randint(20, 50)
        if color: self.color = color
        else:
            if p_type == "smoke": self.color = (30, 30, 35)
            else: self.color = (255, 255, 255)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        if self.type != "smoke": 
            self.vy += 0.3
            self.vx *= 0.96
            self.vy *= 0.96
        else: 
            self.vy -= 0.1
            self.size += 0.2
        self.life -= self.decay
        return self.life > 0

    def draw(self, surf, theme):
        alpha = int(self.life * 255)
        if self.type == "smoke": alpha = int(self.life * 60)
        s = pygame.Surface((int(self.size*2), int(self.size*2)), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha), (int(self.size), int(self.size)), int(self.size))
        surf.blit(s, (self.x - self.size, self.y - self.size))

class PhysicalLetter:
    def __init__(self, char, x, y, word_id, is_random_spawn=False):
        self.char = char
        self.word_id = word_id
        self.surf = FONT_L.render(char, True, (255, 255, 255))
        w, h = self.surf.get_size()
        self.radius = max(w, h) / 2.2
        mass = 1
        moment = pymunk.moment_for_circle(mass, 0, self.radius)
        self.body = pymunk.Body(mass, moment)
        self.body.position = (x, y)
        self.shape = pymunk.Circle(self.body, self.radius)
        self.shape.elasticity, self.shape.friction = 0.6, 0.5
        space.add(self.body, self.shape)
        
        if not is_random_spawn:
            # Explosion impulse
            impulse = (random.uniform(-400, 400), random.uniform(-1000, -500))
            self.body.apply_impulse_at_local_point(impulse)
            self.life = 4.0 # Shorter life so they delete faster
        else:
            # Random spawn for regeneration (starts Kinematic so gravity doesn't pull it immediately)
            self.body.body_type = pymunk.Body.KINEMATIC
            self.life = 10.0 # Long life to survive the ritual
        
        # Regeneration State
        self.is_reviving = False
        self.revive_start_pos = (x, y)

    def update(self, dt, mouse_pos, mouse_vel, ritual_timer=0, target_x=0):
        if self.is_reviving:
            # --- PHASE 1: GATHER (0s - 1s) ---
            if ritual_timer < 1.0:
                t = ritual_timer / 1.0
                t = 1 - pow(1 - t, 3) # Cubic ease out
                
                start_vec = pygame.Vector2(self.revive_start_pos)
                target_vec = pygame.Vector2(target_x, SCREEN_HEIGHT // 2)
                
                new_pos = start_vec.lerp(target_vec, t)
                self.body.position = (new_pos.x, new_pos.y)
                self.body.angle *= 0.8
                self.body.velocity = (0,0)
            
            # --- PHASE 2: HOVER & SHAKE (1s - 4.5s) ---
            else:
                shake_amt = (ritual_timer - 0.5) * 1.5 
                sx = random.uniform(-shake_amt, shake_amt)
                sy = random.uniform(-shake_amt, shake_amt)
                self.body.position = (target_x + sx, SCREEN_HEIGHT // 2 + sy)
                self.body.angle = 0
                self.body.velocity = (0,0)

            return True
        
        # Normal Physics
        mx, my = mouse_pos
        dist = math.hypot(self.body.position.x - mx, self.body.position.y - my)
        if dist < 100 and (abs(mouse_vel[0]) > 5 or abs(mouse_vel[1]) > 5):
            force_dir = pygame.Vector2(self.body.position.x - mx, self.body.position.y - my).normalize()
            force = force_dir * 800
            self.body.apply_impulse_at_local_point(force)

        self.life -= dt
        if self.life <= 0:
            # REMOVAL FROM SPACE
            if self.body in space.bodies: space.remove(self.body, self.shape)
            return False
        return True

    def draw(self, surf, theme, glitch=False):
        angle = math.degrees(-self.body.angle)
        img = pygame.transform.rotate(self.surf, angle)
        draw_pos = list(self.body.position)
        
        if glitch:
            # Cyan Tint
            img.fill((0, 255, 255), special_flags=pygame.BLEND_MULT)
            
            # --- TRANSPARENT CIRCLE OUTLINE ---
            # Create a separate surface to handle alpha properly
            circle_radius = int(self.radius + 8)
            s_glow = pygame.Surface((circle_radius * 2, circle_radius * 2), pygame.SRCALPHA)
            # Alpha 30 (Very transparent)
            pygame.draw.circle(s_glow, (0, 255, 255, 30), (circle_radius, circle_radius), circle_radius, 3)
            surf.blit(s_glow, (draw_pos[0] - circle_radius, draw_pos[1] - circle_radius))

        alpha = 255 if self.life > 1.0 else int(self.life * 255)
        img.set_alpha(max(0, alpha))
        rect = img.get_rect(center=draw_pos)
        surf.blit(img, rect.topleft)

# --- STATE ---
if os.path.exists(OUTPUT_PATH):
    blocks = [l.strip() for l in open(OUTPUT_PATH, encoding="utf-8") if l.strip()]
else:
    if os.path.exists(WORDLIST_PATH):
        blocks = [l.strip() for l in open(WORDLIST_PATH, encoding="utf-8") if l.strip()]
    else:
        blocks = ["apple", "banana", "cherry", "doom", "explode", "physics", "system", "failure"]

target_index, display_index = 0, 0.0
last_del = []
physical_letters = []
particles = []
shake, flash = 0, 0
word_id_counter = 0

ritual_active, ritual_timer = False, 0.0
RITUAL_TOTAL_TIME = 4.5 

search_term, search_timer = "", 0
SEARCH_COOLDOWN = 3000 
combo_count = 0
last_kill_time = 0
COMBO_WINDOW = 1200 
grid_offset = 0.0

def get_combo_color(count):
    if count < 5: return (255, 255, 255)
    if count < 10: return (255, 255, 0)
    if count < 20: return (255, 100, 0)
    if count < 30: return (255, 0, 0)
    return (255, 0, 255)

def spawn_explosion(x, y, combo):
    count = 100 + (min(combo, 50) * 5)
    col = get_combo_color(combo)
    for _ in range(int(count/3)): particles.append(Particle(x, y, "smoke"))
    for _ in range(count): 
        p = Particle(x, y, "ember", col, speed_mult=1.0 + (combo*0.05))
        particles.append(p)

def draw_grid(surf, theme, offset):
    col = theme["grid"]
    horizon_y = SCREEN_HEIGHT // 2 + 100
    for i in range(0, SCREEN_WIDTH + 100, 100):
        top_x = SCREEN_WIDTH // 2 + (i - SCREEN_WIDTH//2) * 0.2
        pygame.draw.line(surf, col, (top_x, horizon_y), (i, SCREEN_HEIGHT), 1)
    for i in range(20):
        y_perc = (i + offset) % 20 / 20.0
        y_screen = horizon_y + (y_perc ** 3) * (SCREEN_HEIGHT - horizon_y)
        pygame.draw.line(surf, col, (0, y_screen), (SCREEN_WIDTH, y_screen), 1)

def draw_crt_lines(surf):
    for y in range(0, SCREEN_HEIGHT, 4):
        pygame.draw.line(surf, (0, 0, 0), (0, y), (SCREEN_WIDTH, y), 1)

# --- MAIN LOOP ---
mouse_prev = pygame.mouse.get_pos()

while True:
    dt = CLOCK.tick(60) / 1000.0
    current_ticks = pygame.time.get_ticks()
    mouse_curr = pygame.mouse.get_pos()
    mouse_vel = (mouse_curr[0] - mouse_prev[0], mouse_curr[1] - mouse_prev[1])
    mouse_prev = mouse_curr
    theme = THEMES[current_theme_idx]

    if search_term and current_ticks - search_timer > SEARCH_COOLDOWN: search_term = ""
    if combo_count > 0 and current_ticks - last_kill_time > COMBO_WINDOW: combo_count = 0
    grid_offset += dt * 5
    
    sim_dt = dt * 0.1 if (ritual_active and ritual_timer > 1.0) else dt
    space.step(sim_dt)
    
    if shake > 0: shake *= 0.85
    if flash > 0: flash -= 10

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            with open(OUTPUT_PATH, "w", encoding="utf-8") as f: f.write("\n".join(blocks))
            pygame.quit(); quit()
        
        if ritual_active: continue 

        if event.type == pygame.KEYDOWN:
            is_ctrl = (event.mod & pygame.KMOD_CTRL)
            if event.key == pygame.K_F1: current_theme_idx = 0
            if event.key == pygame.K_F2: current_theme_idx = 1
            if event.key == pygame.K_F3: current_theme_idx = 2
            if event.key == pygame.K_LEFT: target_index = (target_index - 1) % len(blocks)
            if event.key == pygame.K_RIGHT: target_index = (target_index + 1) % len(blocks)
            
            if event.key == pygame.K_DELETE and blocks:
                idx = int(round(display_index)) % len(blocks)
                word = blocks.pop(idx)
                word_id_counter += 1
                last_del.append((idx, word, word_id_counter))
                combo_count += 1
                last_kill_time = current_ticks
                spawn_explosion(SCREEN_CENTER[0], SCREEN_CENTER[1], combo_count)
                for i, c in enumerate(word):
                    sx = SCREEN_CENTER[0] + (i - len(word)/2) * 20
                    physical_letters.append(PhysicalLetter(c, sx, SCREEN_CENTER[1], word_id_counter))
                if BOOMS: 
                    s = random.choice(BOOMS)
                    s.set_volume(random.uniform(0.5, 1.0))
                    s.play()
                shake = 40 + min(combo_count * 2, 50)
                flash = 200
                if blocks: target_index %= len(blocks)

            # --- REGEN (CTRL + Z) ---
            if event.key == pygame.K_z and is_ctrl and last_del:
                ritual_active = True
                ritual_timer = 0.0
                if REGEN_SOUND: REGEN_SOUND.play()
                
                _, r_word, r_id = last_del[-1]
                
                # Check what still exists
                existing = [l for l in physical_letters if l.word_id == r_id]
                existing_chars = [l.char for l in existing]
                
                # Setup existing for revival
                for l in existing:
                    l.is_reviving = True
                    l.revive_start_pos = l.body.position
                    l.body.body_type = pymunk.Body.KINEMATIC
                    l.body.velocity = (0,0)
                
                # Spawn NEW letters for the missing ones (offscreen)
                # Naive matching: if we need 2 'a's and have 1, spawn 1.
                # Since letters can be duplicates, we just check count.
                import collections
                needed_counts = collections.Counter(r_word)
                have_counts = collections.Counter(existing_chars)
                
                for char, count in needed_counts.items():
                    missing = count - have_counts[char]
                    if missing > 0:
                        for _ in range(missing):
                            # Spawn OFF SCREEN
                            spawn_x = -150 if random.random() < 0.5 else SCREEN_WIDTH + 150
                            spawn_y = random.randint(100, SCREEN_HEIGHT - 100)
                            
                            l = PhysicalLetter(char, spawn_x, spawn_y, r_id, is_random_spawn=True)
                            l.is_reviving = True
                            l.revive_start_pos = (spawn_x, spawn_y)
                            physical_letters.append(l)

            elif event.unicode and not is_ctrl and (event.unicode.isalpha() or event.unicode.isdigit()):
                char = event.unicode.lower()
                if current_ticks - search_timer > SEARCH_COOLDOWN: search_term = ""
                search_term += char
                search_timer = current_ticks
                for i, word in enumerate(blocks):
                    if word.lower().startswith(search_term):
                        target_index = i
                        shake = 5
                        break

    if ritual_active:
        ritual_timer += dt
        _, r_word, r_id = last_del[-1]
        
        # Sort letters to match word order for visual consistency
        # This is a bit tricky with physics objects, so we just group by ID
        rel_letters = [l for l in physical_letters if l.word_id == r_id]
        
        # Simple sorting by char to try and match the word (imperfect but better)
        # We need to map specific letter objects to specific slots in the word.
        # This prevents an 'e' from the left flying to the right slot if there are two 'e's.
        rel_letters.sort(key=lambda x: x.char) # Naive sort
        
        # We actually need to assign target slots.
        # We'll just iterate the word and pick the first matching avail char
        assigned_letters = []
        temp_pool = rel_letters.copy()
        for char in r_word:
            found = next((l for l in temp_pool if l.char == char), None)
            if found:
                assigned_letters.append(found)
                temp_pool.remove(found)
        
        if ritual_timer > 1.0:
            intensity = (ritual_timer - 1.0) * 0.5 
            shake = intensity
            if random.random() < 0.3 and assigned_letters:
                l = random.choice(assigned_letters)
                particles.append(Particle(l.body.position.x, l.body.position.y, "ember", (0, 255, 255)))

        for i, l in enumerate(assigned_letters):
            target_x = SCREEN_CENTER[0] + (i - len(r_word)/2) * 45
            l.update(dt, mouse_curr, mouse_vel, ritual_timer, target_x)
        
        if ritual_timer >= RITUAL_TOTAL_TIME:
            orig_idx, word, _ = last_del.pop()
            current_pos = int(round(display_index)) % (len(blocks) + 1)
            blocks.insert(current_pos, word)
            target_index = current_pos 
            
            ritual_active, ritual_timer = False, 0
            for l in rel_letters:
                if l.body in space.bodies: space.remove(l.body, l.shape)
                if l in physical_letters: physical_letters.remove(l)
            
            spawn_explosion(SCREEN_CENTER[0], SCREEN_CENTER[1], 5)
            flash = 255
            if BOOMS: random.choice(BOOMS).play()

    display_index += (target_index - display_index) * 0.2
    particles = [p for p in particles if p.update()]
    
    # Filter dead letters
    physical_letters = [l for l in physical_letters if (l.is_reviving or l.update(dt, mouse_curr, mouse_vel))]

    sx = random.uniform(-shake, shake)
    sy = random.uniform(-shake, shake)
    SCREEN.fill(theme["bg"])
    draw_grid(SCREEN, theme, grid_offset)

    if blocks:
        center_idx = int(display_index)
        for i in range(center_idx-7, center_idx+8):
            idx = i % len(blocks)
            offset = i - display_index
            x_raw = SCREEN_CENTER[0] + offset * 210
            y_raw = SCREEN_CENTER[1]
            dist = abs(SCREEN_CENTER[0] - x_raw)
            scale = max(0.5, 1.2 - (dist / 1000.0))
            if x_raw < -150 or x_raw > SCREEN_WIDTH + 150: continue

            f_size = int(50 * scale)
            font = pygame.font.SysFont("Consolas", f_size, bold=True)
            word_str = blocks[idx]
            
            col = theme["text"]
            if i == int(round(display_index)):
                if search_term and word_str.lower().startswith(search_term): col = (255, 255, 50)
                else: col = theme["accent"]

            txt = font.render(word_str, True, col)
            txt = pygame.transform.rotate(txt, 45)
            rect = txt.get_rect(center=(x_raw + sx, y_raw + sy))
            
            if i == int(round(display_index)):
                glow = font.render(word_str, True, (col[0], col[1], col[2]))
                glow.set_alpha(50)
                glow = pygame.transform.rotate(glow, 45)
                SCREEN.blit(glow, (rect.x - 3, rect.y - 3))
                SCREEN.blit(glow, (rect.x + 3, rect.y + 3))
            
            SCREEN.blit(txt, rect)

    for p in particles: p.draw(SCREEN, theme)
    for l in physical_letters: l.draw(SCREEN, theme, glitch=ritual_active)

    stats_txt = FONT_S.render(f"WORDS: {len(blocks)} | TARGET: {target_index}", True, (100, 100, 100))
    SCREEN.blit(stats_txt, (10, 10))
    ctrl_txt = FONT_S.render("DEL: Destroy | CTRL+Z: Revive | TYPE: Search | F1-3: Themes", True, (80, 80, 80))
    SCREEN.blit(ctrl_txt, (10, SCREEN_HEIGHT - 30))

    if combo_count > 1:
        c_col = get_combo_color(combo_count)
        combo_txt = FONT_XL.render(f"{combo_count}x COMBO!", True, c_col)
        combo_txt = pygame.transform.rotate(combo_txt, random.randint(-5, 5))
        r = combo_txt.get_rect(center=(SCREEN_WIDTH - 150, 100))
        SCREEN.blit(combo_txt, r)
        time_left = max(0, COMBO_WINDOW - (current_ticks - last_kill_time))
        w = (time_left / COMBO_WINDOW) * 200
        pygame.draw.rect(SCREEN, c_col, (SCREEN_WIDTH - 250, 150, w, 10))

    if search_term:
        s_txt = FONT_M.render(f"SEARCHING: {search_term}_", True, (255, 255, 0))
        SCREEN.blit(s_txt, (SCREEN_WIDTH//2 - s_txt.get_width()//2, SCREEN_HEIGHT - 100))

    if flash > 0:
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        s.fill((255, 255, 255))
        s.set_alpha(flash)
        SCREEN.blit(s, (0, 0))
    draw_crt_lines(SCREEN)
    pygame.display.flip()