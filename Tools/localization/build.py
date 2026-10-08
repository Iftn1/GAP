# -*- coding: utf-8 -*-
"""GAP 汉化 - 阶段2（v2）：构建本地化后的 mod 树
输入: units.json / plan.json / en_values.json / translations.json(可选)
输出: <out>/ 与原 GAP 同构 + Localization/en-us.cfg + Localization/zh-cn.cfg
      build_report.txt / to_translate.json / shared_review.txt
用法: build.py [--out DIR] [--br newline|keep]
"""
import argparse
import json
import os
import re
import shutil
from collections import defaultdict
from pathlib import Path

GAP = Path(os.environ.get('GAP_SRC', r'K:\AI代码\GAP'))
WORK = Path(os.environ.get('GAP_WORK', r'K:\AI代码\.gap_loc_work'))
LINE_RE = re.compile(r'^(\s*)([^\s=]+)(\s*)=(\s*)(.*)$')


def load(name, default=None):
    p = WORK / name
    if not p.exists():
        if default is not None:
            return default
        raise SystemExit('缺少 %s' % p)
    return json.loads(p.read_text(encoding='utf-8'))


def esc(en, br):
    """本地化值转义：
      换行 -> \\n（&br; 策略 + 译文里可能出现的真实换行）
      双引号 -> \\"（依据 stock dictionary.cfg 的既有做法）
    """
    s = en.replace('&br;', '\\n') if br == 'newline' else en
    s = s.replace('\r\n', '\n').replace('\r', '\n').replace('\n', '\\n')
    return s.replace('"', '\\"')


def one_line(s, limit=100):
    s = s.replace('\r', ' ').replace('\n', '\\n')
    return s if len(s) <= limit else s[:limit - 1] + '…'


def br_display(s, br):
    """注释里展示英文时也套用同一换行策略，避免与 en-us 值不一致"""
    return s.replace('&br;', '\\n') if br == 'newline' else s


def apply_edits(rel, edits, out_path, br, issues):
    text = (GAP / rel).read_bytes().decode('utf-8-sig')
    eol = '\r\n' if '\r\n' in text else '\n'
    lines = [l[:-1] if l.endswith('\r') else l for l in text.split('\n')]

    by_line = defaultdict(list)
    for e in edits:
        by_line[e['line']].append(e)
    inserts = defaultdict(list)
    for e in edits:
        for d in e['data']:
            if d['key'][1:] != d['name']:
                issues.append('!! %s:%d DATA 变量名与键不一致 %s / %s'
                              % (rel, e['line'], d['name'], d['key']))
            if not any(x['name'] == d['name'] for x in inserts[e['ct_line']]):
                inserts[e['ct_line']].append(d)

    out = []
    for i, line in enumerate(lines, 1):
        if i in by_line:
            e = by_line[i][0]
            m = LINE_RE.match(line)
            if not m:
                issues.append('!! %s:%d 无法解析行: %r' % (rel, i, line[:60]))
            else:
                cur = m.group(5).strip()
                if cur != e['old_raw'] and cur != '"%s"' % e['old_raw']:
                    issues.append('!! %s:%d 值不匹配\n     期望: %s\n     实际: %s'
                                  % (rel, i, e['old_raw'][:70], cur[:70]))
                else:
                    line = '%s%s%s=%s%s' % (m.group(1), m.group(2), m.group(3),
                                            m.group(4), e['new_text'])
        out.append(line)
        if i in inserts:
            indent = re.match(r'^(\s*)', lines[i - 1]).group(1) + '\t'
            blk = ['', indent + 'DATA', indent + '{',
                   indent + '\ttype = string', indent + '\thidden = true', '']
            for d in inserts[i]:
                blk.append(indent + '\t%s = %s' % (d['name'], d['key']))
            blk += [indent + '}', '']
            out.extend(blk)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    # 必须用 write_bytes：write_text 在 Windows 上会把 \n 再翻译成 \r\n，
    # 与我们已拼接的 \r\n 叠加成 \r\r\n
    out_path.write_bytes(eol.join(out).encode('utf-8'))
    return len(inserts)


