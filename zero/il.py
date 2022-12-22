from .ast import *
from .registry import gn
from .visitor import ExpVisitor
from itertools import islice
from functools import partial

class AlterMany(ExpVisitor):

  def __init__(self):
    self.declarations = []
    self.modifies = []

  def visit_function_call(self, exp):
    ident = exp.expression
    if isinstance(ident, Identifier):
      if ident.name == 'old_uint':
        names = list(islice(gn.names(), 1))
        self.declarations.append(
          VariableDeclarationStatement([
            VariableDeclaration(names[0], ElementaryTypeName('uint')),
          ], self.visit_expression(exp.arguments[0]))
        )
        self.modifies.append(
          ExpressionStatement(
            Assignment(exp.arguments[0], Anything(ElementaryTypeName('uint')), '=')
          )
        )
        return Identifier(names[0])
    return exp

class AlterIdent(ExpVisitor):
  def __init__(self, data):
    self.data = data

  def visit_identifier(self, exp):
    if exp.name in self.data:
      return Identifier(self.data[exp.name])
    return exp

class ILTFM:
  def __init__(self):
    self.functions = {}

  def compile_specification(self, func):
    pre_stmts = []
    post_stmts = []
    assert_stmts = []
    if not func.body: return func
    block = []
    for statement in func.body.statements:
      if isinstance(statement, ExpressionStatement):
        call = statement.expression
        if isinstance(call, FunctionCall):
          ident = call.expression
          if isinstance(ident, Identifier):
            if ident.name == 'ensures': continue
            if ident.name == 'achieves_ok' or ident.name == 'achieves_err':
              func_assert = Identifier(ident.name.split('_')[1])
              alter = AlterMany()
              pre, post = call.arguments
              names = list(islice(gn.names(), 2))

              pre_stmts.append(
                VariableDeclarationStatement([
                  VariableDeclaration(names[0], ElementaryTypeName('bool'))
                ], alter.visit_expression(pre))
              )
              post_stmts.append(
                VariableDeclarationStatement([
                  VariableDeclaration(names[1], ElementaryTypeName('bool'))
                ], alter.visit_expression(post))
              )
              assert_stmts.append(
                ExpressionStatement(
                  FunctionCall('functionCall', func_assert, [
                    BinaryOperation(
                      Identifier(names[0]),
                      Identifier(names[1]),
                      '&&'
                    )
                  ])
                )
              )
              pre_stmts = alter.declarations + pre_stmts
              continue
      block.append(statement)
    func.body = Block(block)
    func.pre = Block(pre_stmts)
    func.post = Block(post_stmts + assert_stmts)
    return func

  def load_specification(self, _id, arguments):
    if _id in self.functions:
      return self.functions[_id](arguments[::])
    return None

  def link_specification(self, _id, func):
    if func.body:
      self.functions[_id] = partial(self.__link_specification__, func)

  def __link_specification__(self, func, arguments):
    pre_stmts = []
    post_stmts = []
    mod_stmts = []
    assume_stmts = []
    # Search for specifications
    for statement in func.body.statements:
      if isinstance(statement, ExpressionStatement):
        call = statement.expression
        if isinstance(call, FunctionCall):
          ident = call.expression
          if isinstance(ident, Identifier):
            if ident.name == 'achieves_ok':
              alter = AlterMany()
              pre, post = call.arguments
              names = list(islice(gn.names(), 2))

              pre_stmts.append(
                VariableDeclarationStatement([
                  VariableDeclaration(names[0], ElementaryTypeName('bool'))
                ], alter.visit_expression(pre))
              )
              post_stmts.append(
                VariableDeclarationStatement([
                  VariableDeclaration(names[1], ElementaryTypeName('bool'))
                ], alter.visit_expression(post))
              )
              assume_stmts.append(
                ExpressionStatement(
                  FunctionCall('functionCall', Identifier('assume'), [
                    BinaryOperation(
                      Identifier(names[0]),
                      Identifier(names[1]),
                      '&&'
                    )
                  ])
                )
              )
              pre_stmts += alter.declarations
              mod_stmts += alter.modifies
    # Build ident mapping
    block, returns = [], []
    if not func.returns:
      # No return -> we return Nothing
      returns.append(Nothing())
    else:
      for param in func.returns:
        name = next(gn.names())
        block.append(
          VariableDeclarationStatement([
            VariableDeclaration(name, param.type_name)
          ], Anything(param.type_name))
        )
        arguments.append(Identifier(name))
        returns.append(Identifier(name))
    # Build mapping
    data = {}
    for param, arg in zip(func.parameters + func.returns, arguments):
      data[param.name] = next(gn.names())
      block.append(
        VariableDeclarationStatement([
          VariableDeclaration(data[param.name], param.type_name)
        ], arg)
      )
    # Alter parameters
    alter = AlterIdent(data)
    for stmt in pre_stmts + mod_stmts + post_stmts + assume_stmts:
      if isinstance(stmt, ExpressionStatement):
        stmt.expression = alter.visit_expression(stmt.expression)
      elif isinstance(stmt, VariableDeclarationStatement):
        if stmt.initial_value:
          stmt.initial_value = alter.visit_expression(stmt.initial_value)
      else:
        raise ValueError(stmt)
      block.append(stmt)
    # Construct return value
    return TupleExpression(returns), Block(block)

