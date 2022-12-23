contract DEF {
	uint counter;
	function ensures(bool, bool) internal {}
	function old_uint(uint) internal returns(uint) {}

	function add(uint x, uint y) public returns(uint z) {
		ensures(true, z == x + y);
		ensures(true, counter == old_uint(counter) + 1);
		counter += 1;
		return x + y;
	}

	function test() public {
		counter = 20;
		uint m = add(20, 40);
		assert(counter == 24);
		assert(counter == 21);
		assert(m == 60);
		assert(m == 61);
	}
}