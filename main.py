import os
from fastapi import FastAPI
from database import engine, get_db
import models
from models import User, Plan, Asset, Beneficiary, TriggerCondition
from routers import  auth, process
from contextlib import asynccontextmanager
from models import init_db#,  create_db_and_tables,
from fastapi import Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse, RedirectResponse
from typing import Annotated
#Admin
from starlette.requests import Request
from starlette.responses import Response
from starlette_admin.auth import AdminConfig, AdminUser, AuthProvider
from starlette_admin.exceptions import FormValidationError, LoginFailed
from fastapi.middleware.cors import CORSMiddleware
from starlette.applications import Starlette
from starlette_admin.contrib.sqla import Admin, ModelView
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import threading
from distri import main
load_dotenv()




origins = [
    "http://localhost",        # Allow requests from localhost
    "http://localhost:3000",  # Allow requests from frontend (React, etc.)
    "http://127.0.0.1",

]

import asyncpg


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code to run on startup
    print("db created ")
    #create_db_and_tables()
    #threading.Thread(target=main, daemon=True).start()
    await init_db()
    print("db updated")
    yield  # Your application runs during this yield

app = FastAPI(lifespan=lifespan, title="Crypto Investment Protocol CIP", 
              summary="This is Backend by @elinteerie@gmail.com", 
              version="1.0", 
              debug=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # Origins allowed to access your app
    allow_credentials=True,          # Allow cookies
    allow_methods=["*"],             # Allow all HTTP methods
    allow_headers=["*"],             # Allow all headers
)


#Include routers
app.include_router(auth.router)
app.include_router(process.router)

#static and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templatesa")

#Admin


users = {
    "admin": {
        "name": "Admin",
        "avatar": "admin.png",
        "company_logo_url": "admin.png",
        "roles": ["read", "create", "edit", "delete", "action_make_published"],
    },
    "johndoe": {
        "name": "John Doe",
        "avatar": None, # user avatar is optional
        "roles": ["read", "create", "edit", "action_make_published"],
    },
    "viewer": {"name": "Viewer", "avatar": "guest.png", "roles": ["read"]},
}


class UsernameAndPasswordProvider(AuthProvider):
    """
    This is only for demo purpose, it's not a better
    way to save and validate user credentials
    """

    async def login(
        self,
        username: str,
        password: str,
        remember_me: bool,
        request: Request,
        response: Response,
    ) -> Response:
        if len(username) < 3:
            """Form data validation"""
            raise FormValidationError(
                {"username": "Ensure username has at least 03 characters"}
            )

        if username in users and password == "passwordy":
            """Save `username` in session"""
            request.session.update({"username": username})
            return response

        raise LoginFailed("Invalid username or password")

    async def is_authenticated(self, request) -> bool:
        if request.session.get("username", None) in users:
            """
            Save current `user` object in the request state. Can be used later
            to restrict access to connected user.
            """
            request.state.user = users.get(request.session["username"])
            return True

        return False

    def get_admin_config(self, request: Request) -> AdminConfig:
        user = request.state.user  # Retrieve current user
        # Update app title according to current_user
        custom_app_title = "Hello, " + user["name"] + "!"
        # Update logo url according to current_user
        custom_logo_url = None
        if user.get("company_logo_url", None):
            custom_logo_url = request.url_for("static", path=user["company_logo_url"])
        return AdminConfig(
            app_title=custom_app_title,
            logo_url=custom_logo_url,
        )

    def get_admin_user(self, request: Request) -> AdminUser:
        user = request.state.user  # Retrieve current user
        photo_url = None
        if user["avatar"] is not None:
            photo_url = request.url_for("static", path=user["avatar"])
        return AdminUser(username=user["name"], photo_url=photo_url)

    async def logout(self, request: Request, response: Response) -> Response:
        request.session.clear()
        return response


admin = Admin(engine, title="CIP: Admin CRUD")

admin.add_view(ModelView(models.User))
admin.add_view(ModelView(models.Plan))
admin.add_view(ModelView(models.Asset))
admin.add_view(ModelView(models.Beneficiary))
admin.add_view(ModelView(models.TriggerCondition))





admin.mount_to(app)





