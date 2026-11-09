# skin-build
import os, json, time
class busy:
    def __init__(self, what, allow_s):
        self.path = os.environ.get("KIT_BUSY"); self.what = str(what); self.allow = float(allow_s); self.since = None
    def __enter__(self):
        self.since = time.time()
        if self.path:
            try:
                with open(self.path, "w", encoding="utf-8") as fh: json.dump({"what": self.what, "since": self.since, "allow_s": self.allow}, fh)
            except OSError: pass
        return self
    def __exit__(self, *a):
        if self.path:
            try:
                with open(self.path + ".done", "a", encoding="utf-8") as fh:
                    fh.write(json.dumps({"what": self.what, "since": self.since, "end": time.time(), "allow_s": self.allow}) + "\n")
            except (OSError, TypeError, ValueError): pass
            try: os.remove(self.path)
            except OSError: pass
        return False
