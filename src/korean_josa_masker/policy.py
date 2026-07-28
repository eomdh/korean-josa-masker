"""마스킹 정책 인터페이스.

정책의 유일한 책임은 **탐지**다: :meth:`MaskPolicy.find_spans` 가 텍스트에서 가릴
이름의 ``(start, end, name)`` 구간을 돌려준다. 치환(placeholder·가명)과 순회(구조체)는
:mod:`korean_josa_masker.masker` 의 상위 함수가 담당한다.

기본 구현은 :class:`RegexJosaPolicy`(조사-인지 정규식, 결정적·무의존). NER 기반 정책 등을
같은 인터페이스(``find_spans``)로 갈아끼울 수 있다.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Protocol

from .particles import COPULA, PARTICLES

__all__ = ["CompositePolicy", "GuardedPolicy", "MaskPolicy", "RegexJosaPolicy", "Span"]

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
    # 서술격 조사 경계(입니다, 예요, 였). 조사와 달리 소거 대상이 아니라 확인 전용.
    _COPULA_ALTERNATION = "|".join(sorted(COPULA, key=len, reverse=True))

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
        copula = rf"(?:{self._COPULA_ALTERNATION})"
        # 끝 경계에서 exclude(치환 결과, 예: "***")는 경계로 치지 않는다 → 재탐지 방지(멱등성).
        skip = rf"(?!{re.escape(exclude)})" if exclude else ""
        end = rf"{skip}\W|$"
        if keep_particle:
            # 이름만 구간에 담고 조사와 서술격은 lookahead로 확인만 → "홍길동입니다"의 "홍길동"만.
            pattern = rf"(?P<name>{names_alt})(?={particle}|{copula}|{end})"
        else:
            # 조사는 구간에 포함해 함께 소거하되(→ "홍길동은" 전체), 서술격은 경계로만 확인해
            # 소거하지 않고 남긴다 → "홍길동입니다"는 "***입니다".
            pattern = rf"(?P<name>{names_alt})(?:{particle})?(?={copula}|{end})"
        return [(m.start(), m.end(), m.group("name")) for m in re.finditer(pattern, text)]


def _overlaps(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    """두 반열림 구간 [a_start, a_end), [b_start, b_end) 가 겹치는가(맞닿음은 겹침 아님)."""
    return a_start < b_end and b_start < a_end


def _merge_spans(spans: list[Span]) -> list[Span]:
    """겹치는 스팬을 union 으로 합쳐 정렬 + 비겹침 리스트로 정규화.

    ``_apply_spans`` 는 스팬이 정렬되고 겹치지 않는다고 가정. 여러 정책의 탐지를 합치면
    동일/포함/부분 겹침이 생기므로 여기서 해소. 규칙: 시작 오름차순(같은 시작이면 넓은 것
    먼저) 정렬 후, 직전 채택과 겹치면 끝을 늘려 union 병합하고 이름은 앞 스팬 것 유지.
    완전 포함은 흡수, 안 겹치면 새로 채택. 부분 겹침의 꼬리도 union 이라 노출되지 않음.
    """
    result: list[Span] = []
    for start, end, name in sorted(spans, key=lambda s: (s[0], -s[1])):
        if result and _overlaps(result[-1][0], result[-1][1], start, end):
            prev_start, prev_end, prev_name = result[-1]
            if end > prev_end:
                result[-1] = (prev_start, end, prev_name)  # union 으로 끝 확장
            # else: 완전 포함 → 흡수(버림)
        else:
            result.append((start, end, name))
    return result


class CompositePolicy:
    """여러 :class:`MaskPolicy` 를 합쳐 탐지의 합집합을 내는 정책.

    각 멤버의 ``find_spans`` 결과를 모아 :func:`_merge_spans` 로 정렬 + 비겹침 정규화.
    멤버 중 하나라도 잡으면 마스킹 대상. 결정적 바닥(:class:`RegexJosaPolicy`) 위에 NER
    등 다른 정책을 의존성 없이 얹는 조립 지점. 자신도 ``MaskPolicy`` 라 중첩 가능.
    """

    def __init__(self, *policies: MaskPolicy) -> None:
        self._policies = policies

    def find_spans(
        self,
        text: str,
        names: list[str],
        *,
        keep_particle: bool = True,
        exclude: str | None = None,
    ) -> list[Span]:
        spans: list[Span] = []
        for policy in self._policies:
            spans.extend(
                policy.find_spans(text, names, keep_particle=keep_particle, exclude=exclude)
            )
        return _merge_spans(spans)


class GuardedPolicy:
    """``inner`` 정책의 탐지 중 보호 표면형과 겹치는 스팬을 제거하는 가드 정책.

    정규식은 의미를 몰라 이름 ``이상`` 과 단어 ``이상 없음`` 을 구분 못 함. 호출자가 보호할
    표면형(``protect``)을 주면, 그 표면형이 나타난 구간과 겹치는 이름 스팬을 결정적으로 제거.
    이름 단위가 아니라 스팬 단위라, 같은 이름이라도 보호 구절 안의 그 위치만 살리고 다른
    위치의 진짜 이름은 그대로 마스킹. NER 없이 동음이의어 과잉 마스킹을 완화.
    """

    def __init__(self, inner: MaskPolicy, protect: Iterable[str]) -> None:
        self._inner = inner
        self._protect = [p for p in protect if p]  # 빈 문자열은 zero-width 매치라 방어적으로 제외

    def find_spans(
        self,
        text: str,
        names: list[str],
        *,
        keep_particle: bool = True,
        exclude: str | None = None,
    ) -> list[Span]:
        spans = self._inner.find_spans(text, names, keep_particle=keep_particle, exclude=exclude)
        if not self._protect:
            return spans
        guard = "|".join(re.escape(p) for p in self._protect)
        regions = [(m.start(), m.end()) for m in re.finditer(guard, text)]
        if not regions:
            return spans
        return [s for s in spans if not any(_overlaps(s[0], s[1], r[0], r[1]) for r in regions)]
