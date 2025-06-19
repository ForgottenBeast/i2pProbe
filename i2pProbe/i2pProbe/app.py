import asyncio
import aiohttp
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from observlib import traced
from fastapi import FastAPI, Response
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from functools import lru_cache
from logging import getLogger
from .config import get_config
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
from opentelemetry.metrics import get_meter

AioHttpClientInstrumentor().instrument()

logger = getLogger(__name__)

service_name = "i2pProbe"
proxy_endpoint = "http://127.0.0.1:4444"
scrape_interval_seconds = 30


app = FastAPI()


def set_proxy_endpoint(val):
    global proxy_endpoint
    proxy_endpoint = val


@lru_cache(maxsize=None)
def get_counter(counter_data):
    return get_meter(service_name).create_counter(**dict(counter_data))


traced_conf = {
    "counter": "polling_events",
    "counter_factory": get_counter,
    "tracer": service_name,
}


async def collect_data(config):
    session = aiohttp.ClientSession(proxy = proxy_endpoint)

    while True:
        tasks = []
        for site in config["eepsites"]:
            tasks.append(session.get(f"http://{site}"))
        await asyncio.gather(*tasks)
        asyncio.sleep(scrape_interval_seconds)


def get_app():
    global app
    return app


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(collect_data(get_config()))


@app.get("/metrics")
@traced(**traced_conf)
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


FastAPIInstrumentor().instrument_app(app)
