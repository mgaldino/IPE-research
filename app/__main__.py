import argparse

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the IPE Breakthrough Idea Swarm server.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", default=8001, type=int, help="Bind port (default: 8001)")
    args = parser.parse_args()
    uvicorn.run("app.main:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
