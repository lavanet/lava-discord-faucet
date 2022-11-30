import configparser
import os

from cosmospy import seed_to_privkey
from dotenv import load_dotenv

load_dotenv()

# Load config
c = configparser.ConfigParser()
c.read("config.ini")

# Load data from config
VERBOSE_MODE = str(c["DEFAULT"]["verbose"])
DECIMAL = float(c["CHAIN"]["decimal"])
REST_PROVIDER = str(c["REST"]["provider"])
MAIN_DENOM = str(c["CHAIN"]["denomination"])
RPC_PROVIDER = str(c["RPC"]["provider"])
CHAIN_ID = str(c["CHAIN"]["id"])
BECH32_HRP = str(c["CHAIN"]["BECH32_HRP"])
GAS_PRICE = int(c["TX"]["gas_price"])
GAS_LIMIT = int(c["TX"]["gas_limit"])
FAUCET_PRIVKEY = str(os.getenv("FAUCET_PRIVATE_KEY"))
FAUCET_SEED = str(os.getenv("FAUCET_SEED"))

if FAUCET_PRIVKEY is None:
    FAUCET_PRIVKEY = str(seed_to_privkey(FAUCET_SEED).hex())

FAUCET_ADDRESS = str(c["FAUCET"]["faucet_address"])
EXPLORER_URL = str(c["OPTIONAL"]["explorer_url"])
if EXPLORER_URL != "":
    EXPLORER_URL = f'{EXPLORER_URL}/transactions/'

DENOMINATION_LST = c["TX"]["denomination_list"].split(",")
AMOUNT_TO_SEND = c["TX"]["amount_to_send"]

REQUEST_TIMEOUT = int(c["FAUCET"]["request_timeout"])
TOKEN = str(os.getenv("DISCORD_BOT_TOKEN"))
LISTENING_CHANNELS = list(c["FAUCET"]["channels_to_listen"].split(","))

FAUCET_EMOJI = "🚰"
APPROVE_EMOJI = "✅"
REJECT_EMOJI = "🚫"
