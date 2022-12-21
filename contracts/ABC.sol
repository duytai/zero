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
    uint c = 0;
    function test(uint k) public returns(uint z) {
        ensures(counter == 1, counter == 2 && c == k + 1);
        c = add(k, 1);
        // ensures(k >= 20, counter == old_uint(counter) + k);
        // ensures(k < 20, counter == old_uint(counter) - k);
        // if (k >= 20) {
        //     counter = add(counter, k);
        // } else {
        //     counter = sub(counter, k);
        // }
    }
    function add(uint x, uint y) public returns(uint z) {
        ensures(true, z == x + y);
        // ensures(true, counter == old_uint(counter) + 1);
        counter = counter + 1;
        return x + y;
    }
    function sub(uint x, uint y) public returns(uint z) {
        ensures(true, z == x - y);
        return x - y;
    }
}