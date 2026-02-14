"""SVG progress card generator for GitHub README embedding."""

from typing import TYPE_CHECKING
from datetime import datetime
import html

if TYPE_CHECKING:
    from schemas import BookSummary


def render_progress_card(books: list["BookSummary"]) -> str:
    """Render an SVG progress card showing reading progress."""
    card_width = 400
    header_height = 40
    book_height = 65
    padding = 16
    card_height = header_height + (len(books) * book_height) + padding

    if not books:
        card_height = header_height + 40

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{card_width}" height="{card_height}" viewBox="0 0 {card_width} {card_height}">',
        '<style>',
        '  .card { fill: #ffffff; stroke: #e1e4e8; stroke-width: 1; rx: 6; }',
        '  .header { fill: #24292f; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; font-size: 14px; font-weight: 600; }',
        '  .book-title { fill: #24292f; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; font-size: 12px; }',
        '  .percentage { fill: #57606a; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; font-size: 11px; }',
        '  .date { fill: #8b949e; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; font-size: 10px; }',
        '  .progress-bg { fill: #e1e4e8; rx: 3; }',
        '  .progress-fill { fill: #2da44e; rx: 3; }',
        '</style>',
        f'<rect class="card" x="0.5" y="0.5" width="{card_width - 1}" height="{card_height - 1}"/>',
        f'<text class="header" x="{padding}" y="26">Currently Reading</text>',
        f'<line x1="{padding}" y1="{header_height}" x2="{card_width - padding}" y2="{header_height}" stroke="#e1e4e8" stroke-width="1"/>',
    ]

    if not books:
        svg_parts.append(
            f'<text class="book-title" x="{padding}" y="{header_height + 25}" fill="#57606a">No books in progress</text>'
        )
    else:
        for i, book in enumerate(books):
            y_offset = header_height + (i * book_height) + 20
            title = html.escape(book.label or book.filename or book.canonical_hash)
            if len(title) > 40:
                title = title[:37] + "..."

            percentage = min(max(book.percentage * 100, 0), 100)
            progress_width = int((card_width - padding * 2 - 50) * (percentage / 100))
            bar_width = card_width - padding * 2 - 50

            # Format the timestamp as a readable date
            last_updated = datetime.fromtimestamp(book.timestamp).strftime("%b %d, %Y")

            svg_parts.extend([
                f'<text class="book-title" x="{padding}" y="{y_offset}">{title}</text>',
                f'<text class="percentage" x="{card_width - padding}" y="{y_offset}" text-anchor="end">{percentage:.0f}%</text>',
                f'<rect class="progress-bg" x="{padding}" y="{y_offset + 8}" width="{bar_width}" height="6"/>',
                f'<rect class="progress-fill" x="{padding}" y="{y_offset + 8}" width="{progress_width}" height="6"/>',
                f'<text class="date" x="{padding}" y="{y_offset + 26}">Last read: {last_updated}</text>',
            ])

    svg_parts.append('</svg>')
    return '\n'.join(svg_parts)