def build_localization(units, en_map, tr_map, br):
    first, per_file, shared = {}, defaultdict(list), []
    for u in sorted(units, key=lambda x: (x['file'], x['line'], x['seg_no'])):
        if u['key'] in first:
            continue
        first[u['key']] = u
        (shared if u['shared'] else per_file[u['file']]).append(u)
    shared.sort(key=lambda u: u['key'])

    def body(lang, val_of, with_en):
        L = ['\t%s' % lang, '\t{']
        L += ['\t\t//==================== 共享片段（多合同复用） ====================', '']
        for u in shared:
            if with_en:
                L.append('\t\t// EN: %s' % one_line(br_display(en_map[u['key']], br)))
            L.append('\t\t%s = %s' % (u['key'], val_of(u)))
        L.append('')
        for f in sorted(per_file):
            L += ['', '\t\t//==================== %s ====================' % f.replace('\\', '/'), '']
            for u in per_file[f]:
                if with_en:
                    L.append('\t\t// EN: %s' % one_line(br_display(en_map[u['key']], br)))
                L.append('\t\t%s = %s' % (u['key'], val_of(u)))
        L += ['', '\t}']
        return L

    head = [
        '// ===========================================================================',
        '// Contract Pack: Giving Aircraft a Purpose (GAP) - 本地化文件',
        '// 路径: GameData/ContractPacks/GAP/Localization/',
        '//',
        '// 键命名空间 : #loc_GAP_*  （与官方 #autoLOC_* 及其他模组命名空间隔离）',
        '// 编码       : UTF-8 无 BOM（含中文，切勿用 GBK 保存）',
        '// 换行       : 值内用 \\n 转义（KSP cfg 解析器会还原为真实换行）',
        '// 双引号     : 值内 " 写作 \\" （stock dictionary.cfg 同样做法）',
        '// 动态片段   : 含 @表达式 的字段在 cfg 里以 @/变量名 拼接，',
        '//              变量名即本文件中对应键去掉 # 后的名字',
        '//',
        '// en-us: 英文；zh-cn: 简体中文（每条键上方 EN 注释为英文原文，便于校对）',
        '// ===========================================================================',
        '',
        'Localization',
        '{',
    ]
    en = head + body('en-us', lambda u: esc(en_map[u['key']], br), False) + ['}', '']
    zh = head + body('zh-cn', lambda u: esc(tr_map.get(u['key'], en_map[u['key']]), br),
                     True) + ['}', '']
    return '\n'.join(en), '\n'.join(zh)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.environ.get('GAP_OUT', r'K:\AI代码\GAP-zh'))
    ap.add_argument('--translations', default=str(WORK / 'translations.json'))
    ap.add_argument('--br', default='newline', choices=['newline', 'keep'])
    args = ap.parse_args()

    plan = load('plan.json')
    units = load('units.json')
    en_map = load('en_values.json')
    tr_map = {}
    tp = Path(args.translations)
    if tp.exists():
        tr_map = json.loads(tp.read_text(encoding='utf-8'))
        tr_map.pop('_meta', None)

    out_root = Path(args.out)
    if out_root.exists():
        shutil.rmtree(out_root)
    issues = []

    n_cfg = n_copy = n_insert = 0
    for src in sorted(GAP.rglob('*')):
        rel = src.relative_to(GAP)
        dst = out_root / rel
        if src.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.suffix.lower() == '.cfg':
            n_insert += apply_edits(str(rel), plan.get(str(rel), []), dst, args.br, issues)
            n_cfg += 1
        else:
            shutil.copy2(src, dst)
            n_copy += 1

    en_txt, zh_txt = build_localization(units, en_map, tr_map, args.br)
    loc = out_root / 'Localization'
    loc.mkdir(parents=True, exist_ok=True)
    # 与其他 GAP cfg 一致使用 CRLF；同样用 write_bytes 避免二次翻译
    (loc / 'en-us.cfg').write_bytes(en_txt.replace('\n', '\r\n').encode('utf-8'))
    (loc / 'zh-cn.cfg').write_bytes(zh_txt.replace('\n', '\r\n').encode('utf-8'))

    # 计划引用的键必须都在 en_values 中
    for f, edits in plan.items():
        for e in edits:
            ks = [d['key'] for d in e['data']] if e['data'] else [e['key']]
            for k in ks:
                if k not in en_map:
                    issues.append('!! %s:%d 计划引用的键未定义: %s' % (f, e['line'], k))

    keys = set(en_map)
    missing_tr = sorted(keys - set(tr_map))
    extra_tr = sorted(set(tr_map) - keys)

    rep = ['=== 构建结果 ===',
           '  输出目录: %s' % out_root,
           '  cfg: %d ; 其他文件: %d ; 插入 DATA 块: %d' % (n_cfg, n_copy, n_insert),
           '  翻译单元: %d ; 唯一键: %d （共享 %d / 来源 %d）'
           % (len(units), len(keys), len({u['key'] for u in units if u['shared']}),
              len(keys) - len({u['key'] for u in units if u['shared']})),
           '  en-us.cfg: %d 字节 ; zh-cn.cfg: %d 字节'
           % (len(en_txt.encode()), len(zh_txt.encode())),
           '  已翻译: %d ; 未翻译(回退英文): %d ; translations 多余: %d'
           % (len(keys) - len(missing_tr), len(missing_tr), len(extra_tr)),
           '  换行策略: %s' % args.br,
           '', '=== 问题 (%d) ===' % len(issues)]
    rep += ['  ' + s for s in issues[:80]]
    (WORK / 'build_report.txt').write_text('\n'.join(rep), encoding='utf-8')
    (WORK / 'to_translate.json').write_text(
        json.dumps(en_map, ensure_ascii=False, indent=1), encoding='utf-8')
    (WORK / 'missing_tr.json').write_text(
        json.dumps(missing_tr, ensure_ascii=False, indent=1), encoding='utf-8')

    rev = ['=== 共享键复核清单（英文相同的片段被合并，共 %d 键）==='
           % len({u['key'] for u in units if u['shared']}), '']
    seen = set()
    for u in sorted(units, key=lambda x: x['key']):
        if u['shared'] and u['key'] not in seen:
            seen.add(u['key'])
            rev.append('x%-3d %s' % (u['shared_by'], u['key']))
            rev.append('      EN: %s' % one_line(u['en'], 150))
    (WORK / 'shared_review.txt').write_text('\n'.join(rev), encoding='utf-8')
    print('\n'.join(rep))


if __name__ == '__main__':
    main()
