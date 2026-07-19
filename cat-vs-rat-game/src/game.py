import importlib
import importlib.util
import io
import wave
import math
import struct
import subprocess
import tempfile
import shutil
import pygame
import sys
import random


def has_pygame_submodule(module_name):
    return importlib.util.find_spec(f"pygame.{module_name}") is not None


pygame_mixer = None
pygame_available_mixer = has_pygame_submodule("mixer")
if pygame_available_mixer:
    try:
        pygame_mixer = importlib.import_module("pygame.mixer")
        pygame_mixer.pre_init(frequency=44100, size=-16, channels=1, buffer=512)
    except Exception:
        pygame_mixer = None
        pygame_available_mixer = False

pygame.init()

# Sound setup
mixer_available = False
hit_sound = None
fallback_sound_path = None


def make_tone(freq, duration_ms, volume=0.5, sample_rate=44100):
    if pygame_mixer is None:
        raise RuntimeError("pygame mixer is unavailable")

    n_samples = int(sample_rate * duration_ms / 1000)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        frames = bytearray()
        for i in range(n_samples):
            t = i / sample_rate
            sample = int(volume * 32767 * math.sin(2 * math.pi * freq * t))
            frames += struct.pack("<h", sample)
        wav_file.writeframes(frames)
    buf.seek(0)
    return pygame_mixer.Sound(file=buf)


