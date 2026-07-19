import argparse

VERSION = "0.2.0"

def main():
    parser = argparse.ArgumentParser(
        prog="flux",
        description="Flux Agents - AI Native Agentic Framework"
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"Flux Agents {VERSION}"
    )

    parser.parse_args()

if __name__ == "__main__":
    main()