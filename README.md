# YTBulk Downloader

Bulk YouTube downloader built on [yt-dlp](https://github.com/yt-dlp/yt-dlp).

## Setup
```bash
git clone <repo-url> && cd YTBulkDownloader
./setup.sh          # creates .venv and installs/updates yt-dlp (needs ffmpeg)
```
Re-run `./setup.sh` whenever downloads start failing; YouTube changes often and yt-dlp updates fix it.

## Usage

### A whole channel
```bash
./ytbulk channel https://www.youtube.com/@SomeChannel            # all uploaded videos
./ytbulk channel @SomeChannel --type streams                       # past live streams
./ytbulk channel @SomeChannel --type shorts
./ytbulk channel @SomeChannel --type all                           # videos + streams + shorts
./ytbulk channel @SomeChannel --limit 10 -q 720                    # 10 newest, max 720p
./ytbulk channel @SomeChannel --after 2025-01-01
```
Saved to `downloads/<Channel>/<videos|streams|shorts>/YYYY-MM-DD - Title [id].mp4`

### A list of videos
Put URLs in a text file (one per line, `#` for comments; see `urls.example.txt`):
```bash
./ytbulk list myvideos.txt                      # -> downloads/myvideos/
./ytbulk list myvideos.txt -o ~/Videos/Course   # custom folder
```

### Individual URLs / playlists / live streams
```bash
./ytbulk url https://youtu.be/AAA https://youtu.be/BBB
./ytbulk url https://www.youtube.com/watch?v=LIVE_ID --live   # record a live stream from its start
```

## Options (all commands)
| Option | Meaning |
|---|---|
| `-o DIR` | output folder |
| `-q best\|1080\|720\|480` | max video quality (default best) |
| `-a` | audio only (mp3) |
| `--subs` | download & embed English subtitles |
| `--thumbnail` | save thumbnails |
| `--live` | record live streams from the beginning; wait for upcoming ones |
| `--limit N` | only the N newest items (per channel tab) |
| `--after YYYY-MM-DD` | only items uploaded on/after date |
| `--browser-cookies firefox` / `--cookies cookies.txt` | for members-only / age-restricted videos |
| `--no-archive` | re-download things already downloaded |

## Resuming
Every finished video ID is recorded in `downloaded.txt`. Re-running the same command
skips what you already have, so you can stop with Ctrl+C anytime and resume later, or
re-run a channel periodically to fetch only new uploads.

## Git notes
`.gitignore` keeps `downloads/`, `.venv/`, `downloaded.txt`, cookies and your own `*.txt`
URL lists out of the repo. Only `urls.example.txt` and `requirements.txt` are tracked.
