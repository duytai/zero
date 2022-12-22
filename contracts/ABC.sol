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
  function add(uint x, uint y) private returns(uint z) {
    ensures(true, z == x + y);
    return x + y;
  }

  function test() public payable returns(uint z) {
    uint[] memory lst;
    ensures(true, z == 80);
    uint k = address(this).balance;
    // ok(k >= lst.length);
    // for (uint i = 0; i < 2; i += 1) {
    //   z += add(20, 20);
    // }
  }
}