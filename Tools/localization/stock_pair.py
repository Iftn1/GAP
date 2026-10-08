# -*- coding: utf-8 -*-
"""用官方 en-us / zh-cn 词典配对，为 GAP 术语表与可复用译名提供依据
词典来源：
  Squad       : LanguageChanger/Languages/Squad/{en-us,zh-cn}/dictionary.cfg
  Serenity    : LanguageChanger/Languages/Serenity/en-us  +  SquadExpansion/Serenity/Localization
"""
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from verify import read_loc  # noqa: E402

GD = Path(os.environ.get('KSP_GAMEDATA', r'G:\Kerbal Space Program\GameData'))
WORK = Path(os.environ.get('GAP_WORK', r'K:\AI代码\.gap_loc_work'))

SOURCES = [
    ('Squad', GD / 'LanguageChanger/Languages/Squad/en-us/dictionary.cfg',
     GD / 'LanguageChanger/Languages/Squad/zh-cn/dictionary.cfg'),
    ('Serenity', GD / 'LanguageChanger/Languages/Serenity/en-us/dictionary.cfg',
     GD / 'SquadExpansion/Serenity/Localization/dictionary.cfg'),
]

TERMS = [
    'Island Airfield', 'Dessert Airfield', 'Woomerang Launch Site',
    'Baikerbanur LaunchPad', 'Mahi Mahi Launch Site', 'Kerbal Space Center',
    'Runway', 'Spaceplane Hangar', 'Vehicle Assembly Building',
    'Mission Control', 'Tracking Station', 'Astronaut Complex', 'Launch Pad',
    'Flag Pole', 'Administration Building', 'Research and Development',
    'Kerbin', 'Kerbal', 'Pilot', 'Engineer', 'Scientist', 'Tourist',
    'Recover', 'Funds', 'Reputation', 'Science', 'Prestige', 'Trivial',
    'Recovery', 'Waypoint', 'Parachute', 'EVA', 'Landed', 'Splashed',
    'Flying', 'Sub-orbital', 'Orbit', 'Docking port', 'Fuel Tank',
]

L = []


def merge_en_zh():
    en_all, zh_all = {}, {}
    for name, enp, zhp in SOURCES:
        en, _ = read_loc(enp)
        zh, _ = read_loc(zhp)
        e = en.get('en-us', {})
        z = zh.get('zh-cn', {})
        L.append('%s: en-us %d 键, zh-cn %d 键, 交集 %d'
                 % (name, len(e), len(z), len(set(e) & set(z))))
        en_all.update(e)
        zh_all.update(z)
    return en_all, zh_all


def main():
    en_all, zh_all = merge_en_zh()
    # 官方英文值 -> 官方中文值
    v2v = defaultdict(set)
    for k, v in en_all.items():
        if k in zh_all:
            v2v[v.strip()].add(zh_all[k].strip())

    L.append('')
    L.append('=== 术语表：官方译名 ===')
    for t in TERMS:
        zh = v2v.get(t)
        L.append('  %-26s -> %s' % (t, ' / '.join(sorted(zh)) if zh else '(官方词典无精确匹配)'))

    # GAP 的英文值里能精确命中官方词典的
    en_map = json.loads((WORK / 'en_values.json').read_text(encoding='utf-8'))
    L.append('')
    L.append('=== GAP 值 与官方词典精确匹配（可直接采用官方译名）===')
    hits = 0
    for k, v in sorted(en_map.items()):
        zh = v2v.get(v.strip())
        if zh:
            hits += 1
            L.append('  %s' % k)
            L.append('      EN : %s' % v.strip()[:90])
            L.append('      官方: %s' % ' / '.join(sorted(zh))[:90])
    L.append('  精确命中: %d / %d' % (hits, len(en_map)))

    # 设施名等长词的包含匹配（辅助）
    L.append('')
    L.append('=== 关键设施名的官方译名（含包含匹配）===')
    for t in ['Island Airfield', 'Dessert Airfield', 'Woomerang', 'Baikerbanur',
              'Mahi Mahi', 'Inland Kerbal Space Center', 'Kerbal Space Center']:
        found = []
        for v, zs in v2v.items():
            if t.lower() in v.lower() and len(v) < 70:
                found.append((v, sorted(zs)[0]))
        L.append('  [%s]' % t)
        for v, z in found[:6]:
            L.append('      %-42s -> %s' % (v, z))

    txt = '\n'.join(L)
    (WORK / 'stock_pair.txt').write_text(txt, encoding='utf-8')
    print(txt)


if __name__ == '__main__':
    main()
