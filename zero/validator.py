from z3 import *
from .generator import *
from copy import deepcopy
from termcolor import colored

def sort_for_type_name(type_name):
  if isinstance(type_name, ElementaryTypeName):
    if type_name.name.startswith('uint') or type_name.name == 'address':
      return IntSort()
    if type_name.name == 'bool':
      return BoolSort()
    if type_name.name == 'string':
      return StringSort()
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
    if type_name.name.startswith('uint'):
      return value >= 0
    if type_name.name == 'address':
      return value >= 0
    if type_name.name == 'bool':
      return BoolVal(True)
    if type_name.name == 'string':
      return BoolVal(True)
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
      return And([key < IntVal(int(type_name.length.value)), key >= 0, constraint])
    return And([key >= 0, constraint])
  raise ValueError((value, type_name))

def default_for_type_name(value, type_name):
  if isinstance(type_name, ElementaryTypeName):
    if type_name.name.startswith('uint'):
      return value == 0
    if type_name.name == 'bool':
      return value == BoolVal(False)
    if type_name.name == 'address':
      return value == 0
  if isinstance(type_name, ArrayTypeName):
    key = FreshConst(IntSort())
    constraint = ForAll(key, default_for_type_name(value[key], type_name.base_type))
    if type_name.length:
      return And([key < IntVal(int(type_name.length.value)), key >= 0, constraint])
    return And([key >= 0, constraint])
  raise ValueError((value, type_name))

@dataclass
class VariableRef:
  type_name: Any
  val: Any
  constraint: Any = BoolVal(True)

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

  def __implies__(self, other):
    type_name = ElementaryTypeName('bool')
    val = Implies(self.val, other.val)
    constraint = And([self.constraint, other.constraint])
    return VariableRef(type_name, val, constraint)

  def __eq__(self, other):
    type_name = ElementaryTypeName('bool')
    val = self.val == other.val
    constraint = And([self.constraint, other.constraint])
    return VariableRef(type_name, val, constraint)

  def __ne__(self, other):
    type_name = ElementaryTypeName('bool')
    val = self.val != other.val
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

  def __truediv__(self, other):
    type_name = self.type_name
    val = self.val / other.val
    constraint = And([
      constraint_for_type_name(val, type_name),
      self.constraint,
      other.constraint
    ])
    return VariableRef(type_name, val, constraint)

  def __mod__(self, other):
    type_name = self.type_name
    val = self.val % other.val
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

  def __getattr__(self, key):
    
    if isinstance(self.type_name, UserDefinedTypeName):
      if isinstance(self.type_name.referenced, StructDefinition):
        for idx, var in enumerate(self.type_name.referenced.members):
          if var.name == key:
            type_name = var.type_name
            val = self.val.sort().accessor(0, idx)(self.val)
            constraint = And([
              self.constraint,
              constraint_for_type_name(val, type_name)
            ])
            return VariableRef(type_name, val, constraint)

    if isinstance(self.type_name, ElementaryTypeName):
      if self.type_name.name == 'address':
        # @B hold of mapping from address => balance
        type_name = Mapping(ElementaryTypeName('address'), ElementaryTypeName('uint'))
        sort = sort_for_type_name(type_name)
        val = Const('@B', sort)
        constraint = constraint_for_type_name(val, type_name)
        tmp = VariableRef(type_name, val, constraint)
        return tmp[self]

    if isinstance(self.type_name, ArrayTypeName):
      # return the length of array
      type_name = ElementaryTypeName('uint')
      name = f'{self.val.sexpr()}.length'
      val = Const(name, IntSort())
      constraint = constraint_for_type_name(val, type_name)
      if self.type_name.length:
        constraint = And([constraint, val < int(self.type_name.length.value)])
      return VariableRef(type_name, val, constraint)

    raise ValueError(key)

@dataclass
class StateRef:
  variables: dict
  conditions: Optional[VariableRef] = None
  runtime_reverts: Optional[VariableRef] = None
  arith_check: bool = True

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
    self.conditions = self.conditions & condition

  def add_runtime_revert(self, revert):
    self.runtime_reverts = self.runtime_reverts | (self.conditions & revert)

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
  if exp.operator == '/':
    return left_expression / right_expression
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
  if exp.operator == '!=':
    return left_expression != right_expression
  if exp.operator == '||':
    return left_expression | right_expression
  if exp.operator == '&&':
    return left_expression & right_expression
  if exp.operator == '=>':
    return left_expression.__implies__(right_expression)
  if exp.operator == '%':
    return left_expression % right_expression
  raise ValueError(exp.operator)

def visit_unary_operation(exp, state):
  sub_expression = visit_expression(exp.sub_expression, state)
  if exp.operator == '!':
    return sub_expression.__not__()
  if exp.operator == '++':
    assignment = Assignment(exp.sub_expression, Literal('number', '1'), '+=')
    visit_assignment(assignment, state)
    return visit_expression(exp.sub_expression, state)
  if exp.operator == '--':
    assignment = Assignment(exp.sub_expression, Literal('number', '1'), '-=')
    visit_assignment(assignment, state)
    return visit_expression(exp.sub_expression, state)
  raise ValueError(exp.operator)

