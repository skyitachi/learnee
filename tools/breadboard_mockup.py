#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""面包板实物模拟图生成器（无依赖，纯 SVG）

坐标体系沿用真实 400 孔面包板：
  - 30 列，列距 0.1in；上下各 5 行，中间凹槽隔开（上下块互不导通）
  - 上下各两条电源轨（内轨 +，外轨 -），左右各有缺口（本图左右连通，简化处理）
  - 同一列（上块 J..F 或下块 A..E）的孔互相导通 —— 这是面包板唯一的"免费连接"

用法见文件末尾 SPEC 与 main()。
"""
import math

S = 3.2                     # 每个板单位 = 3.2 px
COLS = 30
COL_X0, COL_DX = 13.65, 9.0
ROW_Y = {'J': 45, 'I': 54, 'H': 63, 'G': 72, 'F': 81,      # 上块（从上往下）
         'A': 144, 'B': 135, 'C': 126, 'D': 117, 'E': 108}  # 下块
RAIL = {'tm': 9, 'tp': 18, 'bp': 171, 'bm': 180}            # m=外(−) p=内(+)
BOARD_W, BOARD_H = 292.41, 189

C_RED, C_BLUE, C_GREEN = '#d32f2f', '#1565c0', '#2e7d32'
C_ORANGE = '#ef6c00'
C_INK, C_GREY, C_PAPER = '#1a1a1a', '#8a8a8a', '#fdfdfb'


def cx(c):
    return COL_X0 + COL_DX * (c - 1)


def px(v):
    return v * S


# ---------------------------------------------------------------- 基础图元

def rounded_path(pts, r=5.0):
    """折线转角处做圆角，模拟跳线的自然弯折"""
    if len(pts) < 3:
        return 'M%.2f,%.2f L%.2f,%.2f' % (pts[0][0], pts[0][1], pts[-1][0], pts[-1][1])
    d = ['M%.2f,%.2f' % pts[0]]
    for i in range(1, len(pts) - 1):
        p0, p1, p2 = pts[i - 1], pts[i], pts[i + 1]
        v1 = (p0[0] - p1[0], p0[1] - p1[1])
        v2 = (p2[0] - p1[0], p2[1] - p1[1])
        l1, l2 = math.hypot(*v1) or 1, math.hypot(*v2) or 1
        rr = min(r, l1 / 2, l2 / 2)
        a = (p1[0] + v1[0] / l1 * rr, p1[1] + v1[1] / l1 * rr)
        b = (p1[0] + v2[0] / l2 * rr, p1[1] + v2[1] / l2 * rr)
        d.append('L%.2f,%.2f Q%.2f,%.2f %.2f,%.2f' % (a[0], a[1], p1[0], p1[1], b[0], b[1]))
    d.append('L%.2f,%.2f' % pts[-1])
    return ' '.join(d)


def text(x, y, s, size=3.4, color=C_INK, anchor='middle', weight='400', halo=True):
    h = ('stroke="#fdfdfb" stroke-width="1.6" stroke-linejoin="round" paint-order="stroke" '
         if halo else '')
    return ('<text x="%.2f" y="%.2f" font-size="%.2f" fill="%s" text-anchor="%s" '
            'font-weight="%s" %s>%s</text>' % (x, y, size, color, anchor, weight, h, s))


# ---------------------------------------------------------------- 板子

def draw_board():
    o = []
    r = 2.2
    o.append('<rect x="0" y="0" width="%.2f" height="%.2f" rx="%.1f" fill="#e9e9e7" '
             'stroke="#c9c9c6" stroke-width="0.4"/>' % (BOARD_W, BOARD_H, r))
    # 中央凹槽
    o.append('<rect x="1.2" y="%.2f" width="%.2f" height="%.2f" fill="#dbdbd8"/>'
             % (85.5, BOARD_W - 2.4, 19.5))

    # 电源轨底色：内轨红(+)、外轨蓝(−)
    for y, col in ((RAIL['tp'], '#f6dcdc'), (RAIL['tm'], '#d9e4f2'),
                   (RAIL['bp'], '#f6dcdc'), (RAIL['bm'], '#d9e4f2')):
        o.append('<rect x="3.5" y="%.2f" width="%.2f" height="7.5" rx="1" fill="%s"/>'
                 % (y - 3.75, BOARD_W - 7, col))
    # 轨分隔线
    for y in (24.5, 161.5):
        o.append('<line x1="3.5" y1="%.2f" x2="%.2f" y2="%.2f" stroke="#b8b8b5" stroke-width="0.5"/>'
                 % (y, BOARD_W - 3.5, y))

    # 列号 / 行号
    for c in range(1, COLS + 1):
        lab = str(c) if c in (1, 5, 10, 15, 20, 25, 30) else ''
        if lab:
            o.append(text(cx(c), 92.5, lab, 3.0, '#a9a9a4'))
            o.append(text(cx(c), 157.0, lab, 3.0, '#a9a9a4'))
    for row, y in ROW_Y.items():
        if row in 'JHFC':
            o.append(text(7.2, y + 1.2, row, 3.0, '#a9a9a4'))
            o.append(text(BOARD_W - 7.2, y + 1.2, row, 3.0, '#a9a9a4'))

    # 孔
    for c in range(1, COLS + 1):
        for y in ROW_Y.values():
            o.append('<circle cx="%.2f" cy="%.2f" r="1.45" fill="#3c3c3c"/>'
                     '<circle cx="%.2f" cy="%.2f" r="2.55" fill="none" stroke="#d2d2cf" stroke-width="0.9"/>'
                     % (cx(c), y, cx(c), y))
        for y in RAIL.values():
            o.append('<circle cx="%.2f" cy="%.2f" r="1.45" fill="#3c3c3c"/>' % (cx(c), y))

    # 轨标记
    o.append(text(10.5, RAIL['tp'] + 1.2, '＋', 3.4, C_RED, weight='700'))
    o.append(text(10.5, RAIL['tm'] + 1.2, '－', 3.4, C_BLUE, weight='700'))
    return o


# ---------------------------------------------------------------- 元件

def _hole_dot(x, y):
    return '<circle cx="%.2f" cy="%.2f" r="0.75" fill="#555"/>' % (x, y)


def resistor(row, c1, c2, label, bands=('黄', '紫', '橙', '金'), num=None):
    """卧式电阻：两脚分别插在 (c1,row) 和 (c2,row)"""
    y = ROW_Y[row]
    x1, x2 = cx(min(c1, c2)), cx(max(c1, c2))
    half = 6.2
    bx1, bx2 = (x1 + x2) / 2 - half, (x1 + x2) / 2 + half
    o = []
    # 引脚
    o.append('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="#9e9e9e" stroke-width="0.75"/>'
             % (x1, y, bx1, y))
    o.append('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="#9e9e9e" stroke-width="0.75"/>'
             % (bx2, y, x2, y))
    # 本体
    o.append('<rect x="%.2f" y="%.2f" width="%.2f" height="4.6" rx="1.8" fill="#e9d3ae" '
             'stroke="#a1887f" stroke-width="0.35"/>' % (bx1, y - 2.3, bx2 - bx1, ))
    colmap = {'黑': '#222', '棕': '#6d4c41', '红': '#c62828', '橙': '#ef6c00', '黄': '#f9a825',
              '绿': '#2e7d32', '蓝': '#1565c0', '紫': '#6a1b9a', '灰': '#9e9e9e', '白': '#fafafa',
              '金': '#c9a227', '银': '#bdbdbd'}
    n = len(bands)
    for i, b in enumerate(bands):
        bx = bx1 + 1.6 + i * ((bx2 - bx1 - 3.2) / max(n, 1)) * 0.85
        o.append('<rect x="%.2f" y="%.2f" width="%.2f" height="4.6" fill="%s"/>'
                 % (bx, y - 2.3, 1.15, colmap.get(b, '#666')))
    o.append(_hole_dot(x1, y) + _hole_dot(x2, y))
    if label:
        o.append(text((bx1 + bx2) / 2, y - 4.0, label, 3.2, '#5d4037', weight='600'))
    if num:
        o.append(badge(x2 + 4.4, y - 6.2, num))
    return o


def ldr(row, c1, c2, num=None, label=None):
    y = ROW_Y[row]
    x1, x2 = cx(min(c1, c2)), cx(max(c1, c2))
    mx = (x1 + x2) / 2
    w, h = 8.4, 6.4
    o = []
    o.append('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="#9e9e9e" stroke-width="0.75"/>'
             % (x1, y, mx - w / 2, y))
    o.append('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="#9e9e9e" stroke-width="0.75"/>'
             % (mx + w / 2, y, x2, y))
    o.append('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" rx="0.9" fill="#eef3f9" '
             'stroke="#7986cb" stroke-width="0.45"/>' % (mx - w / 2, y - h / 2, w, h))
    # 蛇形感光面
    zig = []
    for i in range(6):
        zig.append((mx - w / 2 + 1.4 + i * 1.15, y - 1.6 if i % 2 == 0 else y + 1.6))
    o.append('<polyline points="%s" fill="none" stroke="#c5a34a" stroke-width="0.55"/>'
             % ' '.join('%.2f,%.2f' % p for p in zig))
    # 入射光箭头
    for dx in (-1.2, 1.4):
        o.append('<path d="M%.2f,%.2f L%.2f,%.2f" stroke="#f9a825" stroke-width="0.6" marker-end=""/>'
                 % (mx + dx + 2.6, y - 3.4, mx + dx, y - 1.4))
    o.append(_hole_dot(x1, y) + _hole_dot(x2, y))
    if num:
        o.append(badge(x2 + 4.4, y - 6.2, num))
    return o


def led(row, c_cathode, c_anode, num=None):
    """卧式 5mm LED：本体跨在两孔上方，两腿垂直插入"""
    y = ROW_Y[row]
    xc, xa = cx(c_cathode), cx(c_anode)
    mx = (xc + xa) / 2
    r = 4.6
    top = y - r - 1.0
    o = []
    # 腿
    o.append('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="#9e9e9e" stroke-width="0.8"/>'
             % (xc, y, xc, y - 0.4))
    o.append('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="#9e9e9e" stroke-width="0.8"/>'
             % (xa, y, xa, y - 0.4))
    o.append('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="#9e9e9e" stroke-width="0.8"/>'
             % (xc, y - 0.4, mx - 2.4, top + r * 0.9))
    o.append('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="#9e9e9e" stroke-width="0.8"/>'
             % (xa, y - 0.4, mx + 2.4, top + r * 0.9))
    # 灯体
    o.append('<path d="M%.2f,%.2f A%.2f,%.2f 0 0 1 %.2f,%.2f L%.2f,%.2f L%.2f,%.2f Z" '
             'fill="#ffcdd2" fill-opacity="0.92" stroke="#c62828" stroke-width="0.45"/>'
             % (mx - r, top + r, r, r, mx + r, top + r, mx + r, top + 2 * r, mx - r, top + 2 * r))
    o.append('<ellipse cx="%.2f" cy="%.2f" rx="1.5" ry="2.0" fill="#fff" fill-opacity="0.75"/>'
             % (mx - 1.6, top + r - 0.4))
    if num:
        o.append(badge(mx, top - 2.6, num))
    o.append(_hole_dot(xc, y) + _hole_dot(xa, y))
    # 极性标注
    o.append(text(xc, y + 5.0, '－', 3.0, C_BLUE, weight='700'))
    o.append(text(xa, y + 5.0, '＋', 3.0, C_RED, weight='700'))
    return o


def to92(row, c_e, c_b, c_c, num=None, label=None):
    """TO-92 三极管：三腿相邻三列垂直插入，本体是半圆 D 形。
    引脚顺序按实物：平面朝自己、引脚朝下，左→右为 E-B-C
    （PN2222 / PN2222A / S8050 / 2N3904 均为此顺序）。"""
    y = ROW_Y[row]
    xs = [cx(c) for c in (c_e, c_b, c_c)]
    left, right = min(xs) - 3.0, max(xs) + 3.0
    body_h, body_top = 8.0, y - 8.0
    o = []
    for x in xs:
        o.append('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="#616161" stroke-width="0.8"/>'
                 % (x, y, x, body_top + body_h))
    o.append('<path d="M%.2f,%.2f L%.2f,%.2f A%.2f,%.2f 0 0 1 %.2f,%.2f L%.2f,%.2f Z" '
             'fill="#2f2f2f" stroke="#111" stroke-width="0.4"/>'
             % (left, body_top + body_h, left, body_top + 4.5, (right - left) / 2, 4.5,
                right, body_top + 4.5, right, body_top + body_h))
    o.append(text((left + right) / 2, body_top + body_h - 1.4, 'PN2222', 2.4, '#cfd8dc', weight='600', halo=False))
    for x in xs:
        o.append(_hole_dot(x, y))
    if num:
        o.append(badge(right + 4.4, body_top - 1.6, num))
    return o


def to92_labels(row, c_e, c_b, c_c):
    """三极管引脚字母，单独一层最后绘制，避免被跳线盖住"""
    y = ROW_Y[row]
    o = []
    for c, lab, col in zip((c_e, c_b, c_c), ('E', 'B', 'C'), (C_BLUE, C_GREEN, C_ORANGE)):
        o.append(text(cx(c) - 2.4, y + 5.4, lab, 3.0, col, weight='700'))
    return o


def battery(x, y, label='3×AA 电池盒  4.5V'):
    """电池盒 + 两根引线"""
    w, h = 74, 30
    o = []
    o.append('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" rx="2" fill="#37474f"/>'
             % (x, y, w, h))
    for i in range(3):
        bx = x + 4 + i * (w - 8) / 3
        o.append('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" rx="2.5" fill="#cfd8dc" '
                 'stroke="#90a4ae" stroke-width="0.4"/>' % (bx, y + 5, (w - 8) / 3 - 2.5, h - 10))
        o.append('<rect x="%.2f" y="%.2f" width="%.2f" height="3.2" fill="#b0bec5"/>'
                 % (bx + 3, y + 8, (w - 8) / 3 - 8.5))
    o.append(text(x + w / 2, y + h + 6.5, label, 3.2, '#37474f', weight='600'))
    # 开关
    o.append('<rect x="%.2f" y="%.2f" width="10" height="6" rx="1" fill="#455a64"/>' % (x + w / 2 - 5, y - 9))
    o.append(text(x + w / 2, y - 4.6, '开关', 2.8, '#455a64'))
    return o


def wire(pts, color, width=1.15, dash=None, opacity=1.0):
    d = rounded_path(pts)
    extra = ' stroke-dasharray="%s"' % dash if dash else ''
    return ('<path d="%s" fill="none" stroke="%s" stroke-width="%.2f" stroke-linecap="round" '
            'stroke-linejoin="round" opacity="%.2f"%s/>'
            % (d, color, width, opacity, extra))


def jumper(pts, color, casing=False):
    """跳线：先画阴影；casing=True 时再垫一条底色，形成"压在另一根线上"的效果"""
    out = [wire(pts, '#00000018', 2.1)]
    if casing:
        out.append(wire(pts, C_PAPER, 3.6))
    out.append(wire(pts, color))
    return out


def badge(x, y, n, color='#37474f'):
    return ('<circle cx="%.2f" cy="%.2f" r="3.4" fill="%s"/>'
            '<text x="%.2f" y="%.2f" font-size="3.4" fill="#fff" text-anchor="middle" '
            'font-weight="700">%d</text>' % (x, y, color, x, y + 1.15, n))


def tag(x, y, s, color):
    return text(x, y, s, 3.0, color, weight='700')


# ---------------------------------------------------------------- 装配

def build(spec):
    W, H = 430, 300
    ox, oy = 122, 26          # 板子左上角在画布中的位置（板单位）
    g = []
    # 画布
    g.append('<rect x="0" y="0" width="%d" height="%d" fill="%s"/>' % (W * S, H * S, C_PAPER))

    # 标题
    g.append('<text x="%.1f" y="%.1f" font-size="26" font-weight="700" fill="%s" '
             'font-family="-apple-system,\'PingFang SC\',sans-serif">%s</text>'
             % (W * S / 2, 34, C_INK, spec['title']))
    g.append('<text x="%.1f" y="%.1f" font-size="13" fill="#666" text-anchor="middle" '
             'font-family="-apple-system,\'PingFang SC\',sans-serif">%s</text>'
             % (W * S / 2, 56, spec['subtitle']))

    body = ['<g transform="translate(%.2f,%.2f) scale(%.3f)">' % (px(ox), px(oy), S)]
    body += draw_board()

    # 元件（按 spec 顺序，先画的在下面）
    for comp in spec['parts']:
        for line in comp:
            body.append(line)

    # 跳线
    for pts, col in spec['wires']:
        body += jumper(pts, col)

    # 顶层标注（引脚字母等，必须在跳线之上）
    for layer in spec.get('labels', []):
        for line in layer:
            body.append(line)

    body.append('</g>')
    g += body

    # 标注（在板外，用画布坐标 = 板坐标 + 偏移）
    for a in spec.get('notes', []):
        g.append(a(ox, oy))

    # 图例
    lg = spec.get('legend', [])
    ly = px(oy + BOARD_H) + 46
    lx = px(ox) / 1.0 - 60
    for i, (col, lab) in enumerate(lg):
        x = lx + i * 200
        g.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="4" '
                 'stroke-linecap="round"/>' % (x, ly - 4, x + 34, ly - 4, col))
        g.append('<text x="%.1f" y="%.1f" font-size="13" fill="#333" '
                 'font-family="-apple-system,\'PingFang SC\',sans-serif">%s</text>'
                 % (x + 44, ly, lab))
    # 元件表（三列换行，避免长说明串到下一格）
    tbl = spec.get('table') or []
    if tbl:
        per_row = 3
        ty0 = px(oy + BOARD_H) + 96
        colw = (W * S - 130) / per_row
        for i, (num, name, note) in enumerate(tbl):
            r, c = divmod(i, per_row)
            x = 70 + c * colw
            ty = ty0 + r * 48
            g.append('<circle cx="%.0f" cy="%.0f" r="11" fill="#37474f"/>'
                     '<text x="%.0f" y="%.0f" font-size="12" fill="#fff" text-anchor="middle" '
                     'font-weight="700">%d</text>' % (x, ty, x, ty + 4, num))
            g.append('<text x="%.0f" y="%.0f" font-size="13.5" font-weight="600" fill="#1a1a1a">%s</text>'
                     % (x + 18, ty - 1, name))
            g.append('<text x="%.0f" y="%.0f" font-size="11.5" fill="#777">%s</text>'
                     % (x + 18, ty + 14, note))

    return ('<svg width="%d" height="%d" viewBox="0 0 %d %d" xmlns="http://www.w3.org/2000/svg" '
            'font-family="-apple-system,\'PingFang SC\',\'Microsoft YaHei\',sans-serif">%s</svg>'
            % (W * S, H * S, W * S, H * S, ''.join(g)))


def page(svg, title):
    return ('<!DOCTYPE html>\n<html lang="zh">\n<head>\n<meta charset="UTF-8">\n<title>%s</title>\n'
            '<style>\n  html,body{margin:0;padding:0;background:#f4f4f2;}\n'
            '  .sheet{display:flex;justify-content:center;padding:24px 0;}\n'
            '  svg{display:block;max-width:100%%;height:auto;box-shadow:0 1px 6px rgba(0,0,0,.08);}\n'
            '</style>\n</head>\n<body>\n<div class="sheet">\n%s\n</div>\n</body>\n</html>\n'
            % (title, svg))


# ---------------------------------------------------------------- 小夜灯

def night_light():
    """小夜灯最终布局：
       分压器 J/I 行第 7–13 列；三极管 G 行第 17/18/19 列（E-B-C，按实物引脚顺序）；
       LED + 220Ω 放 J 行第 22–27 列；基极从 J 行拉过去，集电极走 H 行拉过去。"""
    parts = [
        resistor('J', 7, 10, '47kΩ', ('黄', '紫', '橙', '金'), num=2),
        ldr('I', 10, 13, num=3),
        to92('G', 17, 18, 19, num=4),
        led('J', 22, 23, num=5),
        resistor('J', 23, 27, '220Ω', ('红', '红', '棕', '金'), num=6),
        battery(-100, 96, '3×AA 电池盒 4.5V') + [badge(-64, 89, 1)],
    ]
    wires = [
        ([(cx(7), ROW_Y['J']), (cx(7), RAIL['tp'])], C_RED),
        ([(cx(13), ROW_Y['I']), (cx(13), RAIL['tm'])], C_BLUE),
        ([(cx(10), ROW_Y['J']), (cx(18), ROW_Y['J']), (cx(18), ROW_Y['G'] - 8.6)], C_GREEN),
        ([(cx(19), ROW_Y['G']), (cx(19), ROW_Y['H']), (cx(22), ROW_Y['H']),
          (cx(22), ROW_Y['J'])], C_ORANGE),
        ([(cx(17), ROW_Y['G']), (cx(17), ROW_Y['F']), (cx(28), ROW_Y['F']),
          (cx(28), RAIL['tm'])], C_BLUE),
        ([(cx(27), ROW_Y['J']), (cx(27), RAIL['tp'])], C_RED),
        ([(-26, 103), (-6, 103), (-6, RAIL['tp']), (cx(1), RAIL['tp'])], C_RED),
        ([(-26, 118), (1.2, 118), (1.2, RAIL['tm']), (cx(1), RAIL['tm'])], '#212121'),
    ]

    def x_mark(ox, oy):
        x, y = px(ox + cx(10)), px(oy + ROW_Y['J'] - 7.5)
        return ('<circle cx="%.1f" cy="%.1f" r="6" fill="%s"/>'
                '<text x="%.1f" y="%.1f" font-size="13" font-weight="700" fill="%s">'
                '节点 X</text>' % (x, y, C_GREEN, x + 9, y + 4.5, C_GREEN))

    return dict(
        title='魔法小夜灯 · 实物接线图（面包板）',
        subtitle='元件按编号插、跳线照颜色走；插完按施工文档第 3 节再核对一遍',
        parts=parts, wires=wires, notes=[x_mark],
        labels=[to92_labels('G', 17, 18, 19)],
        legend=[(C_RED, '＋4.5V'), (C_BLUE, 'GND'), (C_GREEN, '节点 X → 基极 B'),
                (C_ORANGE, '集电极 C → LED')],
        table=[
            (1, '3×AA 电池盒', '红线→＋轨，黑线→－轨'),
            (2, '47kΩ 电阻', '第 7→10 列 J 行'),
            (3, '光敏电阻', '第 10→13 列 I 行'),
            (4, 'PN2222 三极管', '第 17/18/19 列 G 行（E-B-C，左→右）'),
            (5, 'LED', '第 22→23 列 J 行（＋长脚在 23）'),
            (6, '220Ω 电阻', '第 23→27 列 J 行'),
        ],
    )


if __name__ == '__main__':
    import sys, os
    svg = build(night_light())
    out = sys.argv[1] if len(sys.argv) > 1 else '/tmp/小夜灯实物图.html'
    os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
    open(out, 'w', encoding='utf-8').write(page(svg, '魔法小夜灯 · 实物接线图'))
    print('written:', out, len(svg), 'bytes')
