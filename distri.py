from web3 import Web3
import time
import json
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from models import User, Asset, TriggerCondition, TriggerTypeEnum
from sqlmodel import SQLModel, Field, Session, select, create_engine
from decimal import Decimal
import time
import os
from dotenv import load_dotenv
load_dotenv()


DATABASE_URL=os.getenv('DATABASE_URL_BOT')

engine = create_engine(DATABASE_URL)

def get_ready_assets():
    with Session(engine) as session:
        now = int(time.time())  # UNIX timestamp
        stmt = (
    select(Asset)
    .where(Asset.validated_funds == True)
    .where(Asset.distributed == False)
    .where(Asset.trigger_condition != None)
    .where(
        or_(
            and_(
                Asset.trigger_condition.has(
                    and_(
                        TriggerCondition.condition_type == TriggerTypeEnum.DUE_DATE,
                        TriggerCondition.value <= now
                    )
                )
            ),
            and_(
                Asset.trigger_condition.has(
                    TriggerCondition.condition_type == TriggerTypeEnum.INACTIVITY
                ),
                Asset.is_now_due_date == True
            )
        )
    )
    .options(selectinload(Asset.trigger_condition))
    )
        
        return session.exec(stmt).all()

# === CONFIGURATION ===
RPC_URL = "https://testnet.coti.io/rpc"
CONTRACT_ADDRESS = Web3.to_checksum_address("0x2bebf9eF4d3F694B47525d8C26B3F6995DE6cEAA")

# Load your wallet's private key and address
PRIVATE_KEY = "0c74b1f098f35805870c2c02e63d23100377a0fcd97c530e7957e14793442b0d"
MY_ADDRESS = "0x0F9Bf01fe3b3eE9027CBf569383761ED55A0b5a2"
NEW = "0x1014BD7f50abb2A3107EC701701fb93542912e3a"

# === LOAD ABI ===
with open("WalletDistributor.abi.json") as f:
    CONTRACT_ABI = json.load(f)

# === INIT WEB3 ===
web3 = Web3(Web3.HTTPProvider(RPC_URL))
assert web3.is_connected(), "Failed to connect to RPC"

# === INIT CONTRACT ===
contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)

# === BOT LOOP ===
def main():
    print("🚀 Starting COTI Will Bot…")
    while True:
        try:
            assets = get_ready_assets()
            print(f"🔍 Found {len(assets)} validated assets to process.")
            for asset in assets:
                owner = Web3.to_checksum_address(asset.wallet_address)
                will_id = asset.blockchain_user_will_id
                inactivity_months = int(asset.trigger_condition.value or 0)

                print(
                    f"📤 Distributing → owner: {owner}, willId: {will_id}, "
                    f"observedInactivity: {inactivity_months} months"
                )

                success, tx_hash, block_number = trigger_distribution(
                    owner, will_id, inactivity_months
                )

                if success:
                    with Session(engine) as session:
                        db_asset = session.get(Asset, asset.id)
                        if db_asset:
                            db_asset.distributed = True
                            session.add(db_asset)
                            session.commit()
                            print(f"📌 Asset {asset.id} marked as distributed ✅")
                else:
                    print(f"❌ Transaction failed for asset {asset.id}")

        except Exception as e:
            print(f"⚠️ Error: {e}")

        time.sleep(3600)  # run every  1Hr




def trigger_distribution(owner: str, will_id: int, observed_inactivity_months: int):
    nonce = web3.eth.get_transaction_count(MY_ADDRESS, "pending")
    gas_price = int(web3.eth.gas_price * 1.1)

    tx = contract.functions.distribute(
        owner,
        will_id,
        observed_inactivity_months
    ).build_transaction({
        "from": MY_ADDRESS,
        "nonce": nonce,
        "gas": 300_000,
        "gasPrice": gas_price
    })

    signed_tx = web3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"✅ Tx sent: {tx_hash.hex()}")

    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"⛏️ Mined in block {receipt.blockNumber}")

    if receipt.status == 1:
        return True, tx_hash.hex(), receipt.blockNumber
    else:
        return False, tx_hash.hex(), receipt.blockNumber

    

if __name__ == "__main__":
    main()
