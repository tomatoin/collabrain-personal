#!/usr/bin/env python3
"""16유형 4x4 그리드 이미지를 개별 아바타 PNG로 잘라낸다.

사용법:
    python3 tools/slice_types.py <그리드이미지경로>

이미지는 원래 업무 도메인(개발·기획·디자인·PM) 기준 프롬프트로 만들어졌지만,
지금 앱은 업무 행위(실행전달·명확화·문제제기·진행관리) 기준으로 분류한다.
그리드는 새로 만들지 않고, 각 열의 그림이 뜻하는 바를 새 분류에 맞게 재해석해서
코드만 다시 매핑한다 (아래 CODES 표 참고). 1열(코딩·망치·활쏘기·동굴)은 원래도
"만들어낸다"는 이미지라 실행·전달과 잘 맞고, 4열(헤드셋·저글링·체스·망원경)은
"조율·관제"라 진행관리와 잘 맞는다. 2·3열은 다소 느슨하게 맞춘 것이라
렌더링 후 어색하면 그 칸만 다시 그려도 된다.

동작:
  1. 이미지를 4x4로 균등 분할 (행 우선: HD HL HI HC / WD WL WI WC / ...)
  2. 각 칸의 바깥 흰 배경을 가장자리에서 flood fill로만 지운다
     (인물 안쪽의 흰색 — 셔츠, 종이 — 은 건드리지 않음)
  3. 여백을 잘라내고 정사각으로 패딩한 뒤 512x512로 저장
"""
import sys, os
from collections import deque
from PIL import Image

# 열 순서는 그림 내용 그대로 유지 (1열 코딩/망치/활/동굴 → D, 2열 청사진/문서/여유/지도 → L,
# 3열 그림/편집/자연/이젤 → I, 4열 헤드셋/저글링/체스/망원경 → C)
CODES = [
    ["HD", "HL", "HI", "HC"],
    ["WD", "WL", "WI", "WC"],
    ["SD", "SL", "SI", "SC"],
    ["QD", "QL", "QI", "QC"],
]
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "assets", "types")
SIZE = 512
TOL = 26          # 배경으로 볼 흰색 허용 오차
PAD_RATIO = 0.06  # 정사각 패딩 여백


def strip_background(im: Image.Image) -> Image.Image:
    """가장자리에서 시작하는 연속된 흰 영역만 투명하게 만든다."""
    im = im.convert("RGBA")
    w, h = im.size
    px = im.load()

    def is_bg(x, y):
        r, g, b, a = px[x, y]
        return a > 0 and r >= 255 - TOL and g >= 255 - TOL and b >= 255 - TOL

    seen = bytearray(w * h)
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if is_bg(x, y) and not seen[y * w + x]:
                seen[y * w + x] = 1
                q.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if is_bg(x, y) and not seen[y * w + x]:
                seen[y * w + x] = 1
                q.append((x, y))

    while q:
        x, y = q.popleft()
        px[x, y] = (255, 255, 255, 0)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx] and is_bg(nx, ny):
                seen[ny * w + nx] = 1
                q.append((nx, ny))
    return im


def square(im: Image.Image) -> Image.Image:
    """내용 기준으로 잘라내고 정사각으로 패딩."""
    bbox = im.getbbox()
    if bbox:
        im = im.crop(bbox)
    w, h = im.size
    side = int(max(w, h) * (1 + PAD_RATIO * 2))
    canvas = Image.new("RGBA", (side, side), (255, 255, 255, 0))
    canvas.paste(im, ((side - w) // 2, (side - h) // 2), im)
    return canvas.resize((SIZE, SIZE), Image.LANCZOS)


def main():
    if len(sys.argv) < 2:
        sys.exit("사용법: python3 tools/slice_types.py <그리드이미지경로>")
    src = sys.argv[1]
    if not os.path.exists(src):
        sys.exit(f"파일을 찾을 수 없습니다: {src}")

    grid = Image.open(src).convert("RGBA")
    W, H = grid.size
    cw, ch = W // 4, H // 4
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"원본 {W}x{H} · 칸 크기 {cw}x{ch}")

    for r, row in enumerate(CODES):
        for c, code in enumerate(row):
            cell = grid.crop((c * cw, r * ch, (c + 1) * cw, (r + 1) * ch))
            out = square(strip_background(cell))
            path = os.path.join(OUT_DIR, f"{code}.png")
            out.save(path)
            print(f"  {code}.png  ({out.size[0]}x{out.size[1]})")

    print(f"\n16장 저장 완료 → {OUT_DIR}")


if __name__ == "__main__":
    main()
