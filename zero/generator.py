from .parser import *

def to_assume(arguments):
  return ExpressionStatement(
    FunctionCall('functionCall', Identifier('assume'), arguments)
  )

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
    ## Heuristic to unroll
    if isinstance(statement.condition, BinaryOperation):
      if isinstance(statement.condition.right_expression, Literal):
        num_unrolled = int(statement.condition.right_expression.value)
    return Block([
      statement.init,
      Block(num_unrolled * [
        to_assume([statement.condition]),
        statement.body,
        statement.loop,
      ]),
      to_assume([UnaryOperation(statement.condition, True, '!')])
    ])
  return statement

def use_loop_invariant(statement):
  if isinstance(statement, Block):
    return Block([use_loop_invariant(x) for x in statement.statements])
  elif isinstance(statement, IfStatement):
    return IfStatement(
      statement.condition,
      use_loop_invariant(statement.true_body),
      use_loop_invariant(statement.false_body) if statement.false_body else None
    )
  elif isinstance(statement, ForStatement):
    stmt = statement.body.statements[0]
    if isinstance(stmt, ExpressionStatement):
      if isinstance(stmt.expression, FunctionCall):
        if isinstance(stmt.expression.expression, Identifier):
          if stmt.expression.expression.name == 'assume':
            init = VariableDeclarationStatement(
              statement.init.declarations,
              Anything(statement.init.declarations[0].type_name)
            )
            return Block([init, stmt, to_assume([UnaryOperation(statement.condition, True, '!')])])
    raise ValueError('Loop invariant ?')
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
      yield to_assume([statement.condition])
      yield from construct_execution_path(statement.true_body, path)
    else:
      yield to_assume([UnaryOperation(statement.condition, True, '!')])
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
  # statement = unroll_loop_statements(statement)
  statement = use_loop_invariant(statement)
  for visited in compute_visited_paths(statement):
    # Execution path stops at revert and return
    path = []
    revert = False
    for v in construct_execution_path(statement, visited):
      path.append(v)
      if isinstance(v, Return): break
      if isinstance(v, ExpressionStatement):
        if isinstance(v.expression, FunctionCall):
          ident = v.expression.expression
          if isinstance(ident, Identifier):
            revert = ident.name == 'revert'
            if revert: break
    if not revert:
      yield path

def generate_execution_paths(root):
  contracts = [x.name for x in root.nodes if isinstance(x, ContractDefinition)]
  for contract in root.nodes:
    if isinstance(contract, ContractDefinition):
      print(f'contract {contract.name}')
      libraries = [x for x in contract.nodes if isinstance(x, UsingForDirective)]
      variables = [x for x in contract.nodes if isinstance(x, VariableDeclaration)]
      functions = [x for x in contract.nodes if isinstance(x, FunctionDefinition)]
      for func in functions:
        if isinstance(func, FunctionDefinition):
          if func.visibility in ['public', 'external']:
            if func.body and func.body.statements:
              print(f'  func {func.name}')
              for path in compute_execution_paths(func.body):
                yield contracts, libraries, variables, functions, func, path