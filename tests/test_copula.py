"""서술격 조사(copula) 경계 마스킹 — 격조사가 아니라 경계 판정에서 빠져 있던 형태."""

from korean_josa_masker import mask, mask_with_spans
from korean_josa_masker.particles import COPULA, PARTICLES


def test_ipnida_is_masked():
    # 가장 흔한 자기소개 형태. 이전에는 "입"이 조사가 아니라 미스.
    assert mask("홍길동입니다", ["홍길동"]) == "***입니다"
    assert mask("홍길동입니까", ["홍길동"]) == "***입니까"


def test_vowel_final_copula_is_masked():
    # 모음 뒤 이-탈락형: 이에요→예요, 이었다→였다.
    assert mask("철수예요", ["철수"]) == "***예요"
    assert mask("철수였다", ["철수"]) == "***였다"


def test_i_initial_copula_already_worked():
    # 회귀: "이" 시작 형태는 격조사 "이"로 이미 잡히던 것.
    assert mask("홍길동이다", ["홍길동"]) == "***이다"
    assert mask("홍길동이에요", ["홍길동"]) == "***이에요"


def test_copula_preserved_even_without_keep_particle():
    # 서술격은 소거 대상이 아니라 경계 전용. keep_particle=False 여도 서술어 보존.
    assert mask("홍길동입니다", ["홍길동"], keep_particle=False) == "***입니다"
    assert mask("철수였다", ["철수"], keep_particle=False) == "***였다"


def test_particle_still_consumed_without_keep_particle():
    # 회귀: 진짜 조사는 keep_particle=False 에서 여전히 함께 소거.
    assert mask("홍길동은 왔다", ["홍길동"], keep_particle=False) == "*** 왔다"


def test_unregistered_name_before_copula_untouched():
    # 오탐 방지: 등록 안 된 말 앞이면 서술격이 있어도 안 건드림.
    assert mask("회의입니다", ["홍길동"]) == "회의입니다"


def test_common_syllable_not_broken_by_copula():
    # "김"이 이름이어도 "김치입니다"의 "김"은 경계 실패로 보존(치 앞은 경계 아님).
    assert mask("김치입니다", ["김"]) == "김치입니다"


def test_span_positions_with_copula():
    masked, spans = mask_with_spans("철수예요", ["철수"])
    assert masked == "***예요"
    assert spans == [(0, 2, "철수")]


def test_copula_disjoint_from_particles():
    # 서술격 집합은 조사 집합과 분리돼 있어야 한다(소거 로직에 섞이면 안 됨).
    assert COPULA.isdisjoint(PARTICLES)
