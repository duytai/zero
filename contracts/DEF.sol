// contract DEF {
//     function ok(bool) internal view {}
//     function assume(bool) internal view {}
//     bool inSwapAndLiquify;
//     function _test(uint x) private {
//         if (!inSwapAndLiquify) {
//         }
//         assume(inSwapAndLiquify);
//         ok(1 == 1);
//     }
//     function test(uint x) public {
//         _test(x);
//     }
// }

interface IPancakePair {
    function sync() external;
}

library SafeMath {
    function ensures(bool, bool) internal pure {}
    function add(uint x, uint y) internal pure returns(uint z) {
        ensures(true, z == x + y);
        return x + y;
    }
    function sub(uint x, uint y) internal pure returns(uint z) {
        ensures(true, z == x - y);
        assert(x >= y);
        return x - y;
    }
    function mul(uint x, uint y) internal pure returns(uint z) {
        ensures(true, z == x * y);
        return x * y;
    }
    function div(uint x, uint y) internal pure returns(uint z) {
        ensures(true, z == x / y);
        assert(y == 0);
        return x / y;
    }
}

contract PanCake {
    using SafeMath for uint;
    mapping (address => uint) _balances;
    uint numTokensSellToAddToLiquidity;
    bool inSwapAndLiquify;
    bool public swapAndLiquifyEnabled;
    address public uniswapV2Pair;
    uint public pairStartTime;
    address public _burnAddress = address(0x000000000000000000000000000000000000dEaD);
    uint public jgTime = 15 * 60; 
    uint public burnFee = 0; 
    uint public devFee = 0; 
    uint public bFee = 0;

    function ok(bool) private view {}
    function assume(bool) private view {}

    function transfer(address to, uint value) public returns(bool) {
        _transfer(msg.sender, to, value);
        return true;
    }

    function balanceOf(address owner) public view returns (uint) {
        return _balances[owner];
    }

    function swapAndLiquify(uint contractTokenBalance) private {
        inSwapAndLiquify = true;
        // swap tokens for ETH
        // swapTokensForEth(contractTokenBalance); // <- this breaks the ETH -> HATE swap when swap+liquify is triggered
        inSwapAndLiquify = false;
    }

    function _transfer(address from, address to, uint value) private {
        uint tmp_0 = _balances[_burnAddress];
        require(value <= _balances[from]);
        require(to != address(0));
        uint contractTokenBalance = balanceOf(address(this));
        bool overMinTokenBalance = contractTokenBalance >= numTokensSellToAddToLiquidity;
        if (
            overMinTokenBalance &&
            !inSwapAndLiquify &&
            to == uniswapV2Pair &&
            swapAndLiquifyEnabled
        ) {
            contractTokenBalance = numTokensSellToAddToLiquidity;
            //add liquidity
            swapAndLiquify(contractTokenBalance);
            assume(true);
        }
        if (block.timestamp >= pairStartTime.add(jgTime) && pairStartTime != 0) {
            if (from != uniswapV2Pair) {
                uint burnValue = _balances[uniswapV2Pair].mul(burnFee).div(1000);
                _balances[uniswapV2Pair] = _balances[uniswapV2Pair].sub(burnValue);
                _balances[_burnAddress] = _balances[_burnAddress].add(burnValue);
                if (block.timestamp >= pairStartTime.add(jgTime)) {
                    pairStartTime += jgTime;
                }
                // emit Transfer(uniswapV2Pair, _burnAddress, burnValue);
                IPancakePair(uniswapV2Pair).sync();
                assume(true);
            }
        }
        uint devValue = value.mul(devFee).div(1000);
        uint bValue = value.mul(bFee).div(1000);
        uint newValue = value.sub(devValue).sub(bValue);
        _balances[from] = _balances[from].sub(value);
        _balances[to] = _balances[to].add(newValue);
        _balances[address(this)] = _balances[address(this)].add(devValue);
        _balances[_burnAddress] = _balances[_burnAddress].add(bValue);
        // ok(_balances[_burnAddress] > tmp_0 && value == 0);
    }
}