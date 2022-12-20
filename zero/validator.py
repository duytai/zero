from z3 import *
from .generator import *

def sort_for_type_name(type_name):
  if isinstance(type_name, ElementaryTypeName):
    if type_name.name.startswith('uint') or type_name.name == 'address':
      return IntSort()
    if type_name.name == 'bool':
      return BoolSort()
  if isinstance(type_name, Mapping):
    key_sort = sort_for_type_name(type_name.key_type)
    value_sort = sort_for_type_name(type_name.value_type)
    return ArraySort(key_sort, value_sort)
  if isinstance(type_name, UserDefinedTypeName):
    if isinstance(type_name.referenced, StructDefinition):
      dt = Datatype(type_name.name)
      members = [(x.name, sort_for_type_name(x.type_name)) for x in type_name.referenced.members]
      dt.declare('data', *members)
      return dt.create()
  if isinstance(type_name, ArrayTypeName):
    key_sort = IntSort()
    value_sort = sort_for_type_name(type_name.base_type)
    return ArraySort(key_sort, value_sort)
  raise ValueError(type_name)

def constraint_for_type_name(value, type_name):
  if isinstance(type_name, ElementaryTypeName):
    if type_name.name.startswith('uint') or type_name.name == 'address':
      return value >= 0
  if isinstance(type_name, Mapping):
    key_sort = sort_for_type_name(type_name.key_type)
    key = FreshConst(key_sort)
    return ForAll(key, constraint_for_type_name(value[key], type_name.value_type))
  if isinstance(type_name, UserDefinedTypeName):
    if isinstance(type_name.referenced, StructDefinition):
      constraints = []
      for idx, var in enumerate(type_name.referenced.members):
        member = value.sort().accessor(0, idx)(value)
        constraint = constraint_for_type_name(member, var.type_name)
        constraints.append(constraint)
      return And(constraints)
  if isinstance(type_name, ArrayTypeName):
    key = FreshConst(IntSort())
    constraint = ForAll(key, constraint_for_type_name(value[key], type_name.base_type))
    if type_name.length:
      return And([key <= IntVal(type_name.length), key >= 0, constraint])
    return And([key >= 0, constraint])
  raise ValueError((value, type_name))

def default_for_type_name(value, type_name):
  if isinstance(type_name, ElementaryTypeName):
    if type_name.name.startswith('uint'):
      return value == 0
    if type_name.name == 'bool':
      return value == BoolVal(False)
  raise ValueError((value, type_name))

@dataclass
class VariableRef:
  type_name: Any
  val: Any
  constraint: Any = BoolVal(True)

  def __post_init__(self):
    if isinstance(self.type_name, ArrayTypeName):
      type_name = ElementaryTypeName('uint')
      name = f'{self.val.sexpr()}.length'
      val = Const(name, IntSort())
      constraint = constraint_for_type_name(val, type_name)
      if self.type_name.length:
        constraint = And([constraint, val < self.type_name.length])
      tmp = VariableRef(type_name, val, constraint)
      setattr(self, 'length', tmp)

    if isinstance(self.type_name, UserDefinedTypeName):
      if isinstance(self.type_name.referenced, StructDefinition):
        for idx, var in enumerate(self.type_name.referenced.members):
          type_name = var.type_name
          val = self.val.sort().accessor(0, idx)(self.val)
          constraint = And([
            self.constraint,
            constraint_for_type_name(val, type_name)
          ])
          tmp = VariableRef(type_name, val, constraint)
          setattr(self, var.name, tmp)

  def __lt__(self, other):
    type_name = ElementaryTypeName('bool')
    val = self.val < other.val
    constraint = And([self.constraint, other.constraint])
    return VariableRef(type_name, val, constraint)

  def __le__(self, other):
    type_name = ElementaryTypeName('bool')
    val = self.val <= other.val
    constraint = And([self.constraint, other.constraint])
    return VariableRef(type_name, val, constraint)

  def __gt__(self, other):
    type_name = ElementaryTypeName('bool')
    val = self.val > other.val
    constraint = And([self.constraint, other.constraint])
    return VariableRef(type_name, val, constraint)

  def __ge__(self, other):
    type_name = ElementaryTypeName('bool')
    val = self.val >= other.val
    constraint = And([self.constraint, other.constraint])
    return VariableRef(type_name, val, constraint)

  def __or__(self, other):
    type_name = ElementaryTypeName('bool')
    val = Or([self.val, other.val])
    constraint = And([self.constraint, other.constraint])
    return VariableRef(type_name, val, constraint)

  def __and__(self, other):
    type_name = ElementaryTypeName('bool')
    val = And([self.val, other.val])
    constraint = And([self.constraint, other.constraint])
    return VariableRef(type_name, val, constraint)

  def __eq__(self, other):
    type_name = ElementaryTypeName('bool')
    val = self.val == other.val
    constraint = And([self.constraint, other.constraint])
    return VariableRef(type_name, val, constraint)

  def __not__(self):
    type_name = ElementaryTypeName('bool')
    val = Not(self.val)
    constraint = self.constraint
    return VariableRef(type_name, val, constraint)

  def __add__(self, other):
    type_name = self.type_name
    val = self.val + other.val
    constraint = And([
      constraint_for_type_name(val, type_name),
      self.constraint,
      other.constraint
    ])
    return VariableRef(type_name, val, constraint)

  def __mul__(self, other):
    type_name = self.type_name
    val = self.val * other.val
    constraint = And([
      constraint_for_type_name(val, type_name),
      self.constraint,
      other.constraint
    ])
    return VariableRef(type_name, val, constraint)

  def __sub__(self, other):
    type_name = self.type_name
    val = self.val - other.val
    constraint = And([
      constraint_for_type_name(val, type_name),
      self.constraint,
      other.constraint
    ])
    return VariableRef(type_name, val, constraint)

  def __getitem__(self, item):
    if isinstance(self.type_name, Mapping):
      type_name = self.type_name.value_type
      val = self.val[item.val]
      constraint = And([
        constraint_for_type_name(val, type_name),
        self.constraint,
        item.constraint
      ])
      return VariableRef(type_name, val, constraint)
    if isinstance(self.type_name, ArrayTypeName):
      type_name = self.type_name.base_type
      val = self.val[item.val]
      constraint = And([
        constraint_for_type_name(val, type_name),
        self.constraint,
        item.constraint
      ])
      return VariableRef(type_name, val, constraint)

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
  left = exp.left_hand_side
  right = visit_expression(exp.right_hand_side, state)
  if exp.operator == '+=':
    right = visit_expression(exp.left_hand_side, state) + visit_expression(exp.right_hand_side, state)
  if exp.operator == '-=':
    right = visit_expression(exp.left_hand_side, state) - visit_expression(exp.right_hand_side, state)
  # TODO: handle assignment
  while not isinstance(left, Identifier):
    if isinstance(left, IndexAccess):
      base = visit_expression(left.base_expression, state)
      index = visit_expression(left.index_expression, state)
      #
      type_name = base.type_name
      val = Store(base.val, index.val, right.val)
      constraint = And([base.constraint, index.constraint, right.constraint])
      right = VariableRef(type_name, val, constraint)
      left = left.base_expression
    else:
      raise ValueError(left)
  return state.store_const(left.name, right)

