# 本地海报库检索与取图

仅在查找真实海报案例或取图时读取。图库与 Skill 分开，新增案例无需修改 Skill。

## 定位

库根目录的优先级：用户本次明确指定 → 当前项目明确配置 → Skill 目录内可选的 `library.local.json` 的 `library_root`。相对路径分别相对声明它的配置文件目录解析。优先级更高的明确路径无效时报告具体问题，保持该库未解析，不自动使用低优先级的其他库；继续不依赖图库的工作，待正确路径或替代选择明确后再访问图库。

Skill 随附的本机默认路径仅保存在 `library.local.json`，分享 Skill 时可去掉此文件或替换配置；用户与项目仍可按上述优先级覆盖。库未配置或确实缺少合适案例时，可以联网检索真实海报作为本次参考，说明缺口；不自动扩充库。

现有库的关键入口：

- `cases/<ID>/case.json`：唯一结构化来源，包含作品身份、图片路径、来源和分析。
- `index.jsonl`：生成的检索索引；查看实际字段后检索，不向索引直接写标注。
- `taxonomy.md`、`GLOSSARY.md`：需要受控流派 ID、别名或判定边界时读取。
- `tools/library.py`：现成的检索、校验、构建和暂存 CLI；消费案例只需 search / stage。

先确认库根和 CLI 存在，再以可用 Python 运行 `--help`。已有检索器不需要新建数据库、服务或嵌入模型。

## 检索

PowerShell 中将 `$libraryRoot` 设为上述解析出的绝对路径，`$posterPython` 设为已确认可用的 Python 命令或绝对路径；`$taskRoot` 是当前任务的绝对输出目录。

```powershell
$posterCli = Join-Path $libraryRoot 'tools/library.py'
& $posterPython -X utf8 $posterCli search --root $libraryRoot --query '超现实主义 拼贴' --diverse --limit 8
```

查询和数量随任务调整。探索用默认 OR 加 `--diverse`，在新任务中传稳定的 `--seed <task-id>`；共同必需的关键词用 `--match all`。可按 `--family`、`--history`、`--relation`、`--composition`、`--concept`、`--driver`、`--use` 筛选，ID 以实际 CLI 为准。同一维度多值取 OR，不同维度取 AND；流派与关系必须来自同一条艺术史记录。

排序先保留每张图的命中覆盖度；多样性模式在同覆盖度内补足尚未出现的查询词，再按相关性权重和作者/视觉路线/构图重复情况排列。同等相关的候选以使用上下文和 seed 排序，不再让早期 ID 固定优先；同一查询与 seed 可复现。查看 `matched_terms`、`missing_terms`、`matched_fields`，不把部分命中当作全部满足。短词“瑞士、留白、网格、超现实”有明确别名；“重复、旋转”保留自由词以避免压成单一形式。未知长词保持完整。需要分类边界或空结果处理时，读取库中的 `RETRIEVAL-GUIDE.md`。

实际读取入选 `case.json` 的 `analysis`、`observed`、`art_history` 并看图；得分不等同于审美或适书程度。硬条件下候选不足时如实说明，不为凑数默默取消限制。

关系类型：`historical_affiliation` 为历史归属；`documented_influence` 为有据影响；`visual_affinity` 为视觉近似；`revival` 为复兴或致敬。结合 `evidence_scope` 和来源理解，不把作者级证据升级为作品级归属。标注状态 `draft` / `needs_review` / `reviewed` 与历史关系是两件事，初标不冒充独立复核。`reviewed` 还须有来源与看图记录，并匹配当前图像哈希；来源不明的作者或约略年代可在已复核记录中保留未知。

## 使用账本与同批上下文

账本是本地使用事实，不是偏好记忆。路径依次采用用户指定、项目配置、`library.local.json` 的可选 `usage_ledger`；未配置时用项目根下 `.poster/reference-usage.jsonl`。记录所用绝对路径。首次无文件视为空历史；格式错误必须修正或明确选择不带历史检索，不能默默忽略。搜索不写文件。

