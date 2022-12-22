from z3 import *
from .generator import *
from .visitor import *
from copy import deepcopy
from termcolor import colored
from dataclasses import field
from functools import partial
from itertools import islice

state = None
search = None
gn = None
before_all = []
after_all = []

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
    referenced = next(search(type_name))
    if isinstance(referenced, StructDefinition):
      dt = Datatype(type_name.name)
      members = [(x.name, sort_for_type_name(x.type_name)) for x in referenced.members]
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
    referenced = next(search(type_name))
    if isinstance(referenced, StructDefinition):
      constraints = []
      for idx, var in enumerate(referenced.members):
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
class GlobalName:
  counter: int = 0

  def names(self):
    while True:
      self.counter += 1
      yield f't!{self.counter}'

gn = GlobalName()

@dataclass
class VariableRef:
  name: str
  type_name: Any
  val: Any
  constraint: Any = BoolVal(True)
  top: Any = None

  def __lt__(self, other):
    type_name = ElementaryTypeName('bool')
    val = self.val < other.val
    constraint = And([self.constraint, other.constraint])
    return VariableRef(None, type_name, val, constraint)

  def __le__(self, other):
    type_name = ElementaryTypeName('bool')
    val = self.val <= other.val
    constraint = And([self.constraint, other.constraint])
    return VariableRef(None, type_name, val, constraint)

  def __gt__(self, other):
    type_name = ElementaryTypeName('bool')
    val = self.val > other.val
    constraint = And([self.constraint, other.constraint])
    return VariableRef(None, type_name, val, constraint)

  def __ge__(self, other):
    type_name = ElementaryTypeName('bool')
    val = self.val >= other.val
    constraint = And([self.constraint, other.constraint])
    return VariableRef(None, type_name, val, constraint)

  def __or__(self, other):
    type_name = ElementaryTypeName('bool')
    val = Or([self.val, other.val])
    constraint = And([self.constraint, other.constraint])
    return VariableRef(None, type_name, val, constraint)

  def __and__(self, other):
    type_name = ElementaryTypeName('bool')
    val = And([self.val, other.val])
    constraint = And([self.constraint, other.constraint])
    return VariableRef(None, type_name, val, constraint)

  def __implies__(self, other):
    type_name = ElementaryTypeName('bool')
    val = Implies(self.val, other.val)
    constraint = And([self.constraint, other.constraint])
    return VariableRef(None, type_name, val, constraint)

  def __eq__(self, other):
    type_name = ElementaryTypeName('bool')
    val = self.val == other.val
    constraint = And([self.constraint, other.constraint])
    return VariableRef(None, type_name, val, constraint)

  def __ne__(self, other):
    type_name = ElementaryTypeName('bool')
    val = self.val != other.val
    constraint = And([self.constraint, other.constraint])
    return VariableRef(None, type_name, val, constraint)

  def __not__(self):
    type_name = ElementaryTypeName('bool')
    val = Not(self.val)
    constraint = self.constraint
    return VariableRef(None, type_name, val, constraint)

  def __add__(self, other):
    type_name = self.type_name
    val = self.val + other.val
    constraint = And([
      constraint_for_type_name(val, type_name),
      self.constraint,
      other.constraint
    ])
    return VariableRef(None, type_name, val, constraint)

  def __mul__(self, other):
    type_name = self.type_name
    val = self.val * other.val
    constraint = And([
      constraint_for_type_name(val, type_name),
      self.constraint,
      other.constraint
    ])
    return VariableRef(None, type_name, val, constraint)

  def __truediv__(self, other):
    type_name = self.type_name
    val = self.val / other.val
    constraint = And([
      constraint_for_type_name(val, type_name),
      self.constraint,
      other.constraint
    ])
    return VariableRef(None, type_name, val, constraint)

  def __mod__(self, other):
    type_name = self.type_name
    val = self.val % other.val
    constraint = And([
      constraint_for_type_name(val, type_name),
      self.constraint,
      other.constraint
    ])
    return VariableRef(None, type_name, val, constraint) 

  def __sub__(self, other):
    type_name = self.type_name
    val = self.val - other.val
    constraint = And([
      constraint_for_type_name(val, type_name),
      self.constraint,
      other.constraint
    ])
    return VariableRef(None, type_name, val, constraint)

  def __lshift__(self, other):
    if self.top:
      left, prop = self.top
      if isinstance(left.type_name, ArrayTypeName):
        type_name = left.type_name
        val = Store(left.val, prop.val, other.val)
        constraint = And([
          constraint_for_type_name(val, type_name),
          prop.constraint,
          other.constraint
        ])
        right = VariableRef(None, type_name, val, constraint)
        left << right
      else:
        raise ValueError(left.type_name)
    else:
      assert self.name
      state.store_const(self.name, other)

  def __getitem__(self, item):
    if isinstance(self.type_name, Mapping):
      type_name = self.type_name.value_type
      val = self.val[item.val]
      constraint = And([
        constraint_for_type_name(val, type_name),
        self.constraint,
        item.constraint
      ])
      return VariableRef(None, type_name, val, constraint)
    if isinstance(self.type_name, ArrayTypeName):
      type_name = self.type_name.base_type
      val = self.val[item.val]
      constraint = And([
        constraint_for_type_name(val, type_name),
        self.constraint,
        item.constraint
      ])
      return VariableRef(None, type_name, val, constraint)

  def __getattr__(self, key):
    if isinstance(self.type_name, UserDefinedTypeName):
      referenced = next(search(self.type_name))
      if isinstance(referenced, StructDefinition):
        for idx, var in enumerate(referenced.members):
          if var.name == key:
            type_name = var.type_name
            val = self.val.sort().accessor(0, idx)(self.val)
            constraint = And([
              self.constraint,
              constraint_for_type_name(val, type_name)
            ])
            return VariableRef(None, type_name, val, constraint)

    if isinstance(self.type_name, ElementaryTypeName):
      if self.type_name.name == 'address':
        if key == 'balance':
          # @B hold of mapping from address => balance
          type_name = Mapping(ElementaryTypeName('address'), ElementaryTypeName('uint'))
          sort = sort_for_type_name(type_name)
          val = Const('@B', sort)
          constraint = constraint_for_type_name(val, type_name)
          tmp = VariableRef(None, type_name, val, constraint)
          return tmp[self]
      if self.type_name.name == 'uint':
        raise ValueError(key)

    if isinstance(self.type_name, ArrayTypeName):
      # return the length of array
      type_name = ElementaryTypeName('uint')
      name = f'{self.val.sexpr()}.length'
      val = Const(name, IntSort())
      constraint = constraint_for_type_name(val, type_name)
      if self.type_name.length:
        constraint = And([constraint, val == int(self.type_name.length.value)])
      return VariableRef(None, type_name, val, constraint)

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
    self.variables[name] = VariableRef(name, type_name, value, constraint)

  def mk_default_const(self, name, type_name):
    sort = sort_for_type_name(type_name)
    value = Const(name, sort)
    constraint = default_for_type_name(value, type_name)
    self.variables[name] = VariableRef(name, type_name, value, constraint)

  def fetch_const(self, name):
    var = self.variables[name]
    var.name = name
    return var

  def store_const(self, name, var):
    var.name = name
    self.variables[name] = var

  def add_condition(self, condition):
    self.conditions = self.conditions & condition

  def add_runtime_revert(self, revert):
    self.runtime_reverts = self.runtime_reverts | (self.conditions & revert)

  def init(self):
    self.variables = {}
    self.conditions = VariableRef(
      None,
      ElementaryTypeName('bool'),
      BoolVal(True),
      BoolVal(True)
    )
    self.runtime_reverts = VariableRef(
      None,
      ElementaryTypeName('bool'),
      BoolVal(False),
      BoolVal(True)
    )
    self.arith_check = True

