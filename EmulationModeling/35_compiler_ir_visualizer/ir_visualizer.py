"""Tiny imperative language parser that produces three-address code and a CFG."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple
import re


# -------------------------- Lexer --------------------------
@dataclass
class Token:
    type: str
    value: str

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"Token({self.type}, {self.value})"


def tokenize(source: str) -> List[Token]:
    token_specification: List[Tuple[str, str]] = [
        ("NUMBER", r"\d+"),
        ("ID", r"[A-Za-z_][A-Za-z0-9_]*"),
        ("OP", r"==|!=|<=|>=|[+\-*/<>]"),
        ("ASSIGN", r"="),
        ("LBRACE", r"\{"),
        ("RBRACE", r"\}"),
        ("LPAREN", r"\("),
        ("RPAREN", r"\)"),
        ("SEMICOLON", r";"),
        ("SKIP", r"[ \t]+"),
        ("NEWLINE", r"\n"),
        ("MISMATCH", r"."),
    ]
    tok_regex = "|".join(f"(?P<{name}>{pattern})" for name, pattern in token_specification)
    tokens: List[Token] = []
    for mo in re.finditer(tok_regex, source):
        kind = mo.lastgroup
        value = mo.group()
        if kind in {"NEWLINE", "SKIP"}:
            continue
        if kind == "MISMATCH":
            raise SyntaxError(f"Unexpected character: {value!r}")
        tokens.append(Token(kind, value))
    tokens.append(Token("EOF", ""))
    return tokens


# -------------------------- AST Nodes --------------------------
@dataclass
class Expr:
    pass


@dataclass
class Number(Expr):
    value: int


@dataclass
class Var(Expr):
    name: str


@dataclass
class BinOp(Expr):
    left: Expr
    op: str
    right: Expr


@dataclass
class Statement:
    pass


@dataclass
class Assign(Statement):
    target: str
    expr: Expr


@dataclass
class If(Statement):
    condition: Expr
    then_branch: List[Statement]
    else_branch: Optional[List[Statement]] = None


@dataclass
class While(Statement):
    condition: Expr
    body: List[Statement]


@dataclass
class Program:
    statements: List[Statement]


# -------------------------- Parser --------------------------
class TinyLangParser:
    def __init__(self, source: str):
        self.tokens = tokenize(source)
        self.pos = 0

    @property
    def current(self) -> Token:
        return self.tokens[self.pos]

    def advance(self) -> Token:
        token = self.current
        self.pos += 1
        return token

    def expect(self, token_type: str, value: Optional[str] = None) -> Token:
        token = self.current
        if token.type != token_type or (value is not None and token.value != value):
            raise SyntaxError(f"Expected {token_type} {value or ''} but got {token.type} {token.value}")
        return self.advance()

    def parse(self) -> Program:
        statements: List[Statement] = []
        while self.current.type != "EOF":
            statements.append(self.parse_statement())
        return Program(statements)

    def parse_statement(self) -> Statement:
        if self.current.type == "ID" and self._peek().type == "ASSIGN":
            return self.parse_assignment()
        if self.current.type == "ID" and self.current.value == "if":
            return self.parse_if()
        if self.current.type == "ID" and self.current.value == "while":
            return self.parse_while()
        raise SyntaxError(f"Unexpected token in statement: {self.current}")

    def parse_block(self) -> List[Statement]:
        self.expect("LBRACE")
        statements: List[Statement] = []
        while self.current.type != "RBRACE":
            statements.append(self.parse_statement())
        self.expect("RBRACE")
        return statements

    def parse_assignment(self) -> Assign:
        target = self.expect("ID").value
        self.expect("ASSIGN")
        expr = self.parse_expression()
        self.expect("SEMICOLON")
        return Assign(target, expr)

    def parse_if(self) -> If:
        self.expect("ID", "if")
        condition = self.parse_expression()
        then_branch = self.parse_block()
        else_branch: Optional[List[Statement]] = None
        if self.current.type == "ID" and self.current.value == "else":
            self.advance()
            else_branch = self.parse_block()
        return If(condition, then_branch, else_branch)

    def parse_while(self) -> While:
        self.expect("ID", "while")
        condition = self.parse_expression()
        body = self.parse_block()
        return While(condition, body)

    def parse_expression(self) -> Expr:
        return self.parse_equality()

    def parse_equality(self) -> Expr:
        node = self.parse_comparison()
        while self.current.type == "OP" and self.current.value in {"==", "!="}:
            op = self.advance().value
            right = self.parse_comparison()
            node = BinOp(node, op, right)
        return node

    def parse_comparison(self) -> Expr:
        node = self.parse_term()
        while self.current.type == "OP" and self.current.value in {"<", "<=", ">", ">="}:
            op = self.advance().value
            right = self.parse_term()
            node = BinOp(node, op, right)
        return node

    def parse_term(self) -> Expr:
        node = self.parse_factor()
        while self.current.type == "OP" and self.current.value in {"+", "-"}:
            op = self.advance().value
            right = self.parse_factor()
            node = BinOp(node, op, right)
        return node

    def parse_factor(self) -> Expr:
        node = self.parse_unary()
        while self.current.type == "OP" and self.current.value in {"*", "/"}:
            op = self.advance().value
            right = self.parse_unary()
            node = BinOp(node, op, right)
        return node

    def parse_unary(self) -> Expr:
        if self.current.type == "OP" and self.current.value == "-":
            self.advance()
            operand = self.parse_unary()
            return BinOp(Number(0), "-", operand)
        return self.parse_primary()

    def parse_primary(self) -> Expr:
        if self.current.type == "NUMBER":
            return Number(int(self.advance().value))
        if self.current.type == "ID" and self.current.value not in {"if", "else", "while"}:
            return Var(self.advance().value)
        if self.current.type == "LPAREN":
            self.advance()
            expr = self.parse_expression()
            self.expect("RPAREN")
            return expr
        raise SyntaxError(f"Unexpected token in expression: {self.current}")

    def _peek(self) -> Token:
        return self.tokens[self.pos + 1]


# -------------------------- Three-address code --------------------------
@dataclass
class TACInstruction:
    op: str
    arg1: Optional[str] = None
    arg2: Optional[str] = None
    result: Optional[str] = None
    label: Optional[str] = None

    def __str__(self) -> str:
        if self.op == "label":
            return f"{self.label}:"
        if self.op == "assign":
            return f"{self.result} = {self.arg1}"
        if self.op == "goto":
            return f"goto {self.label}"
        if self.op == "if_false":
            return f"if_false {self.arg1} goto {self.label}"
        if self.op == "print":
            return f"print {self.arg1}"
        if self.result:
            return f"{self.result} = {self.arg1} {self.op} {self.arg2}"
        return self.op


class IRBuilder:
    def __init__(self) -> None:
        self.temp_counter = 0
        self.label_counter = 0
        self.instructions: List[TACInstruction] = []

    def new_temp(self) -> str:
        self.temp_counter += 1
        return f"t{self.temp_counter}"

    def new_label(self, base: str) -> str:
        self.label_counter += 1
        return f"{base}_{self.label_counter}"

    def build(self, program: Program) -> List[TACInstruction]:
        for stmt in program.statements:
            self.emit_statement(stmt)
        return self.instructions

    def emit_statement(self, stmt: Statement) -> None:
        if isinstance(stmt, Assign):
            value = self.emit_expression(stmt.expr)
            self.instructions.append(TACInstruction("assign", arg1=value, result=stmt.target))
        elif isinstance(stmt, If):
            self.emit_if(stmt)
        elif isinstance(stmt, While):
            self.emit_while(stmt)
        else:
            raise TypeError(f"Unknown statement type: {type(stmt)}")

    def emit_if(self, stmt: If) -> None:
        else_label = self.new_label("else")
        end_label = self.new_label("endif")
        condition_temp = self.emit_expression(stmt.condition)
        self.instructions.append(TACInstruction("if_false", arg1=condition_temp, label=else_label))
        for inner in stmt.then_branch:
            self.emit_statement(inner)
        self.instructions.append(TACInstruction("goto", label=end_label))
        self.instructions.append(TACInstruction("label", label=else_label))
        if stmt.else_branch:
            for inner in stmt.else_branch:
                self.emit_statement(inner)
        self.instructions.append(TACInstruction("label", label=end_label))

    def emit_while(self, stmt: While) -> None:
        start_label = self.new_label("while")
        end_label = self.new_label("endwhile")
        self.instructions.append(TACInstruction("label", label=start_label))
        condition_temp = self.emit_expression(stmt.condition)
        self.instructions.append(TACInstruction("if_false", arg1=condition_temp, label=end_label))
        for inner in stmt.body:
            self.emit_statement(inner)
        self.instructions.append(TACInstruction("goto", label=start_label))
        self.instructions.append(TACInstruction("label", label=end_label))

    def emit_expression(self, expr: Expr) -> str:
        if isinstance(expr, Number):
            return str(expr.value)
        if isinstance(expr, Var):
            return expr.name
        if isinstance(expr, BinOp):
            left = self.emit_expression(expr.left)
            right = self.emit_expression(expr.right)
            temp = self.new_temp()
            self.instructions.append(TACInstruction(expr.op, arg1=left, arg2=right, result=temp))
            return temp
        raise TypeError(f"Unknown expression type: {type(expr)}")


# -------------------------- CFG builder --------------------------
@dataclass
class BasicBlock:
    name: str
    instructions: List[TACInstruction]
    successors: List[str]


def build_basic_blocks(instructions: List[TACInstruction]) -> List[BasicBlock]:
    blocks: List[BasicBlock] = []
    current_instrs: List[TACInstruction] = []
    current_label: Optional[str] = None
    unnamed_counter = 0

    def flush_block():
        nonlocal current_instrs, current_label, unnamed_counter
        if not current_instrs and current_label is None:
            return
        block_name = current_label or f"block_{unnamed_counter}"
        blocks.append(BasicBlock(block_name, current_instrs, []))
        unnamed_counter += 1
        current_instrs = []
        current_label = None

    for instr in instructions:
        if instr.op == "label":
            flush_block()
            current_label = instr.label
            continue
        if current_label is None and not current_instrs:
            current_label = f"block_{unnamed_counter}"
            unnamed_counter += 1
        current_instrs.append(instr)
        if instr.op in {"goto", "if_false"}:
            flush_block()
    flush_block()

    for idx, block in enumerate(blocks):
        if not block.instructions:
            continue
        last = block.instructions[-1]
        successors: List[str] = []
        if last.op == "goto" and last.label:
            successors.append(last.label)
        elif last.op == "if_false":
            if last.label:
                successors.append(last.label)
            if idx + 1 < len(blocks):
                successors.append(blocks[idx + 1].name)
        elif idx + 1 < len(blocks):
            successors.append(blocks[idx + 1].name)
        block.successors = successors
    return blocks


def cfg_to_dot(blocks: List[BasicBlock]) -> str:
    lines = ["digraph cfg {", "  node [shape=box, fontname=Courier];"]
    for block in blocks:
        body = "\\l".join(str(instr) for instr in block.instructions) + "\\l"
        lines.append(f'  "{block.name}" [label="{block.name}:\\l{body}"];')
    for block in blocks:
        for succ in block.successors:
            lines.append(f'  "{block.name}" -> "{succ}";')
    lines.append("}")
    return "\n".join(lines)
