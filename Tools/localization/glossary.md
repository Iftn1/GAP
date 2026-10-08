# GAP 汉化翻译规范与术语表

## 一、任务性质

你在翻译 KSP（坎巴拉太空计划）合同包 **Contract Pack: Giving Aircraft a Purpose (GAP)** 的文本。
这是航空主题的合同包：玩家经营航空公司、海岸警卫队、莱特航空等机构，执行飞行任务、特技表演、救援、购买原型零件。

原文是**航空合同简报**风格：专业、简洁，但常带有幽默与调侃（莱特兄弟的推销口吻、晕机袋玩笑、"你居然从一架完好的飞机上跳下去"）。**中文要保留这种轻松幽默感**，不要译成干巴巴的说明书。

## 二、官方术语表（必须遵守，来自游戏本体官方中文）

| 英文 | 中文 | 说明 |
|---|---|---|
| KSC | KSC | 保留英文缩写 |
| Kerbin | Kerbin | 官方中文也保留 Kerbin |
| Kerbal / Kerbals | 坎巴拉人 | 官方译法 |
| Kerman | Kerman | 姓氏，保留原文（如 Jebediah Kerman） |
| Kerbal Space Center | 坎巴拉太空中心 | 官方译法 |
| Island Airfield | 小岛机场 | **官方译法**（不是"岛屿机场"） |
| Dessert Airfield | 甜品机场 | 官方译法（"Dessert"是双关梗，保留甜品） |
| KSC Runway | KSC 跑道 | |
| KSC Air Terminal | KSC 航站楼 | GAP 自创称呼 |
| Spaceplane Hangar | 航天器机库 | 官方译法 |
| Spaceplane Hangar Air Terminal | 航天器机库航站楼 | |
| Vehicle Assembly Building | 飞行器组装大楼 | 官方译法 |
| Vehicle Assembly Building Helipad | 飞行器组装大楼直升机坪 | |
| Baikerbanur | 拜科努尔 | 官方译法 |
| Woomerang | 乌墨瑞 | 官方译法（Woomerang Launch Site = 乌墨瑞发射台） |
| Mahi Mahi | 海豚鱼 | 官方译法（Mahi Mahi Launch Site = 海豚鱼发射台） |
| Mission Control | 任务控制中心 | |
| Wright Aeronautical | 莱特航空 | GAP 机构名 |
| SSI Aerospace | SSI 航天 | GAP 机构名 |
| KSC Airlines | KSC 航空 | GAP 机构名 |
| KSC Coast Guard | KSC 海岸警卫队 | GAP 机构名 |
| Giving Aircraft a Purpose | 让飞机有用武之地 | 模组名 / 机构名 / 合同组名 |
| Prototype Marketplace | 原型市场 | 合同组名 |
| Air Traffic Control | 空中交通管制 | 对话框说话者名 |
| Pilot / Engineer / Scientist / Tourist | 飞行员 / 工程师 / 科学家 / 游客 | 官方译法 |
| recovery / recover | 回收 | |
| waypoint | 导航点 | 官方译法 |
| clearance | 许可 | 起飞许可 / 着陆许可 |
| squawk | 应答机 | 航空无线电用语 |
| heading | 航向 | |
| airspeed | 空速 | |
| altitude | 高度 / 海拔 | |
| Mach | 马赫 | Mach 1 = 马赫 1 |
| EVA | EVA | 官方保留 |
| parachute | 降落伞 | |
| wings | 机翼 | |
| air-breathing engine | 吸气式发动机 | |
| solid rocket motor / booster | 固体火箭发动机 / 助推器 | |
| liquid rocket engine | 液体火箭发动机 | |
| oxidizer | 氧化剂 | |
| fuel tank | 燃料箱 | |
| propeller | 螺旋桨 | |
| jet engine | 喷气发动机 | |
| air sickness bag | 晕机袋 | |
| snacks | 零食 | KSP 社区梗 |
| pre-flight checks | 飞行前检查 | |
| flight plan | 飞行计划 | |
| crew | 机组 | |
| passengers | 乘客 | |
| stunt | 特技 | |
| glider | 滑翔机 | |
| seaplane | 水上飞机 | |
| helicopter | 直升机 | |
| milestone | 里程碑 | |
| contract | 合同 | |
| agency | 机构 | |
| funds / reputation / science | 资金 / 声望 / 科学 | |
| Trivial（合同难度 prestige） | 低难度 | 官方译法 |
| 人名（Orville、Wilbur、Jebediah、Valentina、Garnerin、Kurtis、Corliss Paraventures、Kemper Keratus） | 保留原文 | 不音译 |

## 三、逐条翻译规则

### 1. 字段类型（batch 文件里每条的 `note` 会写明）

- **合同正文**（description / genericDescription / synopsis / notes / completedMessage）：
  完整句子，正常翻译，保留原文的段落结构与语气。
- **参数标题片段**（title，note 里写"该字段被拆成多个片段"）：
  这类片段会在游戏里被拼成一份**清单**，例如
  `你的飞机必须 / 有机翼 / 有认证飞行员 / 载入全部 4 名乘客 / 在小岛机场着陆`。
  所以请译成**动词短语**，**不加句末标点**，并与相邻片段、数字拼接自然。
