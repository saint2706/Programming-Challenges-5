#include <array>
#include <cstdint>
#include <functional>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

// Minimal subset of a Game Boy style CPU for educational purposes.
class MiniGameBoy {
  public:
    MiniGameBoy() { memory.fill(0); }

    void load_program(const std::vector<uint8_t> &program, uint16_t start = 0x0100) {
        if (program.size() + start > memory.size()) {
            throw std::runtime_error("program too large");
        }
        std::copy(program.begin(), program.end(), memory.begin() + start);
        pc = start;
    }

    // Execute a single instruction and return consumed cycles.
    int step() {
        if (halted) {
            return 4; // pretend we burn cycles while halted
        }

        const uint8_t opcode = fetch8();
        switch (opcode) {
        case 0x00: // NOP
            return 4;
        case 0x3E: // LD A, d8
            a = fetch8();
            return 8;
        case 0x06: // LD B, d8
            b = fetch8();
            return 8;
        case 0x0E: // LD C, d8
            c = fetch8();
            return 8;
        case 0x80: // ADD A, B
            add(a, b);
            return 4;
        case 0x81: // ADD A, C
            add(a, c);
            return 4;
        case 0xAF: // XOR A
            a ^= a;
            update_zero(a);
            return 4;
        case 0xC3: // JP a16
        {
            const uint16_t target = fetch16();
            pc = target;
            return 16;
        }
        case 0x76: // HALT
            halted = true;
            return 4;
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

  private:
    std::array<uint8_t, 0x10000> memory{};
    uint16_t pc = 0x0100;
    uint8_t a = 0, b = 0, c = 0;
    bool zero_flag = false;
    bool carry_flag = false;
    bool halted = false;

    uint8_t fetch8() { return memory[pc++]; }

    uint16_t fetch16() {
        uint16_t value = memory[pc] | (memory[pc + 1] << 8);
        pc += 2;
        return value;
    }

    void add(uint8_t &lhs, uint8_t rhs) {
        uint16_t result = lhs + rhs;
        lhs = static_cast<uint8_t>(result & 0xFF);
        zero_flag = lhs == 0;
        carry_flag = result > 0xFF;
    }

    void update_zero(uint8_t value) { zero_flag = value == 0; }

    static std::string hex_byte(uint8_t value) {
        constexpr char hex[] = "0123456789ABCDEF";
        std::string out = "";
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
        0x76        // HALT
    };
    cpu.load_program(program);

    while (!cpu.is_halted()) {
        cpu.step();
    }

    std::cout << "Register A: " << static_cast<int>(cpu.reg_a()) << "\n";
    return 0;
}
#endif
