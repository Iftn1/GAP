# Tools/localization —— 汉化维护脚本（可选，不影响游戏运行）

这些脚本是本次汉化的**完整生成与校验链路**，用于日后上游更新后重新生成汉化。
它们**不参与游戏运行**，可以整个删除；只要保留 `Localization/*.cfg` 与
合同 cfg，汉化就正常工作。

## 脚本

| 脚本 | 作用 |
|---|---|
| `extract.py` | 遍历 GAP 的 cfg，抽出全部用户可见文本；**按字面量片段**分配 `#loc_GAP_*` 键；对完全相同的英文自动去重为共享键 |
| `make_batches.py` | 把待翻译单元切成批次（每批附完整句子上下文，用 `«»` 标出该片段位置） |
| `merge_tr.py` | 合并分批翻译结果；做确定性措辞统一与"同英文多译法"体检 |
| `build.py` | 生成重构后的 mod 树与 `Localization/en-us.cfg`、`zh-cn.cfg` |
| `verify.py` | 严格校验：结构逐节点比对、键引用与定义一致性、残留英文、编码与转义、全局键冲突 |
| `glossary.md` | 翻译规范与官方术语表（官方译名来自游戏本体词典配对） |

## 路径配置

脚本默认路径可用环境变量覆盖，便于在别的机器上使用：

```powershell
$env:GAP_SRC      = 'D:\work\GAP'            # 上游 GAP 源目录（含 Agencies.cfg 等）
$env:GAP_WORK     = 'D:\work\.gap_loc_work'  # 中间产物目录
$env:GAP_OUT      = 'D:\work\GAP-zh'         # 输出目录
$env:KSP_GAMEDATA = 'C:\KSP\GameData'        # 仅 verify.py 用于全局键冲突复查
```

## 典型流程

```powershell
python extract.py        # 提取 + 分键  -> units.json / plan.json / en_values.json
python make_batches.py   # 切批次      -> batches/batch_NN.json
#   （翻译 batches/*.json，产出 batches/batch_NN.zh.json；可分批 + 多轮校对）
python merge_tr.py       # 合并译文    -> translations.json
python build.py          # 生成成品    -> GAP-zh/
python verify.py         # 校验        -> verify_report.txt
```

## 注意

- `build.py` 会**删除并重建**输出目录，请确认 `GAP_OUT` 指向正确位置。
- 所有产出的 cfg 必须保存为 **UTF-8 无 BOM**；含中文切勿用 GBK/ANSI 另存。
- 新增语言只需复制 `en-us.cfg` 改语言段名，**不要改动任何合同 cfg**。
