from .ast import *


global_variables_by_contract = {}
global_interfaces_by_id = {}

"""
Parse ast without modification
"""

def parse_without_tfm(node):
  if node['nodeType'] == 'SourceUnit':
    nodes = [parse_without_tfm(x) for x in node['nodes']]
    return SourceUnit(nodes)

  if node['nodeType'] == 'ContractDefinition':
    name = node['name']
    nodes  = [parse_without_tfm(x) for x in node['nodes']]
    return ContractDefinition(name, nodes)

  if node['nodeType'] == 'FunctionDefinition':
    name = node['name']
    parameters = [parse_without_tfm(x) for x in node['parameters']['parameters']]
    returns = [parse_without_tfm(x) for x in node['returnParameters']['parameters']]
    body = parse_without_tfm(node['body']) if node['body'] else None
    visibility = node['visibility']
    return FunctionDefinition(name, parameters, returns, body, visibility)

  if node['nodeType'] == 'VariableDeclaration':
    name = node['name']
    type_name = parse_without_tfm(node['typeName'])
    return VariableDeclaration(name, type_name)

  if node['nodeType'] == 'ElementaryTypeName':
    name = node['name']
    return ElementaryTypeName(name)

  if node['nodeType'] == 'Block':
    statements = [parse_without_tfm(x) for x in node['statements']]
    return Block(statements)

  if node['nodeType'] == 'ExpressionStatement':
    expression = parse_without_tfm(node['expression'])
    return ExpressionStatement(expression)

  if node['nodeType'] == 'Assignment':
    left_hand_side = parse_without_tfm(node['leftHandSide'])
    right_hand_side = parse_without_tfm(node['rightHandSide'])
    operator = node['operator']
    return Assignment(left_hand_side, right_hand_side, operator)

  if node['nodeType'] == 'Identifier':
    name = node['name']
    return Identifier(name)

  if node['nodeType'] == 'BinaryOperation':
    left_expression = parse_without_tfm(node['leftExpression'])
    right_expression = parse_without_tfm(node['rightExpression'])
    operator = node['operator']
    return BinaryOperation(left_expression, right_expression, operator)

  if node['nodeType'] == 'IfStatement':
    condition = parse_without_tfm(node['condition'])
    true_body = parse_without_tfm(node['trueBody'])
    false_body = parse_without_tfm(node['falseBody']) if node['falseBody'] else None
    return IfStatement(condition, true_body, false_body)

  if node['nodeType'] == 'UnaryOperation':
    sub_expression = parse_without_tfm(node['subExpression'])
    prefix = node['prefix']
    operator = node['operator']
    return UnaryOperation(sub_expression, prefix, operator)

  if node['nodeType'] == 'TupleExpression':
    components = [parse_without_tfm(x) for x in node['components']]
    return TupleExpression(components)

  if node['nodeType'] == 'Literal':
    kind = node['kind']
    value = node['value']
    return Literal(kind, value)

  if node['nodeType'] == 'FunctionCall':
    kind = node['kind']
    expression = parse_without_tfm(node['expression'])
    arguments = [parse_without_tfm(x) for x in node['arguments']]
    return FunctionCall(kind, expression, arguments)

  if node['nodeType'] == 'Mapping':
    key_type = parse_without_tfm(node['keyType'])
    value_type = parse_without_tfm(node['valueType'])
    return Mapping(key_type, value_type)

  if node['nodeType'] == 'IndexAccess':
    index_expression = parse_without_tfm(node['indexExpression'])
    base_expression = parse_without_tfm(node['baseExpression'])
    return IndexAccess(index_expression, base_expression)

  if node['nodeType'] == 'MemberAccess':
    member_name = node['memberName']
    expression = parse_without_tfm(node['expression'])
    return MemberAccess(member_name, expression)

  if node['nodeType'] == 'StructDefinition':
    name = node['name']
    members = [parse_without_tfm(x) for x in node['members']]
    tmp = StructDefinition(name, members)
    global_interfaces_by_id[node['id']] = StructDefinition
    return tmp

  if node['nodeType'] == 'UserDefinedTypeName':
    name = node['name']
    referenced = global_interfaces_by_id.get(node['referencedDeclaration'])
    return UserDefinedTypeName(name, referenced)

  if node['nodeType'] == 'ArrayTypeName':
    base_type = parse_without_tfm(node['baseType'])
    length = parse_without_tfm(node['length']) if node['length'] else None
    return ArrayTypeName(base_type, length)

  if node['nodeType'] == 'VariableDeclarationStatement':
    declarations = [parse_without_tfm(x) for x in node['declarations']]
    initial_value = parse_without_tfm(node['initialValue']) if node['initialValue'] else None
    return VariableDeclarationStatement(declarations, initial_value)

  if node['nodeType'] == 'ForStatement':
    init = parse_without_tfm(node['initializationExpression'])
    condition = parse_without_tfm(node['condition'])
    loop = parse_without_tfm(node['loopExpression'])
    body = parse_without_tfm(node['body'])
    return ForStatement(init, condition, loop, body)

  if node['nodeType'] == 'Return':
    expression = parse_without_tfm(node['expression']) if node['expression'] else None
    return Return(expression)

  if node['nodeType'] == 'ElementaryTypeNameExpression':
    return ElementaryTypeNameExpression(node['typeName'])

  if node['nodeType'] == 'UsingForDirective':
    return UsingForDirective()

  if node['nodeType'] == 'EmitStatement':
    return EmitStatement()

  if node['nodeType'] == 'EventDefinition':
    return EventDefinition()

  if node['nodeType'] == 'ModifierDefinition':
    return ModifierDefinition()

  raise ValueError(node['nodeType'])


