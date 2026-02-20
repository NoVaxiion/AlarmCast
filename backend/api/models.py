from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# ==================== User Models ====================

class UserCreate(BaseModel):
    username: str
    password_hash: str
    password_algo: Optional[str] = "bcrypt"

class UserLogin(BaseModel):
    username: str
    password: str  # In production, this should be hashed client-side or use OAuth

class UserResponse(BaseModel):
    user_id: int
    username: str

    class Config:
        from_attributes = True

# ==================== Hub Models ====================

class HubCreate(BaseModel):
    hub_name: str

class HubResponse(BaseModel):
    hub_id: int
    hub_name: str

    class Config:
        from_attributes = True

# ==================== Member/Contact Models ====================

class MemberCreate(BaseModel):
    name: str
    phone: str
    role: Optional[str] = "member"
    user_id: Optional[int] = None

class MemberUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None

class MemberResponse(BaseModel):
    member_id: int
    hub_id: int
    name: Optional[str]
    phone: Optional[str]
    role: str
    user_id: Optional[int]

    class Config:
        from_attributes = True

# ==================== Device Models ====================

class DeviceCreate(BaseModel):
    is_active: Optional[int] = 1
    is_initialized: Optional[int] = 0

class DeviceResponse(BaseModel):
    device_id: int
    hub_id: int
    is_active: bool
    is_initialized: bool

    class Config:
        from_attributes = True

# ==================== Device Event Models ====================

class DeviceEventCreate(BaseModel):
    event_type: str  # 'SMOKE', 'CO', or 'TEST'

class DeviceEventResponse(BaseModel):
    device_event_id: int
    device_id: int
    event_type: str
    detected_at: str

    class Config:
        from_attributes = True

# ==================== Alert Models ====================

class AlertCreate(BaseModel):
    hub_id: int
    device_event_id: int
    status: Optional[str] = "pending"

class AlertResponse(BaseModel):
    alert_id: int
    hub_id: int
    device_event_id: int
    status: str

    class Config:
        from_attributes = True

class AlertHistoryResponse(BaseModel):
    alert_id: int
    hub_id: int
    device_event_id: int
    status: str
    event_type: str
    detected_at: str

    class Config:
        from_attributes = True

# ==================== Dashboard Models ====================

class MonitoringStatusResponse(BaseModel):
    is_monitoring: bool
    sound_level: int
    active_devices: int

class TestAlertRequest(BaseModel):
    message: Optional[str] = "Test alert"


