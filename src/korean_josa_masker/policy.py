"""마스킹 정책 인터페이스.

정책의 유일한 책임은 **탐지**다: :meth:`MaskPolicy.find_spans` 가 텍스트에서 가릴
이름의 ``(start, end, name)`` 구간을 돌려준다. 치환(placeholder·가명)과 순회(구조체)는
:mod:`korean_josa_masker.masker` 의 상위 함수가 담당한다.

기본 구현은 :class:`RegexJosaPolicy`(조사-인지 정규식, 결정적·무의존). NER 기반 정책 등을
같은 인터페이스(``find_spans``)로 갈아끼울 수 있다.
"""

from __future__ import annotations

import re
from typing import Protocol

from .particles import PARTICLES

__all__ = ["MaskPolicy", "RegexJosaPolicy", "Span"]

Span = tuple[int, int, str]
"""가려질 구간: (시작 인덱스, 끝 인덱스[제외], 원본 이름)."""


class MaskPolicy(Protocol):
    """텍스트에서 가릴 이름의 위치를 찾는다."""

    def find_spans(
        self,
        text: str,
        names: list[str],
        *,
        keep_particle: bool = True,
        exclude: str | None = None,
    ) -> list[Span]: ...


class RegexJosaPolicy:
    """조사-인지 경계 + 길이 내림차순 정규식 정책 (결정적·무의존).

    이름 뒤가 (조사 | 공백 | 문장부호 | 끝)일 때만 구간으로 잡아, 띄어쓰기 없이 붙는
    명사+조사를 잡되 흔한 음절 이름이 무관한 단어를 파괴하는 것을 막는다.
    """

    # 긴 조사부터 매치되도록 정렬한 대안(예: "에게서" > "에게" > "에").
    _PARTICLE_ALTERNATION = "|".join(sorted(PARTICLES, key=len, reverse=True))

    def find_spans(
        self,
        text: str,
        names: list[str],
        *,
        keep_particle: bool = True,
        exclude: str | None = None,
    ) -> list[Span]:
        if not names:
            return []
        # 길이 내림차순: 긴 이름을 먼저 매치해 부분 문자열 충돌 방지("김민수"가 "김"보다 먼저).
        ordered = sorted(set(names), key=len, reverse=True)
        names_alt = "|".join(re.escape(n) for n in ordered)
        particle = rf"(?:{self._PARTICLE_ALTERNATION})"
        # 끝 경계에서 exclude(치환 결과, 예: "***")는 경계로 치지 않는다 → 재탐지 방지(멱등성).
        skip = rf"(?!{re.escape(exclude)})" if exclude else ""
        end = rf"{skip}\W|$"
        if keep_particle:
            # 이름만 구간에 담고 조사는 lookahead로 확인만 → "홍길동은"의 "홍길동"만.
            pattern = rf"(?P<name>{names_alt})(?={particle}|{end})"
        else:
            # 뒤 조사가 있으면 구간에 포함해 함께 소거 → "홍길동은" 전체.
            pattern = rf"(?P<name>{names_alt})(?:{particle})?(?={end})"
        return [(m.start(), m.end(), m.group("name")) for m in re.finditer(pattern, text)]
