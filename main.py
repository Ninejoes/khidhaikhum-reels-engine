#!/usr/bin/env python3
"""Think for Value (คิดให้คุ้ม) - All-in-One Automated News Reel Engine.

Usage:
  python main.py                  # Render latest news Reel to outputs/latest-reel.mp4
  python main.py --publish        # Render and publish to Facebook Reels
  python main.py --output out.mp4 # Specify custom output file
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from engine.pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Think for Value Automated News Reel Engine")
    parser.add_argument("--output", "-o", type=Path, default=Path("outputs/latest-reel.mp4"), help="Target output MP4 file path")
    parser.add_argument("--publish", action="store_true", help="Publish the generated video Reel to Facebook")
    args = parser.parse_args()

    result = run_pipeline(output_path=args.output, publish=args.publish)
    print("=" * 60)
    print("REEL AUTOMATION COMPLETE")
    print(f"Title: {result['title']}")
    print(f"File: {result['video_path']} ({int(result['video_size']):,} bytes)")
    print(f"Publish Status: {result['publish_url']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
