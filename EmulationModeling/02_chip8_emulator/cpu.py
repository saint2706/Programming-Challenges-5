"""
Emulation/Modeling project implementation.
"""

import random
import pygame

class Chip8:
    """
    Docstring for Chip8.
    """
    def __init__(self):
        """
        Docstring for __init__.
        """
        self.memory = [0] * 4096
        self.registers = [0] * 16  # V0 to VF
        self.I = 0
        self.pc = 0x200
        self.stack = []
        self.delay_timer = 0
        self.sound_timer = 0

        # 64x32 display (1-bit)
        self.display = [0] * (64 * 32)

        # Keypad (0-F)
        self.keypad = [0] * 16

        self.draw_flag = False

        # Fontset (0-F)
        self.fontset = [
            0xF0, 0x90, 0x90, 0x90, 0xF0, # 0
            0x20, 0x60, 0x20, 0x20, 0x70, # 1
            0xF0, 0x10, 0xF0, 0x80, 0xF0, # 2
            0xF0, 0x10, 0xF0, 0x10, 0xF0, # 3
            0x90, 0x90, 0xF0, 0x10, 0x10, # 4
            0xF0, 0x80, 0xF0, 0x10, 0xF0, # 5
            0xF0, 0x80, 0xF0, 0x90, 0xF0, # 6
            0xF0, 0x10, 0x20, 0x40, 0x40, # 7
            0xF0, 0x90, 0xF0, 0x90, 0xF0, # 8
            0xF0, 0x90, 0xF0, 0x10, 0xF0, # 9
            0xF0, 0x90, 0xF0, 0x90, 0x90, # A
            0xE0, 0x90, 0xE0, 0x90, 0xE0, # B
            0xF0, 0x80, 0x80, 0x80, 0xF0, # C
            0xE0, 0x90, 0x90, 0x90, 0xE0, # D
            0xF0, 0x80, 0xF0, 0x80, 0xF0, # E
            0xF0, 0x80, 0xF0, 0x80, 0x80  # F
        ]

        # Load fontset into memory (0x000-0x050)
        for i in range(len(self.fontset)):
            self.memory[i] = self.fontset[i]

    def load_rom(self, filepath):
        """
        Docstring for load_rom.
        """
        with open(filepath, "rb") as f:
            rom_data = f.read()

        for i, byte in enumerate(rom_data):
            if 0x200 + i < 4096:
                self.memory[0x200 + i] = byte

    def cycle(self):
        # Fetch opcode
        """
        Docstring for cycle.
        """
        opcode = (self.memory[self.pc] << 8) | self.memory[self.pc + 1]

        # Decode and Execute
        self.pc += 2

        # Extract common variables
        x = (opcode & 0x0F00) >> 8
        y = (opcode & 0x00F0) >> 4
        n = opcode & 0x000F
        nn = opcode & 0x00FF
        nnn = opcode & 0x0FFF

        if opcode == 0x00E0: # CLS
            self.display = [0] * (64 * 32)
            self.draw_flag = True
        elif opcode == 0x00EE: # RET
            self.pc = self.stack.pop()
        elif (opcode & 0xF000) == 0x1000: # JP addr
            self.pc = nnn
        elif (opcode & 0xF000) == 0x2000: # CALL addr
            self.stack.append(self.pc)
            self.pc = nnn
        elif (opcode & 0xF000) == 0x3000: # SE Vx, byte
            if self.registers[x] == nn:
                self.pc += 2
        elif (opcode & 0xF000) == 0x4000: # SNE Vx, byte
            if self.registers[x] != nn:
                self.pc += 2
        elif (opcode & 0xF000) == 0x5000: # SE Vx, Vy
            if self.registers[x] == self.registers[y]:
                self.pc += 2
        elif (opcode & 0xF000) == 0x6000: # LD Vx, byte
            self.registers[x] = nn
        elif (opcode & 0xF000) == 0x7000: # ADD Vx, byte
            self.registers[x] = (self.registers[x] + nn) & 0xFF
        elif (opcode & 0xF000) == 0x8000:
            if n == 0x0: # LD Vx, Vy
                self.registers[x] = self.registers[y]
            elif n == 0x1: # OR Vx, Vy
                self.registers[x] |= self.registers[y]
            elif n == 0x2: # AND Vx, Vy
                self.registers[x] &= self.registers[y]
            elif n == 0x3: # XOR Vx, Vy
                self.registers[x] ^= self.registers[y]
            elif n == 0x4: # ADD Vx, Vy
                sum_val = self.registers[x] + self.registers[y]
                self.registers[0xF] = 1 if sum_val > 255 else 0
                self.registers[x] = sum_val & 0xFF
            elif n == 0x5: # SUB Vx, Vy
                self.registers[0xF] = 1 if self.registers[x] > self.registers[y] else 0
                self.registers[x] = (self.registers[x] - self.registers[y]) & 0xFF
            elif n == 0x6: # SHR Vx {, Vy}
                # Standard Chip8: VF = LSB, then shift right
                self.registers[0xF] = self.registers[x] & 0x1
                self.registers[x] >>= 1
            elif n == 0x7: # SUBN Vx, Vy
                self.registers[0xF] = 1 if self.registers[y] > self.registers[x] else 0
                self.registers[x] = (self.registers[y] - self.registers[x]) & 0xFF
            elif n == 0xE: # SHL Vx {, Vy}
                # Standard Chip8: VF = MSB, then shift left
                self.registers[0xF] = (self.registers[x] & 0x80) >> 7
                self.registers[x] = (self.registers[x] << 1) & 0xFF
        elif (opcode & 0xF000) == 0x9000: # SNE Vx, Vy
            if self.registers[x] != self.registers[y]:
                self.pc += 2
        elif (opcode & 0xF000) == 0xA000: # LD I, addr
            self.I = nnn
        elif (opcode & 0xF000) == 0xB000: # JP V0, addr
            self.pc = (nnn + self.registers[0]) & 0xFFF
        elif (opcode & 0xF000) == 0xC000: # RND Vx, byte
            self.registers[x] = random.randint(0, 255) & nn
        elif (opcode & 0xF000) == 0xD000: # DRW Vx, Vy, nibble
            x_pos = self.registers[x]
            y_pos = self.registers[y]
            height = n
            self.registers[0xF] = 0

            for row in range(height):
                pixel = self.memory[self.I + row]
                for col in range(8):
                    if (pixel & (0x80 >> col)) != 0:
                        idx = (x_pos + col + ((y_pos + row) * 64))
                        # Wrap handling (simple or clipping? Standard is usually wrapping x/y individually)
                        # Correct logic:
                        screen_x = (x_pos + col) % 64
                        screen_y = (y_pos + row) % 32
                        idx = screen_x + (screen_y * 64)

                        if self.display[idx] == 1:
                            self.registers[0xF] = 1
                        self.display[idx] ^= 1
            self.draw_flag = True
        elif (opcode & 0xF000) == 0xE000:
            if nn == 0x9E: # SKP Vx
                if self.keypad[self.registers[x]] != 0:
                    self.pc += 2
            elif nn == 0xA1: # SKNP Vx
                if self.keypad[self.registers[x]] == 0:
                    self.pc += 2
        elif (opcode & 0xF000) == 0xF000:
            if nn == 0x07: # LD Vx, DT
                self.registers[x] = self.delay_timer
            elif nn == 0x0A: # LD Vx, K (Wait for key)
                key_pressed = False
                for i in range(16):
                    if self.keypad[i] != 0:
                        self.registers[x] = i
                        key_pressed = True
                if not key_pressed:
                    self.pc -= 2 # Decrement PC to repeat instruction
            elif nn == 0x15: # LD DT, Vx
                self.delay_timer = self.registers[x]
            elif nn == 0x18: # LD ST, Vx
                self.sound_timer = self.registers[x]
            elif nn == 0x1E: # ADD I, Vx
                self.I = (self.I + self.registers[x]) & 0xFFF # Some interpreters overflow, some don't.
            elif nn == 0x29: # LD F, Vx
                self.I = self.registers[x] * 5
            elif nn == 0x33: # LD B, Vx
                self.memory[self.I] = self.registers[x] // 100
                self.memory[self.I + 1] = (self.registers[x] % 100) // 10
                self.memory[self.I + 2] = self.registers[x] % 10
            elif nn == 0x55: # LD [I], Vx
                for i in range(x + 1):
                    self.memory[self.I + i] = self.registers[i]
            elif nn == 0x65: # LD Vx, [I]
                for i in range(x + 1):
                    self.registers[i] = self.memory[self.I + i]

    def update_timers(self):
        """
        Docstring for update_timers.
        """
        if self.delay_timer > 0:
            self.delay_timer -= 1
        if self.sound_timer > 0:
            self.sound_timer -= 1
            if self.sound_timer == 0:
                # Play sound (not implemented)
                pass
