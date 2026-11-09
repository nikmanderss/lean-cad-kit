# Installing the Lean CAD Kit

Windows 11 is the platform this release was built and tested on. Every command below is one PowerShell line.
Replace `<you>` with your Windows user name, and the example folders (`C:\CAD\LEAN_KIT`, `C:\CAD\Projects\MyPart`)
with your own.

## 1. What gets installed, and why

| piece | what it does for the kit |
|---|---|
| **Python 3.12** (64-bit, python.org) with `numpy`, `scipy`, `pillow`, `matplotlib` | runs `kit.py` and the Claude Code hooks; Pillow stamps the review frames, numpy and scipy build them |
| **FreeCAD 1.1** | the geometry kernel. The kit runs `FreeCADCmd.exe` headless, one step per process, under a hard timeout. The GUI is for opening deliveries and saving the one template a delivery needs |
| **Claude Code** | the agent: the desktop app or the CLI |
| **A Claude plan** | a Claude Max plan; the ultra tier is recommended |
| **Git for Windows** | Claude Code's Bash tool on Windows runs Git Bash; the kit's guard reads those commands |
| **`LEAN_KIT\`** | the kit itself - one copy per machine, shared by every project |

## 2. Python

1. Download the Python 3.12 Windows installer (64-bit) from <https://www.python.org/downloads/windows/> and run it.
   The default "Install Now" puts it at `C:\Users\<you>\AppData\Local\Programs\Python\Python312\python.exe`.
   Adding it to PATH is optional: the kit always names the interpreter by its full path.
2. Install the four packages with that interpreter:

   ```powershell
   & "C:\Users\<you>\AppData\Local\Programs\Python\Python312\python.exe" -m pip install numpy scipy pillow matplotlib
   ```

3. If you are not sure where your interpreter is, `py -0p` lists every installed Python with its path.

### Windows: Python

On Windows the bare word `python` is often **not a Python at all**: it is the Microsoft Store stub
(`C:\Users\<you>\AppData\Local\Microsoft\WindowsApps\python.exe`), which opens the Store or prints nothing. A hook
whose command cannot start does not fail loudly - it sits in `settings.json` looking installed and never fires.
So the kit never uses the bare word:

- the installer writes the **absolute path of the interpreter that runs it** into every hook, and refuses the Store
  stub outright;
- the guard refuses a command that starts with bare `python`;
- `kit ps "<script>" [args]` generates any command line the agent hands you (`&`-invoked, the interpreter in full,
  absolute quoted paths).

Run the installer with the Python you intend to keep. If you later move or upgrade Python, run the installer again.
To stop the stub from shadowing a real Python in your own shell, turn off `python.exe` and `python3.exe` under
Settings > Apps > Advanced app settings > App execution aliases.

## 3. FreeCAD

1. Install FreeCAD 1.1 from <https://www.freecad.org/downloads.php> (the Windows installer).
2. Check the command-line binary:

   ```powershell
   & "C:\Program Files\FreeCAD 1.1\bin\FreeCADCmd.exe" --version
   ```

3. The kit finds FreeCAD through `LEAN_KIT\kit\env.json` (`freecadcmd_candidates`: the first path that exists wins,
   and a candidate may be a glob). It already lists `C:\Program Files\FreeCAD 1.1\` and `FreeCAD 1.0\`. If yours is
   elsewhere, put its `FreeCADCmd.exe` first in that list.
   `env.json` is YOUR machine's file (never part of a release; `env.example.json` is its template). Two optional keys carry a
   project's specifics so the kit itself stays generic: `"frame": {"forward": [x, y, z], "left": [x, y, z], "up": [x, y, z]}` -
   the axes the words front / aft / left / right / up follow in the kit's pictures and messages (absent: the document's own axes,
   -y / +x / +z); `"atlas_token_aliases": {"<old>": "<new>"}` - older status tokens or key names found in a project's existing
   `ATLAS.json` are read as the current ones (`CLIENT` / `CLIENT_OK` / `client_said`), the file is never rewritten.

FreeCAD's own Python carries the numpy, scipy and VTK that the kernel steps use; nothing needs installing there.

## 4. Claude Code

Install Claude Code (the Claude desktop app's Code tab, or the CLI) from <https://claude.com/claude-code> and sign in.
The session that runs the work is the **orchestrator**: pick an Opus-class model for it. Workers and reviewers are
launched by the kit's agent definitions at their own tiers (`haiku`, `sonnet`, `opus`).

Claude Code asks before it runs a command. Approve the kit's commands as they come, or add allow rules for them in
the project's settings. The kit's hooks refuse what the kit forbids regardless of what Claude Code allows.

## 5. Put the kit in place

Copy the `LEAN_KIT` folder of this release to a permanent place, for example `C:\CAD\LEAN_KIT`.

- **One copy per machine.** Every project runs this copy; nothing is copied into a project.
- **Projects live outside it.** The installer refuses a project inside the kit folder, or under any folder named
  `lean_kit`.
- **Not under `%TEMP%`.** The guard lets a session write anywhere under the Windows temp folder (its scratch space),
  so a project placed there has no write boundary.
- The kit's folder name stays `LEAN_KIT`.

## 6. Make a project and wire it

1. Make the project folder, for example `C:\CAD\Projects\MyPart`.
2. Copy the **contents** of this release's `project_template\` into it (`CLAUDE.md`, `PROJECT_FACTS.md`,
   `PROJECT_SUCCESS_CRITERIA.md`, `claude_code\PA12_MJF_Rules_EVALUATED.md`). Fill them in as described in
   [GETTING_STARTED.md](GETTING_STARTED.md).
3. Run the installer for the project:

   ```powershell
   & "C:\Users\<you>\AppData\Local\Programs\Python\Python312\python.exe" "C:\CAD\LEAN_KIT\install_lean_hooks.py" --project "C:\CAD\Projects\MyPart"
   ```

   It writes `MyPart\.claude\settings.json` (the hooks - PreToolUse, PostToolUse, Stop, SessionStart and a SubagentStop hand-back - and the `KIT_HOME` / `PYTHONPATH` / `PYTHONUTF8` / `PYTHONIOENCODING` environment, pointing at the
   kit; an existing file is kept as `settings.json.bak-<time>` and its other settings are preserved), copies the four
   agent definitions into `MyPart\.claude\agents\`, makes `claude_code\jobs\`, `claude_code\bank\`, `Deliverables\`
   and `references\`, seeds `claude_code\KERNEL_LESSONS.md`, writes `claude_code\WHERE_THE_KIT_IS.md` (the
   project's command lines, generated), and records the kit's control manifest (section 8). It ends by printing
   `--status`.

   `--dry-run` says what it would do; `--status` prints what is wired now; `--python "<path>"` names another interpreter; `--list` prints the
   projects this machine has wired; `--all` re-wires every one of them (section 8).

4. **Set Python's UTF-8 mode for your account, once:**

   The installer sets UTF-8 mode for the hooks (`PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8` in the project's
   settings env; every hook also writes UTF-8 on its own), so the kit's documents reach the agent with their dashes
   and arrows intact. No `setx` is needed.

5. **Open Claude Code on the project folder itself** - not its parent. Claude Code reads `.claude\settings.json` and
   `.claude\agents\` from the folder it has open; opened on a parent folder it finds neither and nothing says so.
   Hooks load when a session starts: if a session was already open on the project, start a new one.

## 7. Check that it works

1. The wiring - every hook should end `OK` (this checks that each hook's interpreter and the hook script itself exist - a moved kit reads
   `HOOK SCRIPT NOT FOUND`, so keep the kit where the install found it, or run the installer again):

   ```powershell
   & "C:\Users\<you>\AppData\Local\Programs\Python\Python312\python.exe" "C:\CAD\LEAN_KIT\install_lean_hooks.py" --project "C:\CAD\Projects\MyPart" --status
   ```

2. The kit's own suites - 28 of them, about six minutes; the last line should read `failing: none`:

   ```powershell
   & "C:\Users\<you>\AppData\Local\Programs\Python\Python312\python.exe" "C:\CAD\LEAN_KIT\_run_selftests.py"
   ```

3. In a new session on the project, the first thing the agent sees is the contract (`CONTRACT.md`, `ORCHESTRATOR.md`)
   pushed by the SessionStart hook. Ask it to run `kit status`: it should report the guard alive. A banner saying
   `kit status` prints `guard: NOT RUNNING - ...` (and the kit's running commands print the banner **THE PRETOOLUSE GUARD IS NOT RUNNING**) when Claude Code is open on the wrong folder or the session started
   before the install; at a new project's very first session the guard has simply not run yet - it runs from the first tool call.

## 8. After updating the kit, and several projects

The installer records a checksum of every control file of the kit (its code, its configuration and the governing
documents) in `%USERPROFILE%\.claude\leankit_manifest.json` - **one file per machine**. Each session start compares
the kit with it and lists any control that changed since; it never refuses, but an agent that sees an unexplained
change is told to stop and say so. Every `--project` install also records its project in `%USERPROFILE%\.claude\leankit_projects.json`
(`--list` prints the list), so after you update or edit the kit, one run re-wires every recorded project and records the manifest once:

```powershell
& "C:\Users\<you>\AppData\Local\Programs\Python\Python312\python.exe" "C:\CAD\LEAN_KIT\install_lean_hooks.py" --all
```

Then start a new session in each project. Because the manifest is per machine, installing a second copy of the kit
(a test copy, say) records THAT copy and makes every other project's banner report changes; run the installer for
your real projects afterwards to put it back.

## 9. Removing the kit from a project

Delete the `hooks` and `env` entries the installer added to `<project>\.claude\settings.json` (the `.bak` copy holds
what was there before) and the four agent files in `<project>\.claude\agents\`. Outside the project the kit leaves
only the manifest file and the project list of section 8, and the `PYTHONUTF8` user variable if you set it (section 6, step 4; remove it
under System Properties > Environment Variables).

## 10. Linux and macOS

Not tested. The kit is Python plus FreeCAD's command-line binary, and `env.json` already lists `/usr/bin/freecadcmd`
and `/usr/local/bin/freecadcmd`; the hooks name the interpreter by its absolute path on any system. Much of the
guidance the agent gives (the PowerShell lines `kit ps` generates, the console-window rule) is written for Windows.
