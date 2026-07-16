"""조사 인지 한국어 이름 마스킹.

- :func:`mask` — 문자열 마스킹 (기본 정책 :class:`RegexJosaPolicy`, ``policy=`` 주입 가능).
- :func:`mask_with_spans` — 마스킹 결과 + 가려진 ``(start, end, name)`` 위치.
- :func:`mask_structured` — dict/list를 재귀로 돌며 문자열 값 마스킹 (LLM JSON 출력용).
- :func:`pseudonymizer` — 이름을 안정적 가명("[사람1]" …)으로 바꾸는 placeholder 팩토리.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from .policy import MaskPolicy, RegexJosaPolicy, Span

__all__ = ["mask", "mask_with_spans", "mask_structured", "pseudonymizer"]

_DEFAULT_POLICY = RegexJosaPolicy()


def _repl_fn(placeholder: str | Callable[[str], str]) -> Callable[[str], str]:
    if callable(placeholder):
        return placeholder
    return lambda _name: placeholder


def _apply_spans(text: str, spans: list[Span], repl: Callable[[str], str]) -> str:
    out: list[str] = []
    last = 0
    for start, end, name in spans:
        out.append(text[last:start])
        out.append(repl(name))
        last = end
    out.append(text[last:])
    return "".join(out)


def _find(
    text: str,
    names: list[str],
    *,
    keep_particle: bool,
    placeholder: str | Callable[[str], str],
    policy: MaskPolicy | None,
) -> list[Span]:
    policy = policy or _DEFAULT_POLICY
    # 고정 문자열 placeholder만 경계 제외에 쓸 수 있다(가명은 매번 달라 멱등성 대상 아님).
    exclude = placeholder if isinstance(placeholder, str) else None
    return policy.find_spans(text, names, keep_particle=keep_particle, exclude=exclude)


def mask(
    text: str,
    names: list[str],
    *,
    placeholder: str | Callable[[str], str] = "***",
    keep_particle: bool = True,
    policy: MaskPolicy | None = None,
) -> str:
    """``text`` 안의 ``names`` 를 조사 경계를 인지해 가린다.

    ``placeholder`` 는 고정 문자열이거나, 이름을 받아 치환값을 돌려주는 함수(가명 등).
    """
    if not names:
        return text
    spans = _find(text, names, keep_particle=keep_particle, placeholder=placeholder, policy=policy)
    return _apply_spans(text, spans, _repl_fn(placeholder))


def mask_with_spans(
    text: str,
    names: list[str],
    *,
    placeholder: str | Callable[[str], str] = "***",
    keep_particle: bool = True,
    policy: MaskPolicy | None = None,
) -> tuple[str, list[Span]]:
    """``(masked_text, spans)`` 반환. ``spans`` 는 원본 텍스트 기준 ``(start, end, name)``."""
    if not names:
        return text, []
    spans = _find(text, names, keep_particle=keep_particle, placeholder=placeholder, policy=policy)
    return _apply_spans(text, spans, _repl_fn(placeholder)), spans


def mask_structured(
    data: Any,
    names: list[str],
    *,
    placeholder: str | Callable[[str], str] = "***",
    keep_particle: bool = True,
    policy: MaskPolicy | None = None,
) -> Any:
    """dict/list/tuple/str를 재귀로 돌며 모든 문자열 값을 마스킹. 그 외 타입은 그대로.

    같은 ``pseudonymizer()`` 인스턴스를 넘기면 구조 전체에서 가명이 일관되게 유지된다.
    """
    kw: dict[str, Any] = {
        "placeholder": placeholder,
        "keep_particle": keep_particle,
        "policy": policy,
    }
    if isinstance(data, str):
        return mask(data, names, **kw)
    if isinstance(data, Mapping):
        return {key: mask_structured(value, names, **kw) for key, value in data.items()}
    if isinstance(data, list):
        return [mask_structured(item, names, **kw) for item in data]
    if isinstance(data, tuple):
        return tuple(mask_structured(item, names, **kw) for item in data)
    return data


def pseudonymizer(template: str = "[사람{n}]") -> Callable[[str], str]:
    """이름 → 안정적 가명 매핑 placeholder를 만든다. 같은 이름은 항상 같은 가명.

    사용::

        mask(text, names, placeholder=pseudonymizer())  # "홍길동" → "[사람1]"

    번호는 텍스트에 등장하는 순서대로 붙는다. 한 인스턴스를 여러 호출/leaf에
    재사용하면 전체에서 일관된 가명이 유지된다.
    """
    mapping: dict[str, str] = {}

    def repl(name: str) -> str:
        if name not in mapping:
            mapping[name] = template.format(n=len(mapping) + 1)
        return mapping[name]

    return repl
