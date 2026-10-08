# -*- coding: utf-8 -*-
"""合并各批翻译 -> translations.json
含：
  1) 校验（键集一致、空值、真实换行、&br;/数字/换行转义一致性、异常长度）
  2) 确定性归一化（航班标题、塔台前缀、跑道句式）——保证跨 51 个合同完全一致
  3) 输出复核样本供人工过目
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

WORK = Path(os.environ.get('GAP_WORK', r'K:\AI代码\.gap_loc_work'))
BATCH = WORK / 'batches'


def load(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))


# ---------- 确定性修正（人工复核后固定下来） ----------
EXACT_FIX = {
    '#loc_GAP_shared_Your_craft_must': '你的载具必须',
    '#loc_GAP_shared_not_have_any_solid_rocket_motors': '不安装任何固体火箭发动机',
    '#loc_GAP_shared_start_from_KSC': '从 KSC 起飞',
    '#loc_GAP_shared_KSC_Coast_Guard_Our_motto_is_Always_Ready_Kemper':
        'KSC 海岸警卫队：我们的格言是时刻准备着——Kemper Keratus！',
}
REGEX_FIX = [
    (re.compile(r'^在 (\S+) 到 (\S+) 之间飞行$'), r'在 \1 至 \2 之间飞行'),
    (re.compile(r'^飞行速度超过 (.+)$'), r'以超过 \1 的速度飞行'),
    (re.compile(r'^爬升到 (.+)$'), r'飞到 \1'),
    (re.compile(r'行政大楼'), '管理大厦'),
]
# 市场合同完成提示：14 个文件同一句式，统一措辞
MARKET_PREFIX = '零件移交完成。&br;&br;你的机构现在可以使用以下内容：'
MARKET_RE = re.compile(r'(&br;&br;- .*?)(&br;&br;Enjoy the new parts?!)$')
# 市场简报"…technology is at your fingertips!"统一模板
TECH_ZH = {
    'Structural and mobility': '结构与机动技术',
    'Command seat': '指令座椅技术',
    'Decoupler': '分离器技术',
    'Electric vehicle': '电动载具技术',
    'Propeller engine': '螺旋桨发动机技术',
    'Flight control': '飞行控制技术',
    'Flight engine': '飞行发动机技术',
}
FINGERTIP_RE = re.compile(r'^(.+?) technology is at your fingertips!')

# 英文完全相同时统一采用的译法：代表键 -> 译文（会应用到所有英文与之相同的键）
CANON_TEXT = {
    '#loc_GAP_Airline_Flight_101_completedMessage_s3':
        '&br;&br;KSC 航空感谢您搭乘本次航班，与我们一同翱翔在友好的天空。',
    '#loc_GAP_Airline_Flight_101_synopsis':
        '这是一趟定期往返航班，无需手动换乘乘客。KSC 航空的定期航班服务合同按乘客人数计费。',
    '#loc_GAP_GAP_Ford_CubicStrut_notes':
        '合同一经接受，该零件将立即向你的机构开放。',
}
# 同组内以代表键的译文为准（代表键, [需要统一的键...]）
CANON_FROM = [
    ('#loc_GAP_Airline_Flight_124_genericDescription',
     ['#loc_GAP_Airline_Flight_122_genericDescription']),
    ('#loc_GAP_Airline_Flight_101_description_s1',
     ['#loc_GAP_Airline_Flight_102_description_s1']),
    ('#loc_GAP_Airline_Flight_101_genericDescription',
     ['#loc_GAP_Airline_Flight_102_genericDescription']),
    ('#loc_GAP_Airline_Flight_101_description_s2',
     ['#loc_GAP_Airline_Flight_102_description_s2',
      '#loc_GAP_Airline_Flight_103_description_s2']),
    ('#loc_GAP_Wright_Speed100_synopsis', ['#loc_GAP_Wright_Speed220_synopsis']),
    ('#loc_GAP_Airline_Flight_320_description_s1',
     ['#loc_GAP_Airline_Flight_322_description_s1',
      '#loc_GAP_Airline_Flight_324_description_s1']),
    ('#loc_GAP_Airline_Flight_320_genericDescription',
     ['#loc_GAP_Airline_Flight_322_genericDescription',
      '#loc_GAP_Airline_Flight_324_genericDescription']),
    ('#loc_GAP_Airline_Flight_201_description_s1',
     ['#loc_GAP_Airline_Flight_202_description_s1',
      '#loc_GAP_Airline_Flight_203_description_s1']),
    ('#loc_GAP_Airline_Flight_201_genericDescription',
     ['#loc_GAP_Airline_Flight_202_genericDescription',
      '#loc_GAP_Airline_Flight_203_genericDescription']),
]


def synopsis_fix(en, zh):
    m = FINGERTIP_RE.match(en)
    if not m:
        return zh, None
    tech = TECH_ZH.get(m.group(1))
    if not tech:
        return zh, '未收录技术名: ' + m.group(1)
    part = '原型零件' if 'prototype part' in en else '原型'
    new = tech + '触手可及！只要承担我们首批生产的成本，这个' + part + '就归您了！'
    return new, ('市场简报统一句式' if new != zh else None)



def market_fix(en, zh):
    if not en.startswith('Part transfer complete.'):
        return zh, None
    m = MARKET_RE.search(en)
    if not m:
        return zh, None
    plural = 'new parts!' in en
    new = (MARKET_PREFIX + m.group(1) + '&br;&br;好好享受'
           + ('这些' if plural else '这个') + '新零件吧！')
    return new, ('市场完成提示统一' if new != zh else None)


def apply_fixes(key, en, zh, seg_no=0):
    notes = []
    zh, n = market_fix(en, zh)
    if n:
        notes.append(n)
    if key in EXACT_FIX:
        if EXACT_FIX[key] != zh:
            notes.append('人工固定措辞')
        zh = EXACT_FIX[key]
    zh, n = synopsis_fix(en, zh)
    if n:
        notes.append(n)
    for pat, rep in REGEX_FIX:
        zh2 = pat.sub(rep, zh)
        if zh2 != zh:
            notes.append('措辞统一')
        zh = zh2
    # 片段译文不应以空格开头（中文不需要分词空格；&br;/\n 开头不受影响）
    if seg_no and zh.startswith(' '):
        zh = zh.lstrip(' ')
        notes.append('片段去前导空格')
    return zh, notes


def consistency_report(en_map, tr, meta):
    """英文完全相同（仅忽略首尾空白）的键必须有一致译文；
    句末标点不同（如 Mach 2! 与 Mach 2）不算不一致，故按精确英文分组。"""

    groups = defaultdict(list)
    for k in en_map:
        if k in tr:
            groups[en_map[k].strip()].append(k)
    lines = []
    bad = 0
    for g, ks in sorted(groups.items()):
        if len(ks) < 2:
            continue
        zhs = {tr[k] for k in ks}
        if len(zhs) > 1:
            bad += 1
            lines.append('--- 英文完全相同但译文不同（%d 个键）EN: %s' % (len(ks), g[:90]))
            for k in ks:
                lines.append('      %-70s -> %s' % (k, tr[k][:70]))
    return bad, lines



FLIGHT_TITLE = re.compile(r'^Flight (\d+) - Crew: (\d+) Passengers: ([0-9\-]*)\s*$')
ATC_PREFIX = [
    (re.compile(r'^(?:KSC\s*(?:空中交通管制|ATC|塔台))\s*[:：]\s*'), 'KSC 塔台：'),
    (re.compile(r'^(?:小岛|岛屿)\s*(?:空中交通管制|ATC|塔台)\s*[:：]\s*'), '小岛塔台：'),
    (re.compile(r'^(?:太空中心)\s*(?:空中交通管制|ATC|塔台)\s*[:：]\s*'), '太空中心塔台：'),
]
LAND_ON = [
    (re.compile(r'降落于小岛机场\s*(\d+)'), r'在小岛机场 \1 号跑道降落'),
    (re.compile(r'降落于跑道\s*(\d+)'), r'在 \1 号跑道降落'),
    (re.compile(r'已获准降落于跑道\s*(\d+)'), r'已获准在 \1 号跑道降落'),
]


def normalize(key, en, zh):
    """返回 (zh, 说明列表)"""
    notes = []
    m = FLIGHT_TITLE.match(en.strip())
    if m and (key.endswith('_genericTitle') or key.endswith('_title_s1')):
        num, crew, pax = m.group(1), m.group(2), m.group(3)
        new = '%s 号航班 － 机组 %s 人，乘客 %s' % (num, crew, pax)
        if m.group(3) == '':
            new = new + ' '
        if new != zh:
            notes.append('航班标题归一化')
        zh = new
    if '_text' in key:
        for pat, rep in ATC_PREFIX:
            if pat.match(zh):
                zh2 = pat.sub(rep, zh, count=1)
                if zh2 != zh:
                    notes.append('塔台前缀归一化')
                zh = zh2
                break
        for pat, rep in LAND_ON:
            zh2 = pat.sub(rep, zh)
            if zh2 != zh:
                notes.append('跑道句式归一化')
            zh = zh2
    return zh, notes


def main():
    en_map = load(WORK / 'en_values.json')
    units = load(WORK / 'units.json')
    meta = {}
    for u in units:
        meta.setdefault(u['key'], u)
    keys = set(en_map)

    files = sorted(BATCH.glob('batch_*.zh.json'))
    tr, dup, bad = {}, [], []
    for f in files:
        try:
            data = load(f)
        except Exception as e:
            bad.append('%s JSON 解析失败: %s' % (f.name, e))
            continue
        for k, v in data.items():
            if k in tr and tr[k] != v:
                dup.append('%s 重复且不一致: %s' % (f.name, k))
            tr[k] = v

    issues = []
    missing = sorted(keys - set(tr))
    extra = sorted(set(tr) - keys)
    if missing:
        issues.append('缺失 %d 个键（前 10）: %s' % (len(missing), missing[:10]))
    if extra:
        issues.append('多余 %d 个键（前 10）: %s' % (len(extra), extra[:10]))

    norm_count = Counter()
    for k in sorted(keys & set(tr)):
        en, zh = en_map[k], tr[k]
        u = meta.get(k, {})
        # 规则检查
        if not zh.strip():
            issues.append('空译文: %s' % k)
            continue
        if '\n' in zh or '\r' in zh:
            issues.append('译文含真实换行: %s' % k)
            zh = zh.replace('\r\n', '\\n').replace('\n', '\\n').replace('\r', '\\n')
        if zh.lstrip().startswith('#'):
            issues.append('译文以 # 开头: %s' % k)
        if '=' in zh:
            issues.append('译文含 = 号: %s' % k)
        if en.count('&br;') != zh.count('&br;'):
            issues.append('&br; 数量不一致 (%d vs %d): %s'
                          % (en.count('&br;'), zh.count('&br;'), k))
        if en.count('\\n') != zh.count('\\n'):
            issues.append('\\n 数量不一致 (%d vs %d): %s'
                          % (en.count('\\n'), zh.count('\\n'), k))
        ed = re.findall(r'\d+', en)
        if ed and not re.findall(r'\d', zh):
            issues.append('英文有数字但译文没有: %s | %s' % (k, en[:50]))
        if len(zh) > max(40, len(en) * 3):
            issues.append('译文异常长 (%d vs %d): %s' % (len(zh), len(en), k))
        zh, notes = normalize(k, en, zh)
        zh, notes2 = apply_fixes(k, en, zh, u.get('seg_no', 0))
        for n in notes + notes2:
            norm_count[n] += 1
        tr[k] = zh

    # 同英文统一译法（代表键 -> 所有英文相同的键；再按组复制）
    en2canon = {}
    for rep, txt in CANON_TEXT.items():
        if rep in en_map:
            en2canon[en_map[rep].strip()] = txt
    for k in sorted(keys & set(tr)):
        c = en2canon.get(en_map[k].strip())
        if c is not None and tr[k] != c:
            tr[k] = c
            norm_count['同英文统一译法'] += 1
    for rep, members in CANON_FROM:
        if rep not in tr:
            issues.append('统一译法代表键缺失: %s' % rep)
            continue
        for m in members:
            if m in tr and tr[m] != tr[rep]:
                tr[m] = tr[rep]
                norm_count['同组复制译法'] += 1

    (WORK / 'translations.json').write_text(
        json.dumps(tr, ensure_ascii=False, indent=1), encoding='utf-8')

    bad, clines = consistency_report(en_map, tr, meta)
    (WORK / 'consistency.txt').write_text(
        '\n'.join(['=== 同一英文多译法体检：%d 组不一致 ===' % bad, ''] + clines),
        encoding='utf-8')

    # 复核样本
    sample_keys = []
    for k in sorted(keys):
        u = meta.get(k, {})
        if u.get('shared'):
            sample_keys.append(k)
    for f in sorted({meta[k]['file'] for k in keys if k in meta}):
        cand = [k for k in sorted(keys) if meta.get(k, {}).get('file') == f]
        sample_keys += cand[:1]
    sample_keys = list(dict.fromkeys(sample_keys))
    L = ['=== 复核样本（共享键全部 + 每文件 1 条）共 %d ===' % len(sample_keys), '']
    for k in sample_keys:
        u = meta.get(k, {})
        L.append('%s   [%s/%s]' % (k, u.get('file', '?'), u.get('field', '?')))
        L.append('  EN: %s' % en_map[k].replace('\n', '\\n')[:150])
        if u.get('seg_no'):
            L.append('  ctx: %s' % (u.get('segments') and 'seg%d' % u['seg_no'] or ''))
        L.append('  ZH: %s' % tr.get(k, '<缺失>').replace('\n', '\\n')[:150])
        L.append('')
    (WORK / 'review_sample.txt').write_text('\n'.join(L), encoding='utf-8')

    rep = ['=== 合并结果 ===',
           '  批次文件: %d ; 译文键: %d / %d' % (len(files), len(tr), len(keys)),
           '  确定性归一化/修正: %s' % dict(norm_count),
           '  同一英文多译法不一致组: %d（详见 consistency.txt）' % bad,
           '  问题: %d' % len(issues)]
    rep += ['  ' + s for s in issues[:60]]
    (WORK / 'merge_report.txt').write_text('\n'.join(rep), encoding='utf-8')
    print('\n'.join(rep))


if __name__ == '__main__':
    main()
