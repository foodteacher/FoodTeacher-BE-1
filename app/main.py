from typing import Union
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse

from app.db.session import db_engine
from app.db.base import Base

from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session  # 데이터베이스 세션을 사용하기 위해 추가
from app.db.session import get_db, SessionLocal  # SessionLocal을 가져옴

from . import utils
from .db import base

from .service.clova_ai import get_executor
from .service.bmr_calculator import calculate_bmr
from .service.food_teacher import get_diet_exercise_advice

def create_tables():
    Base.metadata.create_all(bind=db_engine)

def get_application():
    app = FastAPI()
    create_tables()
    return app

app = get_application()

# CORS 설정
origins = [
    "http://localhost:3000",  # 원하는 도메인 및 포트를 추가
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드를 허용하려면 "*"
    allow_headers=["*"],  # 모든 HTTP 헤더를 허용하려면 "*"
)

@app.get("/")
def read_root():
    return "hello, 팩트폭행단~!"

############################################# 임시 api ####################################
def del_db_table(db: Session = Depends(get_db)):
    base.delete_all_users(db)
    return "good"

@app.get("/temp")
def temp_endpoint():
    db = SessionLocal()
    user_data = utils.UserBaseModel(
        name="서경원",
        kakao_token="fdkajklajfdskl223123kfjsklfj3",
        height=173,
        weight=72,
        age=29,
        gender="male",
        targetWeight=65.0   
    )
    result = base.user_create(db, user_data)
    db.close()
    return result

############################################# kakao api ####################################
# KakaO Login
@app.get('/kakao')
def kakao():
    REST_API_KEY = ""
    REDIRECT_URI = "http://127.0.0.1:8000/auth"
    url = f"https://kauth.kakao.com/oauth/authorize?client_id={REST_API_KEY}&response_type=code&redirect_uri={REDIRECT_URI}"
    response = RedirectResponse(url)
    return response
@app.post("/users/kakao_code")
def get_kakao_code(code: utils.KakaoCode):
    print(code)
    return {"message": "success"}

@app.post("/users/")
def create_user(user_data: utils.UserBaseModel, db: Session = Depends(get_db)):
    return base.user_create(db=db, user_data=user_data)

@app.get("/users")
def read_users(db: Session = Depends(get_db)):
    users = base.users_read(db)
    return users

@app.get("/users/{user_id}")
def read_user(user_id: int, db: Session = Depends(get_db)):
    user = base.user_read(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.delete("/users")
def delete_users(db: Session = Depends(get_db)):
    base.delete_all_users(db)
    return {"message": "All users deleted"}

@app.get("/users/{user_id}/bmr")
def read_user_bmr(user_id: int, db: Session = Depends(get_db)):
    user = base.user_read(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"bmr": calculate_bmr(user)}

@app.post("/users/{user_id}/diet-exercise-advice")
def get_answer_from_clova(user_id: int, user_input: utils.UserInput, db: Session = Depends(get_db)):
    executor = get_executor()
    user = base.user_read(db, user_id)
    bmr = calculate_bmr(user)

    result = get_diet_exercise_advice(executor, bmr, user_input.query)
    print(result)
    if result["error"]:
        print("error")
        raise HTTPException(status_code=404, detail="error has been occured")
    return result