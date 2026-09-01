# AI 宣称收复与“收复故土”战略实施计划

日期：2026-09-01

设计依据：`docs/superpowers/specs/2026-09-01-ai-claim-reclamation-design.md`

## 实施约束

- 权威环境：Victoria 3 1.13.11、Tech & Res 1.6、Firefall 0.1.1。
- 加载顺序：Tech & Res → Firefall → 本 Mod。
- 不修改上游文件，不调用 FFPA Firefall Flavor Pack 的 effect、变量或定义。
- 不新增 on_action、define、持久变量或存档迁移。
- 不执行 `git add`、`git commit`、`git reset`、`git checkout --`、`git clean`、rebase 或 push。
- 所有实现编辑使用补丁方式完成，并保留用户已有工作树修改。

## 步骤 1：实施前重新建立最终数据库基线

1. 运行 `git status --short --branch`，确认并保留用户修改。
2. 用 `rg --files -uu -g '!/.git/**'` 重新盘点目标 Mod。
3. 解析并记录当前版本：
   - 游戏 `launcher/launcher-settings.json`；
   - Tech & Res `.metadata/metadata.json`；
   - Firefall `.metadata/metadata.json`；
   - 本 Mod `.metadata/metadata.json`。
4. 重新读取以下最终定义和引用：
   - 原版 `ai_strategy_default` 的战略地区、秘密目标与战争目标评分；
   - Tech & Res/Firefall `ztr_diplomatic_strategies.txt` 的后期及超级大国外交战略；
   - Firefall `uw_homeland_strategies.txt` 的完整 `ai_strategy_uw_reclaim_homelands`；
   - Firefall `uw_triggers.txt` 的故土 trigger；
   - 原版 `return_state` 与 `conquer_state` 战争目标有效性。
5. 保存 Firefall 八个待注入子表的干净基线，用于完成后的逐段差异复核。

完成标准：确认上游版本和目标定义未在设计批准后变化；若已变化，先停止实现并重新评估设计数值与覆盖块。

## 步骤 2：新增宣称检测 trigger

新建 `common/scripted_triggers/ffpa_ai_claim_triggers.txt`。

### `ffpa_has_unowned_claimed_state`

使用与 Firefall `uw_has_unowned_primary_culture_homeland` 相同的 country-scope 遍历结构：

1. 遍历其他国家；
2. 排除 `this = root`；
3. 排除 `is_subject_of = root`；
4. 排除 `is_country_type = decentralized`；
5. 要求其任一州满足 `has_claim_by = root`。

### `ffpa_has_adjacent_unowned_claimed_state`

使用与 Firefall `uw_has_adjacent_unowned_primary_culture_homeland` 相同的相邻州结构：

1. 从 root 国家任一自有州进入 `any_neighbouring_state`；
2. 要求相邻州满足 `has_claim_by = root`；
3. 排除 owner 为 root；
4. 排除 owner 为 root 的附属国；
5. 排除分权国家 owner。

完成后检查：

- 两个 trigger 均为纯判断，无 effect、变量写入或日志副作用；
- `root` 始终保持评估 AI 国家；
- ID 在原版、Tech & Res、Firefall 和本 Mod 中不存在冲突。

## 步骤 3：注入“收复故土”战略

新建 `common/ai_strategies/zzzz_ffpa_claim_reclamation_strategy.txt`，定义：

```text
INJECT:ai_strategy_uw_reclaim_homelands = { ... }
```

只重述以下八个直接子表。每个子表先从 Firefall 0.1.1 完整复制，再进行窄修改。

### 3.1 `possible`

保留：

- `is_subject = no`；
- root 不是分权国家。

将资格条件改为 OR：

- `uw_has_unowned_primary_culture_homeland = yes`；
- `ffpa_has_unowned_claimed_state = yes`。

### 3.2 `weight`

按脚本执行顺序写入：

1. `value = 150`；
2. 相邻文化故土 `add = 150`；
3. 相邻实际宣称 `add = 250`；
4. 保留 `country_fervor_primary_culture / 2`；
5. 强势军方 `multiply = 1.5`；
6. 激进左翼政府 `multiply = 0.5`；
7. 最后在 `ffpa_has_unowned_claimed_state = yes` 时 `add = 11000`。

必须确保 `+11000` 位于所有乘数之后，使实际宣称路径最终高于两个 `10000` 超级大国战略。

### 3.3 `diplomatic_play_boldness`

保留 Firefall 原值和 `+50` 奖励。把目标条件扩展为：目标国任一州为 root 的主流文化故土，或满足 `has_claim_by = root`。

### 3.4 `aggression`

保留 Firefall 的基础值、相邻奖励、相对国力奖励、敌对态度折减和意识形态倍率。把“目标国持有主流文化故土”的条件扩展为“持有主流文化故土或实际宣称”。

### 3.5 `state_value`

保留可达性、本国/附属国排除和相邻倍率。目标州条件扩展为：主流文化故土或 `has_claim_by = root`。

### 3.6 `secret_goal_scores`

保留 `conquer` 秘密目标、可达性、相邻和相对国力加值。目标国家资格扩展为：任一州为主流文化故土或实际宣称。

### 3.7 `wargoal_weights`

完整保留四个上游键并设置：

- `annex_country = 1.25`；
- `conquer_state = 0.75`；
- `return_state = 3.0`；
- `force_nationalization = 0.25`。

### 3.8 `wargoal_scores`