state = StateRef({})

def visit_assignment(exp):
  left = visit_expression(exp.left_hand_side)
  right = visit_expression(exp.right_hand_side)
  left << right

def visit_binary_operation(exp):
  left_expression = visit_expression(exp.left_expression)
  right_expression = visit_expression(exp.right_expression)
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

def visit_unary_operation(exp):
  sub_expression = visit_expression(exp.sub_expression)
  if exp.operator == '!':
    return sub_expression.__not__()
  if exp.operator == '++':
    sub_expression = visit_expression(exp.sub_expression)
    right = visit_expression(Literal('number', '1'))
    sub_expression << (sub_expression + right)
    return visit_expression(exp.sub_expression)
  if exp.operator == '--':
    sub_expression = visit_expression(exp.sub_expression)
    right = visit_expression(Literal('number', '1'))
    sub_expression << (sub_expression - right)
    return visit_expression(exp.sub_expression)
  raise ValueError(exp.operator)

def visit_tuple_expression(exp):
  tmp = [visit_expression(x) for x in exp.components]
  return tmp[0] if len(tmp) == 1 else tmp

def visit_identifier(exp):
  return state.fetch_const(exp.name)

def visit_literal(exp):
  if exp.kind == 'bool':
    type_name = ElementaryTypeName('bool')
    value = BoolVal(exp.value == 'true')
    return VariableRef(None, type_name, value)
  if exp.kind == 'number':
    if exp.value.startswith('0x'):
      int_val = int(exp.value, 16)
    else:
      int_val = int(exp.value)
    type_name = ElementaryTypeName('uint')
    value = IntVal(int_val)
    return VariableRef(None, type_name, value)
  raise ValueError(exp.kind)

def visit_function_call(exp):
  func = visit_expression(exp.expression)
  return func(exp.arguments)

def visit_index_access(exp):
  index_expression = visit_expression(exp.index_expression)
  base_expression = visit_expression(exp.base_expression)
  tmp = base_expression[index_expression]
  tmp.top = (base_expression, index_expression)
  return tmp

def visit_member_access(exp):
  expression = visit_expression(exp.expression)
  tmp = getattr(expression, exp.member_name)
  tmp.top = (expression, exp.member_name)
  return tmp

def visit_anything(exp):
  name = FreshConst(IntSort()).sexpr()
  state.mk_const(name, exp.type_name)
  return state.fetch_const(name)

