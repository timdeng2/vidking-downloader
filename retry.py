import argparse
import sys

from vidking import VidkingPipeline


def main():
    parser = argparse.ArgumentParser(description="Retry missing segments for a Vidking TV episode.")
    parser.add_argument("series_id")
    parser.add_argument("season")
    parser.add_argument("episode")
    parser.add_argument("--max-attempts", type=int, default=5)
                        
    args = parser.parse_args()

    pipeline = VidkingPipeline(args.series_id, args.season, args.episode, args.max_attempts)
    success = pipeline.retry()

    print("SUCCESS" if success else "FAIL")
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
