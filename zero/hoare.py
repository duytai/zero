from .ast import *
from .registry import gn
from .visitor import ExpVisitor
from itertools import islice
from functools import partial

class AlterOld(ExpVisitor):

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
            FunctionCall('functionCall', Identifier('modifies'), exp.arguments)
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

class HoareTFM:
  def __init__(self):
    self.functions = {}
    self.statements = []

  def exec_specification(self, _id, arguments):
    if _id in self.functions:
      val, block = self.functions[_id](arguments)
      self.statements += block
      return val
    return None

  def visit_specification(self, _id, func):
    if func.body:
      self.functions[_id] = partial(self.__visit_specification__, func)

  def __visit_specification__(self, func, arguments):
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
            if ident.name == 'ensures':
              alter = AlterOld()
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
                      '=>'
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
    return TupleExpression(returns), block