"""
Parse ast with modification using tfm
"""


def parse_with_tfm(node, tfm):

  if node['nodeType'] == 'SourceUnit':
    nodes = [parse_with_tfm(x, tfm) for x in node['nodes']]
    return SourceUnit(nodes)

  if node['nodeType'] == 'ContractDefinition':
    parents = node['linearizedBaseContracts'][1:]
    extra = []
    for cid in parents:
      extra += global_variables_by_contract[cid]
    # ->>> Load variables from parent contracts
    name = node['name']
    nodes  = [parse_with_tfm(x, tfm) for x in node['nodes'] + extra]
    extra = []
    for x in nodes:
      if isinstance(x, VariableDeclaration):
        if isinstance(x.type_name, Mapping):
          if isinstance(x.type_name.value_type, ElementaryTypeName):
            if x.type_name.value_type.name.startswith('uint'):
              extra.append(
                VariableDeclaration(
                  f'sum_{x.name}',
                  x.type_name.value_type,
                )
              )
    return ContractDefinition(name, extra + nodes)

  if node['nodeType'] == 'FunctionDefinition':
    name = node['name']
    parameters = [parse_with_tfm(x, tfm) for x in node['parameters']['parameters']]
    returns = [parse_with_tfm(x, tfm) for x in node['returnParameters']['parameters']]
    body = parse_with_tfm(node['body'], tfm) if node['body'] else None
    visibility = node['visibility']
    func = FunctionDefinition(name, parameters, returns, body, visibility)
    return tfm.compile_specification(func)

  if node['nodeType'] == 'VariableDeclaration':
    name = node['name']
    type_name = parse_with_tfm(node['typeName'], tfm)
    return VariableDeclaration(name, type_name)

  if node['nodeType'] == 'ElementaryTypeName':
    name = node['name']
    return ElementaryTypeName(name)

  if node['nodeType'] == 'Block':
    statements = [parse_with_tfm(x, tfm) for x in node['statements']]
    return Block(statements)

  if node['nodeType'] == 'ExpressionStatement':
    expression = parse_with_tfm(node['expression'], tfm)
    return ExpressionStatement(expression)

  if node['nodeType'] == 'Assignment':
    left_hand_side = parse_with_tfm(node['leftHandSide'], tfm)
    right_hand_side = parse_with_tfm(node['rightHandSide'], tfm)
    operator = node['operator']
    return Assignment(left_hand_side, right_hand_side, operator)

  if node['nodeType'] == 'Identifier':
    name = node['name']
    return Identifier(name)

  if node['nodeType'] == 'BinaryOperation':
    left_expression = parse_with_tfm(node['leftExpression'], tfm)
    right_expression = parse_with_tfm(node['rightExpression'], tfm)
    operator = node['operator']
    return BinaryOperation(left_expression, right_expression, operator)

  if node['nodeType'] == 'IfStatement':
    condition = parse_with_tfm(node['condition'], tfm)
    true_body = parse_with_tfm(node['trueBody'], tfm)
    false_body = parse_with_tfm(node['falseBody'], tfm) if node['falseBody'] else None
    return IfStatement(condition, true_body, false_body)

  if node['nodeType'] == 'UnaryOperation':
    sub_expression = parse_with_tfm(node['subExpression'], tfm)
    prefix = node['prefix']
    operator = node['operator']
    return UnaryOperation(sub_expression, prefix, operator)

  if node['nodeType'] == 'TupleExpression':
    components = [parse_with_tfm(x, tfm) for x in node['components']]
    return TupleExpression(components)

  if node['nodeType'] == 'Literal':
    kind = node['kind']
    value = node['value']
    return Literal(kind, value)

  if node['nodeType'] == 'FunctionCall':
    kind = node['kind']
    expression = parse_with_tfm(node['expression'], tfm)
    arguments = [parse_with_tfm(x, tfm) for x in node['arguments']]
    
    # Attached loaded specification
    overridle = None
    # Internal funciton call
    if node['expression']['nodeType'] == 'Identifier':
      id_ = node['expression']['referencedDeclaration']
      overridle = tfm.load_specification(id_, arguments)
    if node['expression']['nodeType'] == 'MemberAccess':
      id_ = node['expression']['referencedDeclaration']
      arguments = [parse_with_tfm(node['expression']['expression'], tfm)] + arguments
      overridle = tfm.load_specification(id_, arguments)
    return FunctionCall(kind, expression, arguments, overridle)

  if node['nodeType'] == 'Mapping':
    key_type = parse_with_tfm(node['keyType'], tfm)
    value_type = parse_with_tfm(node['valueType'], tfm)
    return Mapping(key_type, value_type)

  if node['nodeType'] == 'IndexAccess':
    index_expression = parse_with_tfm(node['indexExpression'], tfm)
    base_expression = parse_with_tfm(node['baseExpression'], tfm)
    return IndexAccess(index_expression, base_expression)

  if node['nodeType'] == 'MemberAccess':
    member_name = node['memberName']
    expression = parse_with_tfm(node['expression'], tfm)
    return MemberAccess(member_name, expression)

  if node['nodeType'] == 'StructDefinition':
    name = node['name']
    members = [parse_with_tfm(x, tfm) for x in node['members']]
    tmp = StructDefinition(name, members)
    global_interfaces_by_id[node['id']] = tmp
    return tmp

  if node['nodeType'] == 'UserDefinedTypeName':
    name = node['name']
    referenced = global_interfaces_by_id.get(node['referencedDeclaration'])
    return UserDefinedTypeName(name, referenced)

  if node['nodeType'] == 'ArrayTypeName':
    base_type = parse_with_tfm(node['baseType'], tfm)
    length = parse_with_tfm(node['length'], tfm) if node['length'] else None
    return ArrayTypeName(base_type, length)

  if node['nodeType'] == 'VariableDeclarationStatement':
    declarations = [parse_with_tfm(x, tfm) for x in node['declarations']]
    initial_value = parse_with_tfm(node['initialValue'], tfm) if node['initialValue'] else None
    return VariableDeclarationStatement(declarations, initial_value)

  if node['nodeType'] == 'ForStatement':
    init = parse_with_tfm(node['initializationExpression'], tfm)
    condition = parse_with_tfm(node['condition'], tfm)
    loop = parse_with_tfm(node['loopExpression'], tfm)
    body = parse_with_tfm(node['body'], tfm)
    return ForStatement(init, condition, loop, body)

  if node['nodeType'] == 'Return':
    expression = parse_with_tfm(node['expression'], tfm) if node['expression'] else None
    return Return(expression)

  if node['nodeType'] == 'ElementaryTypeNameExpression':
    return ElementaryTypeNameExpression(node['typeName'])

  if node['nodeType'] == 'UsingForDirective':
    return UsingForDirective()

  if node['nodeType'] == 'EmitStatement':
    return EmitStatement()

  if node['nodeType'] == 'EventDefinition':
    return EventDefinition()

  if node['nodeType'] == 'ModifierDefinition':
    return ModifierDefinition()

  raise ValueError(node['nodeType'])

def parse_specification(node, tfm = None):
  if node['nodeType'] == 'SourceUnit':
    for x in node['nodes']:
      parse_specification(x, tfm)
  elif node['nodeType'] == 'ContractDefinition':
    cid = node['id']
    global_variables_by_contract[cid] = []
    for x in node['nodes']:
      if x['nodeType'] == 'VariableDeclaration':
        global_variables_by_contract[cid].append(x)
      parse_specification(x, tfm)
  elif node['nodeType'] == 'FunctionDefinition':
    func = parse_without_tfm(node)
    tfm.link_specification(node['id'], func)
  else:
    return

def parse(node, tfm = None):
  parse_specification(node, tfm)
  return parse_with_tfm(node, tfm)