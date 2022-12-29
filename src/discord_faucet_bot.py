import sys
import logging
import datetime
import discord
import aiohttp
import aiofiles
from discord.ext import commands
from config import TOKEN, AMOUNT_TO_SEND, REQUEST_TIMEOUT, FAUCET_ADDRESS, \
    FAUCET_EMOJI, REJECT_EMOJI, BECH32_HRP, EXPLORER_URL
import cosmos_api as api

# Turn Down Discord Logging
from consts import TRANSACTION_CODE_OK, TRANSACTION_CODE_IN_MEMPOOL_CACHE

disc_log = logging.getLogger('discord')
disc_log.setLevel(logging.CRITICAL)

# Configure Logging
logging.basicConfig(stream=sys.stdout, level=logging.CRITICAL)
logger = logging.getLogger(__name__)

ACTIVE_REQUESTS = {}
intents = discord.Intents(messages=True, guilds=True, message_content=True)
bot = commands.Bot(intents=intents,
                   command_prefix="$",
                   description='Funded by the community for the community')

# with open("../help-msg.txt", "r", encoding="utf-8") as help_file:
#     help_msg = help_file.read()


async def save_transaction_statistics(some_string: str):
    """

    :param some_string:
    """
    async with aiofiles.open("../transactions.csv", "a") as csv_file:
        await csv_file.write(f'{some_string}\n')
        await csv_file.flush()


async def submit_tx_info(session: aiohttp.ClientSession, message, requester, transaction=None):
    """

    :param session:
    :param message:
    :param requester:
    :param transaction: optional
    """
    txhash = transaction["hash"] if transaction else ""
    if message.content.startswith('$tx_info') and txhash == "":
        txhash = str(message.content).replace("$tx_info", "").replace(" ", "")

    if not txhash or len(txhash) != 64:
        await message.channel.send(f'Incorrect length for tx_hash: {len(txhash)} instead 64')
        await session.close()
        return False

    if transaction["code"] == TRANSACTION_CODE_OK:
        await message.channel.send(f'🚀 - Transaction was created: {txhash}')
    elif transaction["code"] == TRANSACTION_CODE_IN_MEMPOOL_CACHE:
        await message.channel.send(f'🚀 - Transaction was already in mempool cache: {txhash}')

    try:
        tx = await api.get_transaction_info(session, txhash)

        if "amount" in str(tx) and "fee" in str(tx):
            from_ = tx['tx']['body']['messages'][0]['from_address']
            to_ = tx['tx']['body']['messages'][0]['to_address']
            amount_ = tx['tx']['body']['messages'][0]['amount'][0]['amount']

            tx = f'🚀 - {requester}\n' \
                 f'{amount_} ulava successfully transfered to {to_}' \
                 '```' \
                 f'From:         {from_}\n' \
                 f'To (BECH32):  {to_}\n' \
                 f'Amount:       {amount_} ulava ```' \
                 f'{EXPLORER_URL}/txs/{txhash}'
            await message.channel.send(tx)
            await session.close()
        else:
            await message.channel.send(f'{requester}, `{tx}`')
            await session.close()

    except Exception:
        logger.exception("Can't get transaction info")
        await message.channel.send(f"Can't get transaction info of your request {message.content}")
        await session.close()


async def requester_basic_requirements(session, ctx, address, amount):
    faucet_address_length = len(FAUCET_ADDRESS)
    if len(address) != faucet_address_length or address[:len(BECH32_HRP)] != BECH32_HRP:
        await ctx.send(
            f'{ctx.author.mention}, Invalid address format `{address}`\n'
            f'Address length must be equal to {faucet_address_length}'
            f' and the prefix must be `{BECH32_HRP}`'
        )
        return False

    # check if requester holds already Lava
    requester_balance = float(await api.get_addr_balance(session, address))
    if requester_balance > float(amount):
        await ctx.send(
            f'{REJECT_EMOJI} - {ctx.author.mention} \n'
            f'You already own {round(requester_balance, 2)}'
            f' ulava - please use your funds!'
        )
        await session.close()
        return False

    # check if faucet has enough balance
    faucet_balance = float(await api.get_addr_balance(session, FAUCET_ADDRESS))
    if faucet_balance < float(amount):
        await ctx.send(
            f'{REJECT_EMOJI} - {ctx.author.mention} \nFaucet ran out of funds. \n'
            f'Please reach out to the mods to fill it up.')
        await session.close()
        return False

    return True


