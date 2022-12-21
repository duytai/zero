from typing import List, Any, Optional
from dataclasses import dataclass, field
from itertools import islice
from functools import partial

@dataclass
class ElementaryTypeName:
  name: str

@dataclass
class Mapping:
  key_type: Any
  value_type: Any

@dataclass
class UserDefinedTypeName:
  name: str
  referenced: Any

@dataclass
class ArrayTypeName:
  base_type: Any
  length: Optional[int]

@dataclass
class BinaryOperation:
  left_expression: Any
  right_expression: Any
  operator: str

@dataclass
class UnaryOperation:
  sub_expression: Any
  prefix: bool
  operator: str

@dataclass
class TupleExpression:
  components: List[Any]

@dataclass
class Assignment:
  left_hand_side: Any
  right_hand_side: Any
  operator: str

@dataclass
class Identifier:
  name: str

@dataclass
class Literal:
  kind: str
  value: str

@dataclass
class FunctionCall:
  kind: str
  expression: Any
  arguments: List[Any]

@dataclass
class IndexAccess:
  index_expression: Any
  base_expression: Any

@dataclass
class MemberAccess:
  member_name: str
  expression: Any

@dataclass
class ElementaryTypeNameExpression:
  name: str

@dataclass
class VariableDeclaration:
  name: str
  type_name: Any

@dataclass
class FunctionDefinition:
  name: str
  parameters: List[VariableDeclaration]
  returns: List[VariableDeclaration]
  body: Optional[Any]
  ensures: Optional[Any]

@dataclass
class Block:
  statements: List[Any]

@dataclass
class ExpressionStatement:
  expression: Any

@dataclass
class VariableDeclarationStatement:
  declarations: List[VariableDeclaration]
  initial_value: Optional[Any]

@dataclass
class ForStatement:
  init: Any
  condition: Any
  loop: Any
  body: Any

@dataclass
class IfStatement:
  condition: Any
  true_body: Any
  false_body: Any

@dataclass
class Return:
  expression: Optional[Any]

@dataclass
class ContractDefinition:
  name: str
  nodes: List[Any]

@dataclass
class StructDefinition:
  name: str
  members: List[VariableDeclaration]

@dataclass
class SourceUnit:
  nodes: List[Any]

class ExpVisitor:
  def visit_binary_operation(self, exp):
    return BinaryOperation(
      self.visit_expression(exp.left_expression),
      self.visit_expression(exp.right_expression),
      exp.operator
    )

  def visit_unary_operation(self, exp):
    return UnaryOperation(
      self.visit_expression(exp.sub_expression),
      exp.prefix,
      exp.operator
    )

  def visit_tuple_expression(self, exp):
    return TupleExpression(
      [self.visit_expression(x) for x in exp.components]
    )

  def visit_assignment(self, exp):
    return Assignment(
      self.visit_expression(exp.left_hand_side),
      self.visit_expression(exp.right_hand_side),
      exp.operator
    )

  def visit_identifier(self, exp):
    return Identifier(exp.name)

  def visit_literal(self, exp):
    return Literal(exp.kind, exp.value)

  def visit_function_call(self, exp):
    return FunctionCall(
      exp.kind,
      self.visit_expression(exp.expression),
      [self.visit_expression(x) for x in exp.arguments]
    )

  def visit_index_access(self, exp):
    return IndexAccess(
      self.visit_expression(exp.index_expression),
      self.visit_expression(exp.base_expression)
    )

  def visit_member_access(self, exp):
    return MemberAccess(
      exp.member_name,
      self.visit_expression(exp.expression)
    )

  def visit_elementary_type_name_expression(self, exp):
    return ElementaryTypeNameExpression(exp.name)

  def visit_expression(self, exp):
    if isinstance(exp, BinaryOperation):
      return self.visit_binary_operation(exp)
    if isinstance(exp, UnaryOperation):
      return self.visit_unary_operation(exp)
    if isinstance(exp, TupleExpression):
      return self.visit_tuple_expression(exp)
    if isinstance(exp, Assignment):
      return self.visit_assignment(exp)
    if isinstance(exp, Identifier):
      return self.visit_identifier(exp)
    if isinstance(exp, Literal):
      return self.visit_literal(exp)
    if isinstance(exp, FunctionCall):
      return self.visit_function_call(exp)
    if isinstance(exp, IndexAccess):
      return self.visit_index_access(exp)
    if isinstance(exp, MemberAccess):
      return self.visit_member_access(exp)
    if isinstance(exp, ElementaryTypeNameExpression):
      return self.visit_elementary_type_name_expression(exp)
    raise ValueError(exp)

