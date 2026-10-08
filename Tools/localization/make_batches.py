# -*- coding: utf-8 -*-
"""生成翻译批次：每个"片段"单元附带完整字段上下文（用 «» 标出该片段位置）"""
import json
import os
from collections import defaultdict
from pathlib import Path

WORK = Path(os.environ.get('GAP_WORK', r'K:\AI代码\.gap_loc_work'))
OUT = WORK / 'batches'
TARGET = 9000   # 每批目标字符数
MAXC = 13000

FIELD_NOTE = {
    'title': '合同/参数标题',
    'genericTitle': '合同通用标题（不含动态数字）',
    'description': '合同详细描述（正文）',
    'genericDescription': '合同通用描述（不含动态数字）',
    'synopsis': '合同简报',
    'notes': '合同备注',
    'completedMessage': '合同完成提示（正文）',
    'preWaitText': '计时参数-等待前文本',
    'waitingText': '计时参数-进行中文本',
    'completionText': '计时参数-完成文本',
    'text': '对话框正文（飞行员陆空通话）',
    'characterName': '对话框说话者名称',
    'displayName': '合同组显示名',
    'tip': '合同组提示',
    'name': '导航点名称',
}


def context_of(u):
    segs = u.get('segments') or []
    if u.get('seg_no'):
        out = []
        n = 0
        for kind, txt in segs:
            if kind == 'expr':
                out.append('【动态值】')
                continue
            if not txt.strip():
                out.append(txt)
                continue
            n += 1
            out.append('«%s»' % txt if n == u['seg_no'] else txt)
        return ''.join(out)
    return u['en']


def note_of(u):
    bits = []
    if u.get('node') == 'PQS_CITY':
        bits.append('导航点名称')
    elif u['field'] in FIELD_NOTE:
        bits.append(FIELD_NOTE[u['field']])
    if u.get('seg_no'):
        bits.append('该字段被拆成多个片段，用「+」与动态值拼接；本项是第 %d 个片段，'
                    '«» 标出它在整句中的位置' % u['seg_no'])
    if u.get('has_br') or '\\n' in u['en']:
        bits.append('含换行（值里的 \\n 是换行转义，必须保留）')
    if not u.get('seg_no') and ('\\n' not in u['en']):
        bits.append('完整字段')
    return '；'.join(bits)


def main():
    units = json.loads((WORK / 'units.json').read_text(encoding='utf-8'))
    first = {}
    order = []
    for u in units:
        if u['key'] not in first:
            first[u['key']] = u
            order.append(u['key'])

    items = []
    for k in order:
        u = first[k]
        en = u['en']
        items.append({
            'key': k,
            'en': en,
            'ctx': context_of(u),
            'field': u['field'],
            'node': u['node'],
            'file': u['file'].replace('\\', '/'),
            'shared': bool(u.get('shared')),
            'reuse': u.get('shared_by', 1),
            'note': note_of(u),
        })

    OUT.mkdir(parents=True, exist_ok=True)
    # 只清理旧批次，绝不删除已翻译的 *.zh.json
    for f in OUT.glob('batch_*.json'):
        if not f.name.endswith('.zh.json'):
            f.unlink()

    batches, cur, curc = [], [], 0
    for it in items:
        c = len(it['en']) + len(it['ctx']) + 120
        if cur and (curc + c > MAXC or curc >= TARGET):
            batches.append(cur)
            cur, curc = [], 0
        cur.append(it)
        curc += c
    if cur:
        batches.append(cur)

    lines = ['=== 批次 ===']
    for i, b in enumerate(batches, 1):
        chars = sum(len(x['en']) for x in b)
        p = OUT / ('batch_%02d.json' % i)
        p.write_text(json.dumps({'id': i, 'items': b}, ensure_ascii=False, indent=1),
                     encoding='utf-8')
        lines.append('  %s  条目 %3d  英文 %6d 字符  最大 ctx %d'
                     % (p.name, len(b), chars, max(len(x['ctx']) for x in b)))
    lines.append('  合计: %d 批, %d 条目' % (len(batches), len(items)))
    (WORK / 'batches_report.txt').write_text('\n'.join(lines), encoding='utf-8')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