def visit_nothing(exp):
  return FreshConst(BoolSort())

def visit_elementary_type_name_expression(exp):
  if exp.name == 'address':
    return state.fetch_const('address')
  raise ValueError(exp)

def visit_expression(exp):
  if isinstance(exp, Assignment):
    return visit_assignment(exp)
  if isinstance(exp, BinaryOperation):
    return visit_binary_operation(exp)
  if isinstance(exp, Identifier):
    return visit_identifier(exp)
  if isinstance(exp, UnaryOperation):
    return visit_unary_operation(exp)
  if isinstance(exp, TupleExpression):
    return visit_tuple_expression(exp)
  if isinstance(exp, Literal):
    return visit_literal(exp)
  if isinstance(exp, FunctionCall):
    return visit_function_call(exp)
  if isinstance(exp, IndexAccess):
    return visit_index_access(exp)
  if isinstance(exp, MemberAccess):
    return visit_member_access(exp)
  if isinstance(exp, Anything):
    return visit_anything(exp)
  if isinstance(exp, Nothing):
    return visit_nothing(exp)
  if isinstance(exp, ElementaryTypeNameExpression):
    return visit_elementary_type_name_expression(exp)
  if isinstance(exp, EmitStatement):
    return None
  raise ValueError(exp)

def visit_statement(statement, returns):
  if isinstance(statement, ExpressionStatement):
    visit_expression(statement.expression)
  elif isinstance(statement, VariableDeclarationStatement):
    declarations = []
    for var in statement.declarations:
      state.mk_default_const(var.name, var.type_name)
      declarations.append(var.name)
    if statement.initial_value:
      init = visit_expression(statement.initial_value)
      for name, val in zip(declarations, init if is_array(init) else [init]):
        state.store_const(name, val)
  elif isinstance(statement, Return):
    if statement.expression:
      init = visit_expression(statement.expression)
      for r, val in zip(returns, init if is_array(init) else [init]):
        state.store_const(r.name, val)
  elif isinstance(statement, EmitStatement):
    pass
  else:
    condition = visit_expression(statement)
    state.add_condition(condition)

# solidity ensures functions
def sol_ensures(arguments):
  pre, post = arguments
  names = list(islice(gn.names(), 2))
  # Add to before all
  stmt = VariableDeclarationStatement([
    VariableDeclaration(names[0], ElementaryTypeName('bool'))
  ], pre)
  before_all.append(stmt)
  # Search for old_uint
  @dataclass
  class A(ExpVisitor):
    statements = []
    def visit_function_call(self, node):
      if isinstance(node.expression, Identifier):
        if node.expression.name == 'old_uint':
          name = next(gn.names())
          stmt = VariableDeclarationStatement([
            VariableDeclaration(name, ElementaryTypeName('uint'))
          ], self.visit_expression(node.arguments[0]))
          self.statements.append(stmt)
          return Identifier(name)
      return node
  a = A()
  post = a.visit_expression(post)
  before_all.extend(a.statements)
  # Add to after all
  stmt = VariableDeclarationStatement([
    VariableDeclaration(names[1], ElementaryTypeName('bool'))
  ], post)
  after_all.append(stmt)
  stmt = ExpressionStatement(
    FunctionCall(
      'functionCall',
      Identifier('assert'),
      [
        BinaryOperation(
          Identifier(names[0]),
          Identifier(names[1]),
          '=>'
        )
      ]
    )
  )
  after_all.append(stmt)
  return FreshConst(BoolSort())

# solidity assert functions
def sol_assert(arguments):
  arg = visit_expression(arguments[0])
  pre = And([state.conditions.constraint, state.conditions.val, arg.constraint])
  assertion = Implies(pre, arg.val)
  solver = Solver()
  solver.add(Not(assertion))
  if solver.check() == unsat:
    print(colored(f'    assert({arg.val})', 'green'))
  else:
    print(colored(f'    assert({arg.val})', 'yellow'))
  return FreshConst(BoolSort())

# solidity address cast function
def sol_address(arguments):
  return visit_expression(arguments[0])

def validate(root):
  global search
  search = partial(type_search, root)

  # validate
  for variables, functions, func, path in generate_execution_paths(root):
    state.init()
    # state functions
    state.store_const('assert', partial(sol_assert))
    state.store_const('ensures', partial(sol_ensures))
    state.store_const('address', partial(sol_address))
    # state variables
    Msg = UserDefinedTypeName('struct Msg')
    msg = VariableDeclaration('msg', Msg)
    state.mk_const(msg.name, msg.type_name)
    state.mk_const('this', ElementaryTypeName('address'))
    # global variables and parameters
    for var in variables + func.parameters:
      state.mk_const(var.name, var.type_name)
    # returns
    for var in func.returns:
      state.mk_default_const(var.name, var.type_name)
    # start validating every execution paths
    for statement in path:
      visit_statement(statement, func.returns)
      while before_all:
        visit_statement(before_all.pop(0), func.returns)
    while after_all:
      visit_statement(after_all.pop(0), func.returns)
