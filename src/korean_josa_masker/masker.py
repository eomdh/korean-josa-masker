"""조사 인지 이름 마스킹.

공개 API는 :func:`mask` 하나. 한국어는 이름 뒤에 조사가 띄어쓰기 없이 붙어("홍길동은"),
영어식 word boundary(``\\b``)가 통하지 않는다. 단순 치환은 흔한 음절 이름이 무관한
단어를 파괴한다("김"이 "김치"를). 이름 뒤가 (조사 | 공백 | 문장부호 | 끝)일 때만
마스킹하는 조사-인지 경계로 이를 막는다.
"""

from __future__ import annotations

import re

from .particles import PARTICLES

__all__ = ["mask"]

# 긴 조사부터 매치되도록 정렬한 대안(예: "에게서" > "에게" > "에").
_PARTICLE_ALTERNATION = "|".join(sorted(PARTICLES, key=len, reverse=True))


def mask(
    text: str,
    names: list[str],
    *,
    placeholder: str = "***",
    keep_particle: bool = True,
) -> str:
    """``text`` 안의 ``names`` 를 조사 경계를 인지해 ``placeholder`` 로 가린다.

    Args:
        text: 원본 문자열.
        names: 가릴 이름 목록.
        placeholder: 치환 문자열. 기본 ``"***"``.
        keep_particle: True면 조사를 남긴다("홍길동은" → "***은"),
            False면 뒤따르는 조사까지 소거한다("홍길동은" → "***").

    Returns:
        마스킹된 문자열.
    """
    if not names:
        return text

    result = text
    particle = rf"(?:{_PARTICLE_ALTERNATION})"
    # 길이 내림차순: 긴 이름을 먼저 치환해 부분 문자열 충돌 방지("김"이 "김민수"를 먼저 먹지 않게).
    for name in sorted(names, key=len, reverse=True):
        if keep_particle:
            # 이름만 치환하고 뒤 조사는 lookahead로 확인만 한다 → "홍길동은" → "***은".
            pattern = re.escape(name) + rf"(?={particle}|\s|\W|$)"
        else:
            # 뒤따르는 조사가 있으면 함께 소거한다 → "홍길동은" → "***".
            pattern = re.escape(name) + rf"{particle}?(?=\s|\W|$)"
        result = re.sub(pattern, placeholder, result)
    return result
