#!/usr/bin/env python3
"""A/B 对比：同一组问题，不加 skill 和加 skill 各问一遍，统计长度和口癖。

接口是 OpenAI 兼容的 /chat/completions，只用标准库。环境变量：
  HDW_BASE_URL   默认 https://api.deepseek.com
  HDW_MODEL      默认 deepseek-flash
  HDW_API_KEY    直接给 key；不给就读 HDW_KEY_FILE
  HDW_KEY_FILE   默认 ~/.config/deepseek/key
  HDW_EXTRA      合并进请求体的 JSON，默认 {"reasoning_effort": "max"}
                 OpenAI 例子：{"reasoning_effort": "low", "verbosity": "low"}

用法：
  python3 evals/ab.py                     # 用 evals/cases.txt 和 SKILL.md
  python3 evals/ab.py --system snippets/short.md --cases my_cases.txt

cases.txt 每行一题；写成「问题 || 追问」时会接着发第二轮，用来测被质疑时会不会改口。
统计只算第一轮回答，第二轮附在对照里人工看。

结果写到 evals/results/（不进 git）。口癖命中是按正则粗略计数：
同一个句式有时有信息量，最终要人工读对照。
"""

import argparse
import concurrent.futures as cf
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TICS = {
    "防御性否定": r"(并)?不(代表|意味着|说明|等于)|不一定|并非一定|不能保证|也不排除|并不是说"
    r"|doesn't (necessarily )?mean|does not establish|isn't to say|not guaranteed",
    "否定式对比": r"不是[^。！？\n]{1,30}而是|与其说[^。！？\n]{1,30}不如说|不仅仅是[^。！？\n]{1,30}更是"
    r"|[Ii]t'?s not [^.\n]{1,40}, it'?s",
    "万能兜底": r"取决于|结合(实际|具体)|因人而异|视(具体)?情况而定|综合考虑|没有标准答案"
    r"|depends on|one-size-fits-all",
    "标签/复述": r"(先说|短)?结论[:：]|一句话(总结)?[:：]|总结[:：]|核心原因[:：]|简单说[:：]|TL;?DR",
    "提示语/总结": r"需要注意的是|值得(注意|一提)的是|总的来说|综上所述|总而言之"
    r"|[Ii]t'?s worth noting|[Ii]n summary",
    "恭维/套话": r"(很|非常)好的问题|希望(这|以上)?(对你)?有(所)?帮助|欢迎(继续)?(提问|追问)"
    r"|[Gg]reat question|[Hh]ope this helps",
    "黑话": r"收口|兜住|落盘|拉齐|颗粒度|抓手|闭环|链路|底层逻辑|赋能",
    "装口语": r"说白了|讲真|老实说|坦白(讲|说)|说实话|扎心",
    "罗列": r"可能是[^。！？\n]{1,40}也可能|以下(几种|几个)?(可能|原因)|首先[\s\S]{1,200}其次",
}

METRICS = (
    ("chars", "平均字数"),
    ("tics", "口癖命中"),
    ("bullets", "列表行"),
    ("headings", "标题"),
    ("bold", "加粗"),
    ("quotes", "引号对"),
    ("slashes", "斜杠并列"),
)


def load_system(path):
    text = open(path, encoding="utf-8").read()
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            text = text[end + 4:]
    return text.strip()


