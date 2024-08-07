from pydantic.v1 import BaseSettings


class Settings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DATABASE_URL: str

    class Config:
        env_file = ".env"


settings = Settings()