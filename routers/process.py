from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, Plan, TriggerTypeEnum, AssetTypeEnum, CreateAssetSchema, Asset, Beneficiary, TriggerCondition
from typing import Annotated, List
import os
from fastapi import BackgroundTasks
from jose import JWTError, jwt
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
import json
from routers.auth import get_current_user
from sqlmodel import select
from fastapi import Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload



router = APIRouter(prefix='/process',tags=['Plans And Triggers'])
db_dependency = Annotated[AsyncSession, Depends(get_db)]


@router.get("/get-all-plans", status_code=status.HTTP_200_OK)
async def get_all_plans(db: db_dependency, user: dict= Depends(get_current_user)):

    statement = select(Plan)
    result = await db.execute(statement)
    plans = result.scalars().all()
    
    print("plans:", plans)

    return {
        "plans": plans
    }



@router.patch("/user-select-plan", status_code=status.HTTP_200_OK)
async def up_all_plans(db: db_dependency, plan_id:int, user: dict= Depends(get_current_user)):

    statement = select(Plan).where(Plan.id == plan_id)
    result = await db.execute(statement)
    plan = result.scalars().first()

    user_id = user.get("id")
    result = select(User).where(User.id == user_id)
    existing_user = await db.execute(result)
    existing_user = existing_user.scalars().first()
    
    existing_user.plan = plan

    ##Charge First Before Upgrading

    await db.commit()
    db.refresh(existing_user)

    return {
        "status": "Plan Upgraded",
        "message": f"User Plan updated to {plan.name}"
    }




@router.get("/trigger-types", response_model=List[str], status_code=status.HTTP_200_OK)
async def get_trigger_types():
    """
    Get all available trigger types.
    """
    return [trigger.value for trigger in TriggerTypeEnum]



@router.get("/asset-supported", response_model=List[str], status_code=status.HTTP_200_OK)
async def get_trigger_types():
    """
    Get all available trigger types.
    """
    return [asset.value for asset in AssetTypeEnum]


@router.post("/create-asset", status_code=status.HTTP_201_CREATED)
async def create_asset(db: db_dependency, asset_data: CreateAssetSchema, user: dict= Depends(get_current_user)):

    # Step 1: Validate Total Share Percentage
    total_percentage = sum([b.share_percentage for b in asset_data.beneficiaries])
    if total_percentage != 100:
        raise HTTPException(status_code=400, detail="Total share percentage must equal 100%.")
    
    # Step 2: Get the user from the database
    user_id = user.get("id")
    statement = select(User).where(User.id == user_id)
    result = await db.execute(statement)
    existing_user = result.scalars().first()
    
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found.")
    

    if not existing_user.wallet_address and not existing_user.public_key:
        raise HTTPException(status_code=404, detail="Please Connect  A Wallet")
    

    if not existing_user.plan_id:
        raise HTTPException(status_code=404, detail="Choose A Plan FIrst")
        
        
    
    
    # Step 3: Create the Asset
    asset = Asset(
        asset_type=asset_data.asset_type,
        owner_id=user_id,
        wallet_address= "0x98796788",
        txhash="8977839Jjjdj"
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)


    for b in asset_data.beneficiaries:
        beneficiary = Beneficiary(
            wallet_address=b.wallet_address,
            share_percentage=b.share_percentage,
            asset_id=asset.id
        )
        db.add(beneficiary)
    await db.commit()


    trigger_condition = TriggerCondition(
        condition_type=asset_data.trigger_condition,
        value=asset_data.trigger_value,
        asset=asset
    )
    db.add(trigger_condition)
    await db.commit()
    await db.refresh(asset)

    statement = select(Asset).options(
    selectinload(Asset.beneficiaries),
    selectinload(Asset.trigger_condition)
    ).where(Asset.id == asset.id)

    result = await db.execute(statement)
    asset = result.scalars().first()





    return {
        "status": "Asset Created",
        "asset": {
            "id": asset.id,
            "type": asset.asset_type,
            "owner": existing_user.wallet_address,
            "beneficiaries": [{"name": b.wallet_address,"share": str(b.share_percentage)} for b in asset.beneficiaries],
            "trigger_condition": asset.trigger_condition.condition_type,
            "txhash": asset.txhash
        }
    }



@router.get("/an-asset", status_code=status.HTTP_200_OK)
async def an_asset(db: db_dependency, asset_id, user: dict= Depends(get_current_user)):

    user_id = user.get("id")
    statement = select(User).where(User.id == user_id)
    result = await db.execute(statement)
    existing_user = result.scalars().first()
    
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found.")
    


    statement = select(Asset).options(
    selectinload(Asset.beneficiaries),
    selectinload(Asset.trigger_condition)
    ).where(Asset.id == asset_id)

    result = await db.execute(statement)
    asset = result.scalars().first()

    return {
        "status": "Asset Created",
        "asset": {
            "id": asset.id,
            "type": asset.asset_type,
            "owner": existing_user.wallet_address,
            "beneficiaries": [{"name": b.wallet_address,"share": str(b.share_percentage)} for b in asset.beneficiaries],
            "trigger_condition": asset.trigger_condition.condition_type,
            "txhash": asset.txhash,
            "asset_wallet_address": asset.wallet_address
        }
    }



@router.get("/return-user-assets", status_code=status.HTTP_200_OK)
async def an_asset(db: db_dependency, user: dict= Depends(get_current_user)):

    user_id = user.get("id")
    statement = select(User).where(User.id == user_id)
    result = await db.execute(statement)
    existing_user = result.scalars().first()
    
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found.")
    


    statement = (
        select(Asset)
        .options(
            selectinload(Asset.beneficiaries),
            selectinload(Asset.trigger_condition)
        )
        .where(Asset.owner_id == user_id)
    )

    result = await db.execute(statement)
    assets = result.scalars().all()

    if not assets:
        raise HTTPException(status_code=404, detail="No assets found for the user")

    # Serialize the response
    assets_data = [
        {
            "id": asset.id,
            "type": asset.asset_type,
            "beneficiaries": [
                {"wallet_address": b.wallet_address, "share": str(b.share_percentage)}
                for b in asset.beneficiaries
            ],
            "trigger_condition": {
                "type": asset.trigger_condition.condition_type,
                "value": asset.trigger_condition.value
            } if asset.trigger_condition else None
        }
        for asset in assets
    ]

    return {
        "status": "Success",
        "assets": assets_data
    }
    




    



