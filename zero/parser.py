from .ast import *

def type_search(root, libraries, type_name):
  # Search library for simple type name
  if isinstance(type_name, ElementaryTypeName):
    for library in libraries:
      if library.type_name == type_name:
        library_name = library.library_name.name
        ty, canonical_name = library_name.split(' ')
        for node in root.nodes:
          if isinstance(node, ContractDefinition):
            if node.kind == ty and node.name == canonical_name:
              yield node
  # Search for contract or struct definition
  if isinstance(type_name, UserDefinedTypeName):
    ty, canonical_name = type_name.name.split(' ')
    # If is struct definition
    if ty == 'struct':
      # Global structure for msg
      if canonical_name == 'Msg':
        members = [
          VariableDeclaration('sender', ElementaryTypeName('address')),
          VariableDeclaration('value', ElementaryTypeName('uint'))
        ]
        yield StructDefinition('struct Msg', members)
      else:
        contract_name, struct_name = canonical_name.split('.')
        for node in root.nodes:
          if isinstance(node, ContractDefinition):
            if node.name == contract_name:
              for part in node.nodes:
                if isinstance(part, StructDefinition):
                  if part.name == struct_name:
                    yield part
    # If is contract definition
    if ty == 'contract':
      for node in root.nodes:
          if isinstance(node, ContractDefinition):
            if node.name == canonical_name:
              yield node

  raise ValueError(type_name)

def parse(node):

  if node['nodeType'] == 'SourceUnit':
    nodes = [parse(x) for x in node['nodes']]
    return SourceUnit(nodes)

  if node['nodeType'] == 'ContractDefinition':
    kind = node['contractKind']
    name = node['name']
    base_contracts = [parse(x) for x in node['baseContracts']]
    nodes  = [parse(x) for x in node['nodes']]
    return ContractDefinition(base_contracts, kind, name, nodes)

  if node['nodeType'] == 'FunctionDefinition':
    name = node['name']
    parameters = [parse(x) for x in node['parameters']['parameters']]
    returns = [parse(x) for x in node['returnParameters']['parameters']]
    body = parse(node['body']) if node['body'] else None
    visibility = node['visibility']
    modifiers = [parse(x) for x in node['modifiers']]
    return FunctionDefinition(name, parameters, returns, body, visibility, modifiers)

  if node['nodeType'] == 'VariableDeclaration':
    name = node['name']
    type_name = parse(node['typeName'])
    return VariableDeclaration(name, type_name)

  if node['nodeType'] == 'ElementaryTypeName':
    name = node['name']
    return ElementaryTypeName(name)

  if node['nodeType'] == 'Block':
    statements = [parse(x) for x in node['statements']]
    return Block(statements)

  if node['nodeType'] == 'ExpressionStatement':
    expression = parse(node['expression'])
    return ExpressionStatement(expression)

  if node['nodeType'] == 'Assignment':
    left_hand_side = parse(node['leftHandSide'])
    right_hand_side = parse(node['rightHandSide'])
    operator = node['operator']
    return Assignment(left_hand_side, right_hand_side, operator)

  if node['nodeType'] == 'Identifier':
    name = node['name']
    return Identifier(name)

  if node['nodeType'] == 'BinaryOperation':
    left_expression = parse(node['leftExpression'])
    right_expression = parse(node['rightExpression'])
    operator = node['operator']
    return BinaryOperation(left_expression, right_expression, operator)

  if node['nodeType'] == 'IfStatement':
    condition = parse(node['condition'])
    true_body = parse(node['trueBody'])
    false_body = parse(node['falseBody']) if node['falseBody'] else None
    return IfStatement(condition, true_body, false_body)

  if node['nodeType'] == 'UnaryOperation':
    sub_expression = parse(node['subExpression'])
    prefix = node['prefix']
    operator = node['operator']
    return UnaryOperation(sub_expression, prefix, operator)

  if node['nodeType'] == 'TupleExpression':
    components = [parse(x) for x in node['components']]
    return TupleExpression(components)

  if node['nodeType'] == 'Literal':
    kind = node['kind']
    value = node['value']
    return Literal(kind, value)

  if node['nodeType'] == 'FunctionCall':
    kind = node['kind']
    expression = parse(node['expression'])
    arguments = [parse(x) for x in node['arguments']]
    return FunctionCall(kind, expression, arguments)

  if node['nodeType'] == 'Mapping':
    key_type = parse(node['keyType'])
    value_type = parse(node['valueType'])
    return Mapping(key_type, value_type)

  if node['nodeType'] == 'IndexAccess':
    index_expression = parse(node['indexExpression'])
    base_expression = parse(node['baseExpression'])
    return IndexAccess(index_expression, base_expression)

  if node['nodeType'] == 'MemberAccess':
    member_name = node['memberName']
    expression = parse(node['expression'])
    return MemberAccess(member_name, expression)

  if node['nodeType'] == 'StructDefinition':
    name = node['name']
    members = [parse(x) for x in node['members']]
    return StructDefinition(name, members)

  if node['nodeType'] == 'UserDefinedTypeName':
    name = node['typeDescriptions']['typeString']
    return UserDefinedTypeName(name)

  if node['nodeType'] == 'ArrayTypeName':
    base_type = parse(node['baseType'])
    length = parse(node['length']) if node['length'] else None
    return ArrayTypeName(base_type, length)

  if node['nodeType'] == 'VariableDeclarationStatement':
    declarations = [parse(x) for x in node['declarations']]
    initial_value = parse(node['initialValue']) if node['initialValue'] else None
    return VariableDeclarationStatement(declarations, initial_value)

  if node['nodeType'] == 'ForStatement':
    init = parse(node['initializationExpression'])
    condition = parse(node['condition'])
    loop = parse(node['loopExpression'])
    body = parse(node['body'])
    return ForStatement(init, condition, loop, body)

  if node['nodeType'] == 'Return':
    expression = parse(node['expression']) if node['expression'] else None
    return Return(expression)

  if node['nodeType'] == 'ElementaryTypeNameExpression':
    return ElementaryTypeNameExpression(node['typeName'])

  if node['nodeType'] == 'UsingForDirective':
    type_name = parse(node['typeName'])
    library_name = parse(node['libraryName'])
    return UsingForDirective(type_name, library_name)

  if node['nodeType'] == 'EmitStatement':
    return EmitStatement()

  if node['nodeType'] == 'EventDefinition':
    return EventDefinition()

  if node['nodeType'] == 'ModifierDefinition':
    body = parse(node['body'])
    parameters = [parse(x) for x in node['parameters']['parameters']]
    return ModifierDefinition(body, parameters)

  if node['nodeType'] == 'InheritanceSpecifier':
    base_name = parse(node['baseName'])
    return InheritanceSpecifier(base_name)

  if node['nodeType'] == 'ModifierInvocation':
    modifier_name = parse(node['modifierName'])
    arguments = [parse(x) for x in node['arguments']]
    return ModifierInvocation(modifier_name, arguments)

  if node['nodeType'] == 'PlaceholderStatement':
    return PlaceholderStatement()

  raise ValueError(node['nodeType'])