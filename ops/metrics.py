from __future__ import annotations

import time
from dataclasses import dataclass

@dataclass
class Timer:
    start: float = time.time()
    def ms(self) -> int:
        return int((time.time() - self.start) * 1000)
