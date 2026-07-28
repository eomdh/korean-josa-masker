"""정책 조립(CompositePolicy) + 스팬 겹침 병합(_merge_spans) 검증."""

from itertools import pairwise

from korean_josa_masker import (
    CompositePolicy,
    RegexJosaPolicy,
    mask,
    mask_with_spans,
    pseudonymizer,
)
from korean_josa_masker.policy import _merge_spans


class StubPolicy:
    """탐지를 고정 스팬으로 흉내내는 테스트용 정책(MaskPolicy 충족)."""

    def __init__(self, spans):
        self._spans = spans

    def find_spans(self, text, names, *, keep_particle=True, exclude=None):
        return list(self._spans)


# --- _merge_spans 기하 ---


def test_merge_identical_dedupes():
    assert _merge_spans([(0, 3, "홍길동"), (0, 3, "홍길동")]) == [(0, 3, "홍길동")]


def test_merge_nested_keeps_outer():
    assert _merge_spans([(0, 5, "A"), (0, 3, "B")]) == [(0, 5, "A")]


def test_merge_partial_overlap_unions():
    # 부분 겹침은 union 으로 병합, 꼬리 노출 없음. 이름은 앞 스팬 것.
    assert _merge_spans([(0, 3, "A"), (2, 10, "B")]) == [(0, 10, "A")]


def test_merge_disjoint_sorted():
    assert _merge_spans([(5, 8, "B"), (0, 3, "A")]) == [(0, 3, "A"), (5, 8, "B")]


def test_merge_empty():
    assert _merge_spans([]) == []


def test_merge_adjacent_not_overlapping():
    # 끝이 배타적이라 (0,3)과 (3,5)는 안 겹침 → 둘 다 유지.
    assert _merge_spans([(0, 3, "A"), (3, 5, "B")]) == [(0, 3, "A"), (3, 5, "B")]


# --- CompositePolicy 통합 ---


def test_union_of_two_policies():
    # regex 는 "홍길동" 을, 스텁은 별개 구간을 잡음 → 합집합.
    stub = StubPolicy([(9, 11, "메모")])
    policy = CompositePolicy(RegexJosaPolicy(), stub)
    assert mask("홍길동은 xxx 메모", ["홍길동"], policy=policy) == "***은 xxx ***"


def test_duplicate_detection_not_double_masked():
    # 같은 이름을 두 정책이 같은 위치로 잡아도 한 번만 치환.
    policy = CompositePolicy(RegexJosaPolicy(), RegexJosaPolicy())
    assert mask("홍길동은 왔다", ["홍길동"], policy=policy) == "***은 왔다"


def test_empty_composite_is_identity():
    assert mask("홍길동은 왔다", ["홍길동"], policy=CompositePolicy()) == "홍길동은 왔다"


def test_single_member_matches_bare_policy():
    text = "홍길동은 김철수에게"
    names = ["홍길동", "김철수"]
    assert mask(text, names, policy=CompositePolicy(RegexJosaPolicy())) == mask(text, names)


def test_composite_output_is_sorted_and_nonoverlapping():
    # 스텁이 뒤 구간을, regex 가 앞 구간을 잡아도 정렬된 비겹침으로 나옴.
    stub = StubPolicy([(0, 3, "홍길동")])
    policy = CompositePolicy(stub, RegexJosaPolicy())
    _, spans = mask_with_spans("홍길동과 철수", ["홍길동", "철수"], policy=policy)
    assert spans == sorted(spans)
    for (_, e1, _), (s2, _, _) in pairwise(spans):
        assert e1 <= s2


# --- 전달(keep_particle / exclude / 가명) ---


def test_keep_particle_false_forwarded_to_members():
    policy = CompositePolicy(RegexJosaPolicy())
    assert mask("홍길동은 왔다", ["홍길동"], keep_particle=False, policy=policy) == "*** 왔다"


def test_idempotent_through_composite():
    policy = CompositePolicy(RegexJosaPolicy(), RegexJosaPolicy())
    once = mask("홍길동은 김철수와 다시 홍길동이", ["홍길동", "김철수"], policy=policy)
    assert mask(once, ["홍길동", "김철수"], policy=policy) == once


def test_pseudonymizer_through_composite():
    policy = CompositePolicy(RegexJosaPolicy())
    out = mask("홍길동은 김철수와", ["홍길동", "김철수"], placeholder=pseudonymizer(), policy=policy)
    assert out == "[사람1]은 [사람2]와"
