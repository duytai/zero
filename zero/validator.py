from z3 import *
from .generator import *
from .visitor import *
from copy import copy
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
    ty, canonical_name = type_name.name.split(' ')
    if ty == 'contract': return IntSort()
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
    ty, canonical_name = type_name.name.split(' ')
    if ty == 'contract': return value >= 0
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
    if type_name.name == 'string':
      return value == StringVal('')
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
class FunctionRef:
  is_library: bool
  val: Any

@dataclass
class VariableRef:
  type_name: Any
  val: Any
  constraint: Any
  top: Any

  def __lt__(self, other):
    type_name = ElementaryTypeName('bool')
    val = self.val < other.val
    constraint = And([self.constraint, other.constraint])
    return VariableRef(type_name, val, constraint, None)

  def __le__(self, other):
    type_name = ElementaryTypeName('bool')
    val = self.val <= other.val
    constraint = And([self.constraint, other.constraint])
    return VariableRef(type_name, val, constraint, None)

  def __gt__(self, other):
    type_name = ElementaryTypeName('bool')
    val = self.val > other.val
    constraint = And([self.constraint, other.constraint])
    return VariableRef(type_name, val, constraint, None)

  def __ge__(self, other):
    type_name = ElementaryTypeName('bool')
    val = self.val >= other.val
    constraint = And([self.constraint, other.constraint])
    return VariableRef(type_name, val, constraint, None)

  def __or__(self, other):
    type_name = ElementaryTypeName('bool')
    val = Or([self.val, other.val])
    constraint = And([self.constraint, other.constraint])
    return VariableRef(type_name, val, constraint, None)

  def __and__(self, other):
    type_name = ElementaryTypeName('bool')
    val = And([self.val, other.val])
    constraint = And([self.constraint, other.constraint])
    return VariableRef(type_name, val, constraint, None)

  def __implies__(self, other):
    type_name = ElementaryTypeName('bool')
    val = Implies(self.val, other.val)
    constraint = And([self.constraint, other.constraint])
    return VariableRef(type_name, val, constraint, None)

  def __eq__(self, other):
    type_name = ElementaryTypeName('bool')
    val = self.val == other.val
    constraint = And([self.constraint, other.constraint])
    return VariableRef(type_name, val, constraint, None)

  def __ne__(self, other):
    type_name = ElementaryTypeName('bool')
    val = self.val != other.val
    constraint = And([self.constraint, other.constraint])
    return VariableRef(type_name, val, constraint, None)

  def __not__(self):
    type_name = ElementaryTypeName('bool')
    val = Not(self.val)
    constraint = self.constraint
    return VariableRef(type_name, val, constraint, None)

  def __add__(self, other):
    type_name = self.type_name
    val = self.val + other.val
    constraint = And([
      constraint_for_type_name(val, type_name),
      self.constraint,
      other.constraint
    ])
    return VariableRef(type_name, val, constraint, None)

  def __mul__(self, other):
    type_name = self.type_name
    val = self.val * other.val
    constraint = And([
      constraint_for_type_name(val, type_name),
      self.constraint,
      other.constraint
    ])
    return VariableRef(type_name, val, constraint, None)

  def __truediv__(self, other):
    type_name = self.type_name
    val = self.val / other.val
    constraint = And([
      constraint_for_type_name(val, type_name),
      self.constraint,
      other.constraint
    ])
    return VariableRef(type_name, val, constraint, None)

  def __mod__(self, other):
    type_name = self.type_name
    val = self.val % other.val
    constraint = And([
      constraint_for_type_name(val, type_name),
      self.constraint,
      other.constraint
    ])
    return VariableRef(type_name, val, constraint, None)

  def __sub__(self, other):
    type_name = self.type_name
    val = self.val - other.val
    constraint = And([
      constraint_for_type_name(val, type_name),
      self.constraint,
      other.constraint
    ])
    return VariableRef(type_name, val, constraint, None)

  def __lshift__(self, other):
    if isinstance(self.top, Identifier):
      type_name = other.type_name
      val = z3.FreshConst(other.val.sort())
      constraint = z3.BoolVal(True)
      tmp = VariableRef(type_name, val, constraint, None)
      state.add_condition(tmp == other)
      #
      name = self.top.name
      state.store_const(name, tmp)
    else:
      left, prop = self.top
      if isinstance(left.type_name, ArrayTypeName):
        type_name = left.type_name
        val = Store(left.val, prop.val, other.val)
        constraint = And([
          constraint_for_type_name(val, type_name),
          prop.constraint,
          other.constraint
        ])
        right = VariableRef(type_name, val, constraint, None)
        left << right
      elif isinstance(left.type_name, Mapping):
        type_name = left.type_name
        val = Store(left.val, prop.val, other.val)
        constraint = And([
          constraint_for_type_name(val, type_name),
          prop.constraint,
          other.constraint
        ])
        right = VariableRef(type_name, val, constraint, None)
        left << right
      else:
        raise ValueError(left.type_name)

  def __getitem__(self, item):
    if isinstance(self.type_name, Mapping):
      type_name = self.type_name.value_type
      val = self.val[item.val]
      constraint = And([
        constraint_for_type_name(val, type_name),
        self.constraint,
        item.constraint
      ])
      return VariableRef(type_name, val, constraint, None)
    if isinstance(self.type_name, ArrayTypeName):
      type_name = self.type_name.base_type
      val = self.val[item.val]
      constraint = And([
        constraint_for_type_name(val, type_name),
        self.constraint,
        item.constraint
      ])
      return VariableRef(type_name, val, constraint, None)

  def __getattr__(self, key):
    # Check for default properties first
    if isinstance(self.type_name, ElementaryTypeName):
      if self.type_name.name == 'address':
        if key == 'balance':
          return state.fetch_const('@B')[self]
        if key == 'transfer':
          def transfer(arguments):
            balances = state.fetch_const('@B')
            dest = self
            this = state.fetch_const('this')
            value = visit_expression(arguments[0])
            state.add_condition(balances[this] >= value)
            # Update balance
            new_val = Store(balances.val, this.val, (balances[this] - value).val)
            new_val = Store(new_val, dest.val,(balances[this] + value).val)
            new_constraint = And([balances.constraint, dest.constraint, this.constraint, value.constraint])
            balances.val = new_val
            balances.constraint = new_constraint
            return None
          return FunctionRef(False, transfer)
        if key == 'send':
          def send(arguments):
            balances = state.fetch_const('@B')
            dest = self
            this = state.fetch_const('this')
            value = visit_expression(arguments[0])
            result = balances[this] >= value
            # Update balance
            new_val = Store(balances.val, this.val, (balances[this] - value).val)
            new_val = Store(new_val, dest.val,(balances[this] + value).val)
            new_constraint = And([balances.constraint, dest.constraint, this.constraint, value.constraint])
            balances.val = If(result.val, new_val, balances.val)
            balances.constraint = If(result.val, new_constraint, balances.constraint)
            return balances[this] >= value
          return FunctionRef(False, send)

    if isinstance(self.type_name, ArrayTypeName):
      # Return the length of array
      # TODO: load length constraint
      type_name = ElementaryTypeName('uint')
      val = FreshConst(IntSort())
      constraint = constraint_for_type_name(val, type_name)
      if self.type_name.length:
        constraint = And([constraint, val == int(self.type_name.length.value)])
      return VariableRef(type_name, val, constraint, None)

    # Then search for defined properties
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
          return VariableRef(type_name, val, constraint, None)

    if isinstance(referenced, ContractDefinition):
      if referenced.kind == 'library':
        for idx, func in enumerate(referenced.nodes):
          if func.name == key:
            return FunctionRef(True, partial(sol_func, func))
      if referenced.kind == 'interface':
        for idx, func in enumerate(referenced.nodes):
          if func.name == key:
            return FunctionRef(False, partial(sol_interface_function, func))

    raise ValueError(key)

