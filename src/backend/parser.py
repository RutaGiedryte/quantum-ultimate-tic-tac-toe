import argparse


def create_parser(prog: str):
    """Create command line argument parser.

    Args:
        prog: program name

    Returns:
        parser
    """

    parser = argparse.ArgumentParser(prog)

    parser.add_argument(
        "-u", "--ultimate", action="store_true", help="play ultimate version"
    )
    parser.add_argument(
        "-s", "--simulate", action="store_true", help="simulate locally"
    )

    return parser
