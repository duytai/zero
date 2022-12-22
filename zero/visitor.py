from .ast import *

class ExpVisitor:
  def visit_binary_operation(self, exp):
    return BinaryOperation(
      self.visit_expression(exp.left_expression),
      self.visit_expression(exp.right_expression),
      exp.operator
    )

  def visit_unary_operation(self, exp):
    return UnaryOperation(
      self.visit_expression(exp.sub_expression),
      exp.prefix,
      exp.operator
    )

  def visit_tuple_expression(self, exp):
    return TupleExpression(
      [self.visit_expression(x) for x in exp.components]
    )

  def visit_assignment(self, exp):
    return Assignment(
      self.visit_expression(exp.left_hand_side),
      self.visit_expression(exp.right_hand_side),
      exp.operator
    )

  def visit_identifier(self, exp):
    return Identifier(exp.name)

  def visit_literal(self, exp):
    return Literal(exp.kind, exp.value)

  def visit_function_call(self, exp):
    return FunctionCall(
      exp.kind,
      self.visit_expression(exp.expression),
      [self.visit_expression(x) for x in exp.arguments]
    )

  def visit_index_access(self, exp):
    return IndexAccess(
      self.visit_expression(exp.index_expression),
      self.visit_expression(exp.base_expression)
    )

  def visit_member_access(self, exp):
    return MemberAccess(
      exp.member_name,
      self.visit_expression(exp.expression)
    )

  def visit_elementary_type_name_expression(self, exp):
    return ElementaryTypeNameExpression(exp.name)

  def visit_anything(self, exp):
    return Anything(exp.type_name)

  def visit_nothing(self, exp):
    return Nothing()

  def visit_expression(self, exp):
    if isinstance(exp, BinaryOperation):
      return self.visit_binary_operation(exp)
    if isinstance(exp, UnaryOperation):
      return self.visit_unary_operation(exp)
    if isinstance(exp, TupleExpression):
      return self.visit_tuple_expression(exp)
    if isinstance(exp, Assignment):
      return self.visit_assignment(exp)
    if isinstance(exp, Identifier):
      return self.visit_identifier(exp)
    if isinstance(exp, Literal):
      return self.visit_literal(exp)
    if isinstance(exp, FunctionCall):
      return self.visit_function_call(exp)
    if isinstance(exp, IndexAccess):
      return self.visit_index_access(exp)
    if isinstance(exp, MemberAccess):
      return self.visit_member_access(exp)
    if isinstance(exp, ElementaryTypeNameExpression):
      return self.visit_elementary_type_name_expression(exp)
    if isinstance(exp, Anything):
      return self.visit_anything(exp)
    if isinstance(exp, Nothing):
      return self.visit_nothing(exp)
    raise ValueError(exp)

class StmtVisitor:
  def visit_block(self, statement):
    return Block([self.visit_statement(x) for x in statement.statements])

  def visit_for_statement(self, statement):
    return ForStatement(
      self.visit_statement(statement.init),
      statement.condition,
      self.visit_statement(statement.loop),
      self.visit_statement(statement.body)
    )

  def visit_if_statement(self, statement):
    return IfStatement(
      statement.condition,
      self.visit_statement(statement.true_body),
      self.visit_statement(statement.false_body) if statement.false_body else None
    )

  def visit_emit_statement(self, statement):
    return EmitStatement()

  def visit_statement(self, statement):
    if isinstance(statement, Block):
      return self.visit_block(statement)
    if isinstance(statement, ExpressionStatement):
      return self.visit_expression_statement(statement)
    if isinstance(statement, VariableDeclarationStatement):
      return self.visit_variable_declaration_statement(statement)
    if isinstance(statement, ForStatement):
      return self.visit_return(statement)
    if isinstance(statement, IfStatement):
      return self.visit_if_statement(statement)
    if isinstance(statement, Return):
      return self.visit_return(statement)
    if isinstance(statement, EmitStatement):
      return self.visit_emit_statement(statement)
    raise ValueError(statement)

  def visit_return(self, statement):
    return Return(statement.expression)

  def visit_expression_statement(self, statement):
    return ExpressionStatement(statement.expression)

  def visit_variable_declaration_statement(self, statement):
    return VariableDeclarationStatement(
      statement.declarations,
      statement.initial_value
    )