@dataclass
class StateRef:
  variables: dict
  conditions: Optional[VariableRef] = None

  def __copy__(self):
    _variables = dict(self.variables.items())
    _conditions = self.conditions
    return StateRef(_variables, _conditions)

  def mk_const(self, name, type_name):
    sort = sort_for_type_name(type_name)
    value = FreshConst(sort)
    constraint = constraint_for_type_name(value, type_name)
    self.variables[name] = VariableRef(type_name, value, constraint, None)

  def mk_default_const(self, name, type_name):
    sort = sort_for_type_name(type_name)
    value = FreshConst(sort)
    constraint = default_for_type_name(value, type_name)
    self.variables[name] = VariableRef(type_name, value, constraint, None)

  def fetch_const(self, name):
    var = self.variables[name]
    return var

  def store_const(self, name, var):
    self.variables[name] = var

  def add_condition(self, condition):
    self.conditions = self.conditions & condition

  def init(self):
    self.variables = {}
    self.conditions = VariableRef(
      ElementaryTypeName('bool'),
      BoolVal(True),
      BoolVal(True),
      None
    )

state = StateRef({})

def visit_assignment(exp):
  right = visit_expression(exp.right_hand_side)
  left = visit_expression(exp.left_hand_side)
  if exp.operator == '+=':
    right = left + right
  if exp.operator == '-=':
    right = left - right

  tmp = next(gn.names())
  ident = None
  if isinstance(exp.left_hand_side, IndexAccess):
    if isinstance(exp.left_hand_side.base_expression, Identifier):
      ident = exp.left_hand_side.base_expression
      if f'sum_{ident.name}' in state.variables:
        statement = VariableDeclarationStatement([
          VariableDeclaration(tmp, ElementaryTypeName('uint'))
        ], exp.left_hand_side)
        visit_statement(statement)
      else:
        ident = None

  left << right

  if ident:
    statement = ExpressionStatement(
      Assignment(
        Identifier(f'sum_{ident.name}'),
        BinaryOperation(
          BinaryOperation(
            Identifier(f'sum_{ident.name}'),
            Identifier(tmp),
            '-'
          ),
          exp.left_hand_side,
          '+'
        ),
        '='
      )
    )
    visit_statement(statement)

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
  tmp = state.fetch_const(exp.name)
  tmp.top = exp
  return tmp

