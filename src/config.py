import configparser
import os

from cosmospy import seed_to_privkey
from dotenv import load_dotenv

load_dotenv()

# Load data from envs
VERBOSE_MODE = str(os.getenv("DEFAULT_VERBOSE"))
DECIMAL = float(os.getenv("CHAIN_DECIMAL"))
REST_PROVIDER = str(os.getenv("REST_PROVIDER"))
MAIN_DENOM = str(os.getenv("CHAIN_DENOMINATION"))
RPC_PROVIDER = str(os.getenv("RPC_PROVIDER"))
CHAIN_ID = str(os.getenv("CHAIN_ID"))
BECH32_HRP = str(os.getenv("CHAIN_BECH32_HRP"))
GAS_PRICE = int(os.getenv("TX_GAS_PRICE"))
GAS_LIMIT = int(os.getenv("TX_GAS_LIMIT"))
FAUCET_PRIVKEY = os.getenv("FAUCET_PRIVATE_KEY", None)
FAUCET_SEED = os.getenv("FAUCET_SEED", None)
BLOCK_TIME_SECONDS = int(os.getenv("BLOCK_TIME_SECONDS"))

if FAUCET_PRIVKEY is None:
    FAUCET_PRIVKEY = str(seed_to_privkey(FAUCET_SEED).hex())

FAUCET_ADDRESS = str(os.getenv("FAUCET_ADDRESS"))
EXPLORER_URL = str(os.getenv("OPTIONAL_EXPLORER_URL"))
if EXPLORER_URL != "":
    EXPLORER_URL = f'{EXPLORER_URL}/transactions'

DENOMINATION_LST = os.getenv("TX_DENOMINATION_LIST").split(",")
AMOUNT_TO_SEND = os.getenv("TX_AMOUNT_TO_SEND")

REQUEST_TIMEOUT = int(os.getenv("FAUCET_REQUEST_TIMEOUT"))
TOKEN = str(os.getenv("DISCORD_BOT_TOKEN"))
LISTENING_CHANNELS = list(os.getenv("FAUCET_CHANNELS_TO_LISTEN").split(","))

FAUCET_EMOJI = "🚰"
APPROVE_EMOJI = "✅"
REJECT_EMOJI = "🚫"