def visit_binary_operation(exp, state):
  left_expression = visit_expression(exp.left_expression, state)
  right_expression = visit_expression(exp.right_expression, state)
  if exp.operator == '+':
    return left_expression + right_expression
  if exp.operator == '-':
    return left_expression - right_expression
  if exp.operator == '*':
    return left_expression * right_expression
  if exp.operator == '>':
    return left_expression > right_expression
  if exp.operator == '<':
    return left_expression < right_expression
  if exp.operator == '<=':
    return left_expression <= right_expression
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
  if exp.operator == '++':
    assignment = Assignment(exp.sub_expression, Literal('number', '1'), '+=')
    visit_assignment(assignment, state)
    return visit_expression(exp.sub_expression, state)
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
  if exp.kind == 'typeConversion':
    if isinstance(exp.expression, ElementaryTypeNameExpression):
      return visit_expression(exp.arguments[0], state)
  if exp.kind == 'functionCall':
    if isinstance(exp.expression, Identifier):
      if exp.expression.name == 'require':
        condition = visit_expression(exp.arguments[0], state)
        state.add_condition(condition)
        return
      if exp.expression.name == 'assert':
        assertion = visit_expression(exp.arguments[0], state)
        pre = And([And([x.constraint, x.val]) for x in state.conditions] + [assertion.constraint])
        post = assertion.val
        solver = Solver()
        solver.add(Not(Implies(pre, post)))
        print(solver.check())
        print(assertion.val)
        return
  raise ValueError(exp)

def visit_index_access(exp, state):
  index_expression = visit_expression(exp.index_expression, state)
  base_expression = visit_expression(exp.base_expression, state)
  return base_expression[index_expression]

def visit_member_access(exp, state):
  expression = visit_expression(exp.expression, state)
  return getattr(expression, exp.member_name)

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
  if isinstance(exp, IndexAccess):
    return visit_index_access(exp, state)
  if isinstance(exp, MemberAccess):
    return visit_member_access(exp, state)
  raise ValueError(exp)

def validate(root):
  for resources, parameters, returns, path in generate_execution_paths(root):
    state = StateRef({}, [])
    # state variables
    Msg = UserDefinedTypeName('Msg', StructDefinition('Msg', [
      VariableDeclaration('sender', ElementaryTypeName('address')),
      VariableDeclaration('value', ElementaryTypeName('uint')),
    ]))
    msg = VariableDeclaration('msg', Msg)
    state.mk_const(msg.name, msg.type_name)
    # global variables and parameters
    for var in resources + parameters:
      state.mk_const(var.name, var.type_name)
    # returns
    for var in returns:
      state.mk_default_const(var.name, var.type_name)
    # start validating every execution paths
    for statement in path:
      if isinstance(statement, ExpressionStatement):
        visit_expression(statement.expression, state)
      elif isinstance(statement, VariableDeclarationStatement):
        declarations = []
        for var in statement.declarations:
          state.mk_default_const(var.name, var.type_name)
          declarations.append(var.name)
        if statement.initial_value:
          init = visit_expression(statement.initial_value, state)
          for name, val in zip(declarations, init if is_array(init) else [init]):
            state.store_const(name, val)
      elif isinstance(statement, Return):
        pass # TODO
      else:
        condition = visit_expression(statement, state)
        state.add_condition(condition)
