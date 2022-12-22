contract TestSuite {
  function reverts_if(bool) internal pure;
  function ensures(bool, bool) internal pure;
  function old_uint(uint) internal pure returns(uint);
  function over_uint(uint) internal pure returns(bool);
  function under_uint(uint) internal pure returns(bool);
  function sum_uint(mapping(address => uint) memory) internal pure returns(uint);
  function ok(bool) internal pure;
}

library SafeMath {
  function ensures(bool, bool) internal pure {}
  function add(uint x, uint y) internal pure returns(uint z) {
    ensures(true, z == x + y);
    return x + y;
  }
}

contract ABC is TestSuite {
  // using SafeMath for uint;
  struct Hello {
    uint a;
    uint b;
  }
  Hello hello;
  uint c;
  function test() public payable returns(uint z) {
    ensures(true, z == 89 + old_uint(c));
    uint m = 100;
    m++;
    m--;
    assert(m == 100);
    uint[10][20] memory lst;
    lst[0][0] = 10;
    assert(lst[0][0] == 10 + hello.a);
    c = 987;
    z = 1000;
    assert(z == m + c);
  }
}