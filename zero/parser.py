from typing import List, Any, Optional
from dataclasses import dataclass

@dataclass
class ElementaryTypeName:
  name: str

@dataclass
class Mapping:
  key_type: Any
  value_type: Any

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
class VariableDeclaration:
  name: str
  type_name: Any

@dataclass
class FunctionDefinition:
  name: str
  parameters: List[VariableDeclaration]
  returns: List[VariableDeclaration]
  body: Optional[Any]

@dataclass
class Block:
  statements: List[Any]

@dataclass
class ExpressionStatement:
  expression: Any

@dataclass
class IfStatement:
  condition: Any
  true_body: Any
  false_body: Any

@dataclass
class ContractDefinition:
  name: str
  nodes: List[Any]

@dataclass
class SourceUnit:
  nodes: List[Any]

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
    return FunctionDefinition(name, parameters, returns, body)

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

  raise ValueError(node['nodeType'])