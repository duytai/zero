contract ABC {
    mapping(address => uint) balances;
    function add(uint x, uint y) public returns (uint z) {
        y = 20;
        x = y + 1;
        assert((x == 21 && y == 20) && (z == 0));
    }
}