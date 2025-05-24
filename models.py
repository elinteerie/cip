from database import engine
from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional
import string
from sqlalchemy import Column, DateTime
from datetime import datetime, timezone, timedelta, date
import uuid
from enum import Enum
from decimal import Decimal
import random



def generate_random_hex_secret(length=6):
    """
    Generate a random hexadecimal string of the specified length.
    
    :param length: Length of the hex string (default is 16).
    :return: Random hex string.
    """
    hex_characters = string.hexdigits.lower()[:6]  # '0123456789abcdef'
    return ''.join(random.choice(hex_characters) for _ in range(length))



class RoleEnum(str, Enum):
    USER = "user"
    ADMIN = "admin"


class TriggerTypeEnum(str, Enum):
    MULTISIG = "multisig"
    INACTIVITY = "inactivity"
    DUE_DATE = "due_date"


class AssetTypeEnum(str, Enum):
    BTC = "BTC"
    ETH = "ETH"
    COTI = "COTI"
    USDT = "USDT"
    BNB = "BNB"
    MATIC = "MATIC"


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)
    email: str  = Field(nullable=True)
    balance: Decimal = Field(default=0, max_digits=12, decimal_places=2)
    is_active: bool = Field(default=False)
    role: RoleEnum = Field(nullable=True, default="user")
    hashed_password: str = Field(nullable=True)
    public_key: str = Field(nullable=True)
    wallet_address: str = Field(nullable=True)
    is_wallet_connected: bool = Field(default=False)
    connection_timestamp: datetime = Field(nullable=True)
    plan_id: Optional[int] = Field(default=None, foreign_key="plan.id")
    plan: Optional["Plan"] = Relationship(back_populates="users")
    assets: List["Asset"] = Relationship(back_populates="owner", cascade_delete=True)




class Asset(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    asset_type: AssetTypeEnum
    wallet_address: str
    balance: Decimal = Field(default=0.0)
    owner_id: Optional[int] = Field(default=None, foreign_key="user.id")
    owner: Optional[User] = Relationship(back_populates="assets")
    txhash: str
    beneficiaries: List["Beneficiary"] = Relationship(back_populates="asset", cascade_delete=True)
    trigger_condition_id: Optional[int] = Field(default=None, foreign_key="triggercondition.id")
    trigger_condition: Optional["TriggerCondition"] = Relationship(back_populates="asset")



class Beneficiary(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    wallet_address: str
    share_percentage: Decimal
    asset_id: Optional[int] = Field(default=None, foreign_key="asset.id")
    asset: Optional[Asset] = Relationship(back_populates="beneficiaries")



class Plan(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)
    name: str
    price: Decimal = Field(default=0, max_digits=5, decimal_places=2)
    users: List[User] = Relationship(back_populates="plan")
    

class TriggerCondition(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    condition_type: TriggerTypeEnum
    value: Optional[str] = None
    asset: Optional[Asset] = Relationship(back_populates="trigger_condition", cascade_delete=True)



class ResetPassword(SQLModel, table=False):
    email: str = Field(description="Be A Valid Email Address")
    password: str  = Field(description="Password")
    otp: str

    class Config:
        json_schema_extra = {
            "example": {
                "email": "elinteerie@gmail.com",
                "password": "12345",
                "otp": "9877"
            }
        }



class BeneficiarySchema(SQLModel, table=False):
    wallet_address: str
    share_percentage: Decimal


class CreateAssetSchema(SQLModel, table =False):
    asset_type: AssetTypeEnum
    beneficiaries: List[BeneficiarySchema]
    trigger_condition: TriggerTypeEnum
    trigger_value: Optional[str] = None


class CreateAssetSchemaSome(SQLModel, table =False):
    asset_type: AssetTypeEnum
    percentage: Decimal
    balance: Decimal
    beneficiaries: List[BeneficiarySchema]
    trigger_condition: TriggerTypeEnum
    trigger_value: Optional[str] = None


class CreateUserRequest(SQLModel, table=False):
    reg_type: str # "send" or "verify"
    email: Optional[str] = None  
    password: Optional[str] = Field(default=None, min_length=6, description="Password must be at least 6 characters.")
    wallet_address: Optional[str] = None 
    public_key: Optional[str] = None 

    class Config:
        json_schema_extra = {
            "example": {
                "reg_type": "web2",
                "email": "elinteerie@gmail.com",
                "password": "12345678"
            }
        }


class UpdateFirstPin(SQLModel, table=False):
    pin: str 

class UpdateUserInfoRequest(SQLModel, table=False):
    wallet_address: Optional[str] = None
    public_key: Optional[str] = None
    
    

class EmailVRequest(SQLModel, table=False):
    action: str # "send" or "verify"
    email: str
    otp: Optional[str] = None  # Required only for verification

    class Config:
        json_schema_extra = {
            "example": {
                "action": "send",
                "email": "elint@gmail.con",
                "otp": None
            }
        }


class AirtimeRequest(SQLModel, table=False):
    network: int # "send" or "verify"
    amount: float
    phone_number: str = Field(nullable=False)
    transaction_pin: str

    class Config:
        json_schema_extra = {
            "example": {
                "network": 1,
                "amount": 100.0,
                "phone_number": "08107807411",
                "transaction_pin": "5555"
            }
        }




class DataRequest(SQLModel, table=False):
    network: int # "send" or "verify"
    package: int
    phone_number: str = Field(nullable=False)
    transaction_pin: str

    class Config:
        json_schema_extra = {
            "example": {
                "network": 1,
                "package": 1,
                "phone_number": "08107807411",
                "transaction_pin": "5555"
            }
        }



"""def create_db_and_tables():
    SQLModel.metadata.create_all(engine)"""


async def init_db():
    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)