def load_cases(path):
    cases = []
    with open(path, encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln or ln.startswith("#"):
                continue
            turns = [t.strip() for t in ln.split("||")]
            cases.append(turns)
    return cases


def api_key():
    if os.environ.get("HDW_API_KEY"):
        return os.environ["HDW_API_KEY"]
    path = os.path.expanduser(os.environ.get("HDW_KEY_FILE", "~/.config/deepseek/key"))
    return open(path, encoding="utf-8").read().strip()


def chat(messages, cfg):
    body = {"model": cfg["model"], "messages": messages, "max_tokens": 32000}
    body.update(cfg["extra"])
    req = urllib.request.Request(
        cfg["base_url"].rstrip("/") + "/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + cfg["key"], "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        return f"[HTTP {e.code}] {e.read().decode(errors='replace')[:300]}"
    except Exception as e:  # 网络错误不中断整批
        return f"[ERROR] {e}"
    return (data["choices"][0]["message"].get("content") or "").strip()


def run_case(turns, system, cfg):
    messages = [{"role": "system", "content": system}] if system else []
    replies = []
    for turn in turns:
        messages.append({"role": "user", "content": turn})
        reply = chat(messages, cfg)
        replies.append(reply)
        messages.append({"role": "assistant", "content": reply})
    return replies


def measure(answer):
    hits = {name: len(re.findall(pat, answer)) for name, pat in TICS.items()}
    return {
        "chars": len(re.sub(r"\s", "", answer)),
        "tics": sum(hits.values()),
        "hits": {k: v for k, v in hits.items() if v},
        "bullets": len(re.findall(r"^\s*(?:[-*•]|\d+[.、)])\s", answer, re.M)),
        "headings": len(re.findall(r"^#{1,6}\s", answer, re.M)),
        "bold": len(re.findall(r"\*\*[^*\n]+\*\*", answer)),
        "quotes": len(re.findall(r"“[^”\n]{1,30}”", answer)),
        "slashes": len(re.findall(r"[一-鿿]{1,8}/[一-鿿]{1,8}", answer)),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", default=os.path.join(ROOT, "evals", "cases.txt"))
    ap.add_argument("--system", default=os.path.join(ROOT, "SKILL.md"))
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    cfg = {
        "base_url": os.environ.get("HDW_BASE_URL", "https://api.deepseek.com"),
        "model": os.environ.get("HDW_MODEL", "deepseek-flash"),
        "extra": json.loads(os.environ.get("HDW_EXTRA", '{"reasoning_effort": "max"}')),
        "key": api_key(),
    }
    system = load_system(args.system)
    cases = load_cases(args.cases)
    jobs = [(i, arm) for i in range(len(cases)) for arm in ("base", "skill")]

    replies = {}
    with cf.ThreadPoolExecutor(args.workers) as pool:
        futs = {
            pool.submit(run_case, cases[i], system if arm == "skill" else None, cfg): (i, arm)
            for i, arm in jobs
        }
        for n, fut in enumerate(cf.as_completed(futs), 1):
            replies[futs[fut]] = fut.result()
            print(f"\r{n}/{len(jobs)}", end="", file=sys.stderr, flush=True)
    print(file=sys.stderr)

    m = {k: measure(v[0]) for k, v in replies.items()}
    n = len(cases)

    def total(arm, field):
        return sum(m[(i, arm)][field] for i in range(n))

    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    stem = os.path.splitext(os.path.basename(args.system))[0]
    out_dir = os.path.join(ROOT, "evals", "results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"{stamp}-{cfg['model']}-{stem}.md")

    table = ["| 指标（第一轮） | 不加 skill | 加 skill |", "|---|---|---|"]
    for field, label in METRICS:
        b, s = total("base", field), total("skill", field)
        if field == "chars":
            table.append(f"| {label} | {b / n:.0f} | {s / n:.0f} |")
        else:
            table.append(f"| {label}（合计） | {b} | {s} |")

    lines = [
        f"# A/B：{cfg['model']}",
        "",
        f"- 时间：{stamp}",
        f"- 接口：{cfg['base_url']}，额外参数：`{json.dumps(cfg['extra'], ensure_ascii=False)}`",
        f"- system：`{os.path.relpath(args.system, ROOT)}`",
        "",
        *table,
        "",
    ]
    for i, turns in enumerate(cases):
        lines += [f"## {i + 1}. {turns[0]}", ""]
        for arm, label in (("base", "不加 skill"), ("skill", "加 skill")):
            mm = m[(i, arm)]
            hits = "，".join(f"{k}×{v}" for k, v in mm["hits"].items()) or "无"
            lines += [f"### {label}（{mm['chars']} 字，口癖：{hits}）", "", replies[(i, arm)][0], ""]
            for turn, reply in zip(turns[1:], replies[(i, arm)][1:]):
                lines += [f"#### 追问：{turn}", "", reply, ""]
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("\n".join(table))
    print(f"\n完整对照：{out}")


if __name__ == "__main__":
    main()
