import pygame
from .player import Player
from .obstacle import Obstacle
from .sound import SoundBank

# Game Engine

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BROWN = (120, 80, 40)
DARK_GREEN = (30, 100, 30)

# Starting speed, frames between spawns, and the speed ceiling per difficulty.
DIFFICULTIES = {
    "Easy":   {"speed": 5, "spawn_interval": 90, "max_speed": 12},
    "Medium": {"speed": 6, "spawn_interval": 70, "max_speed": 15},
    "Hard":   {"speed": 8, "spawn_interval": 55, "max_speed": 18},
}

DIFFICULTY_KEYS = {
    pygame.K_1: "Easy", pygame.K_e: "Easy",
    pygame.K_2: "Medium", pygame.K_m: "Medium",
    pygame.K_3: "Hard", pygame.K_h: "Hard",
}

class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.ground_y = height - 40

        self.font = pygame.font.SysFont("Arial", 30)
        self.big_font = pygame.font.SysFont("Arial", 56, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 22)
        self.sounds = SoundBank()
        self.quit_requested = False

        self.reset("Medium")

    def reset(self, difficulty):
        settings = DIFFICULTIES[difficulty]
        self.difficulty = difficulty

        self.player = Player(80, self.ground_y)

        self.speed = settings["speed"]
        self.speed_increase_per_frame = 0.003
        # Ceiling on speed so the game stays playable on long runs.
        self.max_speed = settings["max_speed"]

        self.spawn_interval = settings["spawn_interval"]  # frames between obstacle spawns
        self._spawn_timer = 0
        self.obstacles = []

        self.distance = 0
        self.score = 0
        self.game_over = False

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if self.game_over:
            if event.key in DIFFICULTY_KEYS:
                self.reset(DIFFICULTY_KEYS[event.key])
            elif event.key in (pygame.K_ESCAPE, pygame.K_q):
                self.quit_requested = True
            return

        if event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
            if self.player.jump():
                self.sounds.jump.play()

    def handle_input(self):
        # Reserved for continuously-held-key input; this runner only
        # needs an edge-triggered jump, handled in handle_event.
        pass

    def update(self):
        if self.game_over:
            return

        self.speed = min(self.speed + self.speed_increase_per_frame, self.max_speed)
        self.player.update()

        self._spawn_timer += 1
        if self._spawn_timer >= self.spawn_interval:
            self._spawn_timer = 0
            self.obstacles.append(Obstacle(self.width, self.ground_y, self.speed))

        for obstacle in self.obstacles:
            obstacle.speed = self.speed
            obstacle.move()

        # Swept collision: test the full horizontal span each obstacle
        # covered this frame, so a fast obstacle can't jump past the
        # player between two frames without registering a hit.
        player_rect = self.player.rect()
        for obstacle in self.obstacles:
            if obstacle.swept_rect().colliderect(player_rect):
                self.game_over = True
                self.sounds.game_over.play()
                return

        for obstacle in self.obstacles:
            if not obstacle.scored and obstacle.x + obstacle.width < self.player.x:
                obstacle.scored = True
                self.score += 1
                self.sounds.score.play()

        self.obstacles = [o for o in self.obstacles if not o.off_screen()]

        self.distance += self.speed

    def render(self, screen):
        pygame.draw.line(screen, BROWN, (0, self.ground_y), (self.width, self.ground_y), 4)

        pygame.draw.rect(screen, WHITE, self.player.rect())
        for obstacle in self.obstacles:
            pygame.draw.rect(screen, DARK_GREEN, obstacle.rect())

        score_text = self.font.render(f"Score: {self.score}", True, BLACK)
        screen.blit(score_text, (10, 10))
        diff_text = self.small_font.render(self.difficulty, True, BLACK)
        screen.blit(diff_text, (self.width - diff_text.get_width() - 10, 14))

        if self.game_over:
            self._render_game_over(screen)

    def _render_game_over(self, screen):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))

        lines = [
            (self.big_font, "GAME OVER", 110),
            (self.font, f"Final score: {self.score}", 175),
            (self.small_font, "Play again:  1 Easy   2 Medium   3 Hard", 240),
            (self.small_font, "Esc / Q to quit", 275),
        ]
        for font, text, y in lines:
            surf = font.render(text, True, WHITE)
            screen.blit(surf, surf.get_rect(center=(self.width // 2, y)))
