"""불변식(property) 테스트 — 마스킹의 핵심 보증을 randomized로 검증.

간판 시그널: "마스킹 뒤에는 그 이름이 남지 않는다"를 무작위 입력으로 보증한다.
"""

from hypothesis import given
from hypothesis import strategies as st

from korean_josa_masker import mask
from korean_josa_masker.particles import PARTICLES

# 한글 음절(가~힣) 2~4자 이름
hangul_name = st.text(
    alphabet=st.characters(min_codepoint=0xAC00, max_codepoint=0xD7A3),
    min_size=2,
    max_size=4,
)


@given(
    names=st.lists(hangul_name, min_size=1, max_size=4, unique=True),
    data=st.data(),
)
def test_idempotent(names, data):
    # 두 번 마스킹해도 결과가 같다 (입력·출력 이중 방어에서 안전).
    # 이름 + 구분자(빈 문자열 포함 → 인접 반복)로 실제 마스킹이 일어나는 텍스트를 만든다.
    seps = ["", " ", "은 ", "이 ", "에게 ", "와 ", ". ", "다"]
    parts = []
    for _ in range(data.draw(st.integers(min_value=0, max_value=6))):
        parts.append(data.draw(st.sampled_from(names)))
        parts.append(data.draw(st.sampled_from(seps)))
    text = "".join(parts)
    once = mask(text, names)
    assert mask(once, names) == once


@given(text=st.text())
def test_empty_names_is_identity(text):
    assert mask(text, []) == text


@given(name=hangul_name, particle=st.sampled_from(sorted(PARTICLES)))
def test_standalone_name_with_particle_is_masked(name, particle):
    # ASCII 캐리어로 우연한 겹침을 차단한 뒤, 이름이 통째로 사라지는지 확인
    masked = mask(f"x {name}{particle} y", [name])
    assert name not in masked
