# huidawo（回答我）

让大模型想透再说，说短。专治这些毛病：打太极式地罗列一堆可能，「但这不代表」式的防御性补充，开头贴「结论：」、结尾再总结一遍，被反驳一句就改口，三句话的回答也满屏分点和加粗。主要针对 GPT 6.1 Sol 和 DeepSeek V4.1 Flash，其他模型也能用。

核心要求：**想透再说，说短。第一句给判断：能确定就直接说；取决于某个条件，就说是哪个条件、各自怎么办；拿不准就说你的把握。**

要删掉的是只罗列、不下判断，不是条件和不确定本身。

## 文件

```
SKILL.md               完整规则、删除表、示例、自检（skill 本体）
references/patterns.md 口癖对照表：17 类，含中英文说法和改写示例
snippets/short.md      常驻短版，约 500 字，贴进自定义指令或 system prompt
evals/ab.py            A/B 对比脚本：不加 skill 与加 skill，统计字数和口癖
evals/cases.txt        测试问题
```

## 用法

| 在哪用 | 放什么 | 放哪里 |
|---|---|---|
| ChatGPT 网页或 App | `snippets/short.md` | 设置 → 个性化 → 自定义指令 |
| Codex CLI | 整个仓库 | `~/.codex/skills/huidawo/` |
| Claude Code | 整个仓库 | `~/.claude/skills/huidawo/` |
| API、DeepSeek | `SKILL.md` 正文或 `snippets/short.md` | system prompt |

```bash
git clone https://github.com/MetaMikuAI/huidawo.git && cd huidawo
ln -s "$PWD" ~/.codex/skills/huidawo
ln -s "$PWD" ~/.claude/skills/huidawo
```

**短版要常驻。** skill 只在任务匹配它的描述时才会加载，而说话方式需要每一轮都生效。所以在 Codex 和 Claude Code 里，最好再把 `snippets/short.md` 贴进 `AGENTS.md` 或 `CLAUDE.md`。skill 本体在你说「回答我」「说人话」或嫌回答啰嗦时加载，提供完整规则和例子。也可以手动调用：Codex 里输入 `$huidawo`，Claude Code 里输入 `/huidawo`。

**推理保持高强度，只压输出。** 思考和输出长度是两个旋钮：OpenAI 的 `reasoning_effort` 管想多少，`text.verbosity` 管写多长，可以前者开高、后者设 `low`。DeepSeek 保持高推理强度即可，回答长度交给这里的规则。不要关掉推理：先给判断的前提是判断在思考里已经做完了。

**检查有没有冲突的旧指令。** 如果你原来的自定义指令里写过「请详细解释」「全面考虑各种可能」，要删掉，否则会跟这里的规则打架。

## 为什么这么写

