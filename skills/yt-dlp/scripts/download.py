#!/usr/bin/env python3
"""Download media through yt-dlp with explicit, reviewable defaults."""

from __future__ import annotations

import argparse
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Sequence


DEFAULT_OUTPUT_DIR = "~/Downloads/yt-dlp"
OUTPUT_TEMPLATE = "%(title).160B [%(id)s].%(ext)s"
DEFAULT_SUBTITLE_LANGS = "zh.*,en.*"


def positive_int(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download video, audio, subtitles, or metadata with yt-dlp.",
    )
    parser.add_argument("url", help="video or playlist URL")
    parser.add_argument(
        "-o",
        "--output",
        default=DEFAULT_OUTPUT_DIR,
        help=f"output directory (default: {DEFAULT_OUTPUT_DIR})",
    )

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "-F",
        "--list-formats",
        action="store_true",
        help="list formats without downloading",
    )
    mode.add_argument(
        "--info",
        action="store_true",
        help="print JSON metadata without downloading",
    )
    mode.add_argument(
        "-a",
        "--audio",
        action="store_true",
        help="extract audio as MP3",
    )

    parser.add_argument(
        "-m",
        "--max-height",
        type=positive_int,
        metavar="PIXELS",
        help="maximum video height, for example 1080 or 720",
    )
    parser.add_argument(
        "-s",
        "--subtitles",
        action="store_true",
        help="download manual and automatic subtitles",
    )
    parser.add_argument(
        "--sub-langs",
        default=DEFAULT_SUBTITLE_LANGS,
        help=f"subtitle languages (default: {DEFAULT_SUBTITLE_LANGS})",
    )
    parser.add_argument(
        "--cookies",
        metavar="BROWSER",
        help="read cookies from BROWSER only when explicitly authorized",
    )
    parser.add_argument(
        "--playlist",
        action="store_true",
        help="allow downloading a complete playlist",
    )
    parser.add_argument(
        "--playlist-items",
        metavar="ITEMS",
        help="playlist item range, for example 1:10; requires --playlist",
    )
    return parser


def build_command(args: argparse.Namespace) -> list[str]:
    command = ["yt-dlp"]

    if args.cookies:
        command.extend(["--cookies-from-browser", args.cookies])

    if args.list_formats:
        command.extend(["-F", args.url])
        return command

    if args.info:
        command.extend(["--skip-download", "--dump-single-json", args.url])
        return command

    output_dir = Path(args.output).expanduser().resolve()
    command.extend(
        [
            "--newline",
            "--no-overwrites",
            "--paths",
            str(output_dir),
            "--output",
            OUTPUT_TEMPLATE,
        ]
    )

    if not args.playlist:
        command.append("--no-playlist")
    elif args.playlist_items:
        command.extend(["--playlist-items", args.playlist_items])

    if args.audio:
        command.extend(
            [
                "--format",
                "bestaudio/best",
                "--extract-audio",
                "--audio-format",
                "mp3",
                "--audio-quality",
                "0",
            ]
        )
    elif args.max_height:
        command.extend(
            [
                "--format",
                (
                    f"bv*[height<={args.max_height}]+ba/"
                    f"b[height<={args.max_height}]"
                ),
            ]
        )
    else:
        command.extend(["--format", "bv*+ba/b"])

    if args.subtitles:
        command.extend(
            [
                "--write-subs",
                "--write-auto-subs",
                "--sub-langs",
                args.sub_langs,
            ]
        )

    command.append(args.url)
    return command


def validate_args(
    parser: argparse.ArgumentParser, args: argparse.Namespace
) -> None:
    if args.audio and args.max_height:
        parser.error("--audio cannot be combined with --max-height")
    if args.playlist_items and not args.playlist:
        parser.error("--playlist-items requires --playlist")


def requires_ffmpeg(args: argparse.Namespace) -> bool:
    return not (args.list_formats or args.info)


def run(command: Sequence[str], needs_ffmpeg: bool) -> int:
    if shutil.which("yt-dlp") is None:
        print(
            "错误：未找到 yt-dlp。请先安装并确认 `yt-dlp --version` 可用。",
            file=sys.stderr,
        )
        return 127

    if needs_ffmpeg and shutil.which("ffmpeg") is None:
        print(
            "错误：未找到 ffmpeg。音视频合并和音频提取需要 ffmpeg。",
            file=sys.stderr,
        )
        return 127

    print(f"$ {shlex.join(command)}", file=sys.stderr)
    try:
        return subprocess.run(command, check=False).returncode
    except FileNotFoundError:
        print("错误：无法启动 yt-dlp。", file=sys.stderr)
        return 127
    except KeyboardInterrupt:
        print("\n下载已中断。", file=sys.stderr)
        return 130


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    validate_args(parser, args)

    if not (args.list_formats or args.info):
        output_dir = Path(args.output).expanduser()
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            print(f"错误：无法创建输出目录 {output_dir}: {exc}", file=sys.stderr)
            return 1

    return run(build_command(args), requires_ffmpeg(args))


if __name__ == "__main__":
    sys.exit(main())
