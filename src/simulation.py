from random import random
import numpy as np


async def fx_adjustment(symbol_fx_rate: tuple[str, float], no_sim: int = 1_000_000) -> (str, float):
    symbol, fx_rate = symbol_fx_rate
    return symbol, await _fx_adjustment(fx_rate, no_sim)


async def _fx_adjustment(fx_rate: float, no_sim:int = 1_000_000) -> float:
    adjustment = np.average([(random()*2 - 1)**99 for _ in range(no_sim)])
    return fx_rate + adjustment

