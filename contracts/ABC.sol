contract ABC {
    mapping(address => uint256) balances;
    function batchTransfer(address[] memory _receivers, uint256 _value) public returns (bool) {
        uint cnt = _receivers.length;
        uint256 amount = uint256(cnt) * _value;
        require(cnt > 0 && cnt <= 20);
        require(_value > 0 && balances[msg.sender] >= amount);

        uint x = balances[msg.sender];
        balances[msg.sender] = balances[msg.sender] - amount;
        uint i;
        for (i = 0; i < cnt; i++) {
            balances[_receivers[i]] = balances[_receivers[i]] - _value;
        }
        assert(i >= 2);
        return true;
    }
}