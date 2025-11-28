"""
Emulation/Modeling project implementation.
"""

import sys
import time
import pygame
from cpu import Chip8
from display import Display
from keypad import Keypad

def main():
    """
    Docstring for main.
    """
    if len(sys.argv) < 2:
        print("Usage: python main.py <rom_path>")
        print("Running internal test ROM (IBM Logo imitation)...")
        # Creating a fake ROM that draws a sprite
        # 0x00E0 (CLS)
        # 0x6000 (LD V0, 0)
        # 0x6100 (LD V1, 0)
        # 0xA20A (LD I, 0x20A) -> Address of sprite data (after program)
        # 0xD015 (DRW V0, V1, 5) -> Draw 5-byte sprite at (0,0)
        # 0x1208 (JP 0x208) -> Infinite loop
        # Data: 0xF0, 0x90, 0xF0, 0x90, 0xF0 (Number 8)

        program = [
            0x00, 0xE0,
            0x60, 0x00,
            0x61, 0x00,
            0xA2, 0x0C,
            0xD0, 0x15,
            0x12, 0x08,
            0xF0, 0x90, 0xF0, 0x90, 0xF0
        ]
        with open("test.ch8", "wb") as f:
            f.write(bytearray(program))
        rom_path = "test.ch8"
    else:
        rom_path = sys.argv[1]

    cpu = Chip8()
    cpu.load_rom(rom_path)

    display = Display(scale=15)
    keypad = Keypad()

    clock = pygame.time.Clock()

    running = True
    while running:
        # CHIP-8 usually runs around 500-700Hz.
        # We can do multiple CPU cycles per frame (60Hz).
        # 10 cycles * 60 fps = 600 Hz
        for _ in range(10):
            cpu.cycle()

        cpu.update_timers()

        if cpu.draw_flag:
            display.draw(cpu.display)
            cpu.draw_flag = False

        running = keypad.process_input(cpu.keypad)
        clock.tick(60)

    display.quit()

if __name__ == "__main__":
    main()
