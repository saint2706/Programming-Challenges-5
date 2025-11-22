#include <algorithm>
#include <cstdint>
#include <deque>
#include <functional>
#include <iostream>
#include <optional>
#include <queue>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

struct Instruction {
    enum Type { ADD, LOAD_IMM, SUB, JMP, HALT } type;
    uint8_t dst = 0;
    uint8_t src = 0;
    int32_t imm = 0;
};

// Five-stage pipeline (IF, ID, EX, MEM, WB) with simple forwarding.
class RiscPipelineSimulator {
  public:
    explicit RiscPipelineSimulator(std::vector<Instruction> program)
        : program(std::move(program)), pc(0), registers(8, 0), halted(false) {}

    void step() {
        if (halted) {
            return;
        }

        if (pc >= program.size()) {
            halted = true;
            return;
        }

        write_back();
        mem();
        execute();
        decode();
        fetch();
    }

    bool is_halted() const { return halted; }
    const std::vector<int32_t> &regs() const { return registers; }

  private:
    std::vector<Instruction> program;
    size_t pc;
    std::vector<int32_t> registers;
    bool halted;

    std::optional<Instruction> if_id;
    std::optional<Instruction> id_ex;
    std::optional<std::pair<Instruction, int32_t>> ex_mem;
    std::optional<std::pair<Instruction, int32_t>> mem_wb;

    void fetch() {
        if_id = program[pc++];
    }

    void decode() {
        if (!if_id)
            return;
        id_ex = if_id;
        if_id.reset();
    }

    void execute() {
        if (!id_ex)
            return;
        Instruction instr = *id_ex;
        id_ex.reset();

        auto reg_val = [&](uint8_t idx) {
            if (idx >= registers.size())
                throw std::runtime_error("register index out of range");
            if (mem_wb && mem_wb->first.dst == idx)
                return mem_wb->second; // forwarding
            if (ex_mem && ex_mem->first.dst == idx)
                return ex_mem->second;
            return registers[idx];
        };

        int32_t result = 0;
        switch (instr.type) {
        case Instruction::ADD:
            result = reg_val(instr.dst) + reg_val(instr.src);
            break;
        case Instruction::SUB:
            result = reg_val(instr.dst) - reg_val(instr.src);
            break;
        case Instruction::LOAD_IMM:
            result = instr.imm;
            break;
        case Instruction::JMP:
            pc = static_cast<size_t>(instr.imm);
            ex_mem.reset();
            mem_wb.reset();
            if_id.reset();
            id_ex.reset();
            return;
        case Instruction::HALT:
            halted = true;
            ex_mem.reset();
            mem_wb.reset();
            return;
        }

        ex_mem = std::make_pair(instr, result);
    }

    void mem() {
        if (!ex_mem)
            return;
        mem_wb = ex_mem;
        ex_mem.reset();
    }

    void write_back() {
        if (!mem_wb)
            return;
        const auto &instr = mem_wb->first;
        const int32_t value = mem_wb->second;
        switch (instr.type) {
        case Instruction::ADD:
        case Instruction::SUB:
        case Instruction::LOAD_IMM:
            registers[instr.dst] = value;
            break;
        case Instruction::JMP:
        case Instruction::HALT:
            break;
        }
        mem_wb.reset();
    }
};

#ifdef RISC_PIPELINE_DEMO
int main() {
    std::vector<Instruction> program = {
        {Instruction::LOAD_IMM, 0, 0, 5},  // r0 = 5
        {Instruction::LOAD_IMM, 1, 0, 3},  // r1 = 3
        {Instruction::ADD, 0, 1, 0},       // r0 = r0 + r1 = 8
        {Instruction::SUB, 0, 1, 0},       // r0 = 5
        {Instruction::HALT, 0, 0, 0},
    };

    RiscPipelineSimulator cpu(program);
    while (!cpu.is_halted()) {
        cpu.step();
    }

    std::cout << "Register 0: " << cpu.regs()[0] << "\n";
    return 0;
}
#endif
