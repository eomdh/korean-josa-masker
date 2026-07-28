"""오탐 가드(GuardedPolicy) + 겹침 술어(_overlaps) 검증.

동음이의어 과잉 마스킹(이름 '이상' vs 단어 '이상 없음')을 보호 표면형으로 결정적으로 완화.
"""

from korean_josa_masker import (
    CompositePolicy,
    GuardedPolicy,
    RegexJosaPolicy,
    mask,
)
from korean_josa_masker.policy import _overlaps

# --- _overlaps 술어 ---


def test_overlaps_true_when_intersecting():
    assert _overlaps(0, 3, 2, 5) is True


def test_overlaps_false_when_touching():
    # 반열림 구간이라 맞닿음(3==3)은 겹침 아님.
    assert _overlaps(0, 3, 3, 5) is False


def test_overlaps_true_when_contained():
    assert _overlaps(1, 2, 0, 5) is True


def test_overlaps_false_when_disjoint():
    assert _overlaps(0, 2, 5, 8) is False


# --- GuardedPolicy 억제 ---


def _guarded(protect):
    return GuardedPolicy(RegexJosaPolicy(), protect)


def test_name_inside_protected_phrase_is_kept():
    # "이상 없음"의 "이상"은 사람이 아니라 단어 → 마스킹 안 함.
    assert mask("이상 없음이 확인됐다", ["이상"], policy=_guarded(["이상 없음"])) == "이상 없음이 확인됐다"


def test_only_the_protected_occurrence_is_spared():
    # 킬러 케이스: 같은 이름이라도 보호 구절 안의 위치만 살리고, 사람 위치는 마스킹.
    out = mask("이상 없음을 이상에게 보고", ["이상"], policy=_guarded(["이상 없음"]))
    assert out == "이상 없음을 ***에게 보고"


def test_no_protect_behaves_like_inner():
    text, names = "이상은 담당자다", ["이상"]
    assert mask(text, names, policy=_guarded([])) == mask(text, names)


def test_protect_absent_in_text_leaves_inner_unchanged():
    assert mask("이상은 담당자다", ["이상"], policy=_guarded(["이상 없음"])) == "***은 담당자다"


def test_multiple_protect_forms():
    policy = _guarded(["이상 없음", "이상형"])
    assert mask("이상형은 이상이 아니다", ["이상"], policy=policy) == "이상형은 ***이 아니다"


def test_empty_string_in_protect_is_ignored():
    # 빈 문자열은 zero-width 매치라 걸러야 함. 안 그러면 전부 억제됨.
    assert mask("이상은 담당자다", ["이상"], policy=_guarded(["", "이상 없음"])) == "***은 담당자다"


# --- 조립과 합성 ---


def test_guard_over_composite():
    inner = CompositePolicy(RegexJosaPolicy())
    policy = GuardedPolicy(inner, ["이상 없음"])
    assert mask("이상 없음을 이상에게", ["이상"], policy=policy) == "이상 없음을 ***에게"


def test_composite_over_guard():
    guarded = GuardedPolicy(RegexJosaPolicy(), ["이상 없음"])
    policy = CompositePolicy(guarded)
    assert mask("이상 없음을 이상에게", ["이상"], policy=policy) == "이상 없음을 ***에게"


# --- 전달 ---


def test_keep_particle_false_forwarded_to_inner():
    policy = _guarded(["이상 없음"])
    assert mask("이상은 왔다", ["이상"], keep_particle=False, policy=policy) == "*** 왔다"


def test_idempotent_through_guard():
    policy = _guarded(["이상 없음"])
    once = mask("이상 없음을 이상에게", ["이상"], policy=policy)
    assert mask(once, ["이상"], policy=policy) == once
