from brownie import network, config, interface
from scripts.get_weth import get_weth
from scripts.helpful_scripts import get_account
from web3 import Web3

# 0.1 WETH
amount = Web3.toWei(0.1, "ether")


def main():
    account = get_account()
    erc20_addresss = config["networks"][network.show_active()]["weth_token"]
    if network.show_active() in ["mainnet-fork"]:
        get_weth()
    # ABI -automatically generated when `interface` is used
    # address
    # for AAVE V3
    pool = get_pool()
    # approve sending our ERc20 tokens
    approve_erc20(amount, pool.address, erc20_addresss, account)
    # deposit() method -> supply() in V3
    print("Supplying...")
    tx = pool.supply(erc20_addresss, amount, account.address, 0, {"from": account})
    tx.wait(1)
    print("Asset supplied!")
    # borrow
    borrowable_eth, total_debt = get_borrowable_data(pool, account)
    # 0.1 ETH deposited
    # 0.08 borrowable (threshold applied - 80% of ETH on AAVE)
    print("Let's borrow!")
    # DAI in USD for Sepolia
    if network.show_active() in ["sepolia"]:
        dai_price = get_asset_price(
            config["networks"][network.show_active()]["dai_usd_price_feed"]
        )
    # DAI in terms of ETH
    dai_price = get_asset_price(
        config["networks"][network.show_active()]["dai_eth_price_feed"]
    )
    amount_dai_to_borrow = (1 / dai_price) * (borrowable_eth * 0.95)
    # borrowable_eth -> borrowable_dai * 95%
    print(f"We are going to borrow {amount_dai_to_borrow} DAI")
    # Now we will borrow!
    dai_address = config["networks"][network.show_active()]["dai_token"]
    # function borrow(address asset, amount, interestRateMode [1-Stable,2-Variable], referralCode, address onBehalfOf)
    borrow_tx = pool.borrow(
        dai_address,
        Web3.toWei(amount_dai_to_borrow, "ether"),
        1,
        0,
        account.address,
        {"from": account},
    )
    borrow_tx.wait(1)
    print("We borrowed some DAI")
    get_borrowable_data(pool, account)
    repay_all(amount, pool, account)


def get_pool():
    pool_addresses_provider = interface.IPoolAddressesProvider(
        config["networks"][network.show_active()]["pool_addresses_provider"]
    )
    pool_address = pool_addresses_provider.getPool()
    # ABI -automatically generated when `interface` is used
    # address - checked!
    pool = interface.IPool(pool_address)
    return pool


def approve_erc20(amount, pool_address, erc20_address, account):
    print("Approving ERC20 token...")
    erc20 = interface.IERC20(erc20_address)
    tx = erc20.approve(pool_address, amount, {"from": account})
    tx.wait(1)
    print("Approved!")
    return True
    # ABI -automatically generated when `interface` is used
    # address


def get_borrowable_data(pool, account):
    (
        total_collateral_eth,
        total_debt_eth,
        available_borrow_eth,
        current_liquidation_threshold,
        ltv,
        health_factor,
    ) = pool.getUserAccountData(account.address)
    available_borrow_eth = Web3.fromWei(available_borrow_eth, "ether")
    total_collateral_eth = Web3.fromWei(total_collateral_eth, "ether")
    total_debt_eth = Web3.fromWei(total_debt_eth, "ether")
    print(f"You have {total_collateral_eth} worth of ETH deposited.")
    print(f"You have {total_debt_eth} worth of ETH borrowed.")
    print(f"You can borrow {available_borrow_eth} worth of ETH.")
    return (float(available_borrow_eth), float(total_debt_eth))


def get_asset_price(price_feed_address):
    # ABI & Address
    dai_eth_price_feed = interface.AggregatorV3Interface(price_feed_address)
    latest_price = dai_eth_price_feed.latestRoundData()[1]
    converted_latest_price = Web3.fromWei(latest_price, "ether")
    print(f"The DAI/ETH price is {converted_latest_price}")
    return float(converted_latest_price)


def repay_all(amount, pool, account):
    approve_erc20(
        Web3.toWei(amount, "ether"),
        pool,
        config["networks"][network.show_active()]["dai_token"],
    )
    repay_tx = pool.repay(
        config["networks"][network.show_active()]["dai_token"],
        amount,
        1,
        account.address,
    )
    repay_tx.wait(1)
    print("You just supplied, borrowed and repayed with AAVE, Brownie and Chainlink!")
