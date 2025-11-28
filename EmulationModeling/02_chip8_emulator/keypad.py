"""
Emulation/Modeling project implementation.
"""

import pygame

class Keypad:
    """
    Docstring for Keypad.
    """
    def __init__(self):
        # Map QWERTY keys to CHIP-8 HEX keys
        # 1 2 3 4 -> 1 2 3 C
        # Q W E R -> 4 5 6 D
        # A S D F -> 7 8 9 E
        # Z X C V -> A 0 B F
        """
        Docstring for __init__.
        """
        self.key_map = {
            pygame.K_1: 0x1, pygame.K_2: 0x2, pygame.K_3: 0x3, pygame.K_4: 0xC,
            pygame.K_q: 0x4, pygame.K_w: 0x5, pygame.K_e: 0x6, pygame.K_r: 0xD,
            pygame.K_a: 0x7, pygame.K_s: 0x8, pygame.K_d: 0x9, pygame.K_f: 0xE,
            pygame.K_z: 0xA, pygame.K_x: 0x0, pygame.K_c: 0xB, pygame.K_v: 0xF
        }

    def process_input(self, cpu_keypad):
        """
        Docstring for process_input.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key in self.key_map:
                    cpu_keypad[self.key_map[event.key]] = 1
                if event.key == pygame.K_ESCAPE:
                    return False

            if event.type == pygame.KEYUP:
                if event.key in self.key_map:
                    cpu_keypad[self.key_map[event.key]] = 0

        return True
