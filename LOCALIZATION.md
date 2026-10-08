# GAP 本地化说明（KSP 官方 Localization 机制）

本仓库是 **Contract Pack: Giving Aircraft a Purpose (GAP)** 的本地化分支。
原版把全部界面文本硬编码在 55 个 `.cfg` 里，本分支将其重构为 KSP 官方
Localization 机制，并提供完整的简体中文。

---

## 1. 做了什么

| 项目 | 数值 |
|---|---|
| 处理的 cfg 文件 | 55 个 |
| 原硬编码用户可见文本 | 1161 处 |
| 抽出的本地化键 | **504 个唯一键**（其中 78 个为跨合同共享键） |
| 新增文件 | `Localization/en-us.cfg`、`Localization/zh-cn.cfg` |
| 重构后残留硬编码英文 | **0** |
| 与原版的结构差异 | 仅「被本地化的字段」与「新增的 DATA 拼接块」，逐节点比对确认 |

玩法、数值、条件、奖励、参数逻辑**完全未改动**；只替换文本。

---

## 2. 键名规则

命名空间统一为 `#loc_GAP_`，与官方 `#autoLOC_*` 及其他模组完全隔离。

| 场景 | 键形式 | 示例 |
|---|---|---|
| 合同级字段 | `#loc_GAP_<合同名>_<字段>` | `#loc_GAP_Airline_Flight_101_synopsis` |
| 嵌套字段 | `#loc_GAP_<合同名>_<节点路径>_<字段>` | `#loc_GAP_..._BEHAVIOUR3_DIALOG_BOX1_TEXT1_text` |
| 跨合同共享片段 | `#loc_GAP_shared_<英文摘要>` | `#loc_GAP_shared_have_wings` |
| 动态拼接的片段 | 来源键 + `_s1` / `_s2` / `_s3` | `#loc_GAP_Airline_Flight_101_description_s1` |

**冲突防护**：已对整机 `GameData` 全部本地化文件（78 个 `Localization` 目录、
277 个 cfg、19997 个键）做键名查重，`loc_GAP` 前缀零命中；重构后再次复查，
与既有模组的键冲突为 **0**。

---

## 3. 动态文本如何拼接

含运行时数值的字段不能整句放进本地化文件，否则会丢掉动态值。
做法是把**字面片段**放进本地化文件，在合同的 `DATA` 节点里声明为字符串变量，
再用表达式拼接（这是 Contract Configurator 支持、且经实测验证的写法）：

```cfg
CONTRACT_TYPE
{
	DATA
	{
		type = string
		hidden = true
		loc_GAP_Airline_Flight_101_title_s1 = #loc_GAP_Airline_Flight_101_title_s1
		loc_GAP_shared_load_all = #loc_GAP_shared_load_all
	}
	...
	title = @/loc_GAP_Airline_Flight_101_title_s1 + @/numPassengers
}
```

约定：**DATA 变量名 = 该片段的本地化键去掉 `#`**。因此 cfg 里 `@/xxx`
引用的变量，总能在同合同的 DATA 块里找到同名键，便于查错。

---

## 4. 编码与转义规则（重要）

| 规则 | 说明 |
|---|---|
| 编码 | **UTF-8 无 BOM**。含中文，切勿用 GBK/ANSI 另存 |
| 换行 | 值内用 `\n`（反斜杠 + n）表示换行，KSP 解析时还原为真实换行 |
| 双引号 | 值内的 `"` 写作 `\"` |
| 禁止 | 值以 `#` 开头；值内含真实换行；值内含 `//`（会被当注释） |

### 关于 `&br;`

原版用 Contract Configurator 的 `&br;` 标记换行，本分支统一改为 `\n`。依据：

1. 官方 `Squad` 的 en-us 词典自身就用 `\n`（例 `#autoLOC_8005077`）；
2. 同环境内已实测可用的 KUM 合同包，其本地化值全部使用 `\n`，CC 的解析日志显示其被正确还原为真实换行；
3. `&br;` 是 CC 的历史标记，其替换发生在合同配置解析阶段；文本一旦移入本地化文件，
   `&br;` 存在被原样显示的风险，而 `\n` 由 KSP 配置解析器统一处理，不依赖 CC 的处理时机。

---

## 5. 新增其他语言

1. 复制 `Localization/en-us.cfg` 为 `Localization/<语言代码>.cfg`
   （语言代码用 KSP 的取值，如 `ja`、`ru`、`de-de`、`es-es`）；
2. 把顶层语言段名 `en-us` 改成对应代码；
3. 翻译值，**键名不要动**；
4. 无需改动任何合同 cfg。

缺失的键会回退显示为该键的英文（因为 `en-us.cfg` 始终定义全部键）。

---

## 6. 有意保留为英文的标识符

以下都是**标识符**而非显示文本，翻译会导致引用失效，故保持原样：

- `AGENT` 的 `name`
- `CONTRACT_GROUP` 的 `name`、`agent`
- 合同里的 `group`、`agent`、`part`、`contractType`
- `PARAMETER` / `BEHAVIOUR` 的 `name`（被 `parameter = xxx` 引用）
- `PQS_CITY` 的 `pqsCity`、`logoURL` 等资源路径

> 注意：`AGENT` 的 `title` 与 `description`、`CONTRACT_GROUP` 的 `displayName` 与 `tip`
> **是**显示文本，已本地化。

---

## 7. 术语来源

中文译名优先采用**游戏本体官方译法**（取自 `Squad` 的 en-us / zh-cn 词典按
`#autoLOC` 键配对），例如：

| 英文 | 官方中文 |
|---|---|
| Island Airfield | 小岛机场 |
| Dessert Airfield | 甜品机场 |
| Woomerang Launch Site | 乌墨瑞发射台 |
| Mahi Mahi Launch Site | 海豚鱼发射台 |
| Baikerbanur | 拜科努尔 |
| Spaceplane Hangar | 航天器机库 |
| Vehicle Assembly Building | 飞行器组装大楼 |
| Kerbal | 坎巴拉人 |
| island Airfield / KSC / Kerbin | 保留原文 |

机构与人名（Wright Aeronautical、SSI Aerospace、KSC Airlines、KSC Coast Guard、
Orville/Wilbur/Jebediah Kerman 等）按社区习惯处理：机构名译为中文，
人名保留原文。

---

## 8. 维护工具

`Tools/localization/` 内含生成与校验脚本（可选，不影响游戏运行）：

| 脚本 | 作用 |
|---|---|
| `extract.py` | 遍历 cfg，抽取用户可见字符串、按字面量片段分配键、去重 |
| `build.py` | 生成重构后的 mod 树与 `Localization/*.cfg` |
| `verify.py` | 结构逐节点比对、键引用与定义一致性、残留英文、编码、全局键冲突 |
| `merge_tr.py` | 合并分批翻译结果、确定性归一化重复模式 |
| `glossary.md` | 翻译规范与官方术语表 |

---

## 9. 验证状态

见 `VALIDATION.md`。
