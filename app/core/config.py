from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Femora"
    DEBUG: bool = False
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    DATABASE_URL: str

    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str

    FIREBASE_CREDENTIALS_PATH: str = "firebase-credentials.json"

    GEMINI_API_KEY: str = ""
    HF_TOKEN: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
