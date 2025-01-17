import logging

from pydantic import BaseModel, field_validator
from typing import List
from pathlib import Path
import yaml
import os

class CoinBaseConfig(BaseModel):
    pricing_url: str
    supported_ccy: List


class CacheConfig(BaseModel):
    refresh_time: int


class Log(BaseModel):
    format: str
    level: str

    @field_validator('level')
    @classmethod
    def transform_level(cls, level: str):
        return {'INFO': logging.INFO,
                'DEBUG': logging.DEBUG,
                'ERROR': logging.ERROR,
                'WARNING': logging.WARNING
                }.get(level, logging.INFO)



class Config(BaseModel):
    coinbase: CoinBaseConfig
    cache: CacheConfig
    log: Log


def _load_yml_config(path: Path):
    try:
        return yaml.safe_load(path.read_text())
    except FileNotFoundError as error:
        message = "Error: yml config file not found."
        raise FileNotFoundError(error, message) from error


deploy_env = os.getenv('DEPLOY_ENV', 'dev')

config_file = Path(__file__).parent.parent/Path(f'configs/{deploy_env}.yaml')
Settings = Config(**_load_yml_config(config_file))

if __name__ == '__main__':
    print(Settings.cache, Settings.coinbase)
