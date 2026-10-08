# -*- coding: utf-8 -*-
"""GAP 汉化 - 阶段3：严格校验
1. 结构对比：构建树 vs 原树，差异只允许出现在 (a) 被本地化的字段 (b) 新增 DATA 块
2. 键完整性：cfg 引用的每个 #loc_GAP_* 必须在 en-us.cfg 与 zh-cn.cfg 中都有定义
3. 无孤儿键、无重复定义、两语言键集一致
4. 无残留英文硬编码（范围内字段必须是 #loc_ 或 @表达式）
5. 编码/转义/EOL 检查
6. 与整机 GameData 的全局键冲突复查
产物: verify_report.txt
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

GAP = Path(os.environ.get('GAP_SRC', r'K:\AI代码\GAP'))
OUT = Path(os.environ.get('GAP_OUT', r'K:\AI代码\GAP-zh'))
WORK = Path(os.environ.get('GAP_WORK', r'K:\AI代码\.gap_loc_work'))
GD = Path(os.environ.get('KSP_GAMEDATA', r'G:\Kerbal Space Program\GameData'))
LANG_RE = re.compile(r'^[a-z]{2}(?:-[A-Za-z]{2})?$')
KEY_RE = re.compile(r'#(loc_GAP_[A-Za-z0-9_]+)')

from extract import (parse_cfg, base_name, strip_comment, IDENTITY_FIELDS,
                     GLOBAL_FIELDS, EXPR_START)  # noqa: E402

LOG = []


def log(s=''):
    LOG.append(s)


# ---------- 本地化文件解析 ----------
def read_loc(path):
    """返回 {lang: {key: value}} 及重复定义列表
    注意：KSP cfg 里节点名与 '{' 常分处两行，必须追踪"待定节点名"
    """
    dup = []
    out = defaultdict(dict)
    stack, pending, lang, lang_depth = [], None, None, None
    text = path.read_bytes().decode('utf-8-sig')
    for lineno, line in enumerate(text.splitlines(), 1):
        line = strip_comment(line).strip()
        if not line:
            continue
        if line.endswith('{'):
            name = line[:-1].strip() or (pending or '')
            stack.append(name)
            pending = None
            if LANG_RE.match(name):
                lang, lang_depth = name.lower(), len(stack)
            continue
        if line == '}':
            if lang_depth is not None and len(stack) <= lang_depth:
                lang, lang_depth = None, None
            if stack:
                stack.pop()
            pending = None
            continue
        if '=' in line:
            k, _, v = line.partition('=')
            k = k.strip()
            if k.startswith('#') and lang:
                key = k[1:]
                if key in out[lang]:
                    dup.append('%s:%d [%s] %s' % (path.name, lineno, lang, key))
                out[lang][key] = v.strip()
            pending = None
            continue
        pending = line
    return out, dup


# ---------- 结构对比 ----------
def is_inserted_data(node):
    if base_name(node.name) != 'DATA':
        return False
    vals = {k: v for k, v, _ in node.values}
    if vals.get('type') != 'string' or vals.get('hidden') != 'true':
        return False
    rest = [k for k in vals if k not in ('type', 'hidden')]
    return bool(rest) and all(k.startswith('loc_GAP_') for k in rest)


def filtered_children(node):
    return [c for c in node.children if not is_inserted_data(c)]


def compare(o, n, path, diffs):
    on, nn = filtered_children(o), filtered_children(n)
    if len(on) != len(nn):
        diffs.append('节点数不同 @%s : 原 %d / 新 %d (%s)'
                     % (path, len(on), len(nn), [base_name(c.name) for c in nn]))
        return
    for co, cn in zip(on, nn):
        if base_name(co.name) != base_name(cn.name):
            diffs.append('节点名不同 @%s : %s -> %s' % (path, co.name, cn.name))
            continue
        p = path + '/' + base_name(co.name)
        ov = {k: v for k, v, _ in co.values}
        nv = {k: v for k, v, _ in cn.values}
        if set(ov) != set(nv):
            diffs.append('字段集不同 @%s : 原 %s / 新 %s'
                         % (p, sorted(set(ov) - set(nv)), sorted(set(nv) - set(ov))))
        for k in set(ov) & set(nv):
            if ov[k] == nv[k]:
                continue
            if nv[k].startswith('#loc_GAP_') or '@/loc_GAP_' in nv[k] or nv[k].startswith('@/loc_GAP_'):
                continue
            diffs.append('意外改动 @%s.%s\n     原: %s\n     新: %s'
                         % (p, k, ov[k][:70], nv[k][:70]))
        compare(co, cn, p, diffs)


def main():
    en, en_dup = read_loc(OUT / 'Localization' / 'en-us.cfg')
    zh, zh_dup = read_loc(OUT / 'Localization' / 'zh-cn.cfg')
    en_keys, zh_keys = set(en.get('en-us', {})), set(zh.get('zh-cn', {}))

    log('=== V1. 本地化文件 ===')
    log('  en-us 键: %d ; zh-cn 键: %d ; 键集差异: %d'
        % (len(en_keys), len(zh_keys), len(en_keys ^ zh_keys)))
    log('  重复定义: en-us %d ; zh-cn %d' % (len(en_dup), len(zh_dup)))
    for d in (en_dup + zh_dup)[:10]:
        log('    !! %s' % d)
    for k in sorted(en_keys ^ zh_keys)[:10]:
        log('    !! 仅一侧存在: %s' % k)

    # 引用 vs 定义
    refs = Counter()
    ref_where = defaultdict(set)
    for f in sorted(OUT.rglob('*.cfg')):
        if 'Localization' in f.parts:
            continue
        text = f.read_bytes().decode('utf-8-sig')
        for m in KEY_RE.finditer(text):
            refs[m.group(1)] += 1
            ref_where[m.group(1)].add(str(f.relative_to(OUT)))
    log('')
    log('=== V2. 引用与定义一致性 ===')
    log('  cfg 中引用的键: %d ; 定义: %d' % (len(refs), len(en_keys)))
    undef = sorted(set(refs) - en_keys)
    orphan = sorted(en_keys - set(refs))
    log('  引用了但未定义: %d' % len(undef))
    for k in undef[:15]:
        log('    !! %s   <- %s' % (k, sorted(ref_where[k])[:2]))
    log('  定义了但未被引用(孤儿键): %d' % len(orphan))
    for k in orphan[:15]:
        log('    ?  %s = %s' % (k, en['en-us'][k][:60]))

    # 结构对比
    log('')
    log('=== V3. 结构对比（构建树 vs 原树）===')
    diffs = []
    n_files = 0
    for src in sorted(GAP.rglob('*.cfg')):
        rel = src.relative_to(GAP)
        dst = OUT / rel
        if not dst.exists():
            diffs.append('!! 输出缺失文件: %s' % rel)
            continue
        n_files += 1
        diff = []
        compare(parse_cfg(src), parse_cfg(dst), str(rel), diff)
        diffs.extend(diff)
    log('  对比文件: %d ; 结构意外差异: %d' % (n_files, len(diffs)))
    for d in diffs[:25]:
        log('    %s' % d)

    # 残留英文检查
    log('')
    log('=== V4. 范围内字段是否还有硬编码英文 ===')
    residual = []
    for dst in sorted(OUT.rglob('*.cfg')):
        if 'Localization' in dst.parts:
            continue
        root = parse_cfg(dst)

        def walk(node, ident):
            bname = base_name(node.name)
            allowed = IDENTITY_FIELDS.get(bname, GLOBAL_FIELDS)
            for k, v, ln in node.values:
                if (k in allowed or (bname == 'PQS_CITY' and k == 'name')):
                    # 允许：#loc_ 键 或 纯 @表达式（动态值，无可翻译文字）
                    if not (v.startswith('#loc_GAP_') or v.startswith('@')):
                        residual.append('%s:%d %s = %s'
                                        % (dst.relative_to(OUT), ln, k, v[:60]))
            for c in node.children:
                walk(c, ident)
        walk(root, None)
    log('  残留: %d' % len(residual))
    for r in residual[:15]:
        log('    !! %s' % r)

    # 编码/转义
    log('')
    log('=== V5. 编码与转义 ===')
    bad = []
    for f in sorted(OUT.rglob('*')):
        if not f.is_file():
            continue
        b = f.read_bytes()
        if b[:3] == b'\xef\xbb\xbf':
            bad.append('带 BOM: %s' % f.relative_to(OUT))
        if f.suffix.lower() == '.cfg':
            try:
                b.decode('utf-8')
            except UnicodeDecodeError:
                bad.append('非 UTF-8: %s' % f.relative_to(OUT))

    # 行尾检查：不得出现重复 CR（\r\r\n，通常由 write_text 二次翻译换行造成），
    # 也不得有孤立 CR（会导致 KSP 读到残缺值，也会让 Git 出现伪差异）
    eol_bad = []
    for f in sorted(OUT.rglob('*.cfg')):
        b = f.read_bytes()
        if b'\r\r' in b:
            eol_bad.append('%s 含重复 CR（\\r\\r）' % f.relative_to(OUT))
        elif b.count(b'\r') != b.count(b'\r\n'):
            eol_bad.append('%s 存在孤立 CR' % f.relative_to(OUT))
    bad.extend(eol_bad[:20])
    log('  行尾异常文件: %d' % len(eol_bad))
    for name in ('en-us.cfg', 'zh-cn.cfg'):
        # 只看值，不看注释（注释里保留英文原文，可能含 &br;）
        vals = []
        for ln in (OUT / 'Localization' / name).read_text(encoding='utf-8').splitlines():
            ln = strip_comment(ln).strip()
            if '=' in ln and ln.startswith('#'):
                vals.append(ln.split('=', 1)[1])
        joined = '\n'.join(vals)
        if '&br;' in joined:
            bad.append('%s 的值仍含 &br;（换行策略未生效）' % name)
        if '\\r' in joined:
            bad.append('%s 的值含 \\r' % name)

    # 值级安全检查（两种语言）：// 会被当注释、# 开头会被当本地化键、空值
    for lang, name in (('en-us', 'en-us.cfg'), ('zh-cn', 'zh-cn.cfg')):
        per, _ = read_loc(OUT / 'Localization' / name)
        vals = per.get(lang, {})
        same = 0
        for k, v in vals.items():
            if '//' in v:
                bad.append('[%s] 值含 //（会被当注释截断）: %s' % (lang, k))
            if v.startswith('#'):
                bad.append('[%s] 值以 # 开头（会被当本地化键）: %s' % (lang, k))
            if not v.strip():
                bad.append('[%s] 空值: %s' % (lang, k))
            if v[:1].isspace() and not v.startswith('\\n'):
                bad.append('[%s] 值以空白开头: %s = %r' % (lang, k, v[:30]))
        en_vals = per.get('en-us', {})
        if lang == 'zh-cn':
            same = sum(1 for k, v in vals.items() if v == en_vals.get(k))
            log('  zh-cn 与英文完全相同（专有名词/缩写属正常）: %d' % same)
            for k, v in vals.items():
                if v == en_vals.get(k):
                    log('      = %s' % k)
    # 段落结构：连续换行转义的长度序列必须与英文一致
    # （只看 \n 总数不够——分布错了会造成多余空行，例如 ：\n\n\n\n- 零件）
    en_v = read_loc(OUT / 'Localization' / 'en-us.cfg')[0].get('en-us', {})
    zh_v = read_loc(OUT / 'Localization' / 'zh-cn.cfg')[0].get('zh-cn', {})

    def nl_runs(v):
        return [len(m.group(0)) // 2 for m in re.finditer(re.escape('\\n') + '+', v)]

    struct = 0
    for k, v in zh_v.items():
        if k in en_v and nl_runs(v) != nl_runs(en_v[k]):
            struct += 1
            bad.append('段落结构不一致 [%s]: EN=%s ZH=%s'
                       % (k, nl_runs(en_v[k]), nl_runs(v)))
    log('  段落结构不一致: %d' % struct)

    # 英文侧忠实性：en-us.cfg 的值反向还原转义后，必须与原始英文逐字一致
    en_map = json.loads((WORK / 'en_values.json').read_text(encoding='utf-8'))
    faithful = 0
    for k, orig in en_map.items():
        got = en_v.get(k)
        if got is None:
            continue
        back = got.replace('\\n', '&br;').replace('\\"', '"')
        if back != orig:
            faithful += 1
            bad.append('英文侧不忠实 [%s]: 原=%r 文件=%r'
                       % (k, orig[:70], back[:70]))
    log('  英文侧不忠实: %d / %d' % (faithful, len(en_map)))

    log('  问题: %d' % len(bad))
    for x in bad[:15]:
        log('    !! %s' % x)

    # EOL 保持
    eol_mismatch = []
    for src in sorted(GAP.rglob('*.cfg')):
        rel = src.relative_to(GAP)
        dst = OUT / rel
        if dst.exists():
            a = b'\r\n' in src.read_bytes()
            c = b'\r\n' in dst.read_bytes()
            if a != c:
                eol_mismatch.append('%s 原 CRLF=%s 新 CRLF=%s' % (rel, a, c))
    log('  EOL 不一致: %d' % len(eol_mismatch))
    for x in eol_mismatch[:10]:
        log('    !! %s' % x)

    # 全局冲突复查
    log('')
    log('=== V6. 与整机 GameData 的键冲突复查 ===')
    table = defaultdict(set)
    for d in [x for x in GD.rglob('*') if x.is_dir() and x.name.lower() == 'localization']:
        for f in d.glob('*.cfg'):
            stack, lang, lang_depth = [], None, None
            for line in f.read_bytes().decode('utf-8-sig', errors='replace').splitlines():
                line = strip_comment(line).strip()
                if not line:
                    continue
                if line.endswith('{'):
                    name = line[:-1].strip()
                    stack.append(name)
                    if LANG_RE.match(name):
                        lang, lang_depth = name.lower(), len(stack)
                    continue
                if line == '}':
                    if lang_depth is not None and len(stack) <= lang_depth:
                        lang, lang_depth = None, None
                    if stack:
                        stack.pop()
                    continue
                if '=' in line and line.strip().startswith('#'):
                    key = line.split('=', 1)[0].strip()[1:]
                    if lang:
                        table[(lang, key)].add(str(f))
    clash = []
    for lang in ('zh-cn', 'en-us'):
        for k in en_keys:
            fs = table.get((lang, k), set())
            if fs and not any('GAP-zh' in x for x in fs):
                clash.append('[%s] %s -> %s' % (lang, k, sorted(fs)[:2]))
    log('  与既有模组的键冲突: %d' % len(clash))
    for x in clash[:20]:
        log('    !! %s' % x)

    txt = '\n'.join(LOG)
    (WORK / 'verify_report.txt').write_text(txt, encoding='utf-8')
    print(txt)


if __name__ == '__main__':
    main()
