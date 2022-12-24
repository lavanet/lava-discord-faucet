import logging
import sys
import time

import aiohttp
from tabulate import tabulate
from mospy import Transaction, Account
from mospy.clients import HTTPClient
from config import VERBOSE_MODE, REST_PROVIDER, FAUCET_SEED, MAIN_DENOM, RPC_PROVIDER, GAS_LIMIT, CHAIN_ID, GAS_PRICE, \
    FAUCET_ADDRESS, DECIMAL

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

faucet_account = Account(
    seed_phrase=FAUCET_SEED,
    hrp="lava@",
    eth=False,
)


def coins_dict_to_string(coins: dict, table_fmt_: str = "") -> str:
    """
    :param table_fmt_: grid | pipe | html
    :param coins: {'clink': '100000000000000000000', 'chot': '100000000000000000000'}
    :return: str
    """

    headers = ["Token", "Amount (ulava)", "amount / decimal"]
    hm = []
    for i in range(len(coins)):
        hm.append([list(coins.keys())[i], list(coins.values())[i], int(int(list(coins.values())[i]) / DECIMAL)])
    d = tabulate(hm, tablefmt=table_fmt_, headers=headers)
    return d


async def async_request(session, url, data: str = ""):
    headers = {"Content-Type": "application/json"}
    try:
        if data == "":
            async with session.get(url=url, headers=headers) as resp:
                data = await resp.text()
        else:
            async with session.post(url=url, data=data, headers=headers) as resp:
                data = await resp.text()

        if data is None or "error" in data:
            return await resp.text()

        return await resp.json()

    except Exception as err:
        return f'error: in async_request()\n{url} {err}'


async def get_addr_balance(session, addr: str, denom: str = MAIN_DENOM):
    data = ""
    try:
        data = await async_request(session, url=f'{REST_PROVIDER}/cosmos/bank/v1beta1/balances/{addr}/by_denom?denom={denom}')
        if "balance" in str(data):
            return data["balance"]["amount"]
        return 0
    except Exception:
        logger.exception("not able to query balance", extra={data: data})


async def get_addr_all_balance(session, addr: str):
    data = ""
    coins = {}
    try:
        data = await async_request(session, url=f'{REST_PROVIDER}/cosmos/bank/v1beta1/balances/{addr}')
        if "balances" in data:
            for i in data["balances"]:
                coins[i["denom"]] = i["amount"]
            return coins
        return 0
    except Exception:
        if VERBOSE_MODE == "yes":
            logger.exception("Error occurred during get_addr_all_balance", extra={data: data})
        return 0


async def get_address_info(session, addr: str):
    """:returns sequence: int, account_number: int, coins: dict"""
    try:

        info = await async_request(session, url=f'{REST_PROVIDER}/cosmos/auth/v1beta1/accounts/{addr}')
        acc_num = int(info['account']['account_number'])
        logger.info(info['account']['account_number'])
        try:
            seq = int(info['account']['sequence']) or 0

        except Exception:
            seq = 0
        return seq, acc_num

    except Exception:
        if VERBOSE_MODE == "yes":
            logger.exception("Error occurred during get_address_info")
        return 0, 0


async def get_node_status(session: aiohttp.ClientSession):
    """

    :param session:
    :return:
    """
    url = f'{RPC_PROVIDER}/status'
    return await async_request(session, url=url)


async def get_transaction_info(session: aiohttp.ClientSession, trans_id_hex: str):
    """

    :param session:
    :param trans_id_hex:
    :return:
    """
    time.sleep(6)
    url = f'{REST_PROVIDER}/cosmos/tx/v1beta1/txs/{trans_id_hex}'
    resp = await async_request(session, url=url)
    return resp


async def send_tx(session: aiohttp.ClientSession, recipient: str, amount: int) -> str:
    """

    :param session:
    :param recipient:
    :param amount:
    :return:
    """
    try:
        faucet_account.next_sequence, faucet_account.account_number = await get_address_info(session, FAUCET_ADDRESS)

        transaction = Transaction(
            account=faucet_account,
            gas=GAS_LIMIT,
            memo="The first faucet tx!",
            chain_id=CHAIN_ID,
        )

        transaction.set_fee(
            denom="ulava",
            amount=GAS_PRICE
        )

        transaction.add_msg(
            tx_type="transfer",
            sender=faucet_account,
            receipient=recipient,
            amount=amount,
            denom=MAIN_DENOM,
        )

        client = HTTPClient(api=REST_PROVIDER)

        tx_response = client.broadcast_transaction(transaction=transaction)
        return tx_response

    except Exception as req_errs:
        if VERBOSE_MODE == "yes":
            logger.error('error in send_txs()', extra={REST_PROVIDER: req_errs})
        return f"error: {req_errs}"

