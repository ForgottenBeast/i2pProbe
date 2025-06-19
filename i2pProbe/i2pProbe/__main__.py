from .app import get_app, set_proxy_endpoint
from .config import load_config
import uvicorn
import argparse
from observlib import configure_telemetry


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-o",
        "--opentelemetry",
        action="store",
        help="opentelemetry server",
        dest="otel_server",
        default=None,
    )
    parser.add_argument(
        "-f",
        "--profiling",
        action="store",
        help="pyroscope server address for profiling",
        dest="pyroscope_server",
        default=None,
    )
    parser.add_argument(
        "-b",
        "--bind-addr",
        action="store",
        help="host:port to run the app on",
        dest="bind_addr",
        default="127.0.0.1:9734",
    )

    parser.add_argument(
        "-c",
        "--config",
        action="store",
        help="config file",
        dest="config",
    )

    parser.add_argument(
        "-e",
        "--endpoints",
        action="store",
        help="eepsites to check",
        nargs="+",
        dest="endpoints",
    )

    parser.add_argument(
        "-p",
        "--i2p-proxy",
        action="store",
        dest="proxy",
        default="http://127.0.0.1:4444",
    )

    args = parser.parse_args()

    sname = "i2pProbe"
    load_config(args.config)

    configure_telemetry(
        sname,
        args.otel_server,
        args.pyroscope_server,
        args.debug,
    )

    [host, port] = args.bind_addr.split(":")
    set_proxy_endpoint(args.proxy)

    app = get_app()
    uvicorn.run(app, host=host, port=int(port))
