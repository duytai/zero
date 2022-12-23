contract TestSuite {
  function reverts_if(bool) internal pure;
  function ensures(bool, bool) internal pure;
  function old_uint(uint) internal pure returns(uint);
  function over_uint(uint) internal pure returns(bool);
  function under_uint(uint) internal pure returns(bool);
  function sum_uint(mapping(address => uint) memory) internal pure returns(uint);
  function ok(bool) internal pure;
}

library SafeMath {
  function ensures(bool, bool) internal pure {}
  function sub(uint x, uint y) internal pure returns(uint z) {
    ensures(true, z == x - y);
    return x - y;
  }
}

contract Double is TestSuite {
  uint dd = 100;
  function double(uint x, uint y) public returns(uint z) {
    ensures(true, z == x * 2 + y * 2);
    ensures(true, dd == old_uint(dd) + 1);
    dd ++;
    return x * 2 + y * 2;
  }
}

contract ABC is Double {
  using SafeMath for uint;
  struct Hello {
    uint ax;
    uint bx;
  }
  Hello hello;
  uint c;
  uint counter;

  function haizz(uint k) public {
    dd = 30;
    uint m = double(k, 2);
    assert(dd == 100);
    assert(dd == 31);
    assert(m == k*2 + 4);
    assert(m == k*2 + 9);
  }

  function add(uint x, uint y) public returns(uint z) {
    ensures(true, z == x + y);
    ensures(true, counter == old_uint(counter) + 1);
    counter += 1;
    return x + y;
  }
  function test() public payable returns(uint z) {
    assert(hello.ax >= 0);
    counter = 20;
    uint mm = add(z, 30);
    assert(counter == 21);
    assert(counter == 20);
    assert(mm == 30);
    assert(mm == 51);
    uint jj = 90;
    uint k = jj.sub(20);
    assert(k == 70);
    assert(k == 71);
    assert(counter == 21);
    assert(counter == 22);
    assert(address(this).balance >= 0);
    ensures(true, z == 89 + old_uint(c));
    uint m = 100;
    m++;
    m--;
    assert(m == 100);
    assert(m == 101);
    uint[10] memory lst;
    lst[0] = 10;
    assert(lst.length == 10);
    assert(lst.length == 11);
    c = 987;
    m = 1000;
    assert(m == m + c);
    assert(m == m + c + 1);
  }
}


// SPDX-License-Identifier: MIT

contract Counter {
    uint public count;

    function increment() external {
        count += 1;
    }
}

interface ICounter {
    function count() external view returns (uint);

    function increment() external;
}

contract MyContract {
    function incrementCounter(address _counter) external {
        ICounter(_counter).increment();
    }

    function getCount(address _counter) external view returns (uint) {
        return ICounter(_counter).count();
    }
}

// Uniswap example
interface UniswapV2Factory {
    function getPair(address tokenA, address tokenB)
        external
        view
        returns (address pair);
}

interface UniswapV2Pair {
    function getReserves()
        external
        view
        returns (
            uint112 reserve0,
            uint112 reserve1,
            uint32 blockTimestampLast
        );
}

contract UniswapExample {
    address private factory = 0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f;
    address private dai = 0x6B175474E89094C44Da98b954EedeAC495271d0F;
    address private weth = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;
    function assume(bool) internal view {} 
    function getTokenReserves() external view returns (uint, uint) {
        address pair = UniswapV2Factory(factory).getPair(dai, weth);
        (uint reserve0, uint reserve1, uint ok) = UniswapV2Pair(pair).getReserves();
        assume(reserve0 + reserve1 == ok);
        assert(ok == reserve0 + reserve1);
        // return (reserve0, reserve1);
    }
}
