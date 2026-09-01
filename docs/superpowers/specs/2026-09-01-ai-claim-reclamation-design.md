# AI 宣称收复与“收复故土”战略设计

日期：2026-09-01

## 目标

在 Victoria 3 1.13.11、Tech & Res 1.6、Firefall 0.1.1 与本 Mod 的最终加载数据库中，让 AI：

- 普遍更倾向于使用 `return_state` 收复已有实际宣称，而不是优先夺取无宣称州；
- 更容易采用 Firefall 的 `ai_strategy_uw_reclaim_homelands`；
- 当存在境外实际宣称时，即使是拥有 `ztr_superpower` 的国家，也可让“收复故土”压过权重为 `10000` 的霸权战略；
- 保留普通征服能力，不把宣称优先写成绝对禁令。

本功能只改变 AI 评估，不改变玩家战争目标、恶名、合法性或外交规则。

## 已确认的产品决策

1. 采用定向注入 Firefall“收复故土”战略的实现，不重写全局 `ai_strategy_default`，也不使用周期 on_action 强制战略。
2. 实际宣称可使“收复故土”压过超级大国霸权战略。
3. 只有境外文化故土、没有实际宣称时，只提高普通战略权重，不压过超级大国霸权战略。
4. 战争目标使用强软偏好：明显奖励 `return_state`，压低 `conquer_state`，但不把后者设为零。
5. 不新增持久变量、迁移状态或高频全世界扫描。

## 最终数据库与上游边界

加载顺序为：原版 → Tech & Res → Firefall → 本 Mod。

最终目标定义 `ai_strategy_uw_reclaim_homelands` 由 Firefall 创建。本 Mod 通过 `INJECT:` 接管其中八个直接子表：

- `possible`
- `weight`
- `diplomatic_play_boldness`
- `aggression`
- `state_value`
- `secret_goal_scores`
- `wargoal_weights`
- `wargoal_scores`

每个被接管的子表都以 Firefall 0.1.1 为基线完整重述，保留无关逻辑。Firefall 更新后必须逐段重新比较。

本功能不修改 Firefall 文件本体，不调用 FFPA Firefall Flavor Pack 的 scripted effect、临时变量或定义。

## 组件设计

### 宣称检测层

新增 `common/scripted_triggers/ffpa_ai_claim_triggers.txt`，定义两个无副作用 country-scope trigger：

- `ffpa_has_unowned_claimed_state`：其他非分权国家拥有至少一个 `has_claim_by = root` 的州；排除本国以及本国附属国持有的州。
- `ffpa_has_adjacent_unowned_claimed_state`：本国任一州的相邻州具有本国宣称，且其拥有者不是本国、本国附属国或分权国家。

两个 `ffpa_*` ID 作为稳定技术接口保留，不用于存档持久状态。

### 战略资格与出现权重

`possible` 保留独立、非分权国家限制，并允许以下任一条件成立：

- Firefall 的 `uw_has_unowned_primary_culture_homeland = yes`；
- `ffpa_has_unowned_claimed_state = yes`。

`weight` 按顺序计算：

1. 基础值 `150`；
2. 存在相邻境外文化故土时 `+150`；
3. 存在相邻境外实际宣称时 `+250`；
4. 保留 Firefall 的民族热情加值；
5. 保留强势军方 `×1.5`；
6. 保留激进左翼政府 `×0.5`；
7. 若存在任何境外实际宣称，最后追加 `+11000`。

将实际宣称奖励放在其他倍率之后，确保其最终权重高于 Tech & Res 两个 `10000` 权重的超级大国霸权战略。没有实际宣称时，文化故土路径通常为 `150–300+`，只与普通后期战略竞争。

### 目标国家选择

以下现有 Firefall 条件从“目标国拥有本国文化故土”扩展为“目标国拥有本国文化故土或实际宣称”：

- `diplomatic_play_boldness`
- `aggression`
- `secret_goal_scores.conquer`

保留 Firefall 原有的相邻、相对国力、意识形态和可达性计算，不提高总体并发数量，也不改变外交行动合法性。

### 州价值与战争目标选择

`state_value` 将实际宣称州纳入 Firefall 的高价值州集合，并保留相邻州加成。

战争目标权重调整为：

