contract TestSuite {
    function reverts_if(bool) internal pure;
    function ensures(bool, bool) internal pure;
    function old_uint(uint) internal pure returns(uint);
    function old_address(address) internal pure returns(address);
    function over_uint(uint) internal pure returns(bool);
    function under_uint(uint) internal pure returns(bool);
    function sum_uint(mapping(address => uint) memory) internal pure returns(uint);
}

contract ABC is TestSuite {
    mapping(address => uint256) balances;
    uint counter = 0;
    function test(uint k) public returns(uint z) {
        ensures(k > 0, counter == old_uint(counter) + k);
        ensures(k < 0, counter == old_uint(counter) + 100 - 100);
        counter = counter + k;
    }
    function add(uint x, uint y) public returns(uint z) {
        ensures(true, z == x + y);
        return x + y;
    }
}