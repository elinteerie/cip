from models import *
from sqlalchemy import event
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from typing import Annotated
from fastapi import Depends, HTTPException, status
from database import get_db
from utils import get_important_tx_details
import asyncio



db_dependency = Annotated[AsyncSession, Depends(get_db)]


async def validate_asset_created_async(txhash: str, session: AsyncSession):
    await asyncio.sleep(5)  # wait for 4 seconds
    result = await session.execute(select(Asset).where(Asset.txhash == txhash))
    asset = result.scalar_one_or_none()
    info = await get_important_tx_details(txhash=txhash)

    if not info.get("status") == "ok":
            return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Transaction Failed")
    if asset:
        asset.validated_created = True
        session.add(asset)
        await session.commit()
        await session.refresh(asset)
        print(f"Asset {asset.id} validated.")
    else:
        print("No asset found with that txhash.")


async def validate_asset_funded_async(txhash: str, session: AsyncSession):
    await asyncio.sleep(20)  # wait for 4 seconds
    result = await session.execute(select(Asset).where(Asset.txhash_funded == txhash))
    asset = result.scalar_one_or_none()
    info = await get_important_tx_details(txhash=txhash)

    if not info.get("status") == "ok":
         return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Transaction Failed")
    if asset:
        asset.validated_funds = True
        session.add(asset)
        await session.commit()
        await session.refresh(asset)
        print(f"Asset {asset.id} validated.")
    else:
        print("No asset found with that txhash.")