| 战争目标 | Firefall 0.1.1 | 最终值 |
|---|---:|---:|
| `annex_country` | 1.25 | 1.25 |
| `conquer_state` | 2.0 | 0.75 |
| `return_state` | 2.0 | 3.0 |
| `force_nationalization` | 0.25 | 0.25 |

战争目标评分调整为：

- 所有可达实际宣称州为 `return_state` 增加 `500`；相邻时再增加 `250`。
- 无宣称文化故土为 `conquer_state` 增加 `150`；相邻时再增加 `100`。
- 当 `scope:target_country` 仍持有本国任一实际宣称时，其无宣称州的 `conquer_state` 评分额外减少 `250`。

该模型允许其他战略评分、州价值和外交环境在差距足够大时仍选择普通征服。

## 生命周期与存档

- 不修改 `NAI` define，不改变全体 AI 的战略随机因子或刷新频率。
- 不使用月度、年度或加载时 on_action 强制 `set_strategy`。
- 新游戏在初始外交战略选择时使用新权重。
- 旧存档不需要迁移；现有 AI 国家在下一次原生外交战略重抽后采用新逻辑。
- 宣称全部收回后，实际宣称的 `+11000` 消失；若仍有文化故土，战略保持普通权重，之后可在原生重抽时切回霸权或其他外交战略。

## 失败与回退

- 分权国家持有的州不触发实际宣称战略加成，避免不可用于 `return_state` 的目标锁住外交战略。
- 无法到达或因其他游戏规则而无效的宣称州不会获得战争目标评分；本功能不绕过原版和上游合法性检查。
- 没有有效实际宣称时，战略自动回退到文化故土路径；两者都不存在时，`possible` 为假。
- 本功能没有 effect 或持久状态。脚本解析或引用失败只能通过加载日志暴露，不会留下需要清理的半完成存档状态。

## 文件变更

### 新建

- `common/scripted_triggers/ffpa_ai_claim_triggers.txt`
- `common/ai_strategies/zzzz_ffpa_claim_reclamation_strategy.txt`

### 修改

- `localization/english/ffpa_core_balance_l_english.yml`
- `localization/simp_chinese/ffpa_core_balance_l_simp_chinese.yml`
- `README.md`
- `AGENTS.md`
- `.metadata/metadata.json`，版本由 `1.0.0` 提升为 `1.1.0`

现有战略名称保持“Reclaim Homelands / 收复故土”。说明文本改为同时描述实际宣称与主流文化故土，并明确实际宣称优先。

## 验证设计

### 静态验证

- `.metadata/metadata.json` 可解析，版本为 `1.1.0`。
- 新增与修改脚本的括号、字符串、注释和顶层结构正常。
- 八个被注入子表与 Firefall 0.1.1 逐段比较，差异仅限本设计。
- 所有 trigger 引用均能在最终加载数据库中解析。
- 英文与简体中文键集合一致、无重复并保留 UTF-8 BOM。
- 同一 Mod 内不存在意外重复自有顶层键。
- `git diff --check` 无新增空白错误。

### 运行时验收矩阵

| 场景 | 预期结果 |
|---|---|
| 无境外文化故土、无境外实际宣称 | “收复故土”不可选 |
| 只有境外文化故土 | 普通国家更容易采用；超级大国仍保持霸权战略 |
| 存在境外实际宣称 | 普通国家与超级大国均优先采用“收复故土” |
| 只有分权国家持有宣称州 | 不触发实际宣称的 `+11000` |
| 目标国同时拥有宣称州和无宣称州 | AI 优先使用 `return_state` |
| 宣称州较远、无宣称文化故土相邻 | 仍明显偏好宣称，但普通征服保持可用 |
| 宣称全部收回 | `+11000` 消失，后续重抽可恢复其他外交战略 |
| 玩家控制相同国家 | 战争目标、恶名和外交合法性不变 |
| 旧存档加载 | 无迁移错误；下一次原生战略重抽后生效 |

运行时证据依次区分：文件加载、顶层注入解析、战略实际采用、外交博弈发起、战争目标选择和最终战争目标未被后续内容改写。

## 非目标

- 不强制 AI 立即发动战争。
- 不保证弱国攻击无法战胜的宣称持有国。
- 不修改统一战争的四种开战分支或 10% 恶名功能。
- 不修改殖民并发上限、普通战争并发上限或全局战略刷新 define。
- 不让普通征服完全失效。
