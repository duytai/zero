contract ABC {
    mapping(address => uint256) balances;
    function batchTransfer(address[] memory _receivers, uint256 _value) public returns (bool) {
        uint cnt = _receivers.length;
        uint256 amount = uint256(cnt) * _value;
        require(cnt > 0 && cnt <= 20);
        require(_value > 0 && balances[msg.sender] >= amount);

        uint x = balances[msg.sender];
        balances[msg.sender] = balances[msg.sender] - amount;
        assert(balances[msg.sender] >= amount || cnt <= 20 && cnt > 0);
        for (uint i = 0; i < cnt; i++) {
            balances[_receivers[i]] = balances[_receivers[i]] - _value;
        }
        return true;
    }
}