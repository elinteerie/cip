import httpx
from datetime import datetime
import os
from dotenv import load_dotenv
from fastapi import HTTPException
from datetime import datetime, timezone

load_dotenv()

MAIN_URL = os.getenv('COTI_MAIN')


async def get_important_tx_details(txhash):
    url = f"{MAIN_URL}/{txhash}"

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



URL= "https://mainnet.cotiscan.io/api/v2/addresses"


async def get_latest_transaction(wallet_address):
    url = f"{URL}/{wallet_address}/transactions"
    print(url, flush=True)

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch transactions")
        data = response.json()
        items = data.get("items", [])
        if not items:
            raise HTTPException(status_code=404, detail="No transactions found for this address")
        
        latest_tx = items[0]  # first item is the latest
        timestamp_str= latest_tx.get("timestamp")

        tx_time = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00")).replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)

        diff_days = (now - tx_time).days
        print("diff_day:", diff_days)
        diff_months = diff_days / 30.44  # approx months
        print("diff_m:", diff_months)

        if diff_days <= 7:  # ≤ 1 week
            score = 0.25
        elif diff_days <= 30:  # > 1 week ≤ 1 month
            score = 1
        elif diff_days <= 60:  # > 1 month ≤ 2 months
            score = 2
        else:  # > 2 months
            score = round(diff_months)


        return score