def make_tone_wav_file(freq, duration_ms, volume=0.5, sample_rate=44100):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
        path = temp_file.name
    with wave.open(path, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        frames = bytearray()
        n_samples = int(sample_rate * duration_ms / 1000)
        for i in range(n_samples):
            t = i / sample_rate
            sample = int(volume * 32767 * math.sin(2 * math.pi * freq * t))
            frames += struct.pack("<h", sample)
        wav_file.writeframes(frames)
    return path


def play_hit_sound():
    global hit_sound, fallback_sound_path
    if hit_sound:
        hit_sound.play()
        return
    if fallback_sound_path:
        if sys.platform == "darwin" and shutil.which("afplay"):
            subprocess.Popen(["afplay", fallback_sound_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
        if sys.platform.startswith("linux") and shutil.which("aplay"):
            subprocess.Popen(["aplay", fallback_sound_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
        if sys.platform.startswith("win"):
            try:
                import winsound
                winsound.PlaySound(fallback_sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            except Exception:
                pass

if pygame_available_mixer and pygame_mixer is not None:
    try:
        pygame_mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
        mixer_available = True
    except Exception:
        mixer_available = False

if mixer_available:
    try:
        hit_sound = make_tone(880, 100, volume=0.4)
    except Exception:
        hit_sound = None

if hit_sound is None:
    try:
        fallback_sound_path = make_tone_wav_file(880, 100, volume=0.4)
    except Exception:
        fallback_sound_path = None

# Screen
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cat vs Rat")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
CAT_COLOR = WHITE
RAT_GRAY = (70, 70, 70)
PINK = (255, 192, 203)

# Player (blue cat)
player_size = 50
player_x = WIDTH // 2
player_y = HEIGHT // 2
player_speed = 5
player_anim_frame = 0.0
player_anim_speed = 0.18

# Enemy (auto moving rat)
enemy_size = 50
enemy_x = random.randint(0, WIDTH - enemy_size)
enemy_y = random.randint(0, HEIGHT - enemy_size)
enemy_speed_x = 3
enemy_speed_y = 3
enemy_anim_frame = 0.0
enemy_anim_speed = 0.15

clock = pygame.time.Clock()

score = 0
font = None
if has_pygame_submodule("font"):
    try:
        font = pygame.font.SysFont(None, 36)
    except Exception:
        font = None

# Fallback numeric score drawing if pygame font is unavailable.
DIGIT_SEGMENTS = {
    '0': [1, 1, 1, 0, 1, 1, 1],
    '1': [0, 0, 1, 0, 0, 1, 0],
    '2': [1, 0, 1, 1, 1, 0, 1],
    '3': [1, 0, 1, 1, 0, 1, 1],
    '4': [0, 1, 1, 1, 0, 1, 0],
    '5': [1, 1, 0, 1, 0, 1, 1],
    '6': [1, 1, 0, 1, 1, 1, 1],
    '7': [1, 0, 1, 0, 0, 1, 0],
    '8': [1, 1, 1, 1, 1, 1, 1],
    '9': [1, 1, 1, 1, 0, 1, 1],
}

def draw_digit(surface, x, y, digit, size, color):
    segments = DIGIT_SEGMENTS.get(str(digit), DIGIT_SEGMENTS['0'])
    thickness = max(size // 8, 3)
    width = size
    height = size * 2

    segment_rects = [
        pygame.Rect(x + thickness, y, width - thickness * 2, thickness),
        pygame.Rect(x, y + thickness, thickness, height // 2 - thickness),
        pygame.Rect(x + width - thickness, y + thickness, thickness, height // 2 - thickness),
        pygame.Rect(x + thickness, y + height // 2 - thickness // 2, width - thickness * 2, thickness),
        pygame.Rect(x, y + height // 2 + thickness // 2, thickness, height // 2 - thickness),
        pygame.Rect(x + width - thickness, y + height // 2 + thickness // 2, thickness, height // 2 - thickness),
        pygame.Rect(x + thickness, y + height - thickness, width - thickness * 2, thickness),
    ]

    for active, rect in zip(segments, segment_rects):
        if active:
            pygame.draw.rect(surface, color, rect, border_radius=3)


def draw_score(surface, score_value, x, y, color=(0, 0, 0)):
    score_text = str(score_value)
    digit_size = 20
    spacing = 8
    for i, digit in enumerate(score_text):
        draw_digit(surface, x + i * (digit_size + spacing), y, digit, digit_size, color)


def move_enemy(enemy_x, enemy_y, enemy_speed_x, enemy_speed_y, width, height, enemy_size):
    enemy_x += enemy_speed_x
    enemy_y += enemy_speed_y

    if enemy_x <= 0 or enemy_x >= width - enemy_size:
        enemy_speed_x *= -1
    if enemy_y <= 0 or enemy_y >= height - enemy_size:
        enemy_speed_y *= -1

    return enemy_x, enemy_y, enemy_speed_x, enemy_speed_y


def is_collision(player_x, player_y, player_size, enemy_x, enemy_y, enemy_size):
    player_rect = pygame.Rect(player_x, player_y, player_size, player_size)
    enemy_rect = pygame.Rect(enemy_x, enemy_y, enemy_size, enemy_size)
    return player_rect.colliderect(enemy_rect)


def draw_cat(surface, x, y, size, color, frame):
    body_rect = pygame.Rect(x + size // 8, y + size // 3, size * 3 // 4, size * 7 // 10)
    pygame.draw.ellipse(surface, color, body_rect)
    pygame.draw.ellipse(surface, BLACK, body_rect, 3)

    head_center = (x + size // 2, y + size // 3)
    head_radius = size // 4
    pygame.draw.circle(surface, color, head_center, head_radius)
    pygame.draw.circle(surface, BLACK, head_center, head_radius, 3)

    left_ear = [
        (head_center[0] - head_radius // 2, head_center[1] - head_radius // 2),
        (head_center[0] - head_radius, head_center[1] - head_radius - 4),
        (head_center[0] - head_radius // 6, head_center[1] - head_radius // 4),
    ]
    right_ear = [
        (head_center[0] + head_radius // 2, head_center[1] - head_radius // 2),
        (head_center[0] + head_radius, head_center[1] - head_radius - 4),
        (head_center[0] + head_radius // 6, head_center[1] - head_radius // 4),
    ]
    pygame.draw.polygon(surface, color, left_ear)
    pygame.draw.polygon(surface, BLACK, left_ear, 3)
    pygame.draw.polygon(surface, color, right_ear)
    pygame.draw.polygon(surface, BLACK, right_ear, 3)
    pygame.draw.polygon(surface, PINK, [
        (left_ear[0][0] + 3, left_ear[0][1] + 4),
        (left_ear[1][0] + 5, left_ear[1][1] + 6),
        (left_ear[2][0] + 2, left_ear[2][1] + 4),
    ])
    pygame.draw.polygon(surface, PINK, [
        (right_ear[0][0] - 3, right_ear[0][1] + 4),
        (right_ear[1][0] - 5, right_ear[1][1] + 6),
        (right_ear[2][0] - 2, right_ear[2][1] + 4),
    ])

    eye_radius = max(size // 13, 2)
    left_eye = (head_center[0] - size // 8, head_center[1] - size // 10)
    right_eye = (head_center[0] + size // 8, head_center[1] - size // 10)
    pygame.draw.ellipse(surface, BLACK, pygame.Rect(left_eye[0] - eye_radius, left_eye[1] - eye_radius, eye_radius * 2, eye_radius * 3))
    pygame.draw.ellipse(surface, BLACK, pygame.Rect(right_eye[0] - eye_radius, right_eye[1] - eye_radius, eye_radius * 2, eye_radius * 3))
    pygame.draw.circle(surface, WHITE, (left_eye[0] + eye_radius // 2, left_eye[1] - eye_radius // 2), max(size // 30, 1))
    pygame.draw.circle(surface, WHITE, (right_eye[0] + eye_radius // 2, right_eye[1] - eye_radius // 2), max(size // 30, 1))

    face_rect = pygame.Rect(head_center[0] - size // 10, head_center[1], size // 5, size // 6)
    pygame.draw.ellipse(surface, color, face_rect)
    pygame.draw.ellipse(surface, BLACK, face_rect, 2)

    nose = (head_center[0], head_center[1] + size // 16)
    pygame.draw.circle(surface, PINK, nose, max(size // 25, 2))
    whisker_y = nose[1] + 2
    for dx in (-1, 1):
        pygame.draw.line(surface, BLACK, (nose[0], whisker_y), (nose[0] + dx * (size // 3), whisker_y - 4), 2)
        pygame.draw.line(surface, BLACK, (nose[0], whisker_y + 6), (nose[0] + dx * (size // 3), whisker_y + 10), 2)

    mouth_start = (nose[0], nose[1] + 4)
    pygame.draw.arc(surface, BLACK, pygame.Rect(mouth_start[0] - 10, mouth_start[1], 10, 8), math.pi * 1.1, math.pi * 1.9, 2)
    pygame.draw.arc(surface, BLACK, pygame.Rect(mouth_start[0], mouth_start[1], 10, 8), math.pi * 1.1, math.pi * 1.9, 2)

    step = math.sin(frame * 2 * math.pi)
    leg_shift = int(step * size * 0.08)
    front_leg_x = x + size // 4
    back_leg_x = x + size * 3 // 4
    leg_top = body_rect.bottom - size // 10
    pygame.draw.ellipse(surface, color, pygame.Rect(front_leg_x - size // 16, leg_top, size // 8, size // 4))
    pygame.draw.ellipse(surface, color, pygame.Rect(front_leg_x + size // 10, leg_top, size // 8, size // 4))
    pygame.draw.ellipse(surface, color, pygame.Rect(back_leg_x - size // 4, leg_top, size // 8, size // 4))
    pygame.draw.ellipse(surface, color, pygame.Rect(back_leg_x - size // 8, leg_top, size // 8, size // 4))
    pygame.draw.ellipse(surface, BLACK, pygame.Rect(front_leg_x - size // 16, leg_top, size // 8, size // 4), 2)
    pygame.draw.ellipse(surface, BLACK, pygame.Rect(front_leg_x + size // 10, leg_top, size // 8, size // 4), 2)
    pygame.draw.ellipse(surface, BLACK, pygame.Rect(back_leg_x - size // 4, leg_top, size // 8, size // 4), 2)
    pygame.draw.ellipse(surface, BLACK, pygame.Rect(back_leg_x - size // 8, leg_top, size // 8, size // 4), 2)

    tail_offset = int(math.sin((frame + 0.25) * 2 * math.pi) * size * 0.12)
    tail_points = [
        (body_rect.right - 4, body_rect.centery),
        (body_rect.right + size // 6, body_rect.centery + tail_offset),
        (body_rect.right + size // 3, body_rect.centery + tail_offset * 2),
        (body_rect.right + size // 2, body_rect.centery + tail_offset * 2 - 4),
    ]
    pygame.draw.lines(surface, BLACK, False, tail_points, 8)


def draw_rat(surface, x, y, size, color, frame):
    body_rect = pygame.Rect(x + size // 8, y + size // 3, size * 3 // 4, size // 2)
    pygame.draw.ellipse(surface, color, body_rect)

    head_center = (x + size * 7 // 8, y + size // 2)
    pygame.draw.circle(surface, color, head_center, size // 5)
    pygame.draw.circle(surface, BLACK, (head_center[0] - size // 12, head_center[1] - size // 12), size // 15)
    pygame.draw.circle(surface, BLACK, (head_center[0] + size // 12, head_center[1] - size // 12), size // 15)
    pygame.draw.line(surface, BLACK, (head_center[0] - 4, head_center[1] + size // 20), (head_center[0] + 4, head_center[1] + size // 20), 2)

    left_ear = (head_center[0] - size // 12, head_center[1] - size // 5)
    right_ear = (head_center[0] + size // 12, head_center[1] - size // 5)
    pygame.draw.circle(surface, color, left_ear, size // 12)
    pygame.draw.circle(surface, color, right_ear, size // 12)
    pygame.draw.circle(surface, PINK, left_ear, size // 18)
    pygame.draw.circle(surface, PINK, right_ear, size // 18)

    tail_offset = int(math.sin(frame * 2 * math.pi) * size * 0.15)
    tail_points = [
        (x + size // 8, y + size * 11 // 16),
        (x - size // 6, y + size * 11 // 16 + tail_offset),
        (x - size // 4, y + size * 13 // 16),
    ]
    pygame.draw.lines(surface, BLACK, False, tail_points, 4)

    leg_y = y + size * 5 // 6
    pygame.draw.line(surface, BLACK, (x + size // 4, leg_y), (x + size // 4, leg_y + size // 8), 3)
    pygame.draw.line(surface, BLACK, (x + size // 2, leg_y), (x + size // 2, leg_y + size // 8), 3)
    pygame.draw.line(surface, BLACK, (x + size * 3 // 4, leg_y), (x + size * 3 // 4, leg_y + size // 8), 3)


def run_game():
    global player_x, player_y, enemy_x, enemy_y, enemy_speed_x, enemy_speed_y, score, player_anim_frame, enemy_anim_frame
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Player movement
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            player_x -= player_speed
        if keys[pygame.K_RIGHT]:
            player_x += player_speed
        if keys[pygame.K_UP]:
            player_y -= player_speed
        if keys[pygame.K_DOWN]:
            player_y += player_speed

        # Wrap player around the screen edges
        if player_x < -player_size:
            player_x = WIDTH
        elif player_x > WIDTH:
            player_x = -player_size
        if player_y < -player_size:
            player_y = HEIGHT
        elif player_y > HEIGHT:
            player_y = -player_size

        # Enemy auto movement (bouncing)
        enemy_x, enemy_y, enemy_speed_x, enemy_speed_y = move_enemy(
            enemy_x,
            enemy_y,
            enemy_speed_x,
            enemy_speed_y,
            WIDTH,
            HEIGHT,
            enemy_size,
        )

        player_anim_frame += player_anim_speed
        if player_anim_frame >= 1.0:
            player_anim_frame -= 1.0
        enemy_anim_frame += enemy_anim_speed
        if enemy_anim_frame >= 1.0:
            enemy_anim_frame -= 1.0

        # Collision detection
        if is_collision(player_x, player_y, player_size, enemy_x, enemy_y, enemy_size):
            score += 1
            play_hit_sound()
            # Respawn enemy at random place
            enemy_x = random.randint(0, WIDTH - enemy_size)
            enemy_y = random.randint(0, HEIGHT - enemy_size)

        # Draw
        screen.fill(WHITE)
        draw_cat(screen, player_x, player_y, player_size, CAT_COLOR, player_anim_frame)
        draw_rat(screen, enemy_x, enemy_y, enemy_size, RAT_GRAY, enemy_anim_frame)

        # Show score
        if font:
            score_text = font.render(f"Score: {score}", True, (0, 0, 0))
            screen.blit(score_text, (10, 10))
        else:
            draw_score(screen, score, 10, 10)

        pygame.display.flip()
        clock.tick(60)


def main():
    run_game()


if __name__ == "__main__":
    main()
