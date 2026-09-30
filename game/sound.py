import math
from array import array

import pygame

# Sound effects are synthesized at startup so the project needs no audio
# asset files. If no audio device is available, every sound becomes a no-op.


class _Silent:
    def play(self):
        pass


def _tone(freqs, duration, volume=0.4):
    """Build a Sound that sweeps linearly through the given frequencies."""
    rate, size, channels = pygame.mixer.get_init()
    n = int(rate * duration)
    peak = (1 << (abs(size) - 1)) - 1
    samples = array("h")
    phase = 0.0
    for i in range(n):
        t = i / n
        # Interpolate across the frequency list for simple chirps/drops.
        pos = t * (len(freqs) - 1)
        lo = int(pos)
        hi = min(lo + 1, len(freqs) - 1)
        freq = freqs[lo] + (freqs[hi] - freqs[lo]) * (pos - lo)
        phase += 2 * math.pi * freq / rate
        # Short attack/release envelope avoids clicks.
        env = min(1.0, i / (rate * 0.005), (n - i) / (rate * 0.02))
        value = int(peak * volume * env * math.sin(phase))
        samples.extend([value] * channels)
    return pygame.mixer.Sound(buffer=samples.tobytes())


class SoundBank:
    def __init__(self):
        try:
            init = pygame.mixer.get_init()
            if not init or init[1] != -16:
                # Samples are built as signed 16-bit, so force that format.
                pygame.mixer.quit()
                pygame.mixer.init(frequency=44100, size=-16, channels=1)
            self.jump = _tone([400, 800], 0.12)
            self.score = _tone([880, 1320], 0.08, volume=0.3)
            self.game_over = _tone([440, 330, 220, 110], 0.6, volume=0.5)
        except pygame.error:
            self.jump = self.score = self.game_over = _Silent()
