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
  overridle: Optional[Any] = None

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
  visibility: str
  before: Any = None
  after: Any = None

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

@dataclass
class Nothing: pass

@dataclass
class Anything:
  type_name: Any

@dataclass
class UsingForDirective: pass