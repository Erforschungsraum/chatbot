import ast
from graphviz import Digraph


def parse_python_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        tree = ast.parse(file.read())

    dot = Digraph(comment="Python Function Diagram")
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            dot.node(node.name, node.name)
    return dot

if __name__ == "__main__":
    diagram = parse_python_file("chatbot_command_v0.11.py")
    diagram.render("function_diagram", format="png", cleanup=True)
