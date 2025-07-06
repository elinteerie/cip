import httpx
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

TESTURL = os.getenv('COTI_TEST')

async def get_important_tx_details(txhash):
    url = f"{TESTURL}/{txhash}"

    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()

        return {
            "transaction_hash": data.get("hash"),
            "status": data.get("status"),  # usually "ok" for success
            "from_address": data.get("from", {}).get("hash"),
            "to_address": data.get("to", {}).get("hash"),
            "contract_name": data.get("to", {}).get("name"),
            "value_sent": data.get("value"),  # usually in wei
            "timestamp": data.get("timestamp"),
            "gas_used": data.get("gas_used"),
            "transaction_fee": data.get("fee", {}).get("value")
        }
