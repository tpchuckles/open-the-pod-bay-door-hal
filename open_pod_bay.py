#!/usr/bin/env python3

import shutil
import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import pyautogui

url_list = sys.argv[2:]
png_list = [ # tuple is click offset within the matched screenshot. None = center, else offset from top left corner
	("Pictures/Screenshot_20260910_094527.png", None),
	("Pictures/Screenshot_20260910_094539.png", (179, 51)),
	("Pictures/Screenshot_20260910_161221.png", None),
	("Pictures/Screenshot_20260910_162049.png", None),
	("Pictures/Screenshot_20260910_175820.png",None),
]
delay = 1
timeout = 5
entry_timeout = 30
chrome_name = "google-chrome"

# Capture the entire desktop and return it as an OpenCV image. ImageMagick is used because it reliably captures the active X11 display.
def screen():
	result = subprocess.run(["import", "-window", "root", "png:-"], capture_output=True, check=True)
	# Decode the PNG emitted on stdout without writing a temporary screenshot.
	return cv2.imdecode(np.frombuffer(result.stdout, np.uint8), cv2.IMREAD_COLOR)

# Crop references to compact interior features, excluding borders and long dividers.
# Preserve a small margin and translate explicit click offsets.
def autocrop(ref, point, pad=6):
	h, w = ref.shape[:2]
	edges = cv2.Canny(cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY), 40, 120)
	_, _, stats, _ = cv2.connectedComponentsWithStats(edges)
	regions = []
	for x, y, rw, rh, area in stats[1:]:
		inside = x > pad and y > pad and x + rw < w - pad and y + rh < h - pad
		compact = rw < .8 * w and rh < .8 * h
		if area >= 4 and inside and compact:
			regions.append((x, y, x + rw, y + rh))
	if not regions:
		return ref, point
	x0, y0 = max(0, min(r[0] for r in regions) - pad), max(0, min(r[1] for r in regions) - pad)
	x1, y1 = min(w, max(r[2] for r in regions) + pad), min(h, max(r[3] for r in regions) + pad)
	if point is not None:
		x0, y0, x1, y1 = min(x0, point[0]), min(y0, point[1]), max(x1, point[0] + 1), max(y1, point[1] + 1)
		point = point[0] - x0, point[1] - y0
	return ref[y0:y1, x0:x1], point

# Find a reference image within a screenshot and return its center or configured offset. Why not use pyautogui? not robust, crashes sometimes on linux
def locate(shot, ref, point=None, threshold=.72):
	# Normalized template matching returns comparable confidence scores from -1 to 1.
	result = cv2.matchTemplate(cv2.cvtColor(shot, cv2.COLOR_BGR2GRAY), cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY), cv2.TM_CCOEFF_NORMED)
	# minMaxLoc also returns the unused minimum score and its location.
	_, score, _, corner = cv2.minMaxLoc(result)
	if score < threshold:
		return None
	h, w = ref.shape[:2]
	if point is not None:
		return (corner[0] + point[0], corner[1] + point[1]), score, corner
	return (corner[0] + w // 2, corner[1] + h // 2), score, corner

# Poll the screen until one target is found, then click it. Return its index and position, or None when detection times out.
def click_first(targets, timeout):
	end = time.monotonic() + timeout
	err = None
	while time.monotonic() < end:
		try:
			shot = screen()
			for i, (ref, point) in enumerate(targets):
				match = locate(shot, ref, point)
				if match:
					pos, score, corner = match
					debug = Path(f"match_{time.time_ns()}_{i}.png")
					cv2.imwrite(str(debug), shot)  # Preserve the exact frame that passed the threshold.
					print(f" | diagnostic={debug} score={score:.6f} corner={corner}", end="", flush=True)
					pyautogui.click(*pos)  # Expand the (x, y) tuple into separate arguments.
					return i, pos
		except Exception as e:
			err = e
		time.sleep(.5)
	if err:
		print(f"  screen detection error: {err}")
	return None


def main():
	"""Try each base URL until its PDF is saved with the default name."""
	if not url_list:
		raise SystemExit(f"usage: {Path(sys.argv[0]).name} SUFFIX_FILE URL [URL ...]")
	suffix_file = Path(sys.argv[1])
	base_urls = [url.rstrip("/") for url in url_list]
	chrome = shutil.which(chrome_name)
	if chrome is None or shutil.which("import") is None:
		raise SystemExit("Chrome and ImageMagick's import command must both be installed")
	refs = [(cv2.imread(str(Path.home() / png)), point) for png, point in png_list]
	if any(ref is None for ref, _ in refs):
		raise SystemExit("reference screenshots were not found in ~/Pictures")
	refs = [autocrop(ref, point) for ref, point in refs]
	candidates = refs
	# Ignore blank lines and comment lines while preserving suffix order.
	suffixes = [line.strip() for line in suffix_file.read_text().splitlines() if line.strip() and not line.lstrip().startswith("#")]
	if not suffixes:
		raise SystemExit(f"no URL suffixes found in {suffix_file}")

	for suffix in suffixes:
		entry_end = time.monotonic() + entry_timeout
		expired = False
		for base in base_urls:
			url = f"{base}/{suffix.lstrip('/')}"
			print(url, end="", flush=True)
			subprocess.Popen([chrome, "--new-tab", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
			success = False
			while True:
				remaining = entry_end - time.monotonic()
				if remaining <= 0:
					print(f" | entry timed out after {entry_timeout}s")
					expired = True
					break
				match = click_first(candidates, min(timeout, remaining))
				if match is None:
					expired = time.monotonic() >= entry_end
					if expired:
						print(f" | entry timed out after {entry_timeout}s")
					else:
						print(" | page targets not found before timeout; trying next URL")
					break
				first, pos = match
				print(f" | {png_list[first][0]} @ {pos}", end="", flush=True)
				time.sleep(max(0, delay))
				if refs[first][1] is None:
					continue
				pyautogui.press("enter")
				time.sleep(max(0, delay))
				pyautogui.hotkey("ctrl", "w")
				pyautogui.click(500, 500)
				print(" | success")
				success = True
				break
			if success or expired:
				break


if __name__ == "__main__":
	main()
