"""
Centralne miejsce dla definicji kolorow uzywanych w GUI.
"""

# Mapowanie polskich nazw kolorow na kody HEX (fallback statyczny).
CABINET_COLORS = {
    "Bialy": "#FFFFFF",
    "Biały": "#FFFFFF",
    "Czarny": "#000000",
    "Szary": "#808080",
    "Brazowy": "#8B4513",
    "Brązowy": "#8B4513",
    "Orzech": "#A0522D",
    "Niebieski": "#4169E1",
    "Dab": "#C2B280",
    "Dąb": "#C2B280",
    "Dab Sonoma": "#D2B48C",
    "Dąb Sonoma": "#D2B48C",
    "Dab Artisan": "#A17C5B",
    "Dąb Artisan": "#A17C5B",
    "Dab Craft": "#C49E70",
    "Dąb Craft": "#C49E70",
    "Dab Bielony": "#E3D9C7",
    "Dąb Bielony": "#E3D9C7",
    "Jesion": "#D7B98E",
    "Buk": "#DEB887",
    "Olcha": "#C08A4D",
    "Wenge": "#4B3621",
    "Antracyt": "#2F4F4F",
    "Grafit": "#3B3B3B",
    "Kremowy": "#FFFDD0",
    "Bezowy": "#F5F5DC",
    "Beżowy": "#F5F5DC",
    "Zielony": "#228B22",
    "Czerwony": "#B22222",
    "Granatowy": "#000080",
}

# Problemy kodowania - mapowania dla wariantow zapisu.
ENCODING_VARIANTS = {
    "Bia�y": "Biały",
    "Br�zowy": "Brązowy",
    "D�b": "Dąb",
    "D�b Sonoma": "Dąb Sonoma",
    "D�b Artisan": "Dąb Artisan",
    "D�b Craft": "Dąb Craft",
    "D�b Bielony": "Dąb Bielony",
    "Be�owy": "Beżowy",
    "BiaÂły": "Biały",
    "BrÂązowy": "Brązowy",
    "DÂąb": "Dąb",
    "DÂąb Sonoma": "Dąb Sonoma",
    "DÂąb Artisan": "Dąb Artisan",
    "DÂąb Craft": "Dąb Craft",
    "DÂąb Bielony": "Dąb Bielony",
    "BeÂżowy": "Beżowy",
    "Zielona": "Zielony",
    "Czerwona": "Czerwony",
    "Szara": "Szary",
    "Czarna": "Czarny",
    "Biała": "Biały",
    "Bia�a": "Biały",
}

# Połączone mapowanie - wszystkie warianty na HEX.
COLOR_MAP = {}
COLOR_MAP.update(CABINET_COLORS)
for variant, canonical in ENCODING_VARIANTS.items():
    if canonical in CABINET_COLORS:
        COLOR_MAP[variant] = CABINET_COLORS[canonical]

# Runtime mapowanie z bazy (system + user).
RUNTIME_COLOR_MAP: dict[str, str] = {}

# Lista kolorow do wyswietlenia w GUI, gdy brak historii.
POPULAR_COLORS = [
    "Biały",
    "Czarny",
    "Szary",
    "Brązowy",
    "Orzech",
    "Niebieski",
    "Dąb",
    "Dąb Sonoma",
    "Dąb Artisan",
    "Antracyt",
    "Grafit",
    "Kremowy",
    "Beżowy",
    "Wenge",
    "Jesion",
    "Buk",
]


def _normalize_hex(value: str) -> str:
    value = (value or "").strip().upper()
    if not value.startswith("#"):
        return value
    if len(value) == 4:
        return "#" + value[1] * 2 + value[2] * 2 + value[3] * 2
    return value


def register_runtime_colors(color_map: dict[str, str]) -> None:
    """Rejestruje mapowanie kolorów dostarczone z bazy danych."""
    RUNTIME_COLOR_MAP.clear()
    for name, hex_code in (color_map or {}).items():
        if not name:
            continue
        RUNTIME_COLOR_MAP[name] = _normalize_hex(hex_code)


def _casefold_lookup(color_name: str, mapping: dict[str, str]) -> str | None:
    normalized = color_name.casefold()
    for key, value in mapping.items():
        if key.casefold() == normalized:
            return value
    return None


def get_color_hex(color_name: str) -> str:
    """Konwertuje nazwę koloru na kod HEX."""
    if not color_name:
        return "#FFFFFF"

    name = color_name.strip()

    # Runtime mapowanie z bazy ma wyzszy priorytet.
    if name in RUNTIME_COLOR_MAP:
        return RUNTIME_COLOR_MAP[name]

    # Statyczne mapowania.
    if name in COLOR_MAP:
        return COLOR_MAP[name]

    # Case-insensitive lookup.
    runtime_casefold = _casefold_lookup(name, RUNTIME_COLOR_MAP)
    if runtime_casefold:
        return runtime_casefold

    static_casefold = _casefold_lookup(name, COLOR_MAP)
    if static_casefold:
        return static_casefold

    # Jeśli to juz HEX, zwroc bez zmian (z normalizacja #RGB -> #RRGGBB).
    if name.startswith("#"):
        normalized = _normalize_hex(name)
        if len(normalized) == 7:
            return normalized

    return "#FFFFFF"
