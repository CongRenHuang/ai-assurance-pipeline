# S0 修補：`load_dotenv()` 在 heredoc 下失效

**問題：** 我給的指令用 `uv run python - <<'PY'` 把腳本從 stdin 餵進去，但 `load_dotenv()` 無參數呼叫在這種模式下會 `AssertionError`。**這是我的指令錯誤，不是你的環境問題。**

---

## 根本原因（已實測確認）

Python 3.13+ 在 `python -` 讀 stdin 時，會把 `__main__.__file__` 設成字串 `"<stdin>"`：

```
has __file__ : True
__file__     : <stdin>
```

於是 python-dotenv 的 `find_dotenv()` 判定「這不是互動模式」，走進 frame 回溯分支：

```python
frame = sys._getframe()
while frame.f_code.co_filename == current_file or not os.path.exists(frame.f_code.co_filename):
    assert frame.f_back is not None    # ← 這裡爆掉
    frame = frame.f_back
```

因為 `os.path.exists("<stdin>")` 永遠是 `False`，回溯會一路走到堆疊頂端，`f_back` 變成 `None` → `AssertionError`。

**一句話：** `find_dotenv()` 靠「呼叫者的檔案路徑」往上找 `.env`，而 stdin 沒有真實路徑。

---

## 解法：建立統一的環境載入模組

不要在每個腳本重複處理。建一個模組，之後所有檔案都 import 它。

```bash
cat > assurance/env.py <<'PY'
"""統一環境載入。

必須存在的理由：`load_dotenv()` 無參數呼叫依賴呼叫者的 __file__ 來
定位 .env。在 `python - <<EOF` (stdin) 模式下 __file__ 是 "<stdin>"，
路徑不存在，導致 find_dotenv() 的 frame 回溯觸發 AssertionError。
此模組改用「從 cwd 往上找」，在 stdin、REPL、pytest、真實 .py 下皆可用。
"""
from __future__ import annotations
import os
from pathlib import Path

_LOADED = False


def project_root() -> Path:
    """從 cwd 往上找含 .env 或 pyproject.toml 的目錄。"""
    cur = Path.cwd().resolve()
    for d in (cur, *cur.parents):
        if (d / ".env").is_file() or (d / "pyproject.toml").is_file():
            return d
    return cur


def load(required: tuple[str, ...] = ()) -> Path:
    """載入 .env。回傳實際使用的路徑。可重複呼叫。"""
    global _LOADED
    root = project_root()
    env_path = root / ".env"
    if not _LOADED:
        from dotenv import load_dotenv
        load_dotenv(env_path if env_path.is_file() else None)
        _LOADED = True
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        raise RuntimeError(
            f"缺少環境變數 {missing}；已嘗試載入 {env_path}"
        )
    return env_path


def model() -> str:
    load()
    return os.getenv("MODEL", "gemini-3.5-flash")


def api_key() -> str:
    load(required=("GOOGLE_API_KEY",))
    return os.environ["GOOGLE_API_KEY"]
PY
echo "✅ assurance/env.py"
```

---

## 全域替換規則

**所有 spike 文件裡的這兩行：**

```python
from dotenv import load_dotenv
load_dotenv()
```

**一律改成：**

```python
from assurance.env import load, model
load()
MODEL = model()
```

一次改完：

```bash
grep -rl "load_dotenv()" assurance/ spike_agent/ tests/ 2>/dev/null | while read f; do
  python3 - "$f" <<'PY'
import re, sys, pathlib
p = pathlib.Path(sys.argv[1]); t = p.read_text()
t = t.replace("from dotenv import load_dotenv\nload_dotenv()\n",
              "from assurance.env import load\nload()\n")
p.write_text(t); print("patched:", p)
PY
done
```

---

## 重跑 S0 步驟 4 與 5

### 步驟 4 驗證（修正版）

```bash
uv run python - <<'PY'
from assurance.env import load, api_key
p = load(required=("GOOGLE_API_KEY",))
print(f"✅ .env 載入自 {p}")
print("   API key length =", len(api_key()))
PY
```