class GlobalName:
  _instance = None
  counter = 0

  def __new__(cls):
    if not cls._instance:
      cls._instance = super(GlobalName, cls).__new__(cls)
    return cls._instance

  def names(self):
    while True:
      self.counter += 1
      yield f'tmp_{self.counter}'

class AlterOld(ExpVisitor):
  def __init__(self):
    self.declarations = []
    self.modifies = []

  def visit_function_call(self, exp):
    gn = GlobalName()
    ident = exp.expression
    if isinstance(ident, Identifier):
      if ident.name == 'old_uint':
        names = list(islice(gn.names(), 1))
        self.declarations.append(
          VariableDeclarationStatement([
            VariableDeclaration(names[0], ElementaryTypeName('uint')),
          ], self.visit_expression(exp.arguments[0]))
        )
        self.modifies.append(
          ExpressionStatement(
            FunctionCall('functionCall', Identifier('modifies'), exp.arguments)
          )
        )
        return Identifier(names[0])
    return exp

class AlterIdent(ExpVisitor):
  def __init__(self, data):
    self.data = data

  def visit_identifier(self, exp):
    if exp.name in self.data:
      return Identifier(self.data[exp.name])
    return exp

def parse_ensures(ensures, parameters, returns, arguments):
  pre_statements = []
  mod_statements = []
  post_statements = []
  assume_statements = []
  gn = GlobalName()

  for pre, post in ensures:
    alter = AlterOld()
    names = list(islice(gn.names(), 2))
    pre_statements.append(
      VariableDeclarationStatement([
        VariableDeclaration(names[0], ElementaryTypeName('bool'))
      ], alter.visit_expression(pre))
    )
    post_statements.append(
      VariableDeclarationStatement([
        VariableDeclaration(names[1], ElementaryTypeName('bool'))
      ], alter.visit_expression(post))
    )
    assume_statements.append(
      ExpressionStatement(
        FunctionCall('functionCall', Identifier('assume'), [
          BinaryOperation(
            Identifier(names[0]),
            Identifier(names[1]),
            '=>'
          )
        ])
      )
    )
    pre_statements += alter.declarations
    mod_statements += alter.modifies

  body = []
  data = {}
  for k, v in zip(parameters + returns, arguments):
    data[k.name] = next(gn.names())
    body.append(
      VariableDeclarationStatement([
        VariableDeclaration(data[k.name], k.type_name)
      ], v)
    )
  alter = AlterIdent(data)

  for stmt in pre_statements + mod_statements + post_statements + assume_statements:
    if isinstance(stmt, ExpressionStatement):
      stmt.expression = alter.visit_expression(stmt.expression)
    elif isinstance(stmt, VariableDeclarationStatement):
      if stmt.initial_value:
        stmt.initial_value = alter.visit_expression(stmt.initial_value)
    else:
      raise ValueError(stmt)
    body.append(stmt)

  return Block(body)

