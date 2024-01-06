from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session

from app.core.config import get_setting
from app.core.security import create_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.schemas.token import Token, RefreshToken
from app.schemas.kakao import KakaoCode
from app.crud.user import crud_user
from app.api.depends import get_current_user
from fastapi_sessions import session_verifier

import requests

router = APIRouter()
settings = get_setting()

# @router.post("/register")
# def post(user: UserCreate, db: Session = Depends(get_db)):
#     db_user = crud_user.get_by_username(db, username=user.username)
#     if db_user:
#         raise HTTPException(status_code=400, detail="username already registered")
#     return crud_user.create(db=db, obj_in=user)

# 엑세스 토큰을 저장할 변수
@router.post('/')
async def kakaoAuth(authorization_code: KakaoCode, db: Session = Depends(get_db)):
    kakao_token = get_kakao_token(authorization_code=authorization_code)
    kakao_access_token = kakao_token.get("access_token")
    kakao_refresh_token = kakao_token.get("refresh_token")

    kakao_id = get_kakao_id(kakao_access_token)
    user = crud_user.get_by_kakao_id(db, kakao_id=kakao_id)
    jwt = get_jwt(db=db, kakao_id=kakao_id)
    if user:
        new_user_data = UserUpdate(kakao_refresh_token=kakao_refresh_token, jwt_refresh_token=jwt.refresh_token)
        crud_user.update(db=db, db_obj=user, obj_in=new_user_data)
        return jwt
    obj_in = UserCreate(kakao_id=kakao_id, kakao_refresh_token=kakao_refresh_token, jwt_refresh_token=jwt.refresh_token)
    user = crud_user.create(db, obj_in=obj_in)
    return jwt

def get_kakao_token(authorization_code: KakaoCode):
    REST_API_KEY = settings.REST_API_KEY
    REDIRECT_URI = settings.REDIRECT_URI
    _url = f'https://kauth.kakao.com/oauth/token'
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "authorization_code",
        "client_id": REST_API_KEY,
        "code": authorization_code.code,
        "redirect_uri": REDIRECT_URI
    }
    _res = requests.post(_url, headers=headers, data=data)
    
    if _res.status_code == 200:
        _result = _res.json()
        return _result
    else:
        raise HTTPException(status_code=401, detail="Kakao code authentication failed")

def get_kakao_id(kakao_access_token):
    _url = "https://kapi.kakao.com/v2/user/me"
    headers = {
        "Authorization": f"Bearer {kakao_access_token}"
    }
    _res = requests.get(_url, headers=headers)

    if _res.status_code == 200:
        response_data = _res.json()
        user_id = response_data.get("id")
        return user_id
    else:
        raise HTTPException(status_code=401, detail="Kakao access token authentication failed")
    
def get_jwt(*, kakao_id: int, db: Session = Depends(get_db)) -> Token:
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_token(subject=kakao_id, expires_delta=access_token_expires)
    
    refresh_token_expires = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    refresh_token = create_token(subject=kakao_id, expires_delta=refresh_token_expires)
    res = Token(access_token=access_token, refresh_token=refresh_token, token_type="Bearer")
    return res