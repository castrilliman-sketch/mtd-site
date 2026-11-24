"""SERP pixel widths for titles and meta descriptions.

Approximates Seobility / Google desktop display using Liberation Sans
(Arial-metric) widths, summed per character (no kerning). Titles are
measured at 20px and scaled so the previous homepage title matches
Seobility's 698px reading. Descriptions are measured at 14px.
No third-party dependencies.

Limits: title 580px and 60 characters; description 1000px and 155 characters.
The pixel caps follow Seobility; the character caps keep titles around 50–60
characters and descriptions within a typical SERP snippet.
"""
from __future__ import annotations

TITLE_MAX_PX = 580
TITLE_MAX_CHARS = 60
DESC_MAX_PX = 1000
DESC_MAX_CHARS = 155
_TITLE_SCALE = 1.0035269010445917
_DESC_SCALE = 0.7
# Advance widths at 20px Liberation Sans, keyed by Unicode code point.
_W20 = {
    32: 5.5625,
    33: 5.5625,
    34: 7.09375,
    35: 11.125,
    36: 11.125,
    37: 17.78125,
    38: 13.34375,
    39: 3.8125,
    40: 6.65625,
    41: 6.65625,
    42: 7.78125,
    43: 11.6875,
    44: 5.5625,
    45: 6.65625,
    46: 5.5625,
    47: 5.5625,
    48: 11.125,
    49: 11.125,
    50: 11.125,
    51: 11.125,
    52: 11.125,
    53: 11.125,
    54: 11.125,
    55: 11.125,
    56: 11.125,
    57: 11.125,
    58: 5.5625,
    59: 5.5625,
    60: 11.6875,
    61: 11.6875,
    62: 11.6875,
    63: 11.125,
    64: 20.296875,
    65: 13.34375,
    66: 13.34375,
    67: 14.4375,
    68: 14.4375,
    69: 13.34375,
    70: 12.21875,
    71: 15.5625,
    72: 14.4375,
    73: 5.5625,
    74: 10.0,
    75: 13.34375,
    76: 11.125,
    77: 16.65625,
    78: 14.4375,
    79: 15.5625,
    80: 13.34375,
    81: 15.5625,
    82: 14.4375,
    83: 13.34375,
    84: 12.21875,
    85: 14.4375,
    86: 13.34375,
    87: 18.875,
    88: 13.34375,
    89: 13.34375,
    90: 12.21875,
    91: 5.5625,
    92: 5.5625,
    93: 5.5625,
    94: 9.390625,
    95: 11.125,
    96: 6.65625,
    97: 11.125,
    98: 11.125,
    99: 10.0,
    100: 11.125,
    101: 11.125,
    102: 5.5625,
    103: 11.125,
    104: 11.125,
    105: 4.4375,
    106: 4.4375,
    107: 10.0,
    108: 4.4375,
    109: 16.65625,
    110: 11.125,
    111: 11.125,
    112: 11.125,
    113: 11.125,
    114: 6.65625,
    115: 10.0,
    116: 5.5625,
    117: 11.125,
    118: 10.0,
    119: 14.4375,
    120: 10.0,
    121: 10.0,
    122: 10.0,
    123: 6.6875,
    124: 5.203125,
    125: 6.6875,
    126: 11.6875,
    127: 15.0,
    128: 15.0,
    129: 15.0,
    130: 15.0,
    131: 15.0,
    132: 15.0,
    134: 15.0,
    135: 15.0,
    136: 15.0,
    137: 15.0,
    138: 15.0,
    139: 15.0,
    140: 15.0,
    141: 15.0,
    142: 15.0,
    143: 15.0,
    144: 15.0,
    145: 15.0,
    146: 15.0,
    147: 15.0,
    148: 15.0,
    149: 15.0,
    150: 15.0,
    151: 15.0,
    152: 15.0,
    153: 15.0,
    154: 15.0,
    155: 15.0,
    156: 15.0,
    157: 15.0,
    158: 15.0,
    159: 15.0,
    160: 5.5625,
    161: 6.65625,
    162: 11.125,
    163: 11.125,
    164: 11.125,
    165: 11.125,
    166: 5.203125,
    167: 11.125,
    168: 6.65625,
    169: 14.734375,
    170: 7.40625,
    171: 11.125,
    172: 11.6875,
    173: 0.0,
    174: 14.734375,
    175: 11.046875,
    176: 8.0,
    177: 10.984375,
    178: 6.65625,
    179: 6.65625,
    180: 6.65625,
    181: 11.53125,
    182: 10.75,
    183: 6.65625,
    184: 6.65625,
    185: 6.65625,
    186: 7.3125,
    187: 11.125,
    188: 16.6875,
    189: 16.6875,
    190: 16.6875,
    191: 12.21875,
    192: 13.34375,
    193: 13.34375,
    194: 13.34375,
    195: 13.34375,
    196: 13.34375,
    197: 13.34375,
    198: 20.0,
    199: 14.4375,
    200: 13.34375,
    201: 13.34375,
    202: 13.34375,
    203: 13.34375,
    204: 5.5625,
    205: 5.5625,
    206: 5.5625,
    207: 5.5625,
    208: 14.4375,
    209: 14.4375,
    210: 15.5625,
    211: 15.5625,
    212: 15.5625,
    213: 15.5625,
    214: 15.5625,
    215: 11.6875,
    216: 15.5625,
    217: 14.4375,
    218: 14.4375,
    219: 14.4375,
    220: 14.4375,
    221: 13.34375,
    222: 13.34375,
    223: 12.21875,
    224: 11.125,
    225: 11.125,
    226: 11.125,
    227: 11.125,
    228: 11.125,
    229: 11.125,
    230: 17.78125,
    231: 10.0,
    232: 11.125,
    233: 11.125,
    234: 11.125,
    235: 11.125,
    236: 5.5625,
    237: 5.5625,
    238: 5.5625,
    239: 5.5625,
    240: 11.125,
    241: 11.125,
    242: 11.125,
    243: 11.125,
    244: 11.125,
    245: 11.125,
    246: 11.125,
    247: 10.984375,
    248: 12.21875,
    249: 11.125,
    250: 11.125,
    251: 11.125,
    252: 11.125,
    253: 10.0,
    254: 11.125,
    255: 10.0,
    700: 4.4375,
    8211: 11.125,
    8212: 20.0,
    8216: 4.4375,
    8217: 4.4375,
    8220: 6.65625,
    8221: 6.65625,
    8226: 7.0,
    8230: 20.0,
    8364: 11.125
}
_FALLBACK = 11.125


