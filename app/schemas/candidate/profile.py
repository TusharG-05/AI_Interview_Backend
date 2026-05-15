
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import date, datetime

class CandidateSignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserDetailBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    nationality: Optional[str] = None
    religion: Optional[str] = None
    marital_status: Optional[str] = None
    father_name: Optional[str] = None
    mother_name: Optional[str] = None
    guardian_name: Optional[str] = None
    guardian_relation: Optional[str] = None
    phone_number: Optional[str] = None
    alternate_phone: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    aadhar_number: Optional[str] = None
    pan_number: Optional[str] = None
    passport_number: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None

class CandidateDetailUpdate(UserDetailBase):
    full_name: Optional[str] = None

class CandidateProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    role: str
    details: Optional[UserDetailBase] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
