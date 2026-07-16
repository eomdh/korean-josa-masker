# korean-josa-masker

[![CI](https://github.com/eomdh/korean-josa-masker/actions/workflows/ci.yml/badge.svg)](https://github.com/eomdh/korean-josa-masker/actions/workflows/ci.yml)

한국어 조사(助詞)를 인지해 텍스트 속 이름을 가리는 마스킹 라이브러리.

```text
"홍길동은 담당자입니다"  →  "***은 담당자입니다"
```

## 왜

한국어는 명사와 조사 사이에 띄어쓰기가 없다(`홍길동은`). 그래서 순진하게 `text.replace("홍길동", "***")` 하면 `홍길동은`은 잡아도, 이름이 `김`·`이` 같은 흔한 음절이면 `김치`·`회의`까지 파괴한다. **"이름 + 조사"는 잡되 흔한 음절 오탐은 막는 것**이 목표.

## 사용

```python
from korean_josa_masker import mask, mask_structured, mask_with_spans, pseudonymizer

mask("홍길동은 김철수에게 전달했다", ["홍길동", "김철수"])
# → "***은 ***에게 전달했다"

mask("홍길동은 왔다", ["홍길동"], keep_particle=False)
# → "*** 왔다"

# 구조체(LLM JSON 출력) 재귀 마스킹
mask_structured({"author": "홍길동이 작성", "tags": ["김철수 확인"]}, ["홍길동", "김철수"])
# → {"author": "***이 작성", "tags": ["*** 확인"]}

# 일관된 가명 — 같은 이름은 같은 태그, 등장 순서대로 번호
mask("홍길동은 김철수와 다시 홍길동이", ["홍길동", "김철수"], placeholder=pseudonymizer())
# → "[사람1]은 [사람2]와 다시 [사람1]이"

# 가려진 위치(start, end, name)까지
mask_with_spans("홍길동은 왔다", ["홍길동"])
# → ("***은 왔다", [(0, 3, "홍길동")])
```

## 설계 결정

<!-- TODO(나): 면접 답변이니 본인 말로 다듬어도 좋음. -->
- **조사-인지 경계** — 이름 뒤가 (조사 | 공백 | 문장부호 | 끝)일 때만 마스킹. 띄어쓰기 없는 명사+조사를 잡되 `김`이 `김치`를 파괴하지 않게.
- **길이 내림차순 치환** — `["김", "김민수"]`에서 짧은 이름이 긴 이름을 먼저 먹는 부분 문자열 충돌을 막는다.
- **조사 기본 보존** (`keep_particle=True`) — `***은 담당자입니다`가 문법·가독성을 유지한다. 조사까지 먹으면 문장이 깨진다.
- **멱등성** — 입력·출력 이중 마스킹에서 두 번 돌려도 결과가 같다. `placeholder`를 경계로 치지 않아 인접 이름 재마스킹을 막는다.
- **정책 분리** (`MaskPolicy.find_spans`) — 정책은 "탐지"만 책임진다(이름 위치를 반환). 치환·구조체 순회·가명은 그 위에서 조립된다. 기본은 정규식(`RegexJosaPolicy`, 결정적·무의존), `policy=` 로 NER 기반 등을 끼울 수 있다.

## 한계

- **동음이의어 과잉 마스킹** — 정규식은 의미를 모른다. 이름 `이상`과 단어 `이상 없음`을 구분하지 못한다. → `MaskPolicy` 인터페이스가 열려 있어 `NerPolicy` 같은 정책을 끼워 보완할 수 있다(정규식은 결정적 바닥).
- **범용 PII 범위 밖** — 전화·이메일·주민번호 등은 다루지 않는다. 조사-인지 이름 마스킹에 집중.

## 개발

```bash
uv sync
uv run pytest
```

## License

MIT
