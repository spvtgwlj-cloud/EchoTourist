#!/usr/bin/env python3
"""生成景点占位 SVG 图片（北京/南京/西安各 15 个）。"""

import os

OUTPUT = os.path.join(os.path.dirname(__file__), "../src/frontend/public/images/attractions")

# (slug, name_zh, name_en, color1, color2, icon)
ATTRACTIONS = [
    # ═══ 北京 ═══
    ("forbidden-city",            "故宫博物院",          "Forbidden City",        "#c0392b", "#e74c3c", "🏯"),
    ("badaling-great-wall",       "八达岭长城",          "Badaling Great Wall",   "#2c3e50", "#34495e", "🧱"),
    ("temple-of-heaven",          "天坛公园",            "Temple of Heaven",      "#2980b9", "#3498db", "🏛️"),
    ("summer-palace",             "颐和园",              "Summer Palace",         "#16a085", "#1abc9c", "🌊"),
    ("ming-tombs",                "明十三陵",            "Ming Tombs",            "#7f8c8d", "#95a5a6", "🗿"),
    ("prince-gong-mansion",       "恭王府",              "Prince Gong Mansion",   "#8e44ad", "#9b59b6", "🌸"),
    ("olympic-park",              "奥林匹克公园",        "Olympic Park",          "#f39c12", "#f1c40f", "🏟️"),
    ("old-summer-palace",         "圆明园",              "Old Summer Palace",     "#7f8c8d", "#95a5a6", "🏛️"),
    ("mutianyu-great-wall",       "慕田峪长城",          "Mutianyu Great Wall",   "#8e44ad", "#9b59b6", "🏔️"),
    ("beihai-park",               "北海公园",            "Beihai Park",           "#16a085", "#1abc9c", "🌿"),
    ("lama-temple",               "雍和宫",              "Lama Temple",           "#c0392b", "#d35400", "🙏"),
    ("national-museum",           "中国国家博物馆",      "National Museum",       "#2c3e50", "#34495e", "🏛️"),
    ("jingshan-park",             "景山公园",            "Jingshan Park",         "#27ae60", "#2ecc71", "🌳"),
    ("shichahai",                 "什刹海",              "Shichahai",             "#2980b9", "#3498db", "🚣"),
    ("fragrant-hills",            "香山公园",            "Fragrant Hills Park",   "#e74c3c", "#c0392b", "🍁"),
    # ═══ 南京 ═══
    ("sun-yat-sen-mausoleum",     "中山陵",              "Sun Yat-sen Mausoleum", "#2980b9", "#3498db", "🏛️"),
    ("confucius-temple-nanjing",  "夫子庙秦淮河",        "Confucius Temple",      "#c0392b", "#e74c3c", "🏮"),
    ("ming-xiaoling",             "明孝陵",              "Ming Xiaoling",         "#7f8c8d", "#95a5a6", "🗿"),
    ("nanjing-museum",            "南京博物院",          "Nanjing Museum",        "#8e44ad", "#9b59b6", "🏺"),
    ("xuanwu-lake",               "玄武湖公园",          "Xuanwu Lake Park",      "#16a085", "#1abc9c", "🌊"),
    ("presidential-palace",       "总统府",              "Presidential Palace",   "#2c3e50", "#34495e", "🏛️"),
    ("qinhuai-river",             "秦淮河",              "Qinhuai River",         "#c0392b", "#d35400", "🌙"),
    ("jiming-temple",             "鸡鸣寺",              "Jiming Temple",         "#f39c12", "#e67e22", "🌸"),
    ("purple-mountain",           "紫金山",              "Purple Mountain",       "#8e44ad", "#9b59b6", "⛰️"),
    ("yangtze-river-bridge",      "南京长江大桥",        "Yangtze River Bridge",  "#2c3e50", "#34495e", "🌉"),
    ("memorial-hall-nanjing",     "南京大屠杀纪念馆",    "Memorial Hall",         "#7f8c8d", "#95a5a6", "🕊️"),
    ("zhan-yuan-garden",          "瞻园",                "Zhan Yuan Garden",      "#27ae60", "#2ecc71", "🌿"),
    ("zhonghua-gate",             "中华门",              "Zhonghua Gate",         "#2c3e50", "#34495e", "🏰"),
    ("linggu-temple",             "灵谷寺",              "Linggu Temple",         "#2980b9", "#3498db", "🙏"),
    ("nanjing-city-wall",         "南京城墙",            "Nanjing City Wall",     "#7f8c8d", "#95a5a6", "🧱"),
    # ═══ 西安 ═══
    ("terracotta-warriors",       "兵马俑博物馆",        "Terracotta Warriors",   "#c0392b", "#e74c3c", "⚱️"),
    ("giant-wild-goose-pagoda",   "大雁塔",              "Giant Wild Goose Pagoda", "#2980b9", "#3498db", "🗼"),
    ("huaqing-palace",            "华清宫",              "Huaqing Palace",        "#e67e22", "#f39c12", "🏯"),
    ("xian-city-wall",            "西安城墙",            "Xi'an City Wall",       "#2c3e50", "#34495e", "🧱"),
    ("shaanxi-history-museum",    "陕西历史博物馆",      "Shaanxi History Museum","#8e44ad", "#9b59b6", "🏺"),
    ("muslim-quarter",            "回民街",              "Muslim Quarter",        "#c0392b", "#d35400", "🍜"),
    ("bell-drum-towers",          "钟鼓楼",              "Bell & Drum Towers",    "#2c3e50", "#34495e", "🕰️"),
    ("small-wild-goose-pagoda",   "小雁塔",              "Small Wild Goose Pagoda", "#16a085", "#1abc9c", "🗼"),
    ("tang-paradise",             "大唐不夜城",          "Tang Paradise",         "#e74c3c", "#f39c12", "🌃"),
    ("lishan-mountain",           "骊山",                "Lishan Mountain",       "#27ae60", "#2ecc71", "⛰️"),
    ("famen-temple",              "法门寺",              "Famen Temple",          "#f39c12", "#e67e22", "🙏"),
    ("stele-forest",              "西安碑林",            "Stele Forest Museum",   "#7f8c8d", "#95a5a6", "📜"),
    ("daming-palace",             "大明宫遗址",          "Daming Palace",         "#c0392b", "#e74c3c", "🏛️"),
    ("huashan-mountain",          "华山",                "Huashan Mountain",      "#27ae60", "#2ecc71", "⛰️"),
    ("qin-shi-huang-mausoleum",   "秦始皇陵",            "Qin Shi Huang Mausoleum","#7f8c8d", "#95a5a6", "⚱️"),
]

