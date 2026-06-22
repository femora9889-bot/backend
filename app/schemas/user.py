from pydantic import BaseModel, field_validator


class UserRegister(BaseModel):
    name: str
    phone: str
    password: str

    @field_validator("phone")
    @classmethod
    def phone_must_be_valid(cls, v: str) -> str:
        digits = v.replace("+", "").replace(" ", "")
        if not digits.isdigit() or len(digits) < 9:
            raise ValueError("Invalid phone number")
        return v

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserLogin(BaseModel):
    phone: str
    password: str


class UserResponse(BaseModel):
    id: str
    name: str
    phone: str
    profile_image: str | None
    role: str

    model_config = {"from_attributes": True}


class UserProfileUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None


class MeasurementsCreate(BaseModel):
    height_cm: float
    weight_kg: float
    bust_cm: float | None = None
    waist_cm: float | None = None
    hips_cm: float | None = None
    shoulder_cm: float | None = None
    upper_arm_cm: float | None = None
    thigh_cm: float | None = None
    calf_cm: float | None = None
    torso_length_cm: float | None = None
    skin_tone: str | None = None
    hair_color: str | None = None


class MeasurementsResponse(BaseModel):
    height_cm: float
    weight_kg: float
    body_shape: str | None
    secondary_shape: str | None
    bust_cm: float | None
    waist_cm: float | None
    hips_cm: float | None
    shoulder_cm: float | None
    upper_arm_cm: float | None
    thigh_cm: float | None
    calf_cm: float | None
    torso_length_cm: float | None
    torso_type: str | None = None
    skin_tone: str | None
    hair_color: str | None
    avatar_url: str | None

    model_config = {"from_attributes": True}
