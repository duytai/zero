contract DEF {
    function ensures(bool a, bool b) private {}
    
    function sub(uint a, uint b) private returns(uint c) {
        ensures(true, c == a - b);
        assert(a >= b);
        return a - b;
    }

    function test() public {
        uint t = 100;
        // for (uint i = 0; i < 2; i += 1) {
            t = sub(t, 20);
        // }   
        assert(t == 80);
    }
}