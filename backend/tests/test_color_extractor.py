"""color_extractor.py 단위 테스트."""

import numpy as np
import pytest
from PIL import Image

from backend.scripts.color_extractor import (
    extract_dominant_colors,
    hex_to_rgb,
    map_color_to_tone,
    map_colors_to_tone,
    rgb_distance,
    rgb_to_hex,
)


class TestColorConversion:
    def test_hex_to_rgb(self):
        assert hex_to_rgb("#FF6B6B") == [255, 107, 107]

    def test_hex_to_rgb_no_hash(self):
        assert hex_to_rgb("000000") == [0, 0, 0]

    def test_rgb_to_hex(self):
        assert rgb_to_hex([255, 107, 107]) == "#FF6B6B"

    def test_rgb_to_hex_black(self):
        assert rgb_to_hex([0, 0, 0]) == "#000000"


class TestRgbDistance:
    def test_same_color(self):
        assert rgb_distance([100, 100, 100], [100, 100, 100]) == 0.0

    def test_black_white(self):
        d = rgb_distance([0, 0, 0], [255, 255, 255])
        assert abs(d - 441.67) < 1  # sqrt(3 * 255^2)

    def test_symmetry(self):
        d1 = rgb_distance([10, 20, 30], [40, 50, 60])
        d2 = rgb_distance([40, 50, 60], [10, 20, 30])
        assert d1 == d2


class TestExtractDominantColors:
    def test_solid_red_image(self):
        img = Image.new("RGB", (100, 100), (255, 0, 0))
        colors = extract_dominant_colors(img, n_colors=1)
        assert len(colors) == 1
        assert colors[0]["rgb"][0] > 200  # 빨간색 채널 높음
        assert abs(colors[0]["ratio"] - 1.0) < 0.01

    def test_two_color_image(self):
        img = Image.new("RGB", (100, 100))
        pixels = img.load()
        for x in range(100):
            for y in range(50):
                pixels[x, y] = (255, 0, 0)
            for y in range(50, 100):
                pixels[x, y] = (0, 0, 255)
        colors = extract_dominant_colors(img, n_colors=2)
        assert len(colors) == 2
        assert abs(colors[0]["ratio"] - 0.5) < 0.15

    def test_returns_hex(self):
        img = Image.new("RGB", (50, 50), (128, 64, 32))
        colors = extract_dominant_colors(img, n_colors=1)
        assert colors[0]["hex"].startswith("#")
        assert len(colors[0]["hex"]) == 7


class TestMapColorToTone:
    def test_coral_maps_to_spring(self):
        tone, dist = map_color_to_tone([255, 127, 80])  # 코랄
        assert "spring" in tone

    def test_navy_maps_to_winter_deep(self):
        tone, dist = map_color_to_tone([0, 0, 128])  # 네이비
        assert "winter_cool_deep" == tone or "deep" in tone

    def test_lavender_maps_to_summer(self):
        tone, dist = map_color_to_tone([230, 230, 250])  # 라벤더
        assert "summer" in tone or "winter" in tone  # 쿨 톤

    def test_distance_is_nonnegative(self):
        _, dist = map_color_to_tone([100, 100, 100])
        assert dist >= 0


class TestMapColorsToTone:
    def test_single_color(self):
        colors = [{"rgb": [255, 203, 164], "ratio": 1.0}]  # 피치
        tone, compat = map_colors_to_tone(colors)
        assert tone != ""
        assert "spring" in tone

    def test_weighted_mapping(self):
        colors = [
            {"rgb": [0, 0, 0], "ratio": 0.1},       # 블랙 (소량)
            {"rgb": [255, 107, 107], "ratio": 0.9},   # 코랄 (대부분)
        ]
        tone, _ = map_colors_to_tone(colors)
        assert "spring" in tone  # 코랄이 지배적

    def test_empty_colors(self):
        tone, compat = map_colors_to_tone([])
        assert tone == ""
        assert compat == []
