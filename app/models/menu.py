from sqlalchemy import ForeignKey
from sqlalchemy import Column, Integer, String, Float, TIMESTAMP
from sqlalchemy.orm import relationship
from app.db.session import Base

class Menu(Base):
    __tablename__ = 'Menus'
    id = Column(Integer, primary_key=True, autoincrement=True, comment='Auto Increment')
    user_diet_plan_info_id = Column(Integer, ForeignKey('UserDietPlanInfo.id'), primary_key=True, comment='Auto Increment')
    name = Column(String(255))
    calories = Column(Float)
    meal_time = Column(String(255))
    created_at = Column(TIMESTAMP)