```powershell
# $posterUsageLedger 是按上文解析的绝对路径；不是 --history 艺术史筛选。
& $posterPython -X utf8 $posterCli search --root $libraryRoot --query '记忆 手写' --diverse --limit 12 --seed $posterTaskId --usage-ledger $posterUsageLedger --recent-tasks 20
# 只有其他分支已选参考时才附 --batch-ids；这些 ID 不会被排除。
& $posterPython -X utf8 $posterCli search --root $libraryRoot --query '人物 拼贴' --diverse --limit 12 --seed $posterTaskId --usage-ledger $posterUsageLedger --batch-ids P-0020 P-0032
```

窗口按最后出现的不同任务计数，同一任务的多次展示只记一次；`--recent-tasks 0` 关闭近期降权。默认 20 可按工作频率调整。结果的 `recent_shown` / `recent_used` / `batch_repeat` / `batch_composition_overlap` / `context_penalty` 解释上下文影响。强相关结果保留优先级，重复只作同等相关候选间的轻度降权。

事件保存在任务目录，记录实际发生的展示和生图输入。沿用现有账本语义：shown_ids 是已展示案例，used_ids 仅在确实传入生图时填写。原生排版直接借鉴构图时，将实际依据写在 route_skeletons 与 note，注明原生制作；源照片/画作的直接合成另记任务材料记录，不伪造生图输入。近期 used 统计因此不能覆盖全部原生借鉴，比较时同时看 shown 和构图记录。示例 ID 仅演示格式：

```json
{
  "event_id": "task-id:references:1",
  "task_id": "task-id",
  "timestamp": "2026-11-08T12:00:00+08:00",
  "shown_ids": ["P-0020", "P-0032"],
  "used_ids": [],
  "route_skeletons": [
    {"route_id": "A", "reference_ids": ["P-0020"], "description": "实际借鉴的焦点、轴线与图文关系"}
  ],
  "note": "已展示；尚未生图，不代表用户选中。"
}
```

```powershell
& $posterPython -X utf8 $posterCli record-usage --root $libraryRoot --usage-ledger $posterUsageLedger --event $posterUsageEvent
```

shown_ids、used_ids 和 route_skeletons 中的案例 ID 必须已存在于当前库。联网取得的库外参考在任务参考记录中保留临时标识、来源、实际展示/输入与借鉴事实，不把临时标识传给 record-usage，也不为记账自动入库；其使用历史尚不参与库内近期排序。

协调者单写账本；子代理提交事件，不并发写。相同 event_id 与相同内容重复提交不增计数；同 ID 不同内容报错，新事实使用新事件。不要将示例记为真实历史，或将历史展示说成用户喜好。

离线浏览页默认只用内置查询与多样性排序，不读取本地使用账本。Python/浏览器引擎传入同一 seed、usage_counts、batch_ids 时排序一致；需要跨任务使用上下文时用上述 CLI。不要声称浏览页已经共享 CLI 历史。

## 暂存选定的参考候选

先确定实际要展示的 ID，再调用已有 stage。下面的 ID 只是命令示例，不能成为固定选例。

```powershell
$posterReferenceDest = Join-Path $taskRoot 'references'
& $posterPython -X utf8 $posterCli stage --root $libraryRoot --ids P-0020 P-0032 --dest $posterReferenceDest
```

目标必须尚不存在且位于库外；需要另一组时使用新的任务子目录，不覆盖。stage 保持 ID 输入顺序并去重，复制已有图片原始字节，创建 `images/` 与 `manifest.json`。manifest 保存路径、SHA-256 和完整案例元数据快照；取图成功不表示用户选中了某条设计路线。

读取 manifest 给出的实际图片路径并查看、展示原图。原文件是库里已有预览图的副本，不表示取得馆藏母版。暂存不裁切、压缩、重绘或强制制作集合图；对本任务的改绘另存输出。

这套 CLI 面向海报案例，不能拿来给本次检索的照片和图表建库。具体素材保存在任务的独立目录（如 `materials/`），并在任务材料记录中保存来源和用途，不修改案例库、索引或浏览页。
