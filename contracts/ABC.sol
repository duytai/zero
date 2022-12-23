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
  function sub(uint x, uint y) internal pure returns(uint z) {
    ensures(true, z == x - y);
    return x - y;
  }
}

contract ABC is TestSuite {
  using SafeMath for uint;
  struct Hello {
    uint ax;
    uint bx;
  }
  Hello hello;
  uint c;
  uint counter;
  function add(uint x, uint y) public returns(uint z) {
    ensures(true, z == x + y);
    ensures(true, counter == old_uint(counter) + 1);
    counter += 1;
    return x + y;
  }
  function test() public payable returns(uint z) {
    assert(hello.ax >= 0);
    counter = 20;
    uint mm = add(z, 30);
    assert(mm == 50);
    uint jj = 90;
    uint k = jj.sub(20);
    assert(k == 70);
    assert(counter == 21);
    assert(address(this).balance >= 0);
    ensures(true, z == 89 + old_uint(c));
    uint m = 100;
    m++;
    m--;
    assert(m == 100);
    uint[10] memory lst;
    lst[0] = 10;
    assert(lst.length == 10);
    c = 987;
    m = 1000;
    assert(m == m + c);
  }
}