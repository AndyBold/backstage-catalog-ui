#!/usr/bin/env python3

from app import create_app

from app import create_app
import argparse


def main():
    # Command line arguments
    parser = argparse.ArgumentParser(description="Run the Catalog Manager application")
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host to run the application on"
    )
    parser.add_argument(
        "--port", type=int, default=8001, help="Port to run the application on"
    )
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")

    args = parser.parse_args()

    # Create and run app
    app = create_app()
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
