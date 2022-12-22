contract TestSuite {
  function reverts_if(bool) internal pure;
  function ensures(bool, bool) internal pure;
  function old_uint(uint) internal pure returns(uint);
  function over_uint(uint) internal pure returns(bool);
  function under_uint(uint) internal pure returns(bool);
  function sum_uint(mapping(address => uint) memory) internal pure returns(uint);
}

contract SafeMath is TestSuite {
  function safeMul(uint256 a, uint256 b) internal returns (uint256 r) {
    reverts_if(over_uint(a * b));
    ensures(true, r == a * b);
    uint256 c = a * b;
    assert(a == 0 || c / a == b); // circut break
    return c;
  }

  function safeDiv(uint256 a, uint256 b) internal returns (uint256 r) {
    reverts_if(b <= 0);
    ensures(true, r == a / b);
    assert(b > 0);
    uint256 c = a / b;
    assert(a == b * c + a % b);
    return c;
  }

  function safeSub(uint256 a, uint256 b) internal returns (uint256 r) {
    reverts_if(under_uint(a - b));
    ensures(true, r == a - b);
    assert(b <= a);
    return a - b;
  }

  function safeAdd(uint256 a, uint256 b) internal returns (uint256 r) {
    reverts_if(over_uint(a + b));
    ensures(true, r == a + b);
    uint256 c = a + b;
    assert(c>=a && c>=b);
    return c;
  }
}

