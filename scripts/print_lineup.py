
import argparse
import lineup


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prints a lineup")
    parser.add_argument(
        "--lineup-file", dest="lu_file", type=str,
        default="lineups/latest.json",
        help="File path to print the team")
    args = parser.parse_args()
    lu = lineup.Lineup(args.lu_file).connect()
    print lu
