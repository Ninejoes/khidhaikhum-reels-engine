#!/usr/bin/env python3
"""Think for Value (คิดให้คุ้ม) - All-in-One Automated Video Reel Engine.

Modes:
  1. explainer (Default): Whiteboard Doodly Financial Explainer (matching reference #4742958775935653)
  2. news: Fast 30s breaking news Reel with editorial photos and motion graphics

Usage:
  python main.py                              # Render Whiteboard Explainer to outputs/whiteboard-explainer.mp4
  python main.py --mode news                  # Render 30s News Reel to outputs/latest-reel.mp4
  python main.py --topic "รีไฟแนนซ์บ้าน"        # Custom topic for explainer
  python main.py --publish                    # Render and publish to Facebook Reels
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from engine.pipeline import run_explainer_pipeline, run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Think for Value Automated Video Reel Engine")
    parser.add_argument(
        "--mode",
        choices=["explainer", "news"],
        default="explainer",
        help="Engine mode: 'explainer' (Whiteboard Doodly 2min) or 'news' (Breaking News 35s)",
    )
    parser.add_argument(
        "--topic",
        type=str,
        default=None,
        help="Optional topic prompt for explainer (e.g. 'รีไฟแนนซ์บ้าน')",
    )
    parser.add_argument(
        "--item-id",
        type=str,
        default=None,
        help="Explicit Newsroom D1 item ID to render and publish",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Target output MP4 file path",
    )
    parser.add_argument(
        "--publish",
        action="store_true",
        help="Publish the generated video Reel to Facebook Page",
    )
    args = parser.parse_args()

    if args.item_id:
        args.item_id = args.item_id.strip('"\'').strip()
    if args.topic:
        args.topic = args.topic.strip('"\'').strip()

    if args.mode == "explainer":
        target_out = args.output or Path("outputs/whiteboard-explainer.mp4")
        result = run_explainer_pipeline(
            topic_prompt=args.topic,
            output_path=target_out,
            publish=args.publish,
            item_id=args.item_id,
        )
    else:
        target_out = args.output or Path("outputs/latest-reel.mp4")
        result = run_pipeline(
            output_path=target_out,
            publish=args.publish,
        )

    print("=" * 60)
    print(f"[{args.mode.upper()} REEL AUTOMATION COMPLETE]")
    print(f"Title: {result['title']}")
    print(f"File: {result['video_path']} ({int(result['video_size']):,} bytes)")
    if "duration" in result:
        print(f"Duration: {result['duration']}")
    print(f"Publish Status: {result['publish_url']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