async def eval_transaction(session, ctx, transaction):

    if transaction["code"] in (TRANSACTION_CODE_OK, TRANSACTION_CODE_IN_MEMPOOL_CACHE):
        await submit_tx_info(session, ctx.message, ctx.author.mention, transaction)
        logger.info("successfully send tx info to discord")
    else:
        await ctx.send(
            f'{REJECT_EMOJI} - {ctx.author.mention}, Can\'t send transaction. '
            f'Try making another request\n{transaction}'
        )
        logger.error("Couldn't process tx", extra={transaction: transaction})

    now = datetime.datetime.now()
    await save_transaction_statistics(f'{transaction};{now.strftime("%Y-%m-%d %H:%M:%S")}')
    await session.close()


def main():
    bot.run(TOKEN)


@bot.event
async def on_ready():
    logger.info('Logged in as user', extra={"user": bot.user})


@bot.command(name='faucet_address')
async def faucet_address(ctx):
    session = aiohttp.ClientSession()
    try:
        await ctx.send(
            f'{FAUCET_EMOJI} - **Bot address** \n \n'
            f'The bots active address is: \n'
            f'`{FAUCET_ADDRESS}`\n \n'
        )
        await session.close()
    except Exception:
        logging.exception("Can't send message $faucet_address. Please report the incident to one of the mods.")
        await session.close()


@bot.command(name='balance')
async def balance(ctx):
    session = aiohttp.ClientSession()
    address = str(ctx.message.content).replace("$balance", "").replace(" ", "").lower()
    if address[:len(BECH32_HRP)] == BECH32_HRP:
        coins = await api.get_addr_balance(session, address)
        if float(coins) > 0:
            await ctx.channel.send(
                f'⚖️ - {ctx.author.mention}\nYour current Lava balance\n'
                f'```{api.coins_dict_to_string({"ulava": coins}, "grid")}```\n'
                f'To check your IBC token balance please open the block explorer: {EXPLORER_URL}/account/{address}')
            await session.close()

        else:
            await ctx.channel.send(
                f'{ctx.author.mention} your account is not initialized with Lava (balance is empty)')
            await session.close()


@bot.command(name='info')
async def info(ctx):
    session = aiohttp.ClientSession()
    await ctx.send(help_msg)
    await session.close()


@bot.command(name='faucet_status')
async def status(ctx):
    session = aiohttp.ClientSession()
    logger.info("status request", extra={"by": ctx.author.name})
    try:
        s = await api.get_node_status(session)
        coins = await api.get_addr_all_balance(session, FAUCET_ADDRESS)

        if "node_info" in str(s) and "error" not in str(s):
            s = f'```' \
                f'Moniker:       {s["result"]["node_info"]["moniker"]}\n' \
                f'Address:       {FAUCET_ADDRESS}\n' \
                f'OutOfSync:     {s["result"]["sync_info"]["catching_up"]}\n' \
                f'Last block:    {s["result"]["sync_info"]["latest_block_height"]}\n\n' \
                f'Faucet balance:\n{api.coins_dict_to_string(coins, "")}```'
            await ctx.send(s)
            await session.close()
    except Exception:
        logger.exception("Exception occurred during faucet status request")
        await session.close()


@bot.command(name='tx_info')
async def tx_info(ctx):
    session = aiohttp.ClientSession()
    await submit_tx_info(session, ctx.message, ctx.author.mention)


#@commands.cooldown(1, REQUEST_TIMEOUT, commands.BucketType.user)
@bot.command(name='request')
async def request(ctx):
    logger.info("Request command start")
    session = aiohttp.ClientSession()
    requester_address = str(ctx.message.content).replace("$request", "").replace(" ", "").lower()
    # do basic requirements
    basic_checks = await requester_basic_requirements(session, ctx, requester_address, AMOUNT_TO_SEND)
    if not basic_checks:
        logger.info("Basic checks failed")
        return

    # send and evaluate tx
    transaction = await api.send_tx(session, recipient=requester_address, amount=AMOUNT_TO_SEND)

    await eval_transaction(session, ctx, transaction)


if __name__ == "__main__":
    main()