def visit_tuple_expression(exp, state):
  tmp = [visit_expression(x, state) for x in exp.components]
  return tmp[0] if len(tmp) == 1 else tmp

def visit_identifier(exp, state):
  return state.fetch_const(exp.name)

def visit_literal(exp, _):
  if exp.kind == 'bool':
    type_name = ElementaryTypeName('bool')
    value = BoolVal(exp.value == 'true')
    return VariableRef(type_name, value)
  if exp.kind == 'number':
    if exp.value.startswith('0x'):
      int_val = int(exp.value, 16)
    else:
      int_val = int(exp.value)
    type_name = ElementaryTypeName('uint')
    value = IntVal(int_val)
    return VariableRef(type_name, value)
  raise ValueError(exp.kind)

def visit_function_call(exp, state):
  if exp.overridle:
    ret, block = exp.overridle
    for statement in block.statements:
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
      else:
        raise ValueError(statement)
    return visit_expression(ret, state)

  if exp.kind == 'typeConversion':
    if isinstance(exp.expression, ElementaryTypeNameExpression):
      return visit_expression(exp.arguments[0], state)

  if exp.kind == 'functionCall':
    if isinstance(exp.expression, Identifier):
      if exp.expression.name == 'revert':
        condition = VariableRef(ElementaryTypeName('bool'), BoolVal(False), BoolVal(True))
        state.add_condition(condition)
        return
      if exp.expression.name == 'require':
        condition = visit_expression(exp.arguments[0], state)
        # state.add_runtime_revert(condition.__not__())
        state.add_condition(condition)
        return
      if exp.expression.name == 'assume':
        condition = visit_expression(exp.arguments[0], state)
        state.add_condition(condition)
        return
      if exp.expression.name == 'assert':
        arg = visit_expression(exp.arguments[0], state)
        pre = And([state.conditions.constraint, state.conditions.val, arg.constraint])
        assertion = Implies(pre, arg.val)
        solver = Solver()
        solver.add(Not(assertion))
        if solver.check() == unsat:
          print(colored(f'    assert({arg.val})', 'green'))
        else:
          print(colored(f'    assert({arg.val})', 'yellow'))
        return
      if exp.expression.name == 'ok':
        arg = visit_expression(exp.arguments[0], state)
        assertion = And([state.conditions.constraint, state.conditions.val, arg.constraint, arg.val])
        solver = Solver()
        solver.add(assertion)
        if solver.check() == sat:
          print(colored(f'    ok({arg.val})', 'green'))
        else:
          print(colored(f'    ok({arg.val})', 'yellow'))
        return
      if exp.expression.name == 'err':
        arg = visit_expression(exp.arguments[0], state)
        assertion = And([state.conditions.constraint, state.conditions.val, arg.constraint, arg.val])
        solver = Solver()
        solver.add(assertion)
        if solver.check() == sat:
          print(colored(f'    err({arg.val})', 'green'))
        else:
          print(colored(f'    err({arg.val})', 'yellow'))
        return
  raise ValueError(exp)

def visit_index_access(exp, state):
  index_expression = visit_expression(exp.index_expression, state)
  base_expression = visit_expression(exp.base_expression, state)
  return base_expression[index_expression]

def visit_member_access(exp, state):
  expression = visit_expression(exp.expression, state)
  return getattr(expression, exp.member_name)

def visit_anything(exp, state):
  name = FreshConst(IntSort()).sexpr()
  state.mk_const(name, exp.type_name)
  return state.fetch_const(name)

def visit_nothing(exp, state):
  return FreshConst(BoolSort())

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
  if isinstance(exp, Anything):
    return visit_anything(exp, state)
  if isinstance(exp, Nothing):
    return visit_nothing(exp, state)
  if isinstance(exp, EmitStatement):
    return None
  raise ValueError(exp)

def validate(root):
  for resources, parameters, returns, path in generate_execution_paths(root):
    state = StateRef(
      {},
      VariableRef(ElementaryTypeName('bool'), BoolVal(True), BoolVal(True)),
      VariableRef(ElementaryTypeName('bool'), BoolVal(False), BoolVal(True))
    )
    # state variables
    Msg = UserDefinedTypeName('Msg', StructDefinition('Msg', [
      VariableDeclaration('sender', ElementaryTypeName('address')),
      VariableDeclaration('value', ElementaryTypeName('uint')),
    ]))
    msg = VariableDeclaration('msg', Msg)
    state.mk_const(msg.name, msg.type_name)
    state.mk_const('this', ElementaryTypeName('address'))
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
        if statement.expression:
          init = visit_expression(statement.expression, state)
          for r, val in zip(returns, init if is_array(init) else [init]):
            state.store_const(r.name, val)
      elif isinstance(statement, EmitStatement):
        pass
      else:
        condition = visit_expression(statement, state)
        state.add_condition(condition)