def parse(node):

  if node['nodeType'] == 'SourceUnit':
    nodes = [parse(x) for x in node['nodes']]
    return SourceUnit(nodes)

  if node['nodeType'] == 'ContractDefinition':
    name = node['name']
    nodes  = [parse(x) for x in node['nodes']]
    return ContractDefinition(name, nodes)

  if node['nodeType'] == 'FunctionDefinition':
    name = node['name']
    parameters = [parse(x) for x in node['parameters']['parameters']]
    returns = [parse(x) for x in node['returnParameters']['parameters']]
    body = parse(node['body']) if node['body'] else None
    ensures = None

    if body:
      statements = []
      data = []
      for stmt in body.statements:
        if isinstance(stmt, ExpressionStatement):
          call = stmt.expression
          if isinstance(call, FunctionCall):
            ident = call.expression
            if isinstance(ident, Identifier):
              if ident.name == 'ensures':
                data.append(call.arguments)
                continue
        statements.append(stmt)
      body = Block(statements)
      if data:
        ensures = partial(parse_ensures, data, parameters, returns)
    return FunctionDefinition(name, parameters, returns, body, ensures)

  if node['nodeType'] == 'VariableDeclaration':
    name = node['name']
    type_name = parse(node['typeName'])
    return VariableDeclaration(name, type_name)

  if node['nodeType'] == 'ElementaryTypeName':
    name = node['name']
    return ElementaryTypeName(name)

  if node['nodeType'] == 'Block':
    statements = [parse(x) for x in node['statements']]
    return Block(statements)

  if node['nodeType'] == 'ExpressionStatement':
    expression = parse(node['expression'])
    return ExpressionStatement(expression)

  if node['nodeType'] == 'Assignment':
    left_hand_side = parse(node['leftHandSide'])
    right_hand_side = parse(node['rightHandSide'])
    operator = node['operator']
    return Assignment(left_hand_side, right_hand_side, operator)

  if node['nodeType'] == 'Identifier':
    name = node['name']
    return Identifier(name)

  if node['nodeType'] == 'BinaryOperation':
    left_expression = parse(node['leftExpression'])
    right_expression = parse(node['rightExpression'])
    operator = node['operator']
    return BinaryOperation(left_expression, right_expression, operator)

  if node['nodeType'] == 'IfStatement':
    condition = parse(node['condition'])
    true_body = parse(node['trueBody'])
    false_body = parse(node['falseBody']) if node['falseBody'] else None
    return IfStatement(condition, true_body, false_body)

  if node['nodeType'] == 'UnaryOperation':
    sub_expression = parse(node['subExpression'])
    prefix = node['prefix']
    operator = node['operator']
    return UnaryOperation(sub_expression, prefix, operator)

  if node['nodeType'] == 'TupleExpression':
    components = [parse(x) for x in node['components']]
    return TupleExpression(components)

  if node['nodeType'] == 'Literal':
    kind = node['kind']
    value = node['value']
    return Literal(kind, value)

  if node['nodeType'] == 'FunctionCall':
    kind = node['kind']
    expression = parse(node['expression'])
    arguments = [parse(x) for x in node['arguments']]
    return FunctionCall(kind, expression, arguments)

  if node['nodeType'] == 'Mapping':
    key_type = parse(node['keyType'])
    value_type = parse(node['valueType'])
    return Mapping(key_type, value_type)

  if node['nodeType'] == 'IndexAccess':
    index_expression = parse(node['indexExpression'])
    base_expression = parse(node['baseExpression'])
    return IndexAccess(index_expression, base_expression)

  if node['nodeType'] == 'MemberAccess':
    member_name = node['memberName']
    expression = parse(node['expression'])
    return MemberAccess(member_name, expression)

  if node['nodeType'] == 'StructDefinition':
    name = node['name']
    members = [parse(x) for x in node['members']]
    return StructDefinition(name, members)

  if node['nodeType'] == 'UserDefinedTypeName':
    name = node['name']
    return UserDefinedTypeName(name)

  if node['nodeType'] == 'ArrayTypeName':
    base_type = parse(node['baseType'])
    length = int(node['length']) if node['length'] else None
    return ArrayTypeName(base_type, length)

  if node['nodeType'] == 'VariableDeclarationStatement':
    declarations = [parse(x) for x in node['declarations']]
    initial_value = parse(node['initialValue']) if node['initialValue'] else None
    return VariableDeclarationStatement(declarations, initial_value)

  if node['nodeType'] == 'ForStatement':
    init = parse(node['initializationExpression'])
    condition = parse(node['condition'])
    loop = parse(node['loopExpression'])
    body = parse(node['body'])
    return ForStatement(init, condition, loop, body)

  if node['nodeType'] == 'Return':
    expression = parse(node['expression']) if node['expression'] else None
    return Return(expression)

  if node['nodeType'] == 'ElementaryTypeNameExpression':
    return ElementaryTypeNameExpression(node['typeName'])

  raise ValueError(node['nodeType'])