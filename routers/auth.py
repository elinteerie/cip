from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, status, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.orm import Session
from database import get_db
from models import (User, CreateUserRequest,  EmailVRequest, ResetPassword,
                     UpdateUserInfoRequest)
from passlib.context import CryptContext
from typing import Annotated
from sqlalchemy import or_
import os
from fastapi import BackgroundTasks
from jose import JWTError, jwt
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
import json
from sqlmodel import select
from fastapi.security import OAuth2
from fastapi import Form
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import re


load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
print(SECRET_KEY)
ALGORITHM = os.getenv('ALGORITHM')
print(ALGORITHM)
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES')



router = APIRouter(prefix='/auth',tags=['Authentication'])

#Encrypt Password
bcrypt_context = CryptContext(schemes=['argon2', 'bcrypt'], default='bcrypt', deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')
db_dependency = Annotated[AsyncSession, Depends(get_db)]




EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

def validate_email(email: str):
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please input an email address."
        )
    
    # Check if email matches the regex pattern
    if not re.match(EMAIL_REGEX, email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a valid email address."
        )
    return email



class OAuth2PhoneNumberRequestForm:
    def __init__(
        self,
        email: str = Form(...),
        password: str = Form(...),
        scope: str = Form(""),
        client_id: str = Form(None),
        client_secret: str = Form(None),
    ):
        self.email = email
        self.password = password
        self.scopes = scope.split()
        self.client_id = client_id
        self.client_secret = client_secret


class OAuthWalletRequestForm:
    def __init__(
        self,
        wallet_address: str = Form(...),
        scope: str = Form(""),
        client_id: str = Form(None),
        client_secret: str = Form(None),
    ):
        self.wallet_address = wallet_address
        self.scopes = scope.split()
        self.client_id = client_id
        self.client_secret = client_secret


#Authenticate Users
async def authenticate_user(email: str, password: str, db: db_dependency):

    statement = select(User).where(User.email == email)
    result = await db.execute(statement)
    result = result.scalars().first()
    user = result
    #print("user:",user)

    if not user:
        return False
    
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user

#Create a JWT
async def create_access_token(email: str, wallet_address:str, user_id: int, expires_delta: timedelta ):
    encode = {"sub": str(user_id), "id": user_id, "wallet_address": wallet_address, "email": email}  
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)
    
# In your database module
async def get_user_by_id(user_id: int, db):
    statement = select(User).where(User.id==user_id)
    user = await db.execute(statement)
    user = user.scalars().first()
    return user

#Decode a JWT
async def get_current_user(request: Request, db: db_dependency):

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization token is missing or invalid")
    
    token = auth_header.split(" ")[1]
    print("token:", token)
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

    print("payload")
        
    # Extract common claims
    username: str = payload.get('sub')
    user_id: int = payload.get('id')

    statement = select(User).where(User.id==user_id)
    user = await db.execute(statement)
    user = user.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No User Found, Please Log In")

    #print("token:", user)
    return {
            'username': user.email,
            'id': user.id
        }
    
        



class Token(BaseModel):
    access_token: str
    token_type: str
    expires: str








@router.post('/create-user-request-otp', status_code=status.HTTP_201_CREATED)
async def create_user_request_otp(request: CreateUserRequest, db: db_dependency):
    """
    You either choose either to register with web2 or Web3 wallet
    - When requesting with Web2: {
                "reg_type": "web2",
                "email": "june@gmail.com",
                "password": "j67827489"
            }

    - When Requesting wit Web3: {
                "reg_type": "web3",
                "wallet_address": "0x7346827472489",
                "public_key": "74837567"
            }
    """

    if request.reg_type == "web2":

        result = select(User).where(User.email == request.email)
        existing_user = await db.execute(result)
        existing_user = existing_user.scalars().first()

        if existing_user:
            raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with this Email: {request.email} already exists."
        )

        

        if not request.password:
            raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Please Input a Password to Proceed"
        )

        validate_email(request.email)   # ✅ Valid

        hashed_passwords = bcrypt_context.hash(request.password)


        create_user= User(
            email=request.email,
            hashed_password=hashed_passwords,
            is_active=True,
            role="user")

        db.add(create_user)
        await db.commit()
        await db.refresh(create_user)


        token = await create_access_token(create_user.email, create_user.wallet_address, create_user.id, timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES)))

        return {
            "status":"New Account Created",
            "user_id": create_user.id,
            "message": "New Account Has Been Created with Email and Password",
            'access_token': token,
            "token_expires": f'{ACCESS_TOKEN_EXPIRE_MINUTES}'
        }
    elif request.reg_type == "web3":

        statement = select(User).where(User.wallet_address == request.wallet_address)
        existing_user = await db.execute(statement)
        existing_user = existing_user.scalars().first()

        if existing_user:
            raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with Wallet ALready Exit"
        )






        if not request.wallet_address:
            raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Please Input the Wallet Address to Proceed"
        )

        create_user= User(
            wallet_address=request.wallet_address,
            is_active=True,
            is_wallet_connected=True,
            role="user")

        db.add(create_user)
        await db.commit()
        db.refresh(create_user)


        token = await create_access_token(create_user.email, create_user.wallet_address, create_user.public_key, create_user.id, timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES)))



    return {
        'message': "User Created",
        'access_token': token,
        "user_id": create_user.id,
        'token_type': "bearer",
        "token_expires": f'{ACCESS_TOKEN_EXPIRE_MINUTES}'
        
    }


    

