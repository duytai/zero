contract TestSuite {
    function reverts_if(bool) internal pure;
    function ensures(bool, bool) internal pure;
    function achieves_ok(bool, bool) internal pure;
    function achieves_err(bool, bool) internal pure;
    function old_uint(uint) internal pure returns(uint);
    function old_address(address) internal pure returns(address);
    function over_uint(uint) internal pure returns(bool);
    function under_uint(uint) internal pure returns(bool);
    function sum_uint(mapping(address => uint) memory) internal pure returns(uint);
}


library SafeMath {
  function reverts_if(bool) internal pure {}
  function over_uint(uint) internal pure returns(bool) {}
  function under_uint(uint) internal pure returns(bool) {}
  function ensures(bool, bool) internal pure {}
  /**
   * @dev Multiplies two numbers, throws on overflow.
   */
  function mul(uint256 a, uint256 b) internal pure returns (uint256 r) {
    // reverts_if(over_uint(a * b));
    ensures(true, r == a * b);

    if (a == 0) {
      return 0;
    }
    uint256 c = a * b;
    // assert(c / a == b);
    return c;
  }

  /**
   * @dev Integer division of two numbers, truncating the quotient.
   */
  function div(uint256 a, uint256 b) internal pure returns (uint256 r) {
    ensures(true, r == a / b);

    // assert(b > 0); // Solidity automatically throws when dividing by 0
    uint256 c = a / b;
    // assert(a == b * c + a % b); // There is no case in which this doesn't hold
    return c;
  }

  /**
   * @dev Subtracts two numbers, throws on overflow (i.e. if subtrahend is greater than minuend).
   */
  function sub(uint256 a, uint256 b) internal pure returns (uint256 r) {
    // reverts_if(a < b);
    ensures(true, r == a - b);

    assert(b <= a);
    return a - b;
  }

  /**
   * @dev Adds two numbers, throws on overflow.
   */
  function add(uint256 a, uint256 b) internal pure returns (uint256 r) {
    // reverts_if(over_uint(a + b));
    ensures(true, r == a + b);

    uint256 c = a + b;
    assert(c >= a);
    return c;
  }
}


contract ABC is TestSuite {
    using SafeMath for uint;
    mapping(address => uint256) balances;
    uint totalSupply;

    // function add(uint x, uint y) public returns(uint z) {
    //     achieves_ok(x < 10, z == x + y);
    //     achieves_err(x < 10, z == x + y);
    //     return x + y;
    // }
    function test(uint x) public {
      ensures(true, totalSupply == old_uint(totalSupply) + 10);
      totalSupply = totalSupply.add(10);
        // achieves_ok(true, totalSupply >= 20);
        // achieves_err(true, totalSupply == 20);
        // totalSupply = add(10, 10);
    }

}