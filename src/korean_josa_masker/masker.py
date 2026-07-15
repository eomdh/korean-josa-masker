"""조사 인지 이름 마스킹.

공개 API는 :func:`mask` 하나뿐이다. 지금 본문은 순진한 ``str.replace`` 초안이라
쉬운 케이스만 통과하고 다음 테스트는 **의도적으로 RED**다(TDD 시작점):

    - tests/test_examples.py::test_no_substring_collision      (길이 내림차순 치환 필요)
    - tests/test_examples.py::test_no_false_positive_...        (조사-인지 경계 필요)
    - tests/test_examples.py::test_consume_particle_mode        (keep_particle=False 처리 필요)

구현 가이드는 :func:`mask` 안 TODO 주석 참조. 설계 근거(면접 방어용)는 README '설계 결정'.
"""

from __future__ import annotations

from .particles import PARTICLES

__all__ = ["mask"]

# 긴 조사부터 매치되도록 정렬해 둔 대안 문자열(예: "에게서" > "에게" > "에").
# 진짜 구현의 끝 경계 lookahead 에서 이걸 쓰면 된다.
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

    # ── TODO(구현): 아래 naive 루프를 조사-인지 정규식으로 교체한다 ──────────────
    #   1) names 를 길이 내림차순으로 정렬 → 긴 이름이 먼저 매치 (부분 문자열 충돌 방지)
    #          ordered = sorted(set(names), key=len, reverse=True)
    #   2) 이름별 정규식 — 끝 경계를 (조사 | 공백 | 문장부호 | 문자열 끝)으로:
    #          import re
    #          boundary = rf"(?=(?:{_PARTICLE_ALTERNATION})|\s|\W|$)"
    #          pattern = re.compile(re.escape(name) + boundary)
    #      → 이름 "김"이 "김치"를 파괴하지 않고, "홍길동은"의 "홍길동"만 잡는다.
    #   3) keep_particle=False면 뒤따르는 조사를 그룹으로 함께 잡아 소거한다.
    #   4) placeholder 는 한글이 아니라 재매치되지 않는다 → 멱등성 자연 보장.
    #
    #   이 블록을 완성하고 아래 naive 초안을 지우면 RED 테스트가 GREEN이 된다.
    #
    # naive 초안: 쉬운 케이스만 통과. collision·false-positive·consume 테스트는 실패한다.
    result = text
    for name in names:
        result = result.replace(name, placeholder)
    return result
