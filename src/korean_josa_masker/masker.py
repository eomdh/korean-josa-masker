"""조사 인지 한국어 이름 마스킹.

공개 API는 :func:`mask` 하나. 한국어는 이름 뒤에 조사가 띄어쓰기 없이 붙어("홍길동은"),
영어식 word boundary(``\\b``)가 통하지 않는다. 기본 정책은 :class:`RegexJosaPolicy`이며,
``policy=`` 로 다른 :class:`MaskPolicy`(예: NER 기반)를 주입할 수 있다.
"""

from __future__ import annotations

from .policy import MaskPolicy, RegexJosaPolicy

__all__ = ["mask"]

_DEFAULT_POLICY = RegexJosaPolicy()


def mask(
    text: str,
    names: list[str],
    *,
    placeholder: str = "***",
    keep_particle: bool = True,
    policy: MaskPolicy | None = None,
) -> str:
    """``text`` 안의 ``names`` 를 조사 경계를 인지해 ``placeholder`` 로 가린다.

    Args:
        text: 원본 문자열.
        names: 가릴 이름 목록.
        placeholder: 치환 문자열. 기본 ``"***"``.
        keep_particle: True면 조사를 남긴다("홍길동은" → "***은"),
            False면 뒤따르는 조사까지 소거한다("홍길동은" → "***").
        policy: 마스킹 정책. 기본은 :class:`RegexJosaPolicy`.

    Returns:
        마스킹된 문자열.
    """
    if not names:
        return text
    policy = policy or _DEFAULT_POLICY
    return policy.apply(text, names, placeholder=placeholder, keep_particle=keep_particle)
