import argparse
import sys

from vidking import VidkingPipeline


def main():
    parser = argparse.ArgumentParser(description="Download a Vidking TV episode.")
    parser.add_argument("series_id")
    parser.add_argument("season")
    parser.add_argument("episode")
    args = parser.parse_args()

    pipeline = VidkingPipeline(args.series_id, args.season, args.episode)
    success = pipeline.download()

    print("SUCCESS" if success else "FAIL")
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
