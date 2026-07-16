"""마스킹 정책 인터페이스.

:class:`MaskPolicy` 는 "텍스트에서 이름을 어떻게 찾아 가릴지"를 캡슐화한다.
기본 구현은 :class:`RegexJosaPolicy`(조사-인지 정규식, 결정적·무의존).
NER 기반 정책 등을 같은 인터페이스로 갈아끼울 수 있다(README '한계' 참조).
"""

from __future__ import annotations

import re
from typing import Protocol

from .particles import PARTICLES

__all__ = ["MaskPolicy", "RegexJosaPolicy"]


class MaskPolicy(Protocol):
    """``text`` 안의 ``names`` 를 ``placeholder`` 로 가려 반환한다."""

    def apply(
        self,
        text: str,
        names: list[str],
        *,
        placeholder: str,
        keep_particle: bool,
    ) -> str: ...


class RegexJosaPolicy:
    """조사-인지 경계 + 길이 내림차순 정규식 정책 (결정적·무의존).

    이름 뒤가 (조사 | 공백 | 문장부호 | 끝)일 때만 마스킹해, 띄어쓰기 없이 붙는
    명사+조사를 잡되 흔한 음절 이름이 무관한 단어를 파괴하는 것을 막는다.
    """

    # 긴 조사부터 매치되도록 정렬한 대안(예: "에게서" > "에게" > "에").
    _PARTICLE_ALTERNATION = "|".join(sorted(PARTICLES, key=len, reverse=True))

    def apply(
        self,
        text: str,
        names: list[str],
        *,
        placeholder: str = "***",
        keep_particle: bool = True,
    ) -> str:
        if not names:
            return text
        result = text
        ph = re.escape(placeholder)
        particle = rf"(?:{self._PARTICLE_ALTERNATION})"
        # 끝 경계: 조사 | 공백·문장부호 | 문자열 끝. 단 placeholder(***)는 경계로 치지 않는다 —
        # 이미 마스킹된 자리를 경계로 삼으면 인접 이름을 재마스킹해 멱등성이 깨진다.
        end = rf"(?!{ph})\W|$"
        # 길이 내림차순: 긴 이름을 먼저 치환해 부분 문자열 충돌 방지("김"이 "김민수"를 먼저 먹지 않게).
        for name in sorted(names, key=len, reverse=True):
            if keep_particle:
                # 이름만 치환, 뒤 조사는 lookahead로 확인만 → "홍길동은" → "***은".
                pattern = re.escape(name) + rf"(?={particle}|{end})"
            else:
                # 뒤 조사가 있으면 함께 소거 → "홍길동은" → "***".
                pattern = re.escape(name) + rf"{particle}?(?={end})"
            result = re.sub(pattern, placeholder, result)
        return result