def make_svg(name_zh, name_en, c1, c2, icon):
    # Multi-line safe wrappers for long names
    zh_words = name_zh
    en_words = name_en
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
  <text x="400" y="230" text-anchor="middle" font-size="96" fill="rgba(255,255,255,0.15)">{icon}</text>
  <text x="400" y="320" text-anchor="middle" font-family="system-ui,sans-serif" font-size="34" font-weight="bold" fill="white">{zh_words}</text>
  <text x="400" y="370" text-anchor="middle" font-family="system-ui,sans-serif" font-size="18" fill="rgba(255,255,255,0.7)">{en_words}</text>
  <text x="400" y="560" text-anchor="middle" font-family="system-ui,sans-serif" font-size="13" fill="rgba(255,255,255,0.35)">Echo Tours — Attraction Placeholder</text>
</svg>'''

os.makedirs(OUTPUT, exist_ok=True)

count = 0
for slug, zh, en, c1, c2, icon in ATTRACTIONS:
    svg = make_svg(zh, en, c1, c2, icon)
    svg_path = os.path.join(OUTPUT, f"{slug}.svg")
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg)
    count += 1
    print(f"  ✅ {slug}.svg — {zh}")

print(f"\n共生成 {count} 个景点 SVG 占位图到 {OUTPUT}")
