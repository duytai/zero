contract DEF {
    address owner;
    bool k;
    modifier onlyOwner() {
        k = true;
        require(msg.sender == owner);
        _;
        k = false;
    }

    function test() onlyOwner() public {
        assert(k);
    }
}