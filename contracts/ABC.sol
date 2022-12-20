contract ABC {
    struct OK {
        address sender;
        uint value;
    }
    OK ok;
    mapping(address => uint) balances;
    function add(address to, uint value) public returns (uint z) {
        value = 10;
        if (balances[msg.sender] >= value + ok.value) {
            assert(balances[msg.sender] >= 10);
        }
    }
}