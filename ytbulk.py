#!/usr/bin/env python3
"""YTBulk - bulk YouTube downloader built on yt-dlp.

Examples:
  ./ytbulk channel https://www.youtube.com/@SomeChannel
  ./ytbulk channel https://www.youtube.com/@SomeChannel --type streams
  ./ytbulk channel @SomeChannel --type all --limit 20
  ./ytbulk list urls.txt -o downloads/my-list
  ./ytbulk url https://youtu.be/xxxx https://youtu.be/yyyy
"""
import argparse
import re
import sys
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    sys.exit("yt-dlp is not installed. Run ./setup.sh first.")

ROOT = Path(__file__).resolve().parent
DEFAULT_OUT = ROOT / "downloads"
ARCHIVE = ROOT / "downloaded.txt"  # remembers finished videos so reruns skip them

CHANNEL_TABS = {
    "videos": ["videos"],
    "streams": ["streams"],
    "shorts": ["shorts"],
    "all": ["videos", "streams", "shorts"],
}

QUALITY = {
    "best": "bv*+ba/b",
    "1080": "bv*[height<=1080]+ba/b[height<=1080]",
    "720": "bv*[height<=720]+ba/b[height<=720]",
    "480": "bv*[height<=480]+ba/b[height<=480]",
}


def normalize_channel(url: str) -> str:
    """Accept '@handle', a channel URL, or a URL ending in a tab; return base channel URL."""
    url = url.strip()
    if url.startswith("@"):
        url = f"https://www.youtube.com/{url}"
    elif not url.startswith("http"):
        url = f"https://www.youtube.com/@{url}"
    url = url.split("?")[0].rstrip("/")
    return re.sub(r"/(videos|streams|shorts|featured|live|playlists|community)$", "", url)


def build_opts(args, outtmpl: str) -> dict:
    opts = {
        "outtmpl": outtmpl,
        "ignoreerrors": True,          # skip private/removed videos instead of aborting
        "retries": 10,
        "fragment_retries": 10,
        "concurrent_fragment_downloads": 4,
        "windowsfilenames": True,
        "noplaylist": False,
    }
    if not args.no_archive:
        opts["download_archive"] = str(ARCHIVE)

    if args.audio:
        opts["format"] = "ba/b"
        opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]
    else:
        opts["format"] = QUALITY[args.quality]
        opts["merge_output_format"] = "mp4"

    if args.subs:
        opts.update(writesubtitles=True, writeautomaticsub=True,
                    subtitleslangs=["en.*"], postprocessors=opts.get("postprocessors", []) +
                    [{"key": "FFmpegEmbedSubtitle"}])
    if args.thumbnail:
        opts["writethumbnail"] = True
    if args.limit:
        opts["playlistend"] = args.limit
    if args.after:
        opts["daterange"] = yt_dlp.utils.DateRange(start=args.after.replace("-", ""))
    if args.live:
        opts["live_from_start"] = True     # grab a currently-running stream from its beginning
        opts["wait_for_video"] = (30, 600)  # wait for scheduled/upcoming streams
    if args.cookies:
        opts["cookiefile"] = args.cookies
    if args.browser_cookies:
        opts["cookiesfrombrowser"] = (args.browser_cookies,)
    return opts


def run(urls, opts) -> int:
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.download(urls)


def cmd_channel(args):
    base = normalize_channel(args.channel)
    out = Path(args.output) if args.output else DEFAULT_OUT
    # Layout: downloads/<Channel>/<tab>/<YYYY-MM-DD - title [id]>.ext
    code = 0
    for tab in CHANNEL_TABS[args.type]:
        url = f"{base}/{tab}"
        print(f"\n==> {url}")
        tmpl = str(out / "%(channel)s" / tab /
                   "%(upload_date>%Y-%m-%d)s - %(title).150B [%(id)s].%(ext)s")
        code |= run([url], build_opts(args, tmpl)) or 0
    return code


def read_url_file(path: str):
    urls = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            urls.append(line.split()[0])
    return urls


def cmd_list(args):
    urls = read_url_file(args.file)
    if not urls:
        sys.exit(f"No URLs found in {args.file}")
    out = Path(args.output) if args.output else DEFAULT_OUT / Path(args.file).stem
    print(f"{len(urls)} URL(s) -> {out}")
    tmpl = str(out / "%(title).150B [%(id)s].%(ext)s")
    return run(urls, build_opts(args, tmpl))


def cmd_url(args):
    out = Path(args.output) if args.output else DEFAULT_OUT / "singles"
    tmpl = str(out / "%(title).150B [%(id)s].%(ext)s")
    return run(args.urls, build_opts(args, tmpl))


def add_common(p):
    p.add_argument("-o", "--output", help="output folder (default: ./downloads/...)")
    p.add_argument("-q", "--quality", choices=QUALITY, default="best", help="max video quality")
    p.add_argument("-a", "--audio", action="store_true", help="audio only (mp3)")
    p.add_argument("--subs", action="store_true", help="download & embed English subtitles")
    p.add_argument("--thumbnail", action="store_true", help="also save thumbnails")
    p.add_argument("--live", action="store_true",
                   help="record live streams from the start / wait for upcoming ones")
    p.add_argument("--no-archive", action="store_true",
                   help="re-download even if already in downloaded.txt")
    p.add_argument("--cookies", help="cookies.txt file (for members-only/age-restricted)")
    p.add_argument("--browser-cookies", metavar="BROWSER",
                   help="read cookies from a browser, e.g. firefox or chrome")
    p.add_argument("--limit", type=int, help="only the N most recent items (per tab)")
    p.add_argument("--after", metavar="YYYY-MM-DD", help="only items uploaded on/after this date")


def main():
    ap = argparse.ArgumentParser(prog="ytbulk", description="Bulk YouTube downloader (yt-dlp)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    pc = sub.add_parser("channel", help="download a channel's videos / streams / shorts")
    pc.add_argument("channel", help="channel URL or @handle")
    pc.add_argument("-t", "--type", choices=CHANNEL_TABS, default="videos",
                    help="what to download (default: videos)")
    add_common(pc)
    pc.set_defaults(func=cmd_channel)

    pl = sub.add_parser("list", help="download every URL in a text file (one per line)")
    pl.add_argument("file", help="text file with video/playlist URLs")
    add_common(pl)
    pl.set_defaults(func=cmd_list)

    pu = sub.add_parser("url", help="download one or more URLs (video, playlist, or live)")
    pu.add_argument("urls", nargs="+")
    add_common(pu)
    pu.set_defaults(func=cmd_url)

    args = ap.parse_args()
    try:
        sys.exit(1 if args.func(args) else 0)
    except KeyboardInterrupt:
        sys.exit("\nInterrupted. Re-run the same command to resume.")


if __name__ == "__main__":
    main()
