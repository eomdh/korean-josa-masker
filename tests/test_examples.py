"""구체 케이스.

일부는 의도적으로 RED다(naive 구현이 실패). 조사-인지 정규식을 구현하면 GREEN이 된다.
"""

from korean_josa_masker import mask


# ── GREEN: naive 초안으로도 통과 ────────────────────────────────────────
def test_masks_name_before_particle():
    assert mask("홍길동은 담당자입니다", ["홍길동"]) == "***은 담당자입니다"


def test_masks_bare_name_at_end():
    assert mask("담당자는 홍길동", ["홍길동"]) == "담당자는 ***"


def test_masks_name_before_dative_particle():
    assert mask("홍길동에게 전달", ["홍길동"]) == "***에게 전달"


def test_empty_names_is_identity():
    assert mask("아무도 없다", []) == "아무도 없다"


# ── RED: 구현 필요 (아래 3개를 GREEN으로 만드는 게 다음 할 일) ─────────────
def test_no_substring_collision():
    # "김"이 "김민수/김철수"의 일부를 먼저 먹으면 안 된다 → 길이 내림차순 치환
    assert mask("김민수와 김철수", ["김", "김민수", "김철수"]) == "***와 ***"


def test_no_false_positive_on_common_syllable():
    # 이름 "김"이 단어 "김치"를 파괴하면 안 된다 → 조사-인지 경계
    assert mask("김치가 맛있다", ["김"]) == "김치가 맛있다"


def test_consume_particle_mode():
    # keep_particle=False → 뒤따르는 조사까지 소거
    assert mask("홍길동은 왔다", ["홍길동"], keep_particle=False) == "*** 왔다"
