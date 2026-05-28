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
    particle_sandbox_client_id: str = ""
    particle_sandbox_client_secret: str = ""
    particle_prod_client_id: str = ""
    particle_prod_client_secret: str = ""
    particle_env: str = "sandbox"
    particle_timeout: int = 30
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    def credentials_for(self, env: str) -> tuple[str, str]:
        if env == "production":
            return self.particle_prod_client_id, self.particle_prod_client_secret
        return self.particle_sandbox_client_id, self.particle_sandbox_client_secret

    @property
    def particle_auth_url(self) -> str:
        return ENVIRONMENTS[self.particle_env]["auth_url"]

    @property
    def particle_base_url(self) -> str:
        return ENVIRONMENTS[self.particle_env]["base_url"]


settings = Settings()
