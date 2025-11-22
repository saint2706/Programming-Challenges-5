#include <algorithm>
#include <array>
#include <cstdint>
#include <functional>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

// A small, testable subset of the original Game Boy CPU (Sharp LR35902).
// The goal is to provide a faithful stepping model with flag handling and
// basic memory access so unit tests can exercise instruction edge cases.
class MiniGameBoy {
  public:
    MiniGameBoy() { memory.fill(0); }

    void load_program(const std::vector<uint8_t> &program, uint16_t start = 0x0100) {
        if (program.size() + start > memory.size()) {
            throw std::runtime_error("program too large");
        }
        std::copy(program.begin(), program.end(), memory.begin() + start);
        pc = start;
        halted = false;
    }

    int step() {
        if (halted)
            return 4;
        const uint8_t opcode = fetch8();
        switch (opcode) {
        case 0x00: // NOP
            return 4;
        case 0x3E: // LD A, d8
            a = fetch8();
            set_flags(a == 0, false, false, false);
            return 8;
        case 0x06: // LD B, d8
            b = fetch8();
            return 8;
        case 0x0E: // LD C, d8
            c = fetch8();
            return 8;
        case 0x16: // LD D, d8
            d = fetch8();
            return 8;
        case 0x1E: // LD E, d8
            e = fetch8();
            return 8;
        case 0xAF: // XOR A
            a ^= a;
            set_flags(a == 0, false, false, false);
            return 4;
        case 0x76: // HALT
            halted = true;
            return 4;
        case 0x04: // INC B
            b = inc(b);
            return 4;
        case 0x0C: // INC C
            c = inc(c);
            return 4;
        case 0x05: // DEC B
            b = dec(b);
            return 4;
        case 0x0D: // DEC C
            c = dec(c);
            return 4;
        case 0x80: // ADD A, B
            add(a, b);
            return 4;
        case 0x81: // ADD A, C
            add(a, c);
            return 4;
        case 0x82: // ADD A, D
            add(a, d);
            return 4;
        case 0x83: // ADD A, E
            add(a, e);
            return 4;
        case 0x90: // SUB B
            sub(b);
            return 4;
        case 0x91: // SUB C
            sub(c);
            return 4;
        case 0x20: // JR NZ, r8
        {
            const int8_t offset = static_cast<int8_t>(fetch8());
            if (!flag_z()) {
                pc = static_cast<uint16_t>(pc + offset);
                return 12;
            }
            return 8;
        }
        case 0x18: // JR r8
        {
            const int8_t offset = static_cast<int8_t>(fetch8());
            pc = static_cast<uint16_t>(pc + offset);
            return 12;
        }
        case 0x32: // LD (HL-), A
        {
            const uint16_t addr = hl();
            write(addr, a);
            set_hl(addr - 1);
            return 8;
        }
        case 0x2A: // LD A, (HL+)
        {
            const uint16_t addr = hl();
            a = read(addr);
            set_hl(addr + 1);
            set_flags(a == 0, false, false, false);
            return 8;
        }
        case 0x21: // LD HL, d16
        {
            const uint16_t value = fetch16();
            set_hl(value);
            return 12;
        }
        case 0xC3: // JP a16
        {
            pc = fetch16();
            return 16;
        }
        default:
            throw std::runtime_error("Unsupported opcode: 0x" + hex_byte(opcode));
        }
    }

    uint8_t read(uint16_t addr) const { return memory[addr]; }
    void write(uint16_t addr, uint8_t value) { memory[addr] = value; }

    bool is_halted() const { return halted; }

    uint8_t reg_a() const { return a; }
    uint8_t reg_b() const { return b; }
    uint8_t reg_c() const { return c; }
    uint8_t reg_d() const { return d; }
    uint8_t reg_e() const { return e; }
    uint16_t reg_hl() const { return hl(); }
    void set_hl_public(uint16_t value) { set_hl(value); }

  private:
    std::array<uint8_t, 0x10000> memory{};
    uint16_t pc = 0x0100;
    uint8_t a = 0, b = 0, c = 0, d = 0, e = 0, h = 0, l = 0, f = 0;
    bool halted = false;

    uint8_t fetch8() { return memory.at(pc++); }

    uint16_t fetch16() {
        uint16_t low = fetch8();
        uint16_t high = fetch8();
        return static_cast<uint16_t>((high << 8) | low);
    }

    uint16_t hl() const { return static_cast<uint16_t>((h << 8) | l); }
    void set_hl(uint16_t value) {
        h = static_cast<uint8_t>(value >> 8);
        l = static_cast<uint8_t>(value & 0xFF);
    }

    bool flag_z() const { return f & 0x80; }
    bool flag_n() const { return f & 0x40; }
    bool flag_h() const { return f & 0x20; }
    bool flag_c() const { return f & 0x10; }

    void set_flags(bool z, bool n, bool hflag, bool cflag) {
        f = 0;
        if (z)
            f |= 0x80;
        if (n)
            f |= 0x40;
        if (hflag)
            f |= 0x20;
        if (cflag)
            f |= 0x10;
    }

    uint8_t inc(uint8_t value) {
        const uint8_t result = static_cast<uint8_t>(value + 1);
        const bool half = (value & 0x0F) == 0x0F;
        set_flags(result == 0, false, half, flag_c());
        return result;
    }

    uint8_t dec(uint8_t value) {
        const uint8_t result = static_cast<uint8_t>(value - 1);
        const bool half = (value & 0x0F) == 0x00;
        set_flags(result == 0, true, half, flag_c());
        return result;
    }

    void add(uint8_t &lhs, uint8_t rhs) {
        const uint16_t result = lhs + rhs;
        const bool half = ((lhs & 0x0F) + (rhs & 0x0F)) > 0x0F;
        lhs = static_cast<uint8_t>(result & 0xFF);
        set_flags(lhs == 0, false, half, result > 0xFF);
    }

    void sub(uint8_t rhs) {
        const uint16_t result = static_cast<uint16_t>(a) - rhs;
        const bool half = (a & 0x0F) < (rhs & 0x0F);
        a = static_cast<uint8_t>(result & 0xFF);
        set_flags(a == 0, true, half, a > result); // carry flag is borrow
    }

    static std::string hex_byte(uint8_t value) {
        constexpr char hex[] = "0123456789ABCDEF";
        std::string out;
        out.push_back(hex[value >> 4]);
        out.push_back(hex[value & 0xF]);
        return out;
    }
};

#ifdef GAMEBOY_CORE_DEMO
int main() {
    MiniGameBoy cpu;
    std::vector<uint8_t> program = {
        0x3E, 0x05, // LD A,5
        0x06, 0x03, // LD B,3
        0x80,       // ADD A,B -> A=8
        0x20, 0x02, // JR NZ, +2
        0x0E, 0x00, // (skipped) LD C,0
        0x32,       // LD (HL-),A
        0x76        // HALT
    };
    cpu.load_program(program);
    cpu.set_hl_public(0xC000);

    int guard = 0;
    while (!cpu.is_halted() && guard++ < 32) {
        cpu.step();
    }

    std::cout << "Register A: " << static_cast<int>(cpu.reg_a()) << "\n";
    std::cout << "Memory[0xBFFF]: " << static_cast<int>(cpu.read(0xBFFF)) << "\n";
    return 0;
}
#endif