`return_state`：

- 保留 `can_reach_target_state = yes`；
- 目标州 `has_claim_by = root` 时 `add = 500`；
- 相邻目标州再 `add = 250`。

`conquer_state`：

- 只给无宣称主流文化故土 `add = 150`；
- 相邻时再 `add = 100`；
- 若 `scope:target_country` 任一州满足 `has_claim_by = root`，额外 `add = -250`；
- 不设置零权重、绝对禁令或绕过战争目标 `valid` 的条件。

完成标准：八个子表之外的 Firefall 战略字段完全由上游继续提供；文件中不复制整个顶层战略。

## 步骤 4：同步玩家可见说明

修改：

- `localization/english/ffpa_core_balance_l_english.yml`；
- `localization/simp_chinese/ffpa_core_balance_l_simp_chinese.yml`。

在两份文件中加入相同键 `ai_strategy_uw_reclaim_homelands_desc`，覆盖 Firefall 原说明：

- 英文说明实际宣称优先、主流文化故土其次；
- 简体中文表达相同行为；
- 不承诺立即宣战、必胜或完全禁止普通征服；
- 不覆盖名称键，继续使用上游 “Reclaim Homelands / 收复故土”。

保留两份文件的语言头、UTF-8 BOM、换行和现有缩进风格。

## 步骤 5：更新模块所有权与版本文档

### `README.md`

新增“AI 宣称收复”章节，说明：

- 实际宣称驱动战略选择；
- `return_state` 强软偏好；
- 文化故土仍可普通征服；
- 超级大国在持有境外实际宣称时可切换战略；
- 旧存档等待原生战略重抽。

在“覆盖风险”中加入：

- `INJECT:ai_strategy_uw_reclaim_homelands`；
- 两个 Firefall `uw_*homeland` trigger 依赖；
- Firefall 更新后八个子表必须重比。

### `AGENTS.md`

新增“AI 宣称收复”模块所有权，登记：

- 两个新文件；
- 两个稳定 `ffpa_*` trigger ID；
- 上游稳定 ID `ai_strategy_uw_reclaim_homelands`；
- `INJECT:` 的八个完整子表复核要求；
- 本模块不拥有全局战略刷新 define 或强制 `set_strategy` 生命周期。

同步更新覆盖表和最低验证列表。

### `.metadata/metadata.json`

仅把版本从 `1.0.0` 提升为 `1.1.0`，不改变 Mod ID、游戏版本、依赖或加载顺序。

## 步骤 6：静态验证

依次完成：

1. `jq empty -- .metadata/metadata.json`；
2. 检查新增脚本的括号、字符串、注释和顶层结构；
3. 用 `rg -n` 同时搜索两个新 trigger 的定义与全部引用；
4. 搜索 `ai_strategy_uw_reclaim_homelands`，确认本 Mod 只有一个预期 `INJECT:`；
5. 将八个最终子表与 Firefall 0.1.1 基线逐段比较，逐项标记设计内差异；
6. 搜索本 Mod 自有顶层键，确认没有意外重复；
7. 对两份本地化执行 `xxd -l 3`，确认 BOM 为 `efbbbf`；
8. 提取英文与简体中文键集合，确认集合一致且各自无重复；
9. 运行 `git diff --check`；
10. 运行 `git status --short --branch`，确认只存在计划内文件变化。

静态验证必须明确区分：括号平衡不等于脚本语义正确，最终作用域和战略选择仍需运行时证据。

## 步骤 7：运行时验收

启动游戏或操作 GUI 需要用户明确授权；未经授权时只交付静态结果和以下待测矩阵。

在获得授权或由用户提供测试运行后，使用不纳入版本控制的测试存档验证：

1. 无境外故土、无境外实际宣称：战略不可采用；
2. 只有境外文化故土的普通国家：战略出现率显著高于修改前；
3. 只有境外文化故土的超级大国：仍采用 `10000` 霸权战略；
4. 有非分权国家持有实际宣称：普通国家采用“收复故土”；
5. 有非分权国家持有实际宣称：超级大国也采用“收复故土”；
6. 只有分权国家持有实际宣称：不触发 `+11000`；
7. 同一目标国持有宣称州和无宣称州：AI 首选 `return_state`；
8. 宣称较远、无宣称文化故土相邻：AI 仍偏好宣称，但 `conquer_state` 保持可用；
9. 宣称全部收回：后续战略重抽可恢复霸权或其他外交战略；
10. 玩家控制相同国家：战争目标、恶名和外交合法性不变；
11. 旧存档加载：无迁移错误，下一次外交战略重抽后生效。

跨 `debug*.log`、`error*.log` 和 `game*.log` 搜索稳定 ID，分别建立以下证据：

- 文件加载；
- 顶层注入解析；
- trigger 条件成立；
- 战略实际采用；
- 外交博弈发起；
- `return_state` 成为实际战争目标；
- 最终状态未被后加载内容覆盖。

## 步骤 8：最终交付检查

1. 再次运行 `git diff --check` 和 `git status --short --branch`；
2. 汇总新增、修改文件；
3. 说明 `ai_strategy_uw_reclaim_homelands` 的上游来源和八个注入子表；
4. 声明没有持久变量、存档迁移、全局 define 或玩家规则变化；
5. 分别报告已完成的静态验证、已有日志证据和仍待游戏内验证的项目；
6. 不执行 Git 提交，除非用户另行明确要求。
