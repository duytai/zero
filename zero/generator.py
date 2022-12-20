from .parser import *

def unroll_loop_statements(statement):
  if isinstance(statement, Block):
    return Block([unroll_loop_statements(x) for x in statement.statements])
  elif isinstance(statement, IfStatement):
    return IfStatement(
      statement.condition,
      unroll_loop_statements(statement.true_body),
      unroll_loop_statements(statement.false_body) if statement.false_body else None
    )
  elif isinstance(statement, ForStatement):
    num_unrolled = 2
    return Block([
      statement.init,
      Block(num_unrolled * [
        statement.condition,
        statement.body,
        statement.loop,
      ]),
      UnaryOperation(statement.condition, True, '!'),
    ])
  return statement

def count_if_statements(statement):
  if isinstance(statement, Block):
    for statement in statement.statements:
      yield from count_if_statements(statement)
  elif isinstance(statement, IfStatement):
    yield 1
    yield from count_if_statements(statement.true_body)
    if statement.false_body:
      yield from count_if_statements(statement.false_body)

def construct_execution_path(statement, path=[]):
  if isinstance(statement, Block):
    for statement in statement.statements:
      yield from construct_execution_path(statement, path)
  elif isinstance(statement, IfStatement):
    if path.pop():
      yield statement.condition
      yield from construct_execution_path(statement.true_body, path)
    else:
      yield UnaryOperation(statement.condition, True, '!')
      if statement.false_body:
        yield from construct_execution_path(statement.false_body, path)
  else:
    yield statement

def compute_visited_paths(statement):
  num_ifs = sum(count_if_statements(statement))
  visited_paths = [[]]
  for x in range(num_ifs):
    tmp = []
    for visited in visited_paths:
      true_branch = visited[::] + [True]
      false_branch = visited[::] + [False]
      tmp = tmp + [true_branch, false_branch]
    visited_paths = tmp
  return visited_paths

def compute_execution_paths(statement):
  statement = unroll_loop_statements(statement)
  for visited in compute_visited_paths(statement):
    yield list(construct_execution_path(statement, visited))

def generate_execution_paths(root):
  for contract in root.nodes:
    if isinstance(contract, ContractDefinition):
      resources = [x for x in contract.nodes if isinstance(x, VariableDeclaration)]
      for part in contract.nodes:
        if isinstance(part, FunctionDefinition):
          if part.body:
            for path in compute_execution_paths(part.body):
              yield resources, part.parameters, part.returns, path