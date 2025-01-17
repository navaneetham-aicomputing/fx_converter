## FX Converter

A FastAPI-based currency conversion rest api. This project implements local caching for better performance by avoid going to CoinBase service for every user request.
As per the document CoinBase FX data is changing once an hour.  

### Features
	• Convert amounts between supported currencies using up-to-date FX rates.
	• Fetches FX rates from Coinbase (or other configurable sources).
	• Utilizes a local cache to reduce external API calls and improve performance. 
	• Caching feature is designed with a mind to extend to global caching using redis or other off the self caching services if needed 	
	• Designed with FastAPI and implemented using async feature easy integration and scalability. 
	• Configurable logging to track operations and troubleshoot issues.

### Caveats
	• Cached FX rates are retained for an hour, which may cause discrepancies if the source updates rates before the cache expires.
	• Worstcase user will not get updated currency converted data for about ~1hr if cache refresh time set to 1hr 

### Requirements
	• Python: 3.8 or higher
	• Poetry: For dependency and environment management.

### Getting Started
#### 1. Clone the Repository
```
git clone https://github.com/navaneetham-aicomputing/fx_converter.git
cd fx_converter
```

#### 2.	Install Dependencies
Use Poetry to install project dependencies:
```
poetry install
```

#### 3.	Activate the Virtual Environment
```
poetry shell
export PYTHONPATH=./src
```

#### 4.	Run the Application
Start the FastAPI server:
```
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 5.	Access the API
```
curl "http://127.0.0.1:8000/v1/convert?ccy_from=USD&ccy_to=EUR&quantity=100"
```

#### 6. Run tests
```
poetry run pytest -v
```

#### 7. Build docker image
Docker image for development environment
```
docker build -t fx_convert_dev -f dockers/Dockerfile .
```

Docker image for production environment
```
docker build -t fx_convert_prod -f dockers/Dockerfile .
```

#### 8. Run docker image
Run docker for development environment
```
docker run -d -p 8000:8000 fx_convert_dev
```

Run docker for production environment
```
docker run -d -p 80:80 fx_convert_prod
```
