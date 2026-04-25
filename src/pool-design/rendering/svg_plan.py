"""SVG 2D pool plan generator."""

import math


def generate_pool_svg(design: dict, width: int = 800, height: int = 600) -> str:
    """Generate a simple 2D SVG floor plan from a pool design spec."""
    dims = design.get("dimensions", {})
    length = dims.get("length_ft", 30)
    pool_width = dims.get("width_ft", 15)
    shape = design.get("pool_shape", "rectangle")

    scale = min((width - 100) / length, (height - 100) / pool_width)
    cx, cy = width / 2, height / 2
    pw = length * scale
    ph = pool_width * scale

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">',
        f'<rect width="{width}" height="{height}" fill="#f5f5dc"/>',  # Background (yard)
    ]

    # Pool shape
    x1, y1 = cx - pw / 2, cy - ph / 2
    if shape in ("rectangle", "L-shape", "lazy-L"):
        svg_parts.append(
            f'<rect x="{x1}" y="{y1}" width="{pw}" height="{ph}" '
            f'rx="8" fill="#4fc3f7" stroke="#0288d1" stroke-width="3"/>'
        )
    elif shape == "kidney":
        svg_parts.append(
            f'<ellipse cx="{cx}" cy="{cy}" rx="{pw/2}" ry="{ph/2}" '
            f'fill="#4fc3f7" stroke="#0288d1" stroke-width="3"/>'
        )
    else:
        svg_parts.append(
            f'<rect x="{x1}" y="{y1}" width="{pw}" height="{ph}" '
            f'rx="20" fill="#4fc3f7" stroke="#0288d1" stroke-width="3"/>'
        )

    # Dimensions label
    svg_parts.append(
        f'<text x="{cx}" y="{cy}" text-anchor="middle" font-size="14" fill="#01579b">'
        f'{length}\' × {pool_width}\'</text>'
    )

    # Deck outline
    deck_pad = 30
    svg_parts.append(
        f'<rect x="{x1-deck_pad}" y="{y1-deck_pad}" '
        f'width="{pw+deck_pad*2}" height="{ph+deck_pad*2}" '
        f'rx="12" fill="none" stroke="#795548" stroke-width="2" stroke-dasharray="8,4"/>'
    )

    svg_parts.append(f'<text x="{cx}" y="{height-20}" text-anchor="middle" font-size="12" fill="#555">'
                      f'AzL Pools — {shape.title()} Pool Design</text>')
    svg_parts.append("</svg>")

    return "\n".join(svg_parts)
