import time
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
from opentelemetry import trace
from opentelemetry.metrics import get_meter

AioHttpClientInstrumentor().instrument()

logger = getLogger(__name__)

service_name = "i2pProbe"
proxy_endpoint = "http://127.0.0.1:4444"
scrape_interval_seconds = 30


last_latency = get_meter(service_name).create_gauge(
    name="i2pprobe_last_latency", unit="ms"
)
up_gauge = get_meter(service_name).create_gauge(name="i2pprobe_eepsite_up")

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

@traced(tracer  = service_name)
async def ping_site(session, sitename):
    start = time.perf_counter()
    attrs = {"eepsite": sitename}
    async with session.get(f"http://{sitename}/") as resp:
        last_latency.set(time.perf_counter() - start, attributes=attrs)
        status_family = resp.status // 100
        if status_family == 2:
            up_gauge.set(1, attributes=attrs)
        else:
            up_gauge.set(0, attributes=attrs | {"status": f"{status_family}xx"})


async def collect_data(config):
    session = aiohttp.ClientSession(proxy=proxy_endpoint)

    while True:
        with trace.get_tracer(service_name).start_as_current_span(__name__):
            tasks = []
            for site in config["eepsites"]:
                tasks.append(ping_site(session, site))
            await asyncio.gather(*tasks)
            await asyncio.sleep(scrape_interval_seconds)


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