- **计时参数文本**（preWaitText / waitingText / completionText）：
  游戏会显示成「等待前文本 → 进行中文本 → 完成文本」并配一个倒计时。
  preWaitText/waitingText 若原文有冒号就保留冒号；completionText 不加句号。
  例：`request clearance for takeoff: / requesting clearance for takeoff: / be cleared for takeoff`
  → `请求起飞许可： / 正在请求起飞许可： / 已获准起飞`
- **对话框正文**（text）：飞行员与塔台的通话，中文用航空通话口吻。
- **说话者名称**（characterName）：如 `Air Traffic Control` → `空中交通管制`。
- **导航点名称**（name，节点 PQS_CITY）：地图上的标记名，短而明确。
- **合同组显示名/提示**（displayName / tip）：简短。

### 2. 片段拼接（`ctx` 字段）

`ctx` 给出该片段在**完整句子**里的位置，用 `«»` 标出本片段，`【动态值】`表示运行时插入的动态内容（通常是数字或人名）。

例：`en` = ` passengers to the Island Airfield, wait 30 seconds to disembark...`
`ctx` = `...Fly out « passengers to the Island Airfield, wait 30 seconds...»`
说明整句是 `Fly out [数字] passengers to the Island Airfield...`，
中文可译 `名乘客前往小岛机场，等待 30 秒上下客...`，与前面的"运送"和数字拼成
「运送 4 名乘客前往小岛机场」。

**中文译文请去掉片段首尾的多余空格**（中文不需要空格分词），但要保证与数字拼接后读起来自然。

### 3. 必须原样保留的内容

- **换行转义**：值里的 `\n` 和 `\n\n` 是换行符号（反斜杠 + n 两个字符），**必须原样保留**，数量和位置与原文一致（`\n\n` 表示空行分段）。
- **阿拉伯数字与单位**：`2,500m`、`100 m/s`、`20,000m`、`30 seconds`（→ 30 秒）、`Mach 1`、`KT6A`、"Kitty"。
- **型号与专有名词**：`Oscar-B Fuel Tank`、`KT6A "Kitty" Turboprop Engine`、`KAX`、`AirplanePlus` 等零件/模组名保留原文。
- **呼号与航空数字**：`Kesca One Zero One` → `Kesca 101`；`runway zero niner` → `跑道 09`；`heading zero niner zero` → `航向 090`；`squawk zero one one six` → `应答机 0116`；`Winds three-forty at five to ten` → `风 340 度，5 到 10 节`。

### 4. 禁止事项

- 不要把整句用引号包起来。
- 不要在译文里写真实的换行符（要换行就写 `\n`）。
- 不要改动键名，不要漏条目，不要添加解释性文字。
- 不要出现 `#` 开头的译文。
- 不要把中文译名与官方译法混用（例如必须用"小岛机场"，不能写"岛屿机场"）。

## 四、跨合同重复模式的硬性格式（必须完全一致）

这些模式在 51 个飞行合同里反复出现，各批译文必须统一。

### 1. 航班标题

```
英文: Flight 101 - Crew: 1 Passengers: 4-8
中文: 101 号航班 － 机组 1 人，乘客 4-8

英文: Flight 101 - Crew: 1 Passengers: （片段，后面接动态数字）
中文: 101 号航班 － 机组 1 人，乘客 
```
要点：航班号在前 + `号航班`；分隔用全角 `－`；机组和乘客数量都带`人`；
`Passengers: ` 这种结尾片段保留结尾一个空格，便于与数字拼接。

### 2. 陆空通话（DIALOG_BOX 的 text 字段）

- 前缀：`KSC ATC:` → `KSC 塔台：`；`Island ATC:` → `小岛塔台：`
- 冒号一律用全角 `：`
- 数字用阿拉伯数字：`Kesca One Zero One` → `Kesca 101`；
  `runway zero niner` → `跑道 09`；`runway two seven` → `跑道 27`；
  `heading zero niner zero` → `航向 090`；`squawk zero one one six` → `应答机 0116`；
  `Winds three-forty at five to ten` → `风 340 度，5 到 10 节`
- 标准句式：
  - `you are cleared to the Island Airfield depature on runway zero niner`
    → `你已获准离场前往小岛机场，跑道 09`
  - `we have you on approach` → `我们已看到你进近`
  - `You are cleared to land on Island Airfield zero one`
    → `你已获准在小岛机场 01 号跑道降落`
  - `You are cleared to land on runway two seven` → `你已获准在 27 号跑道降落`
  - `you are cleared to the Space Center airport via the Kerman departure flight plan`
    → `你已获准按 Kerman 离场程序前往太空中心机场`
  - `Depart the Island Airfield heading zero niner zero` → `从小岛机场离场，航向 090`

### 3. 参数清单片段（field=title 且为片段）

拼成清单后要读得通，例如：
```
你的飞机必须 / 有机翼 / 有认证飞行员 / 载入全部 4 名乘客 /
在小岛机场着陆 / 等待乘客换乘 / 安全地 / 不损坏飞机 / 不造成人员伤亡 /
然后着陆并停止 / 在以下回收区域之一 / KSC 跑道 / 或 KSC 航站楼 /
安全回收全部 4 名乘客
```
要点：动词短语、不加句末标点、不重复"必须"、片段首尾不要多余空格。

### 4. 计量与标点

- 数字用阿拉伯数字：`2,500m`、`100 m/s`、`30 seconds` → `30 秒`、`Mach 1` → `马赫 1`
- 中文标点：`，` `。` `：` `；` `！` `？`；分量列举用 `、`
- `&br;` / `\n` 与 `\n\n` 按原文原样保留
