"""Generate PWA icons for Shelfd with the bookmark+play logo."""
import struct
import zlib
import os


def make_png(width, height, pixels):
    """Create a minimal PNG from raw RGBA pixel data."""
    def chunk(chunk_type, data):
        c = chunk_type + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)

    raw = b''
    for y in range(height):
        raw += b'\x00'
        for x in range(width):
            raw += pixels[y][x]

    ihdr = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)
    return (b'\x89PNG\r\n\x1a\n' +
            chunk(b'IHDR', ihdr) +
            chunk(b'IDAT', zlib.compress(raw, 9)) +
            chunk(b'IEND', b''))


def draw_line(pixels, x0, y0, x1, y1, color, thickness, size):
    """Draw a line with thickness using brute force."""
    steps = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
    for i in range(steps + 1):
        t = i / steps if steps > 0 else 0
        cx = x0 + (x1 - x0) * t
        cy = y0 + (y1 - y0) * t
        for dy in range(-thickness, thickness + 1):
            for dx in range(-thickness, thickness + 1):
                if dx * dx + dy * dy <= thickness * thickness:
                    px, py = int(cx + dx), int(cy + dy)
                    if 0 <= px < size and 0 <= py < size:
                        pixels[py][px] = struct.pack('BBBB', *color)


def fill_triangle(pixels, x0, y0, x1, y1, x2, y2, color, size):
    """Fill a triangle using scanline."""
    min_y = max(0, int(min(y0, y1, y2)))
    max_y = min(size - 1, int(max(y0, y1, y2)))
    for y in range(min_y, max_y + 1):
        xs = []
        edges = [(x0, y0, x1, y1), (x1, y1, x2, y2), (x2, y2, x0, y0)]
        for ex0, ey0, ex1, ey1 in edges:
            if ey0 == ey1:
                continue
            if min(ey0, ey1) <= y <= max(ey0, ey1):
                t = (y - ey0) / (ey1 - ey0)
                xs.append(ex0 + t * (ex1 - ex0))
        if len(xs) >= 2:
            xs.sort()
            for px in range(max(0, int(xs[0])), min(size, int(xs[-1]) + 1)):
                pixels[y][px] = struct.pack('BBBB', *color)


def draw_icon(size):
    """Draw the bookmark+play logo at the given size."""
    bg = (26, 46, 34, 255)
    bookmark_c = (197, 216, 204, 255)
    play_c = (45, 157, 90, 255)

    pixels = [[struct.pack('BBBB', *bg) for _ in range(size)] for _ in range(size)]

    s = size
    # Bookmark outline
    bx0 = s * 0.25
    bx1 = s * 0.75
    by0 = s * 0.1
    by1 = s * 0.85
    notch_y = s * 0.7
    mid_x = s * 0.5
    t = max(1, int(s * 0.02))

    # Top
    draw_line(pixels, bx0, by0, bx1, by0, bookmark_c, t, s)
    # Left
    draw_line(pixels, bx0, by0, bx0, by1, bookmark_c, t, s)
    # Right
    draw_line(pixels, bx1, by0, bx1, by1, bookmark_c, t, s)
    # Bottom-left diagonal
    draw_line(pixels, bx0, by1, mid_x, notch_y, bookmark_c, t, s)
    # Bottom-right diagonal
    draw_line(pixels, bx1, by1, mid_x, notch_y, bookmark_c, t, s)

    # Play triangle (centered in upper portion of bookmark)
    px0 = s * 0.38
    py0 = s * 0.28
    px1 = s * 0.38
    py1 = s * 0.58
    px2 = s * 0.67
    py2 = s * 0.43
    fill_triangle(pixels, px0, py0, px1, py1, px2, py2, play_c, s)

    return pixels


def main():
    out_dir = os.path.join(os.path.dirname(__file__), '..', 'public', 'icons')
    os.makedirs(out_dir, exist_ok=True)

    for size in [192, 512]:
        pixels = draw_icon(size)
        png_data = make_png(size, size, pixels)
        path = os.path.join(out_dir, f'icon-{size}x{size}.png')
        with open(path, 'wb') as f:
            f.write(png_data)
        print(f'Generated {path} ({len(png_data)} bytes)')


if __name__ == '__main__':
    main()