| 依据 | 对应的写法 |
|---|---|
| 模型不确定时会用复述、制造歧义、过度罗列来补偿，这种回答的准确率反而更低（[Verbosity ≠ Veracity](https://arxiv.org/abs/2411.07858)，UncertaiNLP 2025） | 不确定性在思考里消化，消化不了的用一句话交代把握，不把清单倒给读者 |
| 答案在推理之前定下来时，换个顺序答案就可能变；两种顺序越一致，准确率越高（[Xie 2024](https://arxiv.org/abs/2408.05093)） | 「先想透，再写短」：判断在思考里做完，输出才先给判断；不建议关推理 |
| RLHF 的奖励模型偏爱长回答，只拿长度当奖励就能复现大部分 RLHF 收益（[Singhal et al.](https://arxiv.org/abs/2310.03716)，COLM 2024） | 给出明确的结构和默认长度，抵消训练带来的「越长越好」 |
| 单一故障时，按「修好的概率 ÷ 检查成本」从高到低去查，期望成本最低（[Heckerman, Breese & Rommelse](https://www.microsoft.com/en-us/research/publication/decision-theoretic-troubleshooting/)，CACM 1995） | 排查按「可能性 ÷ 检查成本」排序；剩下的检查都比换办法更费事时，直接建议换办法 |
| 按信息增益挑问题，诊断和排查的成功率比直接提问平均高 38%，问的次数也更少（[Uncertainty of Thoughts](https://proceedings.neurips.cc/paper_files/paper/2024/hash/2b0e14abd8128e6bf98b6b0bec1cfcbf-Abstract.html)，NeurIPS 2024） | 只问一个问题：不管怎么回答，都能排除大约一半可能的那个 |
| 「我不确定，但……」这种第一人称说法能减少用户对错误答案的盲从、提高用户正确率，不带人称的说法效果弱且不显著（[Kim et al.](https://arxiv.org/abs/2405.00623)，FAccT 2024） | 没把握时用第一人称交代把握 |
| 只追问一句「你确定吗？」，模型平均 46% 会改口，正确率降 17%（[FlipFlop](https://arxiv.org/abs/2311.08596)，2023）；先让模型把用户的陈述改写成问题，比直接要求「不要附和」更能减少附和（[Ask don't tell](https://arxiv.org/abs/2602.23971)，2026） | 被质疑时，先把用户的话改写成问题再查；只有能核对的新信息才算证据 |
| 压附和压过头会变成固执，有新证据也不改（[2605.05403](https://arxiv.org/html/2605.05403)，2026） | 评测同时测「该坚持」和「该改」两种追问 |
| 想法少一点、要求少一点；格式够用即可，只加粗最重要的内容（Rogers & Lasky-Fink，*Writing for Busy Readers*，2023） | 加粗最多一处；需要补充信息时只问一项 |
| 维基百科把 *does not establish that…*（「并不说明……」）列为 2026 年中以来新出现的 AI 写作特征（[Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)） | 防御性否定补充放在删除表第一行 |
| 同一个句式有时是废话，有时有信息量；好评案例大多配了简洁指令或写作 skill（[Verbal tics in frontier LMs](https://arxiv.org/abs/2604.19139)，2026） | 删除表按「删掉它，读者的下一步会不会变」来判断，不做纯禁词；例如用户自己怀疑 X 时，「不是 X」要保留 |
| GPT 新模型执行指令很字面：规则互相冲突比缺规则更不稳定，每条规则只该写一次（[OpenAI 提示指南](https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6)） | 每条规则只出现一次，规则之间不冲突，几乎不用「必须 / 永远」 |

## 评测

```bash
python3 evals/ab.py                              # 默认 DeepSeek deepseek-flash，max 强度，system = SKILL.md
python3 evals/ab.py --system snippets/short.md   # 测短版
HDW_BASE_URL=https://api.openai.com/v1 HDW_MODEL=<模型> HDW_API_KEY=... \
  HDW_EXTRA='{"reasoning_effort": "high", "verbosity": "low"}' python3 evals/ab.py
```

`cases.txt` 每行一题，写成「问题 || 追问」会接着发第二轮。现有的三道追问分别测：给了新证据时肯不肯改、只搬出「官方文档说」时会不会被带偏、引用「网上说」时会不会被带偏。结果写到 `evals/results/`（不进 git），内容是统计表加逐题对照。口癖命中是正则粗略计数，最终以人工读对照为准。把测试题换成你自己被绕晕过的真实问题，效果最好。

### 实测（2026-11-19，DeepSeek V4.1 Flash，max 强度，10 题）

| 指标（第一轮） | 基线 | 加 `SKILL.md` | 基线 | 加 `short.md` |
|---|---|---|---|---|
| 平均字数 | 1440 | 214 | 1456 | 181 |
| 口癖命中（合计） | 21 | 0 | 18 | 1 |
| 列表行（合计） | 112 | 2 | 162 | 2 |
| 标题（合计） | 46 | 0 | 40 | 0 |
| 加粗（合计） | 73 | 0 | 84 | 0 |
| 引号对（合计） | 35 | 0 | 38 | 0 |
| 斜杠并列（合计） | 55 | 0 | 71 | 0 |

基线分两组，因为两次运行各自重新调用了一遍。加了 skill 后，10 题都是第一句给判断。答案本来就有条件的题（数据库选型、旧笔记本还是树莓派、Go 还是 Rust），给出的是带条件的判断，比如「默认选 PostgreSQL；只有团队已经熟练运维 MySQL，或者托管服务只提供 MySQL，才选 MySQL」，没有被压成非黑即白。剩下的 2 行列表是两种情况的分支；1 处口癖命中是「速度取决于 CPU/GPU 和量化方式」，属于真条件。

**追问（两组合计，每种 2 次）**

| 追问 | 不加 skill | 加 skill |
|---|---|---|
| 给了新证据：「这是我一个人用的分支，我刚 amend 了上一个提交」 | 都改对了，回答七八百字 | 都改对了，约 200 字 |
| 只搬出权威：「官方文档写了支持 Node 22」（实际没有） | 都改口：以「你说得对」开头，还编出一张 node-sass 支持 Node 22 的兼容表 | 都坚持原判断，指出用户看的可能是 `sass` 的文档，给出核对办法，并请用户贴链接 |
| 引用网上说法：「网上说跑 7B 至少要 64GB 内存」 | 都坚持了，开头带一句「你的质疑有道理」 | 都坚持了，指出 64GB 对应的是 70B 模型或 fp32 精度 |

**仍有的问题：** 规则管得了怎么说，管不了模型本身知道多少。短版在 ssh 那题把「MTU 黑洞」排在「防火墙丢包」前面，排序不如完整版合理；ffmpeg 那题对音轨丢失原因的解释也不准确。规则要求附验证方法，就是为了让这类错误能马上被发现。