@router.post('/token', response_model=Token)
async def login_for_access_token(db: db_dependency, form_data: OAuth2PhoneNumberRequestForm = Depends()):


    user = await authenticate_user(form_data.email, form_data.password, db)

    if not user:
        raise HTTPException(status_code=401, detail="Could Not Valid Credential")
        
    
    token = await create_access_token(user.email, user.wallet_address, user.id, timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES)))
    
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires": f'{ACCESS_TOKEN_EXPIRE_MINUTES}'
    }



#Authenticate Users
async def authenticate_wallet_user(wallet_address: str, db: db_dependency):

    statement = select(User).where(User.wallet_address == wallet_address)
    result = await db.execute(statement)
    result = result.scalars().first()
    user = result
    #print("user:",user)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with the provided wallet address not found."
        )
    
    return user




@router.post('/token-for-wallet-login', response_model=Token)
async def login_for_access_token(db: db_dependency, form_data: OAuthWalletRequestForm = Depends()):


    user = await authenticate_wallet_user(form_data.wallet_address, db)

    if not user:
        raise HTTPException(status_code=401, detail="Could Not Valid Credential")
        
    
    token = await create_access_token(user.email, user.wallet_address, user.id, timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES)))
    
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires": f'{ACCESS_TOKEN_EXPIRE_MINUTES}'
    }





@router.get("/user-info",status_code=status.HTTP_200_OK )
async def user_info(db: db_dependency, user: dict= Depends(get_current_user)):

    user_id = user.get("id")

    print("userid:", user_id)
    result = select(User).where(User.id == user_id)
    existing_users = await db.execute(result)
    existing_user = existing_users.scalars().first()
    
    return {
        "status": "User Information",
        "wallet_address": existing_user.wallet_address,
        "public_key": existing_user.public_key,
        "is_wallet_connected": existing_user.is_wallet_connected,
        "Plan_id": existing_user.plan_id
    }


@router.patch('/account-wallet-update', status_code=status.HTTP_200_OK)
async def account_info_update(request: UpdateUserInfoRequest, db: db_dependency, user: dict= Depends(get_current_user)):
    """
   Connect Wallet after web2 route {"wallet_address": "786787"
    
     }
    """
    user_id = user.get("id")
    print("userid:", user_id)
    result = select(User).where(User.id == user_id)
    existing_user = await db.execute(result)
    existing_user = existing_user.scalars().first()
    print("userw:", request.wallet_address)

    if not request.wallet_address or request.wallet_address.strip() == "":
        raise HTTPException(
            status_code=400,
            detail="Wallet address cannot be empty."
        )

    if not existing_user.wallet_address:
        print("user_wa:", request.wallet_address, flush=True)
        existing_user.wallet_address = request.wallet_address
        print("user_wa:", request.wallet_address, flush=True)
        existing_user.is_wallet_connected = True

        await db.commit()
        await db.refresh(existing_user)
    

        return {
        'message': "User Wallet Connected"        
        }
    
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You have connected Wallet Already")






"""

@router.post('/passw-reset-request', status_code=status.HTTP_200_OK)
async def request_otp(user_request: PasswordRequest, db: db_dependency, background_tasks: BackgroundTasks):

    user = db.query(User).filter(User.email == user_request.email).first()
    print(user)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


    
    user_otp_create = OTP(user_id=user.id)
    db.add(user_otp_create)

    db.commit()
    db.refresh(user_otp_create)


    background_tasks.add_task(
        send_custom_email,
        user_request.email,
        "FUTO STUDY APP",
        "Password Reset",
        f" This Code last for just 10 minutes {user_otp_create.otp_code}"
    )

    
    return {
        "message": "OTP created and sent",
        "otp_code": user_otp_create.otp_code  # For testing only; remove in production
    }

@router.post('/passw-reset-confirm', status_code=status.HTTP_200_OK)
async def otp_verify(otp_request: OTPVerify, db: db_dependency):

    user = db.query(User).filter(User.email == otp_request.email).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    otp = db.query(OTP).filter(OTP.user_id == user.id, OTP.otp_code ==otp_request.otp_code).order_by(OTP.created_at.desc()).first()
    

    if not otp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OTP not found")
    

    if is_otp_expired(otp):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP has expired")
    

    
    
    

    if otp.is_used:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP has being used")

    hashed_password = bcrypt_context.hash(otp_request.new_password)

    user.hashed_password = hashed_password
    db.add(user)
    otp.is_used = True
    db.add(otp)
    db.commit()




    return {
        "message": "User Password Changed. Action performed."
    }

"""