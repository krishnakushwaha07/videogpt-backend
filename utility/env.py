from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config=SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    GEMINI_API_KEY : str
    HUGGINGFACEHUB_API_TOKEN : str
    GOOGLE_CLIENT_SECRET : str
    GOOGLE_CLIENT_ID : str
    SESSION_SECRET : str
    DB_URL : str
    ACCESS_SECRET_KEY : str
    ACCESS_TOKEN_HR : int
    ENCODING_ALGO : str
    FRONTEND_URL : str
    REDIRECT_URL : str



settings = Settings()

