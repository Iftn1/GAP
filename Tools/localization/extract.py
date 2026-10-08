# -*- coding: utf-8 -*-
"""GAP 汉化 - 阶段1（v3：以"字面量片段"为翻译单元）
要点：
  - 无表达式的字段 -> 1 个单元
  - 含 @表达式 的字段 -> 按字面量片段拆成多个单元，动态部分原样保留
  - 单元去重：短片段/名词性字段共用 #loc_GAP_shared_*；长正文保留来源键
产物:
  units.json      翻译单元（最终键、英文片段、来源）
  plan.json       逐文件改写计划（new_text + 需插入的 DATA 变量，变量名 == 键名去掉 #）
  en_values.json  {键: 英文}
  report_D.txt
"""
import hashlib
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

GAP = Path(os.environ.get('GAP_SRC', r'K:\AI代码\GAP'))
WORK = Path(os.environ.get('GAP_WORK', r'K:\AI代码\.gap_loc_work'))

IDENTITY_FIELDS = {
    'AGENT': ('title', 'description'),
    'CONTRACT_GROUP': ('displayName', 'tip'),
    'CONTRACT_TYPE': ('title', 'genericTitle', 'description', 'genericDescription',
                      'synopsis', 'notes', 'completedMessage'),
    'PART': ('title', 'manufacturer', 'description'),
    'PQS_CITY': ('name',),
}
GLOBAL_FIELDS = frozenset({
    'title', 'genericTitle', 'description', 'genericDescription',
    'synopsis', 'notes', 'completedMessage',
    'preWaitText', 'waitingText', 'completionText',
    'text', 'characterName', 'disabledContractText',
    'displayName', 'tip',
})
IDENTITY_NODES = frozenset(IDENTITY_FIELDS)
EXPR_START = re.compile(r'@(?:/|[A-Za-z_])')
SHARE_MAXLEN = 60


def strip_comment(line):
    out, inq, i, n = [], False, 0, len(line)
    while i < n:
        c = line[i]
        if c == '"':
            inq = not inq
            out.append(c)
            i += 1
            continue
        if c == '/' and not inq and i + 1 < n and line[i + 1] == '/':
            break
        out.append(c)
        i += 1
    return ''.join(out)


class Node:
    __slots__ = ('name', 'values', 'children', 'line')

    def __init__(self, name, line=0):
        self.name = name
        self.values = []
        self.children = []
        self.line = line

    def val(self, key):
        for k, v, ln in self.values:
            if k == key:
                return v
        return None


def parse_cfg(path):
    root = Node('<root>')
    stack = [root]
    pending = None
    text = path.read_bytes().decode('utf-8-sig', errors='replace')
    for lineno, line in enumerate(text.splitlines(), 1):
        line = strip_comment(line).strip()
        if not line:
            continue
        if line.endswith('{'):
            name = (line[:-1].strip() or pending or '<anon>')
            node = Node(name, lineno)
            stack[-1].children.append(node)
            stack.append(node)
            pending = None
            continue
        if line == '}':
            if len(stack) > 1:
                stack.pop()
            pending = None
            continue
        if '=' in line:
            k, _, v = line.partition('=')
            stack[-1].values.append((k.strip(), v.strip(), lineno))
            pending = None
            continue
        pending = line
    return root


def base_name(raw):
    return raw.split(':')[0].strip().lstrip('@%!').strip()


def bracket_name(raw):
    m = re.search(r'\[([^\]]+)\]', raw)
    return m.group(1) if m else None


def sanitize(s, maxlen=None):
    s = re.sub(r'[^0-9A-Za-z]+', '_', s or '').strip('_')
    if maxlen:
        s = s[:maxlen].strip('_')
    return s or 'X'


def split_segments(value):
    segs = []
    i, n = 0, len(value)
    buf = []
    while i < n:
        m = EXPR_START.match(value, i)
        if m:
            if buf:
                segs.append(('lit', ''.join(buf)))
                buf = []
            j = m.end()
            depth = 0
            while j < n:
                c = value[j]
                if c == '(':
                    depth += 1
                elif c == ')':
                    depth -= 1
                    if depth == 0:
                        j += 1
                        continue
                    if depth < 0:
                        depth = 0
                elif depth == 0 and not (c.isalnum() or c in '_/.'):
                    break
                j += 1
            segs.append(('expr', value[i:j]))
            i = j
            continue
        buf.append(value[i])
        i += 1
    if buf:
        segs.append(('lit', ''.join(buf)))
    return segs


