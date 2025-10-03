"""
Centralne miejsce dla definicji kolorów używanych w całej aplikacji.
"""

# Mapowanie polskich nazw kolorów na kody hex
CABINET_COLORS = {
    # Kolory podstawowe
    "Biały": "#FFFFFF",
    "Czarny": "#000000",
    "Szary": "#808080",
    "Brązowy": "#8B4513",
    "Orzech": "#A0522D",
    "Niebieski": "#4169E1",
    # Kolory drewniane
    "Dąb": "#C2B280",  # jasny beżowo-brązowy
    "Dąb Sonoma": "#D2B48C",  # klasyczny meblowy kolor
    "Dąb Artisan": "#A17C5B",
    "Dąb Craft": "#C49E70",
    "Dąb Bielony": "#E3D9C7",
    "Jesion": "#D7B98E",
    "Buk": "#DEB887",
    "Olcha": "#C08A4D",
    "Wenge": "#4B3621",
    # Kolory nowoczesne
    "Antracyt": "#2F4F4F",
    "Grafit": "#3B3B3B",
    "Kremowy": "#FFFDD0",
    "Beżowy": "#F5F5DC",
    # Kolory dodatkowe
    "Zielony": "#228B22",
    "Czerwony": "#B22222",
    "Granatowy": "#000080",
}

# Problemy kodowania - mapowania dla różnych wariantów zapisu
ENCODING_VARIANTS = {
    # cp1250 encoding issues
    "Bia�y": "Biały",
    "Br�zowy": "Brązowy",
    "D�b": "Dąb",
    "Be¿owy": "Beżowy",
    "Be¿owa": "Beżowy",
    "D�b Sonoma": "Dąb Sonoma",
    "D�b Artisan": "Dąb Artisan",
    "D�b Craft": "Dąb Craft",
    "D�b Bielony": "Dąb Bielony",
    "Jesio�": "Jesion",
    "Wêngê": "Wenge",
    "Wêngé": "Wenge",
    # other encoding issues
    "Bia³y": "Biały",
    "Br¹zowy": "Brązowy",
    "D¹b": "Dąb",
    "Be³owy": "Beżowy",
    "D¹b Sonoma": "Dąb Sonoma",
    "D¹b Artisan": "Dąb Artisan",
    "D¹b Craft": "Dąb Craft",
    "D¹b Bielony": "Dąb Bielony",
    "Jesio¬": "Jesion",
    # Odmiany żeńskie
    "Zielona": "Zielony",
    "Czerwona": "Czerwony",
    "Szara": "Szary",
    "Czarna": "Czarny",
    "Bia³a": "Biały",
    "Bia�a": "Biały",
}

# Połączone mapowanie - wszystkie warianty na kody hex
COLOR_MAP = {}
COLOR_MAP.update(CABINET_COLORS)

# Dodaj mapowania dla problemów kodowania
for variant, canonical in ENCODING_VARIANTS.items():
    if canonical in CABINET_COLORS:
        COLOR_MAP[variant] = CABINET_COLORS[canonical]

# Lista kolorów do wyświetlenia w GUI (najczęściej używane)
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


# Funkcja pomocnicza do konwersji nazw kolorów na kody hex
def get_color_hex(color_name: str) -> str:
    """Konwertuje nazwę koloru na kod hex, obsługując problemy kodowania."""
    if not color_name:
        return "#FFFFFF"  # domyślnie biały

    # Spróbuj znaleźć w mapowaniu
    hex_color = COLOR_MAP.get(color_name)
    if hex_color:
        return hex_color

    # Jeśli to już kod hex, zwróć bez zmian
    if color_name.startswith("#"):
        return color_name

    # Fallback na biały
    return "#FFFFFF"