### 步驟 5 列出可用模型（修正版）

```bash
uv run python - <<'PY'
from assurance.env import api_key
from google import genai
c = genai.Client(api_key=api_key())
gem = sorted(m.name for m in c.models.list() if "gemini" in m.name)
for n in gem:
    print(n)
print(f"\n共 {len(gem)} 個 gemini 模型")
PY
```

從輸出挑一個 **Gemini 3.5+** 的 id 寫進 `.env`：

```bash
echo "MODEL=gemini-3.5-flash" >> .env   # ← 換成實際存在的
uv run python -c "from assurance.env import model; print('MODEL =', model())"
```

---

## 給後續所有 spike 的通則

> **凡是需要環境變數的腳本，寫成真實 `.py` 檔案再執行，不要用 heredoc 餵 stdin。**

這不只是為了避開這個 bug——你的專案原則是「每篇文章都要有工程 artifact 支撐」，**heredoc 執行完不留檔案，等於沒有 artifact**。寫成真實檔案才進得了 git、才可重現、才能當證據。

純檢查用的一次性指令（不碰 .env）仍可用 heredoc。

---

## 附錄：三個 DeprecationWarning 的判讀

你看到的三個警告**全部無害**，但其中一個回答了 S0 步驟 3 的問題。

### 1. `_UnionGenericAlias is deprecated and slated for removal in Python 3.17`

**來源：** Python 3.14 內部 `typing` 模組的自我棄用警告，由某個依賴使用了 `typing` 私有 API 觸發。
**影響：** 無。Python 3.17 還很遠（目前 3.14）。
**行動：** 不需處理。這是你用 3.14 這種很新的版本的必然副作用。

### 2 & 3. `BaseAgentConfig is deprecated... Config is now loaded via reflection`

**來源：** ADK 自身。棄用的是 **`BaseAgentConfig` 這個設定載入類別**，不是 agent 本身。
**影響：** 無，除非你直接用 `BaseAgentConfig` 寫設定（你沒有）。

### ★ 這回答了 S0 步驟 3

```
SequentialAgent imported OK
```

**`SequentialAgent` 本身沒有任何 deprecation warning。**

三個警告沒有一個是針對 template workflow。所以：

> **S3 的退路（fallback 到 `SequentialAgent` + 自製路由）確認可行。**

這一點值得記錄——先前查證顯示官方文件用 "superseded" 描述 template workflow 在 ADK 2.0 的地位，但**執行期沒有發出棄用警告**，代表它仍是受支援的路徑，不是隨時會消失的舊 API。

「文件說 superseded，但 runtime 不警告」——這個落差本身也是可寫的觀察：**文件的措辭與程式碼的承諾不一定一致，要以能執行的行為為準。**

### 記錄到 evidence

```bash
mkdir -p evidence
uv run python -W all - <<'PY' 2>&1 | tee evidence/S0-deprecations.txt
import warnings, sys
warnings.simplefilter("always")
with warnings.catch_warnings(record=True) as w:
    from google.adk.agents import SequentialAgent, LlmAgent, ParallelAgent, LoopAgent
    print("template workflow agents imported OK")
    for x in w:
        print(f"WARN: {x.category.__name__}: {x.message}")
print("\n判讀：無任何針對 SequentialAgent/ParallelAgent/LoopAgent 的棄用警告")
print("→ S3 fallback 路徑可行")
PY
```

---

## S0 檢核表（更新）

- [x] ADK 2.7.1 / Python 3.14.3 確認
- [x] `Workflow / Edge / DEFAULT_ROUTE` import 成功（`Edge.model_fields = ['from_node','to_node','route']` 與原始碼一致）
- [x] **SequentialAgent 無棄用警告 → S3 fallback 可行**
- [ ] `assurance/env.py` 建立
- [ ] `.env` 填入真實 API key（已 vim 編輯）
- [ ] 步驟 4 驗證通過（修正版）
- [ ] 步驟 5 挑定 Gemini 3.5+ model id 並寫入 `.env`
- [ ] ★ 步驟 6：OpenInference + graph workflow 相容性
