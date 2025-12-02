"""
Clean Sheet Icon Generator
Creates a professional 256x256 icon with spreadsheet and cleaning theme
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_clean_sheet_icon():
    """Create Clean Sheet application icon - spreadsheet with sparkle effect"""

    # Create 256x256 image with transparent background
    size = 256
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Color scheme: Professional blue/green
    primary_blue = (0, 120, 212)  # #0078D4
    accent_green = (16, 124, 16)  # #107C10
    white = (255, 255, 255)
    light_gray = (240, 240, 240)
    dark_gray = (80, 80, 80)
    sparkle_yellow = (255, 215, 0)

    # Draw spreadsheet/grid background (rounded rectangle)
    margin = 20
    grid_rect = [margin, margin, size - margin, size - margin]

    # Draw shadow for depth
    shadow_offset = 8
    draw.rounded_rectangle(
        [grid_rect[0] + shadow_offset, grid_rect[1] + shadow_offset,
         grid_rect[2] + shadow_offset, grid_rect[3] + shadow_offset],
        radius=20,
        fill=(0, 0, 0, 60)
    )

    # Draw main spreadsheet background
    draw.rounded_rectangle(grid_rect, radius=20, fill=white)
    draw.rounded_rectangle(grid_rect, radius=20, outline=primary_blue, width=4)

    # Draw grid lines (simplified spreadsheet)
    grid_start = margin + 10
    grid_end = size - margin - 10
    cell_size = (grid_end - grid_start) // 5

    # Vertical lines
    for i in range(1, 5):
        x = grid_start + i * cell_size
        draw.line([(x, grid_start), (x, grid_end)], fill=light_gray, width=2)

    # Horizontal lines
    for i in range(1, 5):
        y = grid_start + i * cell_size
        draw.line([(grid_start, y), (grid_end, y)], fill=light_gray, width=2)

    # Draw header row (darker)
    header_rect = [grid_start, grid_start, grid_end, grid_start + cell_size]
    draw.rectangle(header_rect, fill=(230, 240, 255))

    # Add some "data" dots to represent content
    dot_radius = 4
    for row in range(1, 5):
        for col in range(5):
            if row > 0:  # Skip header
                x = grid_start + col * cell_size + cell_size // 2
                y = grid_start + row * cell_size + cell_size // 2
                draw.ellipse([x - dot_radius, y - dot_radius,
                             x + dot_radius, y + dot_radius],
                            fill=dark_gray)

    # Draw cleaning sparkles/shine effect (top right corner)
    sparkle_positions = [
        (size - 60, 40),
        (size - 40, 60),
        (size - 50, 75),
        (size - 70, 55),
    ]

    for x, y in sparkle_positions:
        # Draw 4-pointed star/sparkle
        star_size = 12

        # Horizontal line
        draw.line([(x - star_size, y), (x + star_size, y)],
                 fill=sparkle_yellow, width=3)

        # Vertical line
        draw.line([(x, y - star_size), (x, y + star_size)],
                 fill=sparkle_yellow, width=3)

        # Diagonal lines
        diag = int(star_size * 0.7)
        draw.line([(x - diag, y - diag), (x + diag, y + diag)],
                 fill=sparkle_yellow, width=2)
        draw.line([(x - diag, y + diag), (x + diag, y - diag)],
                 fill=sparkle_yellow, width=2)

        # Center dot
        draw.ellipse([x - 4, y - 4, x + 4, y + 4], fill=sparkle_yellow)

    # Draw checkmark (cleaning complete indicator)
    check_color = accent_green
    check_start_x = 60
    check_start_y = size - 80
    check_mid_x = 80
    check_mid_y = size - 60
    check_end_x = 110
    check_end_y = size - 95

    # Draw thick checkmark
    draw.line([(check_start_x, check_start_y), (check_mid_x, check_mid_y)],
             fill=check_color, width=8)
    draw.line([(check_mid_x, check_mid_y), (check_end_x, check_end_y)],
             fill=check_color, width=8)

    # Add circular badge background for checkmark
    badge_center = (85, size - 75)
    badge_radius = 35
    draw.ellipse([badge_center[0] - badge_radius, badge_center[1] - badge_radius,
                  badge_center[0] + badge_radius, badge_center[1] + badge_radius],
                 fill=(230, 255, 230), outline=accent_green, width=3)

    # Redraw checkmark on top of badge
    draw.line([(check_start_x, check_start_y), (check_mid_x, check_mid_y)],
             fill=check_color, width=8)
    draw.line([(check_mid_x, check_mid_y), (check_end_x, check_end_y)],
             fill=check_color, width=8)

    # Save as PNG
    png_path = 'clean_sheet_icon.png'
    img.save(png_path, 'PNG')
    print(f"✓ Created {png_path}")

    # Convert to ICO format (multiple sizes for Windows)
    ico_path = 'clean_sheet_icon.ico'

    # Create multiple sizes for ICO
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    icons = []

    for icon_size in sizes:
        resized = img.resize(icon_size, Image.Resampling.LANCZOS)
        icons.append(resized)

    # Save as ICO with multiple sizes
    icons[0].save(ico_path, format='ICO', sizes=[(s[0], s[1]) for s in sizes])
    print(f"✓ Created {ico_path} with sizes: {', '.join([f'{s[0]}x{s[1]}' for s in sizes])}")

    return png_path, ico_path

if __name__ == "__main__":
    print("=" * 60)
    print("Clean Sheet Icon Generator")
    print("Professional Data Cleaning Made Simple")
    print("=" * 60)
    print()

    try:
        png, ico = create_clean_sheet_icon()
        print()
        print("✓ Icon creation successful!")
        print()
        print(f"PNG file: {png} (256x256)")
        print(f"ICO file: {ico} (multi-size)")
        print()
        print("These files are ready to use with PyInstaller.")

    except Exception as e:
        print(f"✗ Error creating icon: {e}")
        import traceback
        traceback.print_exc()
