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
  function add(uint x, uint y) internal pure returns(uint z) {
    return x + y;
  }
}

contract ABC {
  using SafeMath for uint;
  struct Hello {
    uint a;
    uint b;
  }
  Hello hello;
  function test() public payable returns(uint z) {
    uint m = 100;
    m++;
    m--;
    assert(m == 100);
    uint[10][20] memory lst;
    lst[0][0] = 10;
    assert(lst[0][0] == 10 + hello.a);
    z = 1000;
  }
}