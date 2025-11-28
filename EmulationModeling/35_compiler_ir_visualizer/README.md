# Compiler IR Visualizer (Emulation/Modeling Challenge 35)

This challenge implements a small imperative language parser that emits three-address
code (TAC) and a control flow graph (CFG) visualization in Graphviz DOT format. The
language supports assignments, arithmetic expressions, `if/else` branches, and `while`
loops.

## What's inside?

- **`ir_visualizer.py`** — lexer, recursive-descent parser, TAC generator, and CFG builder.
- **`main.py`** — runs an example program end-to-end, printing TAC instructions and DOT output.

## Running the example

From the repository root:

```bash
cd EmulationModeling/35_compiler_ir_visualizer
python main.py
```

You should see three-address code instructions followed by a DOT graph you can render
with `dot -Tpng output.dot -o output.png` after copying the printed DOT into `output.dot`.
