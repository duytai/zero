contract TestSuite {
    function reverts_if(bool) internal pure;
    function ensures(bool, bool) internal pure;
    function old_uint(uint) internal pure returns(uint);
    function over_uint(uint) internal pure returns(bool);
    function under_uint(uint) internal pure returns(bool);
    function sum_uint(mapping(address => uint) memory) internal pure returns(uint);
    function ok(bool) internal pure;
}


contract ABC is TestSuite {
  struct Hello {
    uint a;
    uint b;
  }
  Hello hello;
  function add(uint x, uint y) private returns(uint z) {
    ensures(true, z == x + y);
    return x + y;
  }

  function test() public payable returns(uint z) {
    uint[10][20] memory lst;
    lst[0][0] = 10;
    assert(lst[0][0] == 10);
    // z = 1000;
  }
}