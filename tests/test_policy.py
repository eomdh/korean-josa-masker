"""정책 주입(MaskPolicy) 확장점 테스트."""

from korean_josa_masker import RegexJosaPolicy, mask


def test_default_matches_regex_josa_policy():
    # 기본 mask()는 RegexJosaPolicy 직접 호출과 같은 결과여야 한다.
    text, names = "홍길동은 김철수에게", ["홍길동", "김철수"]
    assert mask(text, names) == RegexJosaPolicy().apply(
        text, names, placeholder="***", keep_particle=True
    )


def test_custom_policy_is_used():
    # 주입한 정책이 실제로 호출된다 — 확장점이 진짜 열려 있는가.
    class StubPolicy:
        def apply(self, text, names, *, placeholder, keep_particle):
            return "<stub>"

    assert mask("홍길동은 왔다", ["홍길동"], policy=StubPolicy()) == "<stub>"
