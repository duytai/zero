from z3 import *
from .generator import *

def sort_for_type_name(type_name):
  if isinstance(type_name, ElementaryTypeName):
    if type_name.name.startswith('uint'):
      return IntSort()
  raise ValueError(type_name)

def constraint_for_type_name(value, type_name):
  if isinstance(type_name, ElementaryTypeName):
    if type_name.name.startswith('uint'):
      return value >= 0
  raise ValueError((value, type_name))

def default_for_type_name(value, type_name):
  if isinstance(type_name, ElementaryTypeName):
    if type_name.name.startswith('uint'):
      return value == 0
  raise ValueError((value, type_name))

@dataclass
class VariableRef:
  type_name: Any
  value: Any
  constraint: Any = BoolVal(True)

  def __lt__(self, other):
    type_name = ElementaryTypeName('bool')
    value = self.value < other.value
    constraint = And([self.constraint, other.constraint])
    return VariableRef(type_name, value, constraint)

  def __gt__(self, other):
    type_name = ElementaryTypeName('bool')
    value = self.value > other.value
    constraint = And([self.constraint, other.constraint])
    return VariableRef(type_name, value, constraint)

  def __ge__(self, other):
    type_name = ElementaryTypeName('bool')
    value = self.value >= other.value
    constraint = And([self.constraint, other.constraint])
    return VariableRef(type_name, value, constraint)

  def __or__(self, other):
    type_name = ElementaryTypeName('bool')
    value = Or([self.value, other.value])
    constraint = And([self.constraint, other.constraint])
    return VariableRef(type_name, value, constraint)

  def __and__(self, other):
    type_name = ElementaryTypeName('bool')
    value = And([self.value, other.value])
    constraint = And([self.constraint, other.constraint])
    return VariableRef(type_name, value, constraint)

  def __eq__(self, other):
    type_name = ElementaryTypeName('bool')
    value = self.value == other.value
    constraint = And([self.constraint, other.constraint])
    return VariableRef(type_name, value, constraint)

  def __not__(self):
    type_name = ElementaryTypeName('bool')
    value = Not(self.value)
    constraint = self.constraint
    return VariableRef(type_name, value, constraint)

  def __add__(self, other):
    type_name = self.type_name
    value = self.value + other.value
    constraint = And([
      constraint_for_type_name(value, type_name),
      self.constraint,
      other.constraint
    ])
    return VariableRef(type_name, value, constraint)

@dataclass
class StateRef:
  variables: dict
  conditions: List[Any]

  def mk_const(self, name, type_name):
    sort = sort_for_type_name(type_name)
    value = Const(name, sort)
    constraint = constraint_for_type_name(value, type_name)
    self.variables[name] = VariableRef(type_name, value, constraint)

  def mk_default_const(self, name, type_name):
    sort = sort_for_type_name(type_name)
    value = Const(name, sort)
    constraint = default_for_type_name(value, type_name)
    self.variables[name] = VariableRef(type_name, value, constraint)

  def fetch_const(self, name):
    return self.variables[name]

  def store_const(self, name, var):
    self.variables[name] = var

  def add_condition(self, condition):
    self.conditions.append(condition)

def visit_assignment(exp, state):
  left_hand_side = exp.left_hand_side
  right_hand_side = visit_expression(exp.right_hand_side, state)
  if isinstance(left_hand_side, Identifier):
    return state.store_const(left_hand_side.name, right_hand_side)
  raise ValueError(exp)

def visit_binary_operation(exp, state):
  left_expression = visit_expression(exp.left_expression, state)
  right_expression = visit_expression(exp.right_expression, state)
  if exp.operator == '+':
    return left_expression + right_expression
  if exp.operator == '>':
    return left_expression > right_expression
  if exp.operator == '<':
    return left_expression < right_expression
  if exp.operator == '>=':
    return left_expression >= right_expression
  if exp.operator == '==':
    return left_expression == right_expression
  if exp.operator == '||':
    return left_expression | right_expression
  if exp.operator == '&&':
    return left_expression & right_expression
  raise ValueError(exp.operator)

def visit_unary_operation(exp, state):
  sub_expression = visit_expression(exp.sub_expression, state)
  if exp.operator == '!':
    return sub_expression.__not__()
  raise ValueError(exp.operator)

def visit_tuple_expression(exp, state):
  tmp = [visit_expression(x, state) for x in exp.components]
  return tmp[0] if len(tmp) == 1 else tmp

def visit_identifier(exp, state):
  return state.fetch_const(exp.name)

def visit_literal(exp, _):
  if exp.kind == 'number':
    type_name = ElementaryTypeName('uint')
    value = IntVal(int(exp.value))
    return VariableRef(type_name, value)
  raise ValueError(exp.kind)

def visit_function_call(exp, state):
  if isinstance(exp.expression, Identifier):
    if exp.expression.name == 'assert':
      assertion = visit_expression(exp.arguments[0], state)
      pre = And([And([x.constraint, x.value]) for x in state.conditions] + [assertion.constraint])
      post = assertion.value
      solver = Solver()
      solver.add(Not(Implies(pre, post)))
      print(solver.check())
      print(assertion.value)
      return

def visit_expression(exp, state):
  if isinstance(exp, Assignment):
    return visit_assignment(exp, state)
  if isinstance(exp, BinaryOperation):
    return visit_binary_operation(exp, state)
  if isinstance(exp, Identifier):
    return visit_identifier(exp, state)
  if isinstance(exp, UnaryOperation):
    return visit_unary_operation(exp, state)
  if isinstance(exp, TupleExpression):
    return visit_tuple_expression(exp, state)
  if isinstance(exp, Literal):
    return visit_literal(exp, state)
  if isinstance(exp, FunctionCall):
    return visit_function_call(exp, state)
  raise ValueError(exp)

def validate(root):
  for parameters, returns, path in generate_execution_paths(root):
    state = StateRef({}, [])
    for var in parameters:
      state.mk_const(var.name, var.type_name)
    for var in returns:
      state.mk_default_const(var.name, var.type_name)
    for statement in path:
      if isinstance(statement, ExpressionStatement):
        visit_expression(statement.expression, state)
      else:
        condition = visit_expression(statement, state)
        state.add_condition(condition)
