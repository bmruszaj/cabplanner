"""
Download and set up open-source Feather icons for the Cabplanner application.
This script downloads the icons from feathericons.com and prepares them for use.
"""

import sys
import requests
import zipfile
import io
import shutil
from pathlib import Path

# Define icon set URL and local icon directory
ICON_DOWNLOAD_URL = (
    "https://github.com/feathericons/feather/archive/refs/tags/v4.29.0.zip"
)
ICON_DIR = (
    Path(__file__).resolve().parent.parent / "src" / "gui" / "resources" / "icons"
)

# Map of icon names we need to their Feather equivalent
ICON_MAPPING = {
    # Main toolbar icons
    "new_project": "file-plus",
    "open_project": "folder-open",
    "save": "save",
    "delete": "trash-2",
    "export": "download",
    "print": "printer",
    "settings": "settings",
    "cabinet": "archive",
    "catalog": "list",
    "dashboard": "grid",
    # Action icons
    "add": "plus",
    "edit": "edit",
    "remove": "trash",
    "search": "search",
    "filter": "filter",
    "sort": "sort",
    # Status icons
    "success": "check-circle",
    "warning": "alert-triangle",
    "error": "alert-octagon",
    "info": "info",
    # Misc
    "logo": "box",
    "check": "check",
    "check_white": "check",
    "arrow_right": "arrow-right",
    "arrow_left": "arrow-left",
    "close": "x",
    "menu": "menu",
    "help": "help-circle",
}


def create_icon_directory():
    """Create the icon directory if it doesn't exist"""
    print(f"Creating icon directory: {ICON_DIR}")
    ICON_DIR.mkdir(parents=True, exist_ok=True)


def download_and_extract_icons():
    """Download and extract the Feather icon set"""
    print(f"Downloading icons from: {ICON_DOWNLOAD_URL}")

    try:
        response = requests.get(ICON_DOWNLOAD_URL)
        response.raise_for_status()

        print("Download successful, extracting...")
        z = zipfile.ZipFile(io.BytesIO(response.content))

        # Create a temporary extraction directory
        temp_dir = ICON_DIR / "temp"
        temp_dir.mkdir(exist_ok=True)

        # Extract only the SVG files
        for item in z.namelist():
            if item.endswith(".svg") and "/icons/" in item:
                z.extract(item, temp_dir)

        print("Extraction completed")
        return temp_dir

    except requests.RequestException as e:
        print(f"Error downloading icons: {e}")
        return None


def convert_svg_to_png(svg_path, output_path, size=64):
    """Convert an SVG file to PNG"""
    try:
        # Try to import cairosvg, fallback to using a simpler method if not available
        try:
            import cairosvg

            cairosvg.svg2png(
                url=str(svg_path),
                write_to=str(output_path),
                output_width=size,
                output_height=size,
            )
            return True
        except ImportError:
            # Fallback using QtSvg if available
            try:
                from PySide6.QtSvg import QSvgRenderer
                from PySide6.QtGui import QImage, QPainter, qRgba
                from PySide6.QtCore import QSize

                renderer = QSvgRenderer(str(svg_path))
                image = QImage(size, size, QImage.Format_ARGB32)
                image.fill(qRgba(0, 0, 0, 0))  # Transparent background
                painter = QPainter(image)
                renderer.render(painter)
                painter.end()
                return image.save(str(output_path))
            except ImportError:
                print(
                    "Warning: Neither cairosvg nor QtSvg are available. Cannot convert SVG to PNG."
                )
                return False
    except Exception as e:
        print(f"Error converting SVG to PNG: {e}")
        return False


def process_icons(temp_dir):
    """Process the downloaded icons according to our mapping"""
    svg_dir = next(temp_dir.glob("**/icons"))

    print(f"Processing icons from {svg_dir}...")

    for our_name, feather_name in ICON_MAPPING.items():
        svg_path = svg_dir / f"{feather_name}.svg"
        png_path = ICON_DIR / f"{our_name}.png"

        if svg_path.exists():
            print(f"Converting {feather_name}.svg to {our_name}.png")

            # For check_white, process the icon to have white strokes
            if our_name == "check_white":
                # Copy to a temporary file and modify
                temp_svg = temp_dir / "temp.svg"
                with svg_path.open("r") as f_in:
                    content = f_in.read()
                    # Replace stroke color with white
                    content = content.replace('stroke="currentColor"', 'stroke="white"')
                    with temp_svg.open("w") as f_out:
                        f_out.write(content)

                convert_svg_to_png(temp_svg, png_path)
                temp_svg.unlink(missing_ok=True)  # Delete temp file
            else:
                convert_svg_to_png(svg_path, png_path)
        else:
            print(f"Warning: {feather_name}.svg not found")

    print("Icon processing completed")


def cleanup(temp_dir):
    """Clean up temporary files"""
    if temp_dir and temp_dir.exists():
        shutil.rmtree(temp_dir)
        print("Temporary files cleaned up")


def main():
    """Main function to run the icon setup"""
    print("Setting up icons for Cabplanner...")

    create_icon_directory()
    temp_dir = download_and_extract_icons()

    if temp_dir:
        process_icons(temp_dir)
        cleanup(temp_dir)
        print(f"Icons have been set up successfully in: {ICON_DIR}")
    else:
        print("Failed to download or extract icons")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
