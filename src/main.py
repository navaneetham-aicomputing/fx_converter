import logging
from itertools import combinations
from fastapi import FastAPI, HTTPException
import httpx
from config import Settings
from typing import Dict
from cache import LocalCache
from aiomultiprocess import Pool
from simulation import fx_adjustment

logging.basicConfig(format=Settings.log.format)
logging.root.setLevel(Settings.log.level)


app = FastAPI(title="Currency Converter", description="Convert currencies using CoinDesk FX rates", version="1.0.0")
app.cache = LocalCache(refresh_time=Settings.cache.refresh_time)


async def adjust_fx(fx_rates: dict) -> Dict[str, float]:
    async with Pool() as pool:
        try:
            logging.info('Try adjust fx rate')
            fx_rates = await pool.map(fx_adjustment, list(fx_rates.items()))
            fx_rates = dict(fx_rates)
            logging.info(f'fx rate adjustment success. Adjusted value: {fx_rates}')
        except Exception as e:
            logging.error('Error while ding the adjustment', e)
            raise e

    return fx_rates


async def get_from_coinbase() -> Dict[str, float]:
    logging.info(f'Request to get pricing data from Coinbase using {Settings.coinbase.pricing_url}')
    async with httpx.AsyncClient() as aclient:
        response = await aclient.get(Settings.coinbase.pricing_url)
        if response.status_code != 200:
            msg = "Failed to fetch currency prices from CoinDesk"
            logging.error(msg)
            raise HTTPException(status_code=502, detail=msg)
        price_data = response.json()

    bpi: dict = price_data.get('bpi', {})
    fx_rate = {}
    for ccy1, ccy2 in combinations(bpi.keys(), 2):
        try:
            fx_rate[f'{ccy1}/{ccy2}'] = bpi.get(ccy2, {}).get('rate_float') / bpi.get(ccy1, {}).get('rate_float')
            fx_rate[f'{ccy2}/{ccy1}'] = bpi.get(ccy1, {}).get('rate_float') / bpi.get(ccy2, {}).get('rate_float')
        except Exception as e:
            msg = f'Either {ccy1} or {ccy2} data is not present or issues in Coinbase pricing data.'\
                  f'Further info, ccy1: {bpi.get(ccy1)} ccy2: {bpi.get(ccy2)}'
            logging.error(msg)
            raise HTTPException(status_code=404, detail=msg)

    ad_fx_rate: Dict[str, float] = await adjust_fx(fx_rate)

    return ad_fx_rate


def validate_ccy_convert_data(ccy_from: str, ccy_to: str, quantity: float):
    if ccy_to not in Settings.coinbase.supported_ccy or ccy_from not in Settings.coinbase.supported_ccy:
        msg = f'Either ccy_from {ccy_from} or ccy_to {ccy_to} is not supported or invalid'
        logging.error(msg)
        raise HTTPException(status_code=400, detail=msg)

    if quantity <= 0:
        msg = f'Quantity must be positive value, but given value is: {quantity}'
        logging.error(msg)
        raise HTTPException(status_code=400, detail=msg)


@app.get('/v1/convert', summary='Currency Converter')
async def ccy_convert(ccy_from: str, ccy_to: str, quantity: float):
    # Make sure api able to work even if currency is inputted in non-upper case
    ccy_from = ccy_from.upper()
    ccy_to = ccy_to.upper()

    validate_ccy_convert_data(ccy_from, ccy_to, quantity)

    if ccy_to == ccy_from:
        return {"quantity": quantity, "ccy": ccy_to}

    fx_rates: dict = await app.cache.get(get_from_coinbase)

    fx_pair = f'{ccy_from}/{ccy_to}'
    if fx_pair not in fx_rates:
        msg = f'Unable to find fx rate for {fx_pair}'
        logging.error(msg)
        raise HTTPException(status_code=404, detail=msg)

    rate = fx_rates[fx_pair]
    converted_quantity = quantity * rate

    return {"quantity": round(converted_quantity, 2), "ccy": ccy_to}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
