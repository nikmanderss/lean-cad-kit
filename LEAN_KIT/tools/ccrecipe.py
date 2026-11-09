# KIT INSTRUMENT `ccrecipe` - recover every CC_* lever a run was --set with, per tag, from a session transcript.
# Run: kit tool ccrecipe --job <JOB> --set KEY=VALUE ...   (output lands in that job's folder)
# Inputs: CC_JSONL (the transcript)  CC_SCRIPTS (default "_ccextract.py,_ccweld.py"). For runs made before env<TAG>.json recorded CC_* levers.
import json, os, re, sys

SCRIPTS = os.environ.get("CC_SCRIPTS", "_ccextract.py,_ccweld.py").split(",")
seen = {}
with open(os.environ["CC_JSONL"], encoding="utf-8", errors="replace") as fh:
    for line in fh:
        if "CC_" not in line:
            continue
        try:
            rec = json.loads(line)
        except Exception:
            continue
        msg = rec.get("message") or {}
        for part in (msg.get("content") or []) if isinstance(msg.get("content"), list) else []:
            if not isinstance(part, dict) or part.get("type") != "tool_use":
                continue
            cmd = (part.get("input") or {}).get("command") or ""
            for scr in SCRIPTS:
                if scr not in cmd:
                    continue
                for chunk in cmd.split(scr)[1:]:
                    chunk = chunk.split("kit.py")[0]
                    tag = re.search(r"--tag\s+([A-Za-z0-9_]+)", chunk)
                    sets = re.findall(r'--set\s+"?(CC_[A-Z_0-9]+)=([^"]*?)"?(?=\s+--|\s*$|\s*;|\s*&&|\s*>)', chunk)
                    if not tag or not sets:
                        continue
                    key = (scr, tag.group(1))
                    seen[key] = (rec.get("timestamp", "?"), sets)
for (scr, tag), (ts, sets) in sorted(seen.items(), key=lambda kv: kv[1][0]):
    print("%s  %-12s %-6s" % (ts[:19], scr.replace(".py", ""), tag), flush=True)
    for k, v in sets:
        print("        %-16s %s" % (k, v[:140]), flush=True)
print("DONE", flush=True)
