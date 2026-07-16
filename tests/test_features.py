"""신규 기능: 스팬 반환 · 구조체 재귀 마스킹 · 일관된 가명."""

from korean_josa_masker import mask, mask_structured, mask_with_spans, pseudonymizer


def test_mask_with_spans():
    masked, spans = mask_with_spans("홍길동은 김철수와", ["홍길동", "김철수"])
    assert masked == "***은 ***와"
    assert spans == [(0, 3, "홍길동"), (5, 8, "김철수")]


def test_mask_structured_dict_and_list():
    data = {
        "author": "홍길동이 작성",
        "reviewers": ["김철수 확인", "박영희 반려"],
        "count": 3,
    }
    out = mask_structured(data, ["홍길동", "김철수", "박영희"])
    assert out == {
        "author": "***이 작성",
        "reviewers": ["*** 확인", "*** 반려"],
        "count": 3,
    }


def test_pseudonymizer_is_stable_and_consistent():
    pseudo = pseudonymizer()
    out = mask("홍길동은 김철수와, 다시 홍길동이", ["홍길동", "김철수"], placeholder=pseudo)
    # 같은 이름 → 같은 가명, 등장 순서대로 번호.
    assert out == "[사람1]은 [사람2]와, 다시 [사람1]이"


def test_pseudonymizer_shared_across_structured():
    pseudo = pseudonymizer()
    data = {"a": "홍길동 왔다", "b": "김철수와 홍길동"}
    out = mask_structured(data, ["홍길동", "김철수"], placeholder=pseudo)
    assert out == {"a": "[사람1] 왔다", "b": "[사람2]와 [사람1]"}