def collect():
    fields = []
    skipped = []
    for f in sorted(GAP.rglob('*.cfg')):
        rel = str(f.relative_to(GAP))
        stem = sanitize(f.stem)
        root = parse_cfg(f)
        ct_counter = Counter()
        for top in root.children:
            if base_name(top.name) == 'CONTRACT_TYPE':
                ct_counter[sanitize(top.val('name') or 'CT')] += 1
        ct_seen = Counter()

        def walk(node, parents, ident, path_from_ident, occ_map, ct_line):
            bname = base_name(node.name)
            local_ident, local_path, local_ct = ident, path_from_ident, ct_line
            if bname in IDENTITY_NODES:
                nm = node.val('name') or bracket_name(node.name) or bname
                if bname == 'CONTRACT_TYPE':
                    slug = sanitize(nm)
                    ct_seen[slug] += 1
                    if ct_counter[slug] > 1:
                        slug = '%s%d' % (slug, ct_seen[slug])
                    local_ident = slug
                    local_ct = node.line
                else:
                    local_ident = '%s_%s' % (bname, sanitize(nm))
                local_path = []
            if local_ident is None:
                local_ident = 'FILE_%s' % stem

            allowed = IDENTITY_FIELDS.get(bname)
            if allowed is None:
                allowed = GLOBAL_FIELDS
            for k, v, ln in node.values:
                is_text = k in allowed or (bname == 'PQS_CITY' and k == 'name')
                if not is_text:
                    continue
                raw = v
                quoted = len(raw) >= 2 and raw.startswith('"') and raw.endswith('"')
                val = raw[1:-1] if quoted else raw
                segs = split_segments(val)
                exprs = [s for s in segs if s[0] == 'expr']
                if not [s for s in segs if s[0] == 'lit' and s[1].strip()]:
                    skipped.append({'file': rel, 'line': ln, 'field': k, 'value': val})
                    continue
                occ = occ_map.get((tuple(id(x) for x in parents), k), 0) + 1
                occ_map[(tuple(id(x) for x in parents), k)] = occ
                parts = ['loc_GAP', local_ident]
                for nd, idx in local_path:
                    parts.append('%s%d' % (sanitize(base_name(nd.name)), idx))
                parts.append(sanitize(k))
                base = '_'.join(parts)
                if occ > 1:
                    base = '%s_%d' % (base, occ)
                fields.append({
                    'file': rel, 'line': ln, 'field': k, 'node': bname,
                    'ident': local_ident, 'base': base, 'en': val,
                    'segments': segs, 'n_expr': len(exprs),
                    'path': '/'.join(base_name(n.name) for n, _ in local_path),
                    'ct_line': local_ct, 'has_br': '&br;' in val,
                })

            cc = Counter()
            for ch in node.children:
                cc[ch.name] += 1
                walk(ch, parents + [node], local_ident,
                     local_path + [(ch, cc[ch.name])], occ_map, local_ct)

        for top in root.children:
            walk(top, [], None, [], {}, None)

    # ---- 生成"单元" ----
    units = []
    for fidx, r in enumerate(fields):
        if r['n_expr'] == 0:
            u = dict(r)
            u['uid'] = '%d:0' % fidx
            u['prov_key'] = r['base']
            u['en'] = r['en']
            u['seg_no'] = 0
            units.append(u)
            continue
        n = 0
        for kind, txt in r['segments']:
            if kind != 'lit' or not txt.strip():
                continue
            n += 1
            u = dict(r)
            u['uid'] = '%d:%d' % (fidx, n)
            u['prov_key'] = '%s_s%d' % (r['base'], n)
            u['en'] = txt
            u['seg_no'] = n
            units.append(u)
    return fields, units, skipped


def assign_keys(units):
    byval = defaultdict(list)
    for u in units:
        byval[u['en']].append(u)
    shared = {}
    used = {u['prov_key'] for u in units}
    for val in sorted(byval):
        us = byval[val]
        if len(us) == 1:
            continue
        shareable = (len(val) <= SHARE_MAXLEN or us[0]['field'] == 'characterName'
                     or us[0]['node'] == 'PQS_CITY')
        if not shareable:
            continue
        base = 'loc_GAP_shared_%s' % sanitize(val, 48)
        key = base
        if key in used:
            key = '%s_%s' % (base[:44].strip('_'),
                             hashlib.md5(val.encode('utf-8')).hexdigest()[:4])
        n = 2
        while key in used:
            key = '%s_%d' % (base[:44].strip('_'), n)
            n += 1
        used.add(key)
        shared[val] = key
    for u in units:
        k = shared.get(u['en'])
        u['key'] = '#' + (k if k else u['prov_key'])
        u['shared'] = bool(k)
        u['shared_by'] = len(byval[u['en']]) if k else 1
    return shared