def visit_literal(exp):
  if exp.kind == 'bool':
    type_name = ElementaryTypeName('bool')
    value = BoolVal(exp.value == 'true')
    return VariableRef(type_name, value, BoolVal(True), None)
  if exp.kind == 'number':
    if exp.value.startswith('0x'):
      int_val = int(exp.value, 16)
    else:
      int_val = int(exp.value)
    type_name = ElementaryTypeName('uint')
    value = IntVal(int_val)
    return VariableRef(type_name, value, BoolVal(True), None)
  raise ValueError(exp.kind)

def visit_function_call(exp):
  func = visit_expression(exp.expression)
  if func.is_library:
    return func.val([exp.expression.expression] + exp.arguments)
  return func.val(exp.arguments)

def visit_index_access(exp):
  index_expression = visit_expression(exp.index_expression)
  base_expression = visit_expression(exp.base_expression)
  tmp = base_expression[index_expression]
  tmp.top = (base_expression, index_expression)
  return tmp

def visit_member_access(exp):
  if isinstance(exp.expression, Identifier):
    if exp.expression.name == 'super':
      name = f'super.{exp.member_name}'
      return state.fetch_const(name)
  expression = visit_expression(exp.expression)
  tmp = getattr(expression, exp.member_name)
  tmp.top = (expression, exp.member_name)
  return tmp

def visit_anything(exp):
  name = next(gn.names())
  state.mk_const(name, exp.type_name)
  return state.fetch_const(name)

def visit_nothing(exp):
  return FreshConst(BoolSort())

def visit_elementary_type_name_expression(exp):
  if exp.name == 'address':
    return state.fetch_const('address')
  raise ValueError(exp)

def visit_new_expression(exp):
  def new(exp, arguments):
    type_name = exp.type_name
    if isinstance(type_name, ArrayTypeName):
      base_type = type_name.base_type
      if isinstance(base_type, ElementaryTypeName):
        sort = sort_for_type_name(type_name)
        val = FreshConst(sort)
        constraint = default_for_type_name(val, type_name)
        # TODO: add length constraint
        # e = visit_expression(arguments[0])
        return VariableRef(type_name, val, constraint, None)
    raise ValueError(exp)
  return FunctionRef(False, partial(new, exp))

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
  if isinstance(exp, NewExpression):
    return visit_new_expression(exp)
  raise ValueError(exp)

def visit_statement(statement, returns=None):
  if isinstance(statement, ExpressionStatement):
    visit_expression(statement.expression)
  elif isinstance(statement, VariableDeclarationStatement):
    declarations = [x.name for x in statement.declarations]
    if statement.initial_value:
      init = visit_expression(statement.initial_value)
      for name, val in zip(declarations, init if isinstance(init, list) else [init]):
        state.store_const(name, val)
    else:
      for var in statement.declarations:
        state.mk_default_const(var.name, var.type_name)
  elif isinstance(statement, Return):
    if statement.expression:
      init = visit_expression(statement.expression)
      for r, val in zip(returns, init if isinstance(init, list) else [init]):
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
        if node.expression.name == 'old_address':
          name = next(gn.names())
          stmt = VariableDeclarationStatement([
            VariableDeclaration(name, ElementaryTypeName('address'))
          ], self.visit_expression(node.arguments[0]))
          self.statements.append(stmt)
          return Identifier(name)
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

