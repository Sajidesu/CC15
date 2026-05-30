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
    firstName: str
    lastName: str
    email: EmailStr
    phoneNumber: str
    dateOfBirth: date
    department: str
    category: str 
    role: str 
    password: Optional[str] = None

class ClockAction(BaseModel):
    specialId: str
