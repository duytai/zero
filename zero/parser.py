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
  init: Optional[Any]
  condition: Optional[Any]
  loop: Optional[Any]
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

struct_definitions = {}
name_counter = 0

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
    global name_counter
    if not node['name']:
      name = f'r{name_counter}'
      name_counter += 1
    else:
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
    tmp = StructDefinition(name, members)
    struct_definitions[name] = tmp
    return tmp

  if node['nodeType'] == 'UserDefinedTypeName':
    name = node['name']
    referenced = struct_definitions[name]
    return UserDefinedTypeName(name, referenced)

  if node['nodeType'] == 'ArrayTypeName':
    base_type = parse(node['baseType'])
    length = int(node['length']) if node['length'] else None
    return ArrayTypeName(base_type, length)

  if node['nodeType'] == 'VariableDeclarationStatement':
    declarations = [parse(x) for x in node['declarations']]
    initial_value = parse(node['initialValue']) if node['initialValue'] else None
    return VariableDeclarationStatement(declarations, initial_value)

  if node['nodeType'] == 'ForStatement':
    init = parse(node['initializationExpression']) if node['initializationExpression'] else None
    condition = parse(node['condition']) if node['condition'] else None
    loop = parse(node['loopExpression']) if node['loopExpression'] else None
    body = parse(node['body'])
    return ForStatement(init, condition, loop, body)

  if node['nodeType'] == 'Return':
    expression = parse(node['expression']) if node['expression'] else None
    return Return(expression)

  if node['nodeType'] == 'ElementaryTypeNameExpression':
    return ElementaryTypeNameExpression(node['typeName'])

  raise ValueError(node['nodeType'])