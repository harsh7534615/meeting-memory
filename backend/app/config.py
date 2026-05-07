from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/auth/callback"

    # Gemini AI
    gemini_api_key: str = ""

    # Pinecone
    pinecone_api_key: str = ""
    pinecone_index_name: str = "meeting-memory"
    pinecone_environment: str = ""

    # Supabase / Postgres
    supabase_url: str = ""
    supabase_service_key: str = ""

    # Resend email
    resend_api_key: str = ""

    # Webhook
    webhook_base_url: str = "http://localhost:8000"

    class Config:
        env_file = ".env"


settings = Settings()
