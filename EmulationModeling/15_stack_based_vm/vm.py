"""A tiny stack-based virtual machine implementation."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Sequence


class OpCode(str, Enum):
    """Supported opcodes for the simple stack VM."""

    PUSH = "PUSH"
    POP = "POP"
    DUP = "DUP"
    SWAP = "SWAP"
    ADD = "ADD"
    SUB = "SUB"
    MUL = "MUL"
    DIV = "DIV"
    PRINT = "PRINT"
    JMP = "JMP"
    CJMP = "CJMP"
    LOAD = "LOAD"
    STORE = "STORE"
    HALT = "HALT"


@dataclass
class Instruction:
    """A single VM instruction with an optional argument."""

    opcode: OpCode
    argument: Any = None


class VirtualMachine:
    """A very small stack machine that executes a list of instructions."""

    def __init__(self, instructions: Sequence[Instruction]):
        self.instructions: List[Instruction] = list(instructions)
        self.ip: int = 0  # instruction pointer
        self.stack: List[Any] = []
        self.memory: Dict[str, Any] = {}
        self.outputs: List[Any] = []

    # Stack helpers -----------------------------------------------------
    def _pop(self) -> Any:
        if not self.stack:
            raise IndexError("Attempted to pop from an empty stack")
        return self.stack.pop()

    def _push(self, value: Any) -> None:
        self.stack.append(value)

    def _binary_op(self, func) -> None:
        right = self._pop()
        left = self._pop()
        try:
            result = func(left, right)
        except ZeroDivisionError as exc:  # pragma: no cover - safety
            raise ZeroDivisionError("Division by zero in VM") from exc
        self._push(result)

    # Execution ---------------------------------------------------------
    def step(self) -> bool:
        """Execute a single instruction. Returns False when halting."""

        if self.ip < 0 or self.ip >= len(self.instructions):
            return False

        instruction = self.instructions[self.ip]
        self.ip += 1

        opcode = instruction.opcode
        arg = instruction.argument

        if opcode is OpCode.PUSH:
            self._push(arg)
        elif opcode is OpCode.POP:
            self._pop()
        elif opcode is OpCode.DUP:
            self._push(self.stack[-1])
        elif opcode is OpCode.SWAP:
            if len(self.stack) < 2:
                raise IndexError("Need at least two values to swap")
            self.stack[-1], self.stack[-2] = self.stack[-2], self.stack[-1]
        elif opcode is OpCode.ADD:
            self._binary_op(lambda a, b: a + b)
        elif opcode is OpCode.SUB:
            self._binary_op(lambda a, b: a - b)
        elif opcode is OpCode.MUL:
            self._binary_op(lambda a, b: a * b)
        elif opcode is OpCode.DIV:
            self._binary_op(lambda a, b: a / b)
        elif opcode is OpCode.PRINT:
            value = self._pop()
            self.outputs.append(value)
            print(value)
        elif opcode is OpCode.LOAD:
            self._push(self.memory.get(arg, 0))
        elif opcode is OpCode.STORE:
            self.memory[arg] = self._pop()
        elif opcode is OpCode.JMP:
            self.ip = int(arg)
        elif opcode is OpCode.CJMP:
            condition = self._pop()
            if not condition:
                self.ip = int(arg)
        elif opcode is OpCode.HALT:
            return False
        else:  # pragma: no cover - unreachable with current enum
            raise ValueError(f"Unknown opcode: {opcode}")

        return True

    def run(self) -> List[Any]:
        """Run until completion and return any printed outputs."""

        while self.step():
            pass
        return self.outputs


__all__ = ["Instruction", "OpCode", "VirtualMachine"]