def make_plan(fields, units):
    by_uid = {u['uid']: u for u in units}
    plan = defaultdict(list)
    for fidx, r in enumerate(fields):
        data, out = [], []
        if r['n_expr'] == 0:
            u = by_uid['%d:0' % fidx]
            plan[r['file']].append({
                'line': r['line'], 'field': r['field'], 'key': u['key'],
                'old_raw': r['en'], 'new_text': u['key'], 'data': [],
                'ct_line': r['ct_line'],
            })
            continue
        n = 0
        for kind, txt in r['segments']:
            if kind == 'expr':
                out.append(txt)
                continue
            if not txt.strip():
                out.append('"%s"' % txt)
                continue
            n += 1
            u = by_uid['%d:%d' % (fidx, n)]
            vname = u['key'][1:]
            if not any(d['name'] == vname for d in data):
                data.append({'name': vname, 'key': u['key']})
            out.append('@/%s' % vname)
        plan[r['file']].append({
            'line': r['line'], 'field': r['field'],
            'key': data[0]['key'] if len(data) == 1 else '<%d segments>' % len(data),
            'old_raw': r['en'], 'new_text': ' + '.join(out), 'data': data,
            'ct_line': r['ct_line'],
        })
    return dict(plan)


def report(fields, units, skipped, shared):
    keys = {u['key'] for u in units}
    L = []
    L.append('=== D1. 规模（以"字面量片段"为翻译单元）===')
    L.append('  字段数: %d ; 翻译单元: %d ; 唯一键: %d' % (len(fields), len(units), len(keys)))
    L.append('  其中 含表达式字段: %d ; 纯文本字段: %d'
             % (sum(1 for f in fields if f['n_expr']), sum(1 for f in fields if not f['n_expr'])))
    L.append('  共享键: %d 个，覆盖单元 %d ; 来源键: %d'
             % (sum(1 for u in units if u['shared']), sum(1 for u in units if u['shared']),
                len(keys) - len({u['key'] for u in units if u['shared']})))
    L.append('  跳过(纯表达式): %d' % len(skipped))
    L.append('')
    L.append('  按字段:')
    for k, n in Counter(u['field'] for u in units).most_common():
        L.append('    %-20s %5d' % (k, n))

    L.append('')
    L.append('=== D2. 全部共享键（需人工过一眼是否过度共享）===')
    byval = defaultdict(list)
    for u in units:
        byval[u['en']].append(u)
    for u in sorted((x for x in units if x['shared']), key=lambda x: x['key']):
        L.append('    x%-3d %-34s | %s' % (u['shared_by'], u['key'][1:], u['en'][:70]))

    L.append('')
    L.append('=== D3. 表达式字段拆分样例 ===')
    for r in [f for f in fields if f['n_expr']][:5]:
        L.append('    %s:%d  %s' % (r['file'], r['line'], r['field']))
        L.append('        EN : %s' % r['en'][:100])
        for kind, txt in r['segments']:
            L.append('        %-5s %r' % (kind, txt[:60]))

    L.append('')
    L.append('=== D4. 含 &br; 的单元 (%d) ===' % sum(1 for u in units if '&br;' in u['en']))
    for k, n in Counter(u['field'] for u in units if '&br;' in u['en']).most_common():
        L.append('    %-20s %5d' % (k, n))

    L.append('')
    L.append('=== D5. 抽样最终键 ===')
    for u in units[:5]:
        L.append('    %-66s | %s' % (u['key'], u['en'][:60]))
    for u in [x for x in units if x['seg_no']][:5]:
        L.append('    %-66s | seg%d %s' % (u['key'], u['seg_no'], u['en'][:50]))
    return '\n'.join(L)


def main():
    fields, units, skipped = collect()
    shared = assign_keys(units)
    plan = make_plan(fields, units)
    (WORK / 'units.json').write_text(json.dumps(units, ensure_ascii=False, indent=1),
                                     encoding='utf-8')
    (WORK / 'plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=1),
                                    encoding='utf-8')
    (WORK / 'en_values.json').write_text(
        json.dumps({u['key']: u['en'] for u in units}, ensure_ascii=False, indent=1),
        encoding='utf-8')
    txt = report(fields, units, skipped, shared)
    (WORK / 'report_D.txt').write_text(txt, encoding='utf-8')
    print(txt)


if __name__ == '__main__':
    main()
