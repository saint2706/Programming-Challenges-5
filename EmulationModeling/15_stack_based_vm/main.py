"""
Emulation/Modeling project implementation.
"""

from vm import Instruction, OpCode, VirtualMachine


# Factorial of 5 using stack operations, arithmetic, and control flow.
example_program = [
    Instruction(OpCode.PUSH, 5),          # Initialize counter = 5
    Instruction(OpCode.STORE, "counter"),
    Instruction(OpCode.PUSH, 1),          # Initialize result = 1
    Instruction(OpCode.STORE, "result"),

    # loop_start @ index 4
    Instruction(OpCode.LOAD, "counter"),  # Push counter to check termination
    Instruction(OpCode.CJMP, 15),          # If counter == 0, jump to end
    Instruction(OpCode.LOAD, "result"),
    Instruction(OpCode.LOAD, "counter"),
    Instruction(OpCode.MUL),               # result *= counter
    Instruction(OpCode.STORE, "result"),

    Instruction(OpCode.LOAD, "counter"),
    Instruction(OpCode.PUSH, 1),
    Instruction(OpCode.SUB),               # counter -= 1
    Instruction(OpCode.STORE, "counter"),
    Instruction(OpCode.JMP, 4),            # Jump back to loop start

    # end @ index 15
    Instruction(OpCode.LOAD, "result"),
    Instruction(OpCode.PRINT),
    Instruction(OpCode.HALT),
]


if __name__ == "__main__":
    vm = VirtualMachine(example_program)
    vm.run()
