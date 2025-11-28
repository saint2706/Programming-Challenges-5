# Tiny Stack-Based Virtual Machine (Emulation/Modeling Challenge 15)

This challenge introduces a compact stack-oriented virtual machine written in Python. The VM executes a list of instructions, maintains an instruction pointer, and uses a data stack plus a simple key/value memory for temporary storage. Arithmetic, stack manipulation, and branching opcodes allow you to express small programs such as loops or conditionals.

## Supported opcodes

- `PUSH <value>`: push a literal onto the stack.
- `POP`: remove the top of the stack.
- `DUP`: duplicate the top stack value.
- `SWAP`: swap the top two stack values.
- `ADD`, `SUB`, `MUL`, `DIV`: binary arithmetic operators.
- `STORE <name>` / `LOAD <name>`: move data between the stack and a simple dictionary.
- `PRINT`: pop and print the top of the stack (also recorded in `VirtualMachine.outputs`).
- `JMP <index>`: jump to an instruction index.
- `CJMP <index>`: conditional jump based on the popped top value (jump if falsy).
- `HALT`: stop execution.

## Example program

`main.py` assembles a small factorial program (5!) to demonstrate arithmetic and control flow:

1. Initialize `counter = 5` and `result = 1`.
2. Loop while `counter` is non-zero, multiplying `result` by `counter` and decrementing `counter`.
3. Print the final factorial.

Run it with:

```bash
cd EmulationModeling/15_stack_based_vm
python main.py
```

You should see `120` printed to the console.
