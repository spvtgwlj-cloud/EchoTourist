#!/usr/bin/env python3
"""生成旅游产品占位 SVG 图片。"""

import hashlib, os, textwrap

OUTPUT = os.path.join(os.path.dirname(__file__), "../src/frontend/public/images/tours")

IMAGES = [
    # (filename, label_zh, label_en, color1, color2, icon)
    ("forbidden-city-1", "故宫·太和殿", "Forbidden City", "#c0392b", "#e74c3c", "🏯"),
    ("forbidden-city-2", "故宫·金水桥", "Golden Water Bridge", "#d35400", "#e67e22", "🌉"),
    ("forbidden-city-3", "故宫·御花园", "Imperial Garden", "#27ae60", "#2ecc71", "🌿"),
    ("great-wall-1", "八达岭长城", "Great Wall", "#2c3e50", "#34495e", "🧱"),
    ("great-wall-2", "长城远景", "Great Wall Vista", "#1a252f", "#2c3e50", "⛰️"),
    ("mutianyu-1", "慕田峪长城", "Mutianyu Wall", "#8e44ad", "#9b59b6", "🏔️"),
    ("mutianyu-2", "慕田峪秋色", "Mutianyu Autumn", "#c0392b", "#d35400", "🍁"),
    ("temple-of-heaven-1", "天坛·祈年殿", "Temple of Heaven", "#2980b9", "#3498db", "🏛️"),
    ("summer-palace-1", "颐和园·佛香阁", "Summer Palace", "#16a085", "#1abc9c", "🌊"),
    ("summer-palace-2", "颐和园·长廊", "Long Corridor", "#27ae60", "#2ecc71", "🎨"),
    ("summer-palace-3", "十七孔桥", "17-Arch Bridge", "#2980b9", "#3498db", "🌉"),
    ("gong-mansion-1", "恭王府花园", "Prince Gong's Garden", "#8e44ad", "#9b59b6", "🌸"),
    ("olympic-1", "鸟巢体育场", "Bird's Nest", "#f39c12", "#f1c40f", "🏟️"),
    ("olympic-2", "水立方", "Water Cube", "#2980b9", "#3498db", "💧"),
    ("yuanmingyuan-1", "圆明园·大水法", "Old Summer Palace", "#7f8c8d", "#95a5a6", "🏛️"),
    ("ming-tombs-1", "明十三陵神道", "Ming Tombs Sacred Way", "#2c3e50", "#34495e", "🗿"),
    ("beijing-3day-1", "北京天际线", "Beijing Skyline", "#e74c3c", "#c0392b", "🌆"),
    ("beijing-3day-2", "北京烤鸭", "Peking Duck", "#d35400", "#e67e22", "🦆"),
    ("beijing-3day-3", "胡同文化", "Hutong Culture", "#16a085", "#1abc9c", "🏘️"),
    ("nanjing-1", "南京·中山陵", "Sun Yat-sen Mausoleum", "#2980b9", "#3498db", "🏛️"),
    ("xian-1", "兵马俑", "Terracotta Warriors", "#8e44ad", "#9b59b6", "⚱️"),
    ("xian-2", "西安古城墙", "Xi'an City Wall", "#2c3e50", "#34495e", "🧱"),
]

def make_svg(name, label_zh, label_en, c1, c2, icon):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600">
  <defs>
    <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:{c1};stop-opacity:1" />
      <stop offset="100%" style="stop-color:{c2};stop-opacity:1" />
    </linearGradient>
    <pattern id="dots" x="0" y="0" width="40" height="40" patternUnits="userSpaceOnUse">
      <circle cx="20" cy="20" r="1.5" fill="rgba(255,255,255,0.08)" />
    </pattern>
  </defs>
  <rect width="800" height="600" fill="url(#g)" />
  <rect width="800" height="600" fill="url(#dots)" />
  <text x="400" y="240" text-anchor="middle" font-size="96" fill="rgba(255,255,255,0.15)">{icon}</text>
  <text x="400" y="320" text-anchor="middle" font-family="system-ui,sans-serif" font-size="36" font-weight="bold" fill="white">{label_zh}</text>
  <text x="400" y="370" text-anchor="middle" font-family="system-ui,sans-serif" font-size="20" fill="rgba(255,255,255,0.7)">{label_en}</text>
  <text x="400" y="560" text-anchor="middle" font-family="system-ui,sans-serif" font-size="13" fill="rgba(255,255,255,0.35)">Echo Tours — Placeholder Image</text>
</svg>'''

os.makedirs(OUTPUT, exist_ok=True)
for name, zh, en, c1, c2, icon in IMAGES:
    svg = make_svg(name, zh, en, c1, c2, icon)
    # Save as .svg (proper format)
    svg_path = os.path.join(OUTPUT, f"{name}.svg")
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg)
    # Also save as .jpg for compatibility with existing seed data
    jpg_path = os.path.join(OUTPUT, f"{name}.jpg")
    with open(jpg_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"  ✅ {name}.svg + .jpg")

print(f"\n共生成 {len(IMAGES)} × 2 = {len(IMAGES)*2} 个文件到 {OUTPUT}")