def _sum20(text: str) -> float:
    return sum(_W20.get(ord(c), _FALLBACK) for c in text or "")


def title_px(text: str) -> float:
    return _sum20(text) * _TITLE_SCALE


def desc_px(text: str) -> float:
    return _sum20(text) * _DESC_SCALE


def title_ok(title: str, max_px: int = TITLE_MAX_PX, max_chars: int = TITLE_MAX_CHARS) -> bool:
    title = title or ""
    return title_px(title) <= max_px and len(title) <= max_chars


def desc_ok(desc: str, max_px: int = DESC_MAX_PX, max_chars: int = DESC_MAX_CHARS) -> bool:
    desc = desc or ""
    return desc_px(desc) <= max_px and len(desc) <= max_chars


def _truncate(text: str, fits) -> str:
    """Fit text to a predicate, breaking at a word boundary and adding an ellipsis."""
    if fits(text):
        return text
    ell = "…"
    lo, hi = 0, len(text)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if fits(text[:mid] + ell):
            lo = mid
        else:
            hi = mid - 1
    cut = text[:lo].rstrip()
    if " " in cut:
        snapped = cut.rsplit(" ", 1)[0].rstrip(" ,;:-")
        if snapped and fits(snapped + ell):
            cut = snapped
    cut = cut.rstrip(" ,;:-")
    return (cut + ell) if cut else ell


def fit_title(title: str, max_px: int = TITLE_MAX_PX, max_chars: int = TITLE_MAX_CHARS) -> str:
    """Keep a full title (already including any brand suffix) within the caps.

    Drops trailing ' | …' segments first, then truncates the remainder.
    """
    title = " ".join((title or "").split())
    if title_ok(title, max_px, max_chars):
        return title
    parts = [p.strip() for p in title.split(" | ") if p.strip()]
    while len(parts) > 1:
        parts.pop()
        candidate = " | ".join(parts)
        if title_ok(candidate, max_px, max_chars):
            return candidate
    remainder = parts[0] if parts else ""
    return _truncate(remainder, lambda s: title_ok(s, max_px, max_chars))


def fit_desc(desc: str, max_px: int = DESC_MAX_PX, max_chars: int = DESC_MAX_CHARS) -> str:
    desc = " ".join((desc or "").split())
    if desc_ok(desc, max_px, max_chars):
        return desc
    return _truncate(desc, lambda s: desc_ok(s, max_px, max_chars))
