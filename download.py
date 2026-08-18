import argparse
import sys

from vidking import VidkingPipeline


def main():
    parser = argparse.ArgumentParser(description="Download one or more Vidking TV episodes.")
    parser.add_argument("series_id")
    parser.add_argument("season")
    parser.add_argument("episode", type=int)
    parser.add_argument(
        "--end-episode", type=int, default=None,
        help="Download all episodes from episode through this one, inclusive.",
    )
    args = parser.parse_args()

    end_episode = args.end_episode if args.end_episode is not None else args.episode
    if end_episode < args.episode:
        parser.error("--end-episode must be >= episode")

    all_success = True
    for episode in range(args.episode, end_episode + 1):
        print(f"[*] {args.series_id} S{args.season}E{episode}")
        pipeline = VidkingPipeline(args.series_id, args.season, episode)
        success = pipeline.download()
        print("SUCCESS" if success else "FAIL")
        all_success = all_success and success

    sys.exit(0 if all_success else 1)


if __name__ == "__main__":
    main()
