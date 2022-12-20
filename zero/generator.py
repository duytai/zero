from .parser import *

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

def compute_execution_paths(statement):
  num_ifs = sum(count_if_statements(statement))
  visited_paths = [[]]
  for x in range(num_ifs):
    tmp = []
    for visited in visited_paths:
      true_branch = visited[::] + [True]
      false_branch = visited[::] + [False]
      tmp = tmp + [true_branch, false_branch]
    visited_paths = tmp
  for visited in visited_paths:
    yield list(construct_execution_path(statement, visited))
  # handle loop

def generate_execution_paths(root):
  for contract in root.nodes:
    if isinstance(contract, ContractDefinition):
      for func in contract.nodes:
        if isinstance(func, FunctionDefinition):
          if func.body:
            for path in compute_execution_paths(func.body):
              yield func.parameters, func.returns, path