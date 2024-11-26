from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

    API_ID: int
    API_HASH: str


    REF_LINK: str = ""

    AUTO_TASK: bool = True
    AUTO_CONNECT_WALLET: bool = True
    AUTO_JOIN_CHANNEL: bool = False
    AUTO_GAME: bool = True

    GAMES_TO_PLAY: list[str] = ["stack"]

    DELAY_EACH_ACCOUNT: list[int] = [20, 30] # seconds
    SLEEP_TIME_BETWEEN_EACH_ROUND: list[int] = [2, 3] # hours
    ADVANCED_ANTI_DETECTION: bool = True

    USE_PROXY_FROM_FILE: bool = False


settings = Settings()

