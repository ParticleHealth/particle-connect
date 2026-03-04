from pydantic_settings import BaseSettings

ENVIRONMENTS = {
    "sandbox": {
        "auth_url": "https://sandbox.particlehealth.com",
        "base_url": "https://management.sandbox.particlehealth.com",
    },
    "production": {
        "auth_url": "https://api.particlehealth.com",
        "base_url": "https://management.particlehealth.com",
    },
}


class Settings(BaseSettings):
    particle_client_id: str = ""
    particle_client_secret: str = ""
    particle_env: str = "sandbox"
    particle_timeout: int = 30
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def particle_auth_url(self) -> str:
        return ENVIRONMENTS[self.particle_env]["auth_url"]

    @property
    def particle_base_url(self) -> str:
        return ENVIRONMENTS[self.particle_env]["base_url"]


settings = Settings()
