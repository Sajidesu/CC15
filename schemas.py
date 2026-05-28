from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date

class EmployeeLogin(BaseModel):
    firstName: str
    specialId: str

class AdminLogin(BaseModel):
    firstName: str
    specialId: str
    password: str

class UserSignUp(BaseModel):
    specialId: str
    firstName: str
    lastName: str
    email: EmailStr
    department: str
    category: str # "Full-Time" or "Part-Time"
    role: str # "employee" or "admin"
    password: Optional[str] = None

class ClockAction(BaseModel):
    specialId: str