contract BNB is SafeMath{
  string public name;
  string public symbol;
  uint8 public decimals;
  uint256 public totalSupply;
  address payable public owner;

  /* This creates an array with all balances */
  mapping (address => uint256) public balanceOf;
  mapping (address => uint256) public freezeOf;
  mapping (address => mapping (address => uint256)) public allowance;

  /* This generates a public event on the blockchain that will notify clients */
  event Transfer(address indexed from, address indexed to, uint256 value);

  /* This notifies clients about the amount burnt */
  event Burn(address indexed from, uint256 value);

  /* This notifies clients about the amount frozen */
  event Freeze(address indexed from, uint256 value);

  /* This notifies clients about the amount unfrozen */
  event Unfreeze(address indexed from, uint256 value);

  /* Initializes contract with initial supply tokens to the creator of the contract */
  constructor(
    uint256 initialSupply,
    string memory tokenName,
    uint8 decimalUnits,
    string memory tokenSymbol
  ) public {
    balanceOf[msg.sender] = initialSupply;              // Give the creator all initial tokens
    totalSupply = initialSupply;                        // Update total supply
    name = tokenName;                                   // Set the name for display purposes
    symbol = tokenSymbol;                               // Set the symbol for display purposes
    decimals = decimalUnits;                            // Amount of decimals for display purposes
    owner = msg.sender;
  }

  /* Send coins */
  function transfer(address _to, uint256 _value) public {
    reverts_if(_to == address(0x00));
    reverts_if(_value <= 0);
    reverts_if(under_uint(balanceOf[msg.sender] - _value));
    reverts_if(over_uint(balanceOf[_to] + _value));
    ensures(msg.sender != _to, balanceOf[msg.sender] == old_uint(balanceOf[msg.sender]) - _value);
    ensures(msg.sender != _to, balanceOf[_to] == old_uint(balanceOf[_to]) + _value);
    ensures(msg.sender == _to, balanceOf[msg.sender] == old_uint(balanceOf[msg.sender]));
    ensures(sum_uint(balanceOf) + sum_uint(freezeOf) == totalSupply, sum_uint(balanceOf) + sum_uint(freezeOf) == totalSupply);

    if (_to == address(0x00)) revert();                               // Prevent transfer to 0x0 address. Use burn() instead
    if (_value <= 0) revert();
    if (balanceOf[msg.sender] < _value) revert();           // Check if the sender has enough
    if (balanceOf[_to] + _value < balanceOf[_to]) revert(); // Check for overflows
    balanceOf[msg.sender] = safeSub(balanceOf[msg.sender], _value);                     // Subtract from the sender
    balanceOf[_to] = safeAdd(balanceOf[_to], _value);                            // Add the same to the recipient
    emit Transfer(msg.sender, _to, _value);                   // Notify anyone listening that this transfer took place
  }

  /* Allow another contract to spend some tokens in your behalf */
  function approve(address _spender, uint256 _value) public returns (bool success) {
    reverts_if(_value <= 0);
    ensures(true, allowance[msg.sender][_spender] == _value);
    ensures(sum_uint(balanceOf) + sum_uint(freezeOf) == totalSupply, sum_uint(balanceOf) + sum_uint(freezeOf) == totalSupply);

    if (_value <= 0) revert();
    allowance[msg.sender][_spender] = _value;
    return true;
  }

  /* A contract attempts to get the coins */
  function transferFrom(address _from, address _to, uint256 _value) public returns (bool success) {
    reverts_if(_to == address(0x0));
    reverts_if(_value <= 0);
    reverts_if(under_uint(balanceOf[_from] - _value));
    reverts_if(over_uint(balanceOf[_to] + _value));  // Check for overflows
    reverts_if(under_uint(allowance[_from][msg.sender] - _value));     // Check allowance
    ensures(_from != _to, balanceOf[_from] == old_uint(balanceOf[_from]) - _value);
    ensures(_from != _to, balanceOf[_to] == old_uint(balanceOf[_to]) + _value);
    ensures(_from == _to, balanceOf[_from] == old_uint(balanceOf[_from]));
    ensures(true, allowance[_from][msg.sender] == old_uint(allowance[_from][msg.sender]) - _value);
    ensures(sum_uint(balanceOf) + sum_uint(freezeOf) == totalSupply, sum_uint(balanceOf) + sum_uint(freezeOf) == totalSupply);

    if (_to == address(0x0)) revert();                                // Prevent transfer to 0x0 address. Use burn() instead
    if (_value <= 0) revert();
    if (balanceOf[_from] < _value) revert();                 // Check if the sender has enough
    if (balanceOf[_to] + _value < balanceOf[_to]) revert();  // Check for overflows
    if (_value > allowance[_from][msg.sender]) revert();     // Check allowance
    balanceOf[_from] = safeSub(balanceOf[_from], _value);                           // Subtract from the sender
    balanceOf[_to] = safeAdd(balanceOf[_to], _value);                             // Add the same to the recipient
    allowance[_from][msg.sender] = safeSub(allowance[_from][msg.sender], _value);
    emit Transfer(_from, _to, _value);
    return true;
  }

  function burn(uint256 _value) public returns (bool success) {
    reverts_if(balanceOf[msg.sender] < _value);
    reverts_if(_value <= 0);
    reverts_if(totalSupply < _value);
    ensures(true, balanceOf[msg.sender] == old_uint(balanceOf[msg.sender]) - _value);
    ensures(true, totalSupply == old_uint(totalSupply) - _value);
    ensures(sum_uint(balanceOf) + sum_uint(freezeOf) == totalSupply, sum_uint(balanceOf) + sum_uint(freezeOf) == totalSupply);

    if (balanceOf[msg.sender] < _value) revert();            // Check if the sender has enough
    if (_value <= 0) revert();
    balanceOf[msg.sender] = safeSub(balanceOf[msg.sender], _value);                      // Subtract from the sender
    totalSupply = safeSub(totalSupply, _value);                                // Updates totalSupply
    emit Burn(msg.sender, _value);
    return true;
  }

  function freeze(uint256 _value) public returns (bool success) {
    reverts_if(balanceOf[msg.sender] < _value);
    reverts_if(_value <= 0);
    reverts_if(over_uint(freezeOf[msg.sender] + _value));
    ensures(true, balanceOf[msg.sender] == old_uint(balanceOf[msg.sender]) - _value);
    ensures(true, freezeOf[msg.sender] == old_uint(freezeOf[msg.sender]) + _value);
    ensures(sum_uint(balanceOf) + sum_uint(freezeOf) == totalSupply, sum_uint(balanceOf) + sum_uint(freezeOf) == totalSupply);

    if (balanceOf[msg.sender] < _value) revert();            // Check if the sender has enough
    if (_value <= 0) revert();
    balanceOf[msg.sender] = safeSub(balanceOf[msg.sender], _value);                      // Subtract from the sender
    freezeOf[msg.sender] = safeAdd(freezeOf[msg.sender], _value);                                // Updates totalSupply
    emit Freeze(msg.sender, _value);
    return true;
  }

  function unfreeze(uint256 _value) public returns (bool success) {
    reverts_if(freezeOf[msg.sender] < _value);
    reverts_if(_value <= 0);
    reverts_if(over_uint(balanceOf[msg.sender] + _value));
    ensures(true, freezeOf[msg.sender] == old_uint(freezeOf[msg.sender]) - _value);
    ensures(true, balanceOf[msg.sender] == old_uint(balanceOf[msg.sender]) + _value);
    ensures(sum_uint(balanceOf) + sum_uint(freezeOf) == totalSupply, sum_uint(balanceOf) + sum_uint(freezeOf) == totalSupply);

    if (freezeOf[msg.sender] < _value) revert();            // Check if the sender has enough
    if (_value <= 0) revert();
    freezeOf[msg.sender] = safeSub(freezeOf[msg.sender], _value);                      // Subtract from the sender
    balanceOf[msg.sender] = safeAdd(balanceOf[msg.sender], _value);
    emit Unfreeze(msg.sender, _value);
    return true;
  }

  // transfer balance to owner
  function withdrawEther(uint256 amount) public {
    reverts_if(msg.sender != owner);
    reverts_if(address(this).balance < amount);
    ensures(owner != address(this), address(this).balance == old_uint(address(this).balance) - amount);
    ensures(sum_uint(balanceOf) + sum_uint(freezeOf) == totalSupply, sum_uint(balanceOf) + sum_uint(freezeOf) == totalSupply);

    if(msg.sender != owner) revert();
    owner.transfer(amount);
  }

  // can accept ether
  function() payable external {
  }
}