def get_idents(exp):
  idents = set()
  stack = [exp]
  while stack:
    item = stack.pop()
    if is_const(item) and not item.children():
      kind = item.decl().kind()
      if kind == Z3_OP_UNINTERPRETED:
        idents.add(item)
    stack += item.children()
  return idents

# solidity ok functions
def sol_ok(arguments):
  arg = visit_expression(arguments[0])
  post = arg.val
  pre = And([state.conditions.constraint, state.conditions.val, arg.constraint])
  variables = list(get_idents(pre).difference(get_idents(post)))
  if variables:
    assertion = Implies(post, Exists(variables, pre))
  else:
    assertion = Implies(post, pre)

  # assertion = And([state.conditions.constraint, state.conditions.val, arg.constraint, arg.val])
  solver = Solver()
  solver.add(Not(assertion))
  if solver.check() == unsat:
    print(colored(f'    ok({arg.val})', 'green'))
  else:
    print(colored(f'    ok({arg.val})', 'yellow'))

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

# solidity require function
def sol_require(arguments):
  arg = visit_expression(arguments[0])
  state.add_condition(arg)

# solidity assume function
def sol_assume(arguments):
  arg = visit_expression(arguments[0])
  state.add_condition(arg)

# solidity address cast function
def sol_address(arguments):
  return visit_expression(arguments[0])

# solidity sum(balances)
def sol_sum(arguments):
  name = arguments[0].name
  return visit_expression(Identifier(f'sum_{name}'))

# solidity reverts_if()
def sol_reverts_if(arguments):
  # TODO: handle reverts if
  return None

# solidity interface assignment
# ICounter ic = ICounter(0x0000)
def sol_interface(name, arguments):
  var = visit_expression(arguments[0])
  var.type_name = UserDefinedTypeName(f'contract {name}')
  return var

# solidity interface function
def sol_interface_function(function, arguments):
  returns = []
  for var in function.returns:
    name = next(gn.names())
    stmt = VariableDeclarationStatement([
      VariableDeclaration(name, var.type_name)
    ], Anything(var.type_name))
    visit_statement(stmt)
    returns.append(Identifier(name))
  return visit_expression(TupleExpression(returns))

