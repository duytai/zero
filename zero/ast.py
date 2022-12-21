from typing import List, Any, Optional
from dataclasses import dataclass

@dataclass
class ElementaryTypeName:
  name: str
  def __repr__(self):
    return self.name

@dataclass
class Mapping:
  key_type: Any
  value_type: Any
  def __repr__(self):
    return f'({repr(self.key_type)}=>{repr(self.value_type)})'

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
  def __repr__(self):
    return f'{repr(self.left_expression)} {self.operator} {repr(self.right_expression)}'

@dataclass
class UnaryOperation:
  sub_expression: Any
  prefix: bool
  operator: str

@dataclass
class TupleExpression:
  components: List[Any]
  def __repr__(self):
    return f'({",".join([repr(x) for x in self.components])})'

@dataclass
class Assignment:
  left_hand_side: Any
  right_hand_side: Any
  operator: str
  def __repr__(self):
    return f'{repr(self.left_hand_side)} {self.operator} {repr(self.right_hand_side)}'

@dataclass
class Identifier:
  name: str
  def __repr__(self):
    return self.name

@dataclass
class Literal:
  kind: str
  value: str
  def __repr__(self):
    return self.value

@dataclass
class FunctionCall:
  kind: str
  expression: Any
  arguments: List[Any]
  overridle: Optional[Any] = None
  def __repr__(self):
    if self.overridle:
      ret, block = self.overridle
      return f'////{repr(block)}//// {repr(ret)}'
    return f'{repr(self.expression)}({",".join([repr(x) for x in self.arguments])})'

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
  def __repr__(self):
    return f'{repr(self.type_name)} {self.name}'

@dataclass
class FunctionDefinition:
  name: str
  parameters: List[VariableDeclaration]
  returns: List[VariableDeclaration]
  body: Optional[Any]
  before: Any = None
  after: Any = None
  def __repr__(self):
    parameters = ', '.join([repr(x) for x in self.parameters])
    returns = ', '.join([repr(x) for x in self.returns])
    body = ''
    if self.body:
      statements = []
      if self.pre:
        statements += self.pre.statements
      statements += self.body.statements
      if self.post:
        statements += self.post.statements
      body = '\n'.join([f'\t\t{x}' for x in repr(Block(statements)).split('\n')])
    if not body:
      return f'func {self.name}({parameters}) -> ({returns}) {{}}'
    return f'func {self.name}({parameters}) -> ({returns}):\n {body}'

@dataclass
class Block:
  statements: List[Any]
  def __repr__(self):
    return '\n'.join([repr(x) for x in self.statements])

@dataclass
class ExpressionStatement:
  expression: Any
  def __repr__(self):
    return f'{repr(self.expression)};'

@dataclass
class VariableDeclarationStatement:
  declarations: List[VariableDeclaration]
  initial_value: Optional[Any]
  def __repr__(self):
    right = repr(self.initial_value) if self.initial_value else '?'
    left = ','.join([repr(x) for x in self.declarations])
    return f'{left} = {right};'

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
  def __repr__(self):
    return f'return {repr(self.expression)}' if self.expression else 'return'

@dataclass
class ContractDefinition:
  name: str
  nodes: List[Any]
  def __repr__(self):
    body = '\n'.join([f'\t{repr(x)}' for x in self.nodes])
    return f'contract {self.name}: \n{body}'

@dataclass
class StructDefinition:
  name: str
  members: List[VariableDeclaration]

@dataclass
class SourceUnit:
  nodes: List[Any]
  def __repr__(self):
    return '\n'.join([repr(x) for x in self.nodes])

@dataclass
class Nothing: pass

@dataclass
class Anything:
  type_name: Any
  def __repr__(self):
    return '*'