contract TestSuite {
    function reverts_if(bool) internal pure;
    function ensures(bool, bool) internal pure;
    function achieves_ok(bool, bool) internal pure;
    function old_uint(uint) internal pure returns(uint);
    function old_address(address) internal pure returns(address);
    function over_uint(uint) internal pure returns(bool);
    function under_uint(uint) internal pure returns(bool);
    function sum_uint(mapping(address => uint) memory) internal pure returns(uint);
}

contract ABC is TestSuite {
    mapping(address => uint256) balances;
    uint totalSupply;

    function add(uint x, uint y) public returns(uint z) {
        achieves_ok(x < 10, z == x + y);
        return x + y;
    }
    function test(uint x) public {
        achieves_ok(true, totalSupply >= 20);
        totalSupply = add(10, 10);
    }

}