def sol_func(function, arguments):
  global state, before_all, after_all
  # If it is a private funciton -> try to prove
  if function.visibility in ['private', 'internal']:
    _state, _before_all, _after_all = copy(state), before_all[::], after_all[::]
    # Try to prove before using specification
    for param, arg in zip(function.parameters, arguments):
      statement = VariableDeclarationStatement([
        VariableDeclaration(param.name, param.type_name)
      ], Anything(param.type_name))
      visit_statement(statement)
    for var in function.returns:
      state.mk_default_const(var.name, var.type_name)
    # Backup here
    before_all, after_all = [], []
    for path in compute_execution_paths(function.body):
      __state = copy(state)
      for statement in path:
        visit_statement(statement, function.returns)
        while before_all:
          visit_statement(before_all.pop(0), function.returns)
      while after_all:
        visit_statement(after_all.pop(0), function.returns)
      state = __state
    # Reset state
    state, before_all, after_all = _state, _before_all, _after_all

  # Load specifications
  before, mid, after = [], [], []
  returns = []
  data = {}
  for x in function.returns:
    name = next(gn.names())
    before.append(
      VariableDeclarationStatement([
        VariableDeclaration(name, x.type_name)
      ], Anything(x.type_name))
    )
    returns.append(Identifier(name))
  for var, value in zip(function.parameters + function.returns, arguments + returns):
    name = next(gn.names())
    before.append(
      VariableDeclarationStatement([
        VariableDeclaration(name, var.type_name)
      ], value)
    )
    data[var.name] = name
  # Replace idents
  @dataclass
  class B(ExpVisitor):
    data: Any
    before = []
    mid = []
    def visit_identifier(self, exp):
      if exp.name in self.data:
        return Identifier(self.data[exp.name])
      return exp
    def visit_function_call(self, node):
      if isinstance(node.expression, Identifier):
        if node.expression.name == 'old_address':
          name = next(gn.names())
          ident = self.visit_expression(node.arguments[0])
          stmt = VariableDeclarationStatement([
            VariableDeclaration(name, ElementaryTypeName('address'))
          ], ident)
          self.before.append(stmt)
          stmt = ExpressionStatement(
            Assignment(ident, Anything(ElementaryTypeName('address')), '=')
          )
          self.mid.append(stmt)
          return Identifier(name)
        if node.expression.name == 'old_uint':
          name = next(gn.names())
          ident = self.visit_expression(node.arguments[0])
          stmt = VariableDeclarationStatement([
            VariableDeclaration(name, ElementaryTypeName('uint'))
          ], ident)
          self.before.append(stmt)
          stmt = ExpressionStatement(
            Assignment(ident, Anything(ElementaryTypeName('uint')), '=')
          )
          self.mid.append(stmt)
          return Identifier(name)
      return node
  # Search ensures
  for statement in function.body.statements:
    if isinstance(statement, ExpressionStatement):
      if isinstance(statement.expression, FunctionCall):
        call = statement.expression
        if isinstance(call.expression, Identifier):
          ident = call.expression
          if ident.name == 'ensures':
            b = B(data)
            pre, post = call.arguments
            names = list(islice(gn.names(), 2))
            before.append(
              VariableDeclarationStatement([
                VariableDeclaration(names[0], ElementaryTypeName('bool'))
              ], b.visit_expression(pre))
            )
            pp = b.visit_expression(post)
            before += b.before
            mid += b.mid
            after.append(
              VariableDeclarationStatement([
                VariableDeclaration(names[1], ElementaryTypeName('bool'))
              ], pp)
            )
            after.append(
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
  for x in before + mid + after:
    visit_statement(x)
  return visit_expression(TupleExpression(returns))

def validate(root):
  global search

  # validate
  for contracts, libraries, variables, functions, func, path in generate_execution_paths(root):
    state.init()
    search = partial(type_search, root, libraries)
    # visible contracts
    for name in contracts:
      state.store_const(
        name,
        FunctionRef(False, partial(sol_interface, name))
      )
    # Super detection
    fc = {}
    for function in functions:
      if function.name not in fc: fc[function.name] = 0
      fc[function.name] += 1
    # visible functions
    for function in functions:
      if fc[function.name] > 1:
        state.store_const(
          f'super.{function.name}',
          FunctionRef(False, partial(sol_func, function))
        )
      else:
        state.store_const(
          function.name,
          FunctionRef(False, partial(sol_func, function))
        )
      fc[function.name] -= 1
    # State functions
    state.store_const('ok', FunctionRef(False, partial(sol_ok)))
    state.store_const('assert', FunctionRef(False, partial(sol_assert)))
    state.store_const('require', FunctionRef(False, partial(sol_require)))
    state.store_const('ensures', FunctionRef(False, partial(sol_ensures)))
    state.store_const('address', FunctionRef(False, partial(sol_address)))
    state.store_const('assume', FunctionRef(False, partial(sol_assume)))
    state.store_const('reverts_if', FunctionRef(False, partial(sol_reverts_if)))
    # Block
    Block = UserDefinedTypeName('struct Block')
    block = VariableDeclaration('block', Block)
    state.mk_const(block.name, block.type_name)
    state.mk_const('now', ElementaryTypeName('uint'))
    now = visit_expression(MemberAccess('timestamp', Identifier('block')))
    state.store_const('now', now)
    # Msg
    Msg = UserDefinedTypeName('struct Msg')
    msg = VariableDeclaration('msg', Msg)
    state.mk_const(msg.name, msg.type_name)
    #
    state.mk_const('this', ElementaryTypeName('address'))
    # Balances
    balances = VariableDeclaration(
      '@B',
      Mapping(
        ElementaryTypeName('address'),
        ElementaryTypeName('uint')
      )
    )
    state.mk_const(balances.name, balances.type_name)
    # Create a variable for sum
    for var in variables:
      if isinstance(var.type_name, Mapping):
        type_name = var.type_name
        if isinstance(type_name.value_type, ElementaryTypeName):
          if type_name.value_type.name.startswith('uint'):
            state.mk_const(f'sum_{var.name}', type_name.value_type)
            state.store_const(f'sum_uint', FunctionRef(False, partial(sol_sum)))
    # Global variables and parameters
    for var in variables + func.parameters:
      state.mk_const(var.name, var.type_name)
    # Returns
    for var in func.returns:
      state.mk_default_const(var.name, var.type_name)
    # Start validating every execution paths
    for statement in path:
      visit_statement(statement, func.returns)
      while before_all:
        visit_statement(before_all.pop(0), func.returns)
    while after_all:
      visit_statement(after_all.pop(0), func.returns)
