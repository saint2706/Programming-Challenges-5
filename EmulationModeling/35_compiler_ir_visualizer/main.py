"""Demonstrate parsing and IR/CFG generation for a tiny imperative language."""

from ir_visualizer import IRBuilder, TinyLangParser, build_basic_blocks, cfg_to_dot


def run_example() -> None:
    program_text = """
    x = 0;
    y = 1;
    while x < 5 {
        y = y * 2;
        if y > 10 {
            y = y + 1;
        }
        x = x + 1;
    }
    """

    parser = TinyLangParser(program_text)
    ast = parser.parse()

    ir_builder = IRBuilder()
    instructions = ir_builder.build(ast)

    print("Three-address code instructions:\n")
    for instr in instructions:
        print(instr)

    blocks = build_basic_blocks(instructions)
    dot_output = cfg_to_dot(blocks)
    print("\nGraphviz DOT for the control flow graph:\n")
    print(dot_output)


if __name__ == "__main__":
    run_example()
