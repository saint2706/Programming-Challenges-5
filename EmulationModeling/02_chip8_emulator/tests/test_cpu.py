"""
Emulation/Modeling project implementation.
"""

import unittest
from cpu import Chip8

class TestChip8CPU(unittest.TestCase):
    """
    Docstring for TestChip8CPU.
    """
    def setUp(self):
        """
        Docstring for setUp.
        """
        self.cpu = Chip8()

    def test_initial_state(self):
        """
        Docstring for test_initial_state.
        """
        self.assertEqual(self.cpu.pc, 0x200)
        self.assertEqual(len(self.cpu.memory), 4096)
        self.assertEqual(len(self.cpu.registers), 16)

    def test_opcode_6xkk_ld_vx_byte(self):
        # 0x60FF -> LD V0, 0xFF
        """
        Docstring for test_opcode_6xkk_ld_vx_byte.
        """
        self.cpu.memory[0x200] = 0x60
        self.cpu.memory[0x201] = 0xFF
        self.cpu.cycle()
        self.assertEqual(self.cpu.registers[0], 0xFF)
        self.assertEqual(self.cpu.pc, 0x202)

    def test_opcode_7xkk_add_vx_byte(self):
        # 0x6101 -> LD V1, 0x01
        # 0x7101 -> ADD V1, 0x01
        """
        Docstring for test_opcode_7xkk_add_vx_byte.
        """
        self.cpu.memory[0x200] = 0x61
        self.cpu.memory[0x201] = 0x01
        self.cpu.memory[0x202] = 0x71
        self.cpu.memory[0x203] = 0x01

        self.cpu.cycle()
        self.assertEqual(self.cpu.registers[1], 1)

        self.cpu.cycle()
        self.assertEqual(self.cpu.registers[1], 2)

    def test_opcode_8xy4_add_vx_vy_carry(self):
        # V0 = 0xFF, V1 = 0x01
        """
        Docstring for test_opcode_8xy4_add_vx_vy_carry.
        """
        self.cpu.registers[0] = 0xFF
        self.cpu.registers[1] = 0x01

        # 0x8014 -> ADD V0, V1
        self.cpu.memory[0x200] = 0x80
        self.cpu.memory[0x201] = 0x14

        self.cpu.cycle()
        self.assertEqual(self.cpu.registers[0], 0x00) # Overflow wrapped
        self.assertEqual(self.cpu.registers[0xF], 1) # Carry flag set

    def test_opcode_2nnn_call_and_00ee_ret(self):
        # 0x2300 -> CALL 0x300
        """
        Docstring for test_opcode_2nnn_call_and_00ee_ret.
        """
        self.cpu.memory[0x200] = 0x23
        self.cpu.memory[0x201] = 0x00

        # 0x300: 0x00EE -> RET
        self.cpu.memory[0x300] = 0x00
        self.cpu.memory[0x301] = 0xEE

        self.cpu.cycle()
        self.assertEqual(self.cpu.pc, 0x300)
        self.assertEqual(self.cpu.stack[0], 0x202)

        self.cpu.cycle()
        self.assertEqual(self.cpu.pc, 0x202)
        self.assertEqual(len(self.cpu.stack), 0)

if __name__ == '__main__':
    unittest.main()
