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
    left = repr(self.left_expression)
    right = repr(self.right_expression)
    return f'{left} {self.operator} {right}'

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

  def __repr__(self):
    return self.name

@dataclass
class Literal:
  kind: str
  value: str

@dataclass
class FunctionCall:
  kind: str
  expression: Any
  arguments: List[Any]

  def __repr__(self):
    left = repr(self.expression)
    right = ','.join([repr(x) for x in self.arguments])
    return f'{left}({right})'

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
    return self.name

@dataclass
class FunctionDefinition:
  name: str
  parameters: List[VariableDeclaration]
  returns: List[VariableDeclaration]
  body: Optional[Any]
  visibility: str
  modifiers: List[Any]

@dataclass
class Block:
  statements: List[Any]

@dataclass
class ExpressionStatement:
  expression: Any

  def __repr__(self):
    return repr(self.expression)

@dataclass
class VariableDeclarationStatement:
  declarations: List[VariableDeclaration]
  initial_value: Optional[Any]

  def __repr__(self):
    left = ','.join([repr(x) for x in self.declarations])
    right = repr(self.initial_value) if self.initial_value else None
    return f'{left} = {right}'

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
class PlaceholderStatement: pass

@dataclass
class ContractDefinition:
  base_contracts: List[Any]
  kind: str
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
class UsingForDirective:
  type_name: Any
  library_name: Any

@dataclass
class InheritanceSpecifier:
  base_name: Any

@dataclass
class ModifierInvocation:
  modifier_name: Any
  arguments: List[Any]

@dataclass
class EmitStatement: pass

@dataclass
class EventDefinition: pass

@dataclass
class ModifierDefinition:
  body: Any
  parameters: List[Any]

@dataclass
class InlineAssembly: pass

@dataclass
class PragmaDirective: pass

@dataclass
class Conditional:
  condition: Any
  true_expression: Any
  false_expression: Any

@dataclass
class NewExpression:
  type_name: Any