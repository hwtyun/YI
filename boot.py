"""프로젝트의 src 패키지를 Streamlit Cloud /mount/src 와 분리해 고정한다.

Cloud는 저장소를 /mount/src/<repo>/ 에 둡니다. 패키지 이름이 src 이면
Python이 /mount/src 를 패키지로 잡아 ImportError가 납니다.
또 Streamlit은 app.py만 다시 읽고 src.* 옛 모듈을 남겨, 새 이름을
import하면 ImportError가 반복됩니다. 매 실행마다 디스크의 src/ 로 다시 묶습니다.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PACKAGE_DIR = ROOT / "src"


def bind_project_package() -> Path:
    root = str(ROOT)
    while root in sys.path:
        sys.path.remove(root)
    sys.path.insert(0, root)

    for name in list(sys.modules):
        if name == "src" or name.startswith("src."):
            sys.modules.pop(name, None)

    init_py = PACKAGE_DIR / "__init__.py"
    spec = importlib.util.spec_from_file_location(
        "src",
        str(init_py),
        submodule_search_locations=[str(PACKAGE_DIR)],
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"src 패키지를 열 수 없습니다: {PACKAGE_DIR}")
    module = importlib.util.module_from_spec(spec)
    module.__path__ = [str(PACKAGE_DIR)]
    sys.modules["src"] = module
    spec.loader.exec_module(module)
    return PACKAGE_DIR
