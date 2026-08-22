#!/usr/bin/env python3
"""Assemble the deployable site and stamp it with the commit it came from.

There is no build step to speak of - the working tree is the site - so this
copies the files the site actually needs into a clean directory and stamps two
things into them:

  * the credits line in index.html, so a phone in a field can be asked which
    version it is running, which is otherwise unanswerable once the app is
    cached and there is no signal;
  * the service worker's cache version, so every deploy retires the previous
    shell instead of relying on someone remembering to bump it by hand.

Nothing here is imported by the app or the tests, and it needs no third-party
packages. Every setting can be given as an option, an environment variable, or
left to its default:

    --out    NPMS_BUILD_OUT    where to write the site      (_site)
    --rev    NPMS_BUILD_REV    commit to stamp              (short git HEAD)
    --time   NPMS_BUILD_TIME   build time, ISO 8601         (now, UTC)
"""
import argparse
import datetime
import os
import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# What the site is made of. Everything else in the repo - tests, tools, notes,
# the archived species work - stays behind.
SITE_FILES = ["index.html", "app.js", "geo.js", "sw.js", "manifest.webmanifest",
              "robots.txt", "tl3443_overlay.png"]
SITE_DIRS = ["icons", "vendor"]

# Written into a directory this script has built, so that rebuilding can clear
# it without ever clearing a directory it was pointed at by mistake.
MARKER = ".npms-site"


def git_rev():
    """The commit being built, marked dirty if the tree does not match it."""
    def git(*args):
        return subprocess.run(["git", "-C", str(ROOT), *args],
                              capture_output=True, text=True, check=True).stdout.strip()
    try:
        rev = git("rev-parse", "--short", "HEAD")
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"
    try:
        if git("status", "--porcelain"):
            rev += "-dirty"
    except subprocess.CalledProcessError:
        pass
    return rev


def build_time(given):
    if not given:
        return datetime.datetime.now(datetime.timezone.utc)
    when = datetime.datetime.fromisoformat(given.replace("Z", "+00:00"))
    if when.tzinfo is None:
        when = when.replace(tzinfo=datetime.timezone.utc)
    return when.astimezone(datetime.timezone.utc)


def stamp_index(text, rev, when):
    """Put the build into the sources and licence section of the app itself."""
    line = ('<p id="build">Build <b>{rev}</b> &middot; {day} {rest} UTC</p>'
            .format(rev=rev, day=when.day, rest=when.strftime("%B %Y, %H:%M")))
    out, n = re.subn(r'<p id="build">.*?</p>', line, text, count=1, flags=re.S)
    if n != 1:
        sys.exit("index.html has no build line to stamp")
    return out


def stamp_sw(text, rev):
    """Name the shell cache after the commit, so a deploy retires the old one."""
    out, n = re.subn(r'const VERSION = "[^"]*";',
                     'const VERSION = "{}";'.format(rev), text, count=1)
    if n != 1:
        sys.exit("sw.js has no VERSION to stamp")
    return out


def clear(out):
    if not out.exists():
        return
    if not out.is_dir():
        sys.exit("{} is not a directory".format(out))
    if any(out.iterdir()) and not (out / MARKER).exists():
        sys.exit("{} is not empty and was not built by this script; "
                 "remove it first".format(out))
    shutil.rmtree(out)


def build(out, rev, when):
    clear(out)
    out.mkdir(parents=True)
    (out / MARKER).write_text("built from {} at {}\n".format(rev, when.isoformat()))
    for name in SITE_FILES:
        shutil.copy2(ROOT / name, out / name)
    for name in SITE_DIRS:
        shutil.copytree(ROOT / name, out / name)
    index = out / "index.html"
    index.write_text(stamp_index(index.read_text(), rev, when))
    sw = out / "sw.js"
    sw.write_text(stamp_sw(sw.read_text(), rev))
    return out


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--out", default=os.environ.get("NPMS_BUILD_OUT", "_site"),
                   help="directory to write the site into (default: _site)")
    p.add_argument("--rev", default=os.environ.get("NPMS_BUILD_REV"),
                   help="commit to stamp (default: the short git HEAD)")
    p.add_argument("--time", default=os.environ.get("NPMS_BUILD_TIME"),
                   help="build time as ISO 8601 (default: now, UTC)")
    args = p.parse_args(argv)

    rev = args.rev or git_rev()
    when = build_time(args.time)
    out = build(pathlib.Path(args.out).resolve(), rev, when)
    print("built {} from {} at {:%Y-%m-%d %H:%M} UTC".format(out, rev, when))


if __name__ == "__main__":
    main()
