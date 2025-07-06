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
    #MULTISIG = "multisig"
    #INACTIVITY = "inactivity"
    DUE_DATE = "due_date"


class AssetTypeEnum(str, Enum):
    #BTC = "BTC"
    #ETH = "ETH"
    COTI = "COTI"
    #USDT = "USDT"
    #BNB = "BNB"
    #MATIC = "MATIC"


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
    txhash: str | None = Field(unique=True)
    validated_created: bool | None = Field(default=False)
    validated_funds: bool | None = Field(default=False)
    beneficiaries: List["Beneficiary"] = Relationship(back_populates="asset", cascade_delete=True)
    trigger_condition: Optional["TriggerCondition"] = Relationship(back_populates="asset", cascade_delete=True)



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
    individual_users: bool = Field(default=False, nullable=True)
    crypto_investors: bool = Field(default=False, nullable=True)
    legal_executirs: bool = Field(default=False, nullable=True)
    institutions: bool = Field(default=False, nullable=True)
    create_inherent_plans: bool = Field(default=False, nullable=True)
    multi_signature_wallet: bool = Field(default=False, nullable=True)
    encrypted_document_storage: bool = Field(default=False, nullable=True)
    ai_fraud_detection: bool = Field(default=False, nullable=True)
    ai_powered_plan_creation: bool = Field(default=False, nullable=True)
    api_access_for_institution: bool = Field(default=False, nullable=True)
    users: List[User] = Relationship(back_populates="plan")
    

class TriggerCondition(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    condition_type: TriggerTypeEnum
    value: Optional[int] = None
    asset_id: Optional[int] = Field(default=None, foreign_key="asset.id")
    asset: Optional[Asset] = Relationship(back_populates="trigger_condition")



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
    trigger_value: Optional[float] = None
    txhash: str


class CreateAssetSchemaSome(SQLModel, table =False):
    asset_type: AssetTypeEnum
    percentage: Decimal
    balance: Decimal
    beneficiaries: List[BeneficiarySchema]
    trigger_condition: TriggerTypeEnum
    trigger_value: Optional[float] = None


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







"""def create_db_and_tables():
    SQLModel.metadata.create_all(engine)"""


async def init_db():
    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)