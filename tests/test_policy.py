"""정책(MaskPolicy) 탐지·주입 테스트."""

from korean_josa_masker import RegexJosaPolicy, mask


def test_find_spans_returns_original_positions():
    spans = RegexJosaPolicy().find_spans("홍길동은 김철수와", ["홍길동", "김철수"])
    assert spans == [(0, 3, "홍길동"), (5, 8, "김철수")]


def test_custom_policy_is_used():
    # 정책의 유일한 책임은 탐지(find_spans). 주입한 정책이 실제로 쓰이는가.
    class WholeTextPolicy:
        def find_spans(self, text, names, *, keep_particle=True, exclude=None):
            return [(0, len(text), names[0])] if text else []

    assert mask("홍길동은 왔다", ["홍길동"], policy=WholeTextPolicy()) == "***"
