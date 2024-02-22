# util/charts.py

colorPalette = ["#fd7e14", "#ffc107", "#6f42c1", "#0dcaf0", "#fab1a0", "#ff7675", "#198754"]
colorPrimary, colorOwed, colorOwe = "#000", "#20c997", "#dc3545"


def generate_color_palette(amount):
    palette = []

    i = 0
    while i < len(colorPalette) and len(palette) < amount:
        palette.append(colorPalette[i])
        i += 1
        if i == len(colorPalette) and len(palette) < amount:
            i = 0

    return palette