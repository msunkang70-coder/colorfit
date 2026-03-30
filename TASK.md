# ColorFit Task Tracker

**프로젝트 기간:** 5주 (W1: 3/24~3/28 ~ W5: 4/21~4/25)
**현재 상태:** W1 진행 중 (2026-03-30)
**Fallback 기준:** W3 금요일에 가격비교 미완이면 Fallback 발동

**사용법:** Claude Code에게 `"Task 1.3을 진행해줘"` 처럼 번호로 지시하세요.

---

## 병렬 실행 맵

각 Task의 `🅐 🅑 🅒` 태그는 어떤 터미널에서 실행하는지를 표시합니다.
같은 태그끼리는 **순차**, 다른 태그끼리는 **동시에** 실행 가능합니다.

```
W1 ─── 🅐 Task 1.1~1.11 (데이터)     ┐ 동시 실행 OK
       🅑 Task 1.12~1.16 (인프라)     ┘

W2 ─── 🅐 Task 2.1~2.6 (스코어링)    ┐
       🅑 Task 2.7~2.12 (필터+API)    │ 동시 실행 OK (3개도 가능)
       🅒 Task 2.13~2.24 (프론트)     ┘
       ※ 🅑는 🅐의 2.1~2.5 완료 후 시작 권장 (scoring.py import)

W3 ─── 🅐 Task 3.1~3.2 (백엔드)      ┐ 동시 실행 OK
       🅑 Task 3.3~3.7 (프론트)       ┘

W4 ─── 🅐 Task 4.1~4.2, 4.7~4.8 (백) ┐ 동시 실행 OK
       🅑 Task 4.3~4.6, 4.9 (프론트)  ┘
       ── Task 4.10 (통합 테스트)       ← 단독 (전체 합친 후)

W5 ─── 단독 실행 (통합 작업)
```

**TASK.md 동기화 규칙:**
- 🅐 터미널만 TASK.md를 직접 업데이트
- 🅑 🅒 터미널은 완료 시 "Task X.X 끝났어"라고 알려주기만 함
- 사람이 🅑 🅒 결과를 확인 후 TASK.md에 수동 체크

---

## W1: 데이터 + 인프라 (3/24~3/28)

### 🅐 Lane A: 데이터 파이프라인

**Task 1.1 — 12톤 팔레트 JSON 생성** ✅ `2026-03-30`
- [x] `backend/data/palettes/` 디렉토리 생성
- [x] 12개 톤별 JSON 파일 생성 (예: `spring_warm_light.json`)
- [x] 각 톤당 20~30개 대표 색상 (HEX, RGB, HSL, 한글 색상명)
- [x] 총 ~300개 색상 데이터
- [x] 참조: 기획서 섹션 7.1 (12-tone 분류 체계)

**Task 1.2 — 브랜드 화이트리스트 JSON** ✅ `2026-03-30`
- [x] `backend/data/brand_whitelist.json` 생성
- [x] 인지도 있는 브랜드 120개+ 리스트 (무신사 스탠다드, 유니클로, COS 등)
- [x] 형식: `["무신사 스탠다드", "유니클로", ...]`

**Task 1.3 — 네이버 쇼핑 API 수집 스크립트 기본 구조** ✅ `2026-03-30`
- [x] `backend/scripts/curate_by_tone.py` 생성
- [x] 네이버 쇼핑 API 호출 함수 (`search_products(query, display, start)`)
- [x] API 응답 파싱 + raw JSON 저장
- [x] Rate limit 처리 (exponential backoff)
- [x] `.env`에서 `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET` 읽기
- [x] 테스트: API 연결 테스트 스크립트

**Task 1.4 — 톤별 수집 키워드 설계** ✅ `2026-03-30`
- [x] `backend/data/tone_queries.json` 생성
- [x] 12톤별 검색 키워드 리스트 (톤 x 카테고리) — 314개 쿼리
- [x] 예: `"spring_warm_light": ["봄 코랄 블라우스", "아이보리 원피스", ...]`
- [x] 카테고리: outer, top, bottom, onepiece, shoes, bag, acc
- [x] 참조: 기획서 섹션 5.2 (수집 쿼리 설계)

**Task 1.5 — 상품 수집 실행** ⏳ `2026-03-30` ⚠️ .env 미설정 — API 키 입력 후 수동 실행 필요
- [ ] Task 1.3 스크립트로 실제 수집 실행
- [ ] 4톤 병렬 수집 x 3라운드 = 12톤 커버
- [ ] raw JSON을 `backend/data/raw/` 에 톤별 저장
- [ ] 목표: 25,000개 상품
- [ ] 톤별 수집량 확인 (최소 1,000개/톤)

**Task 1.6 — 전처리: 상품 정규화** ✅ `2026-03-30`
- [x] `backend/scripts/rebuild_from_tones.py` 생성
- [x] HTML 태그 제거 (`<b>` 등 title에 포함된 태그)
- [x] 브랜드명 추출 (title 파싱 또는 mallName 기반)
- [x] 정규화 결과를 `NormalizedProduct` 형식으로 출력
- [x] 참조: 기획서 섹션 5.4 (전처리 과정)

**Task 1.7 — 전처리: 이미지 색상 추출 + 톤 매핑** ✅ `2026-03-30`
- [x] PIL + scikit-learn K-means로 상위 3개 dominant color 추출
- [x] 추출된 HEX → 12톤 팔레트와 RGB 유클리드 거리 비교
- [x] 가장 가까운 톤 ID 매핑 (`tone_id` 부여)
- [x] 참조: 기획서 섹션 7.1 (상품 색상 → 톤 매핑 흐름도)

**Task 1.8 — 전처리: 하이브리드 카테고리 분류**
- [ ] 키워드 기반 분류 딕셔너리 (31개 카테고리 x 3~5 키워드)
- [ ] 키워드 매칭 실패 시 Gemini Flash 폴백 분류
- [ ] LLM 분류 결과 캐싱 (`backend/data/llm_cache.json`)
- [ ] 분류 속성: category, silhouette, formality, tpo, gender
- [ ] 참조: 기획서 섹션 5.4.1 (하이브리드 분류 체계)

**Task 1.9 — 코디 레시피 JSON 정의**
- [ ] `backend/data/outfit_recipes.json` 생성
- [ ] 여성 TPO 8종 x 무드 레시피 (필수/선택/금지 카테고리, 포멀도 범위)
- [ ] 남성 TPO 8종 x 무드 레시피
- [ ] 참조: 기획서 섹션 5.3.1 (TPO x 무드 레시피 매트릭스)

**Task 1.10 — 코디 조합 생성 알고리즘**
- [ ] 레시피 기반 코디 조합 생성 스크립트
- [ ] 필수 카테고리 선택 → 선택 카테고리 확률적 추가 → 금지 카테고리 검증
- [ ] 포멀도 편차 ≤ 2, 가격 비율 5배 이내, 중복 조합 방지
- [ ] designed_tpo, designed_moods 태그 부여
- [ ] 목표: 2(성별) x 12(톤) x 8(TPO) x 8~10(코디) = 1,500~1,900개
- [ ] 참조: 기획서 섹션 5.3.1 (조합 알고리즘 의사코드)

**Task 1.11 — Gemini 코디 품질 평가**
- [ ] `backend/scripts/evaluate_outfits.py` 생성
- [ ] Gemini Flash 배치 평가 (5점 척도)
- [ ] 3점 미만 코디 제거
- [ ] 평가 결과를 `llm_quality_score` 필드에 저장
- [ ] 비용 추산: ~$6 (1,900개 x ~$0.003)

### 🅑 Lane B: 인프라 셋업 (🅐와 동시 실행 가능)

**Task 1.12 — Next.js 15 프로젝트 초기화**
- [ ] `frontend/` 디렉토리에 Next.js 15 (App Router) 생성
- [ ] TypeScript 설정
- [ ] TailwindCSS 4.0 설치 + 설정
- [ ] Framer Motion 11 설치
- [ ] 동작 확인: `npm run dev` → localhost:3000

**Task 1.13 — 프론트엔드 디자인 토큰 세팅**
- [ ] DESIGN.md 읽고 CSS variables 세팅 (`globals.css`)
- [ ] 컬러 토큰 (--bg, --surface, --accent, --border 등)
- [ ] 스코어 축 컬러 5개
- [ ] 다크모드 토큰 (`[data-theme="dark"]`)
- [ ] 스페이싱 스케일 (--space-2xs ~ --space-3xl)
- [ ] Nanum Myeongjo Google Fonts 로딩 설정

**Task 1.14 — FastAPI 프로젝트 초기화**
- [ ] `backend/` 디렉토리에 FastAPI 프로젝트 생성
- [ ] `requirements.txt` (fastapi, uvicorn, pydantic, sqlalchemy, httpx, pillow, numpy, scikit-learn)
- [ ] 프로젝트 구조: `app/main.py`, `app/config.py`, `app/routers/`, `app/services/`, `app/models/`, `app/schemas/`, `app/db/`
- [ ] CORS 미들웨어 설정 (localhost:3000 허용)
- [ ] 헬스체크 엔드포인트 (`GET /health`)
- [ ] 동작 확인: `uvicorn app.main:app --reload` → localhost:8000/docs

**Task 1.15 — DB 스키마 적용**
- [ ] Supabase 연결 설정 (`app/db/database.py`)
- [ ] SQLAlchemy 2.0 모델 정의
  - [ ] `models/user.py` (users 테이블)
  - [ ] `models/product.py` (products 테이블)
  - [ ] `models/outfit.py` (outfits 테이블)
  - [ ] `models/reaction.py` (reactions 테이블)
  - [ ] `models/style_seed.py` (style_seeds 테이블)
  - [ ] `models/user_preference.py` (user_preferences 테이블)
- [ ] 인덱스 생성 (tone_id, designed_tpo, gender)
- [ ] 참조: 기획서 섹션 14.4 (DB 스키마)

**Task 1.16 — 배포 설정**
- [ ] Vercel 연결 (frontend/) — `vercel.json` 또는 자동 감지
- [ ] Railway 연결 (backend/) — `Dockerfile` 또는 `railway.json`
- [ ] 환경변수 설정 (각 플랫폼)
- [ ] 배포 확인: 프론트 + 백엔드 둘 다 접속 가능

### W1 완료 기준
- [ ] 상품 DB 20,000건 이상 (Task 1.5)
- [ ] 코디 1,500개 이상, Gemini 평가 통과 (Task 1.11)
- [ ] 프론트/백엔드 빈 프로젝트 배포 성공 (Task 1.16)

---

## W2: 추천 엔진 + 온보딩 (3/31~4/4)

### 🅐 Lane C: 추천 엔진 — 스코어링 (Task 2.1~2.6)

**Task 2.1 — PCF 스코어링 (퍼스널컬러 적합도)**
- [ ] `backend/app/services/scoring.py` 생성
- [ ] `calculate_pcf(item_tone_ids, item_hex_colors, user_tone_id)` 함수
- [ ] 톤 레벨 매칭 (동일 100, 호환 95) + 색상 레벨 매칭 (RGB 거리 → 점수)
- [ ] pytest 테스트: 동일 톤, 호환 톤, 반대 시즌, 경계값
- [ ] 참조: 기획서 섹션 5.5.1

**Task 2.2 — OF 스코어링 (TPO 적합도)**
- [ ] `calculate_of(outfit_tags, user_tpo_list)` 함수
- [ ] TPO 동의어 확장 매핑 (commute↔office 등)
- [ ] match_count 기반 점수 변환 (30점 하한)
- [ ] pytest 테스트: 정확 매칭, 동의어 매칭, 미매칭
- [ ] 참조: 기획서 섹션 5.5.2

**Task 2.3 — CH 스코어링 (색상 조화)**
- [ ] `calculate_ch(item_hex_colors)` 함수
- [ ] 모든 아이템 쌍의 RGB 거리 → 구간별 점수 (유사색/보색/과도한 대비)
- [ ] 채도 보너스 (+5점, 표준편차 0.15~0.40)
- [ ] pytest 테스트: 올블랙, 톤온톤, 보색, 형광+파스텔
- [ ] 참조: 기획서 섹션 5.5.3

**Task 2.4 — PE 스코어링 (가격 효율)**
- [ ] `calculate_pe(total_price, budget_min, budget_max)` 함수
- [ ] 3개 Case: 범위 내 (중앙 가까울수록 높음), 초과 (감점), 미만 (완만 감점, 최저 40점)
- [ ] pytest 테스트: 중앙, 상한, 하한, 50%+ 초과, 극단 저가
- [ ] 참조: 기획서 섹션 5.5.4

**Task 2.5 — SF 스코어링 (스타일 적합도)**
- [ ] `calculate_sf(items)` 함수
- [ ] 카테고리 궁합 점수 (50%) — `data/style_compat.json` 매트릭스 참조
- [ ] 실루엣 밸런스 점수 (25%) — Y/A/I/X 라인 15개 규칙
- [ ] 포멀도 일관성 점수 (25%) — 표준편차 x 40 감점
- [ ] pytest 테스트: 블라우스+슬랙스(높음), 후드+정장(낮음), 경계값 55점
- [ ] 참조: 기획서 섹션 5.5.5, 6.6

**Task 2.6 — 스타일 호환성 데이터 파일**
- [ ] `backend/data/style_compat.json` 생성 — 카테고리 궁합 227개 조합 점수
- [ ] `backend/data/silhouette_rules.json` 생성 — 실루엣 15개 조합
- [ ] `backend/data/formality_map.json` 생성 — 아이템별 포멀도 (1~5) 33개 규칙
- [ ] 참조: 기획서 섹션 6.6

### 🅑 Lane C: 추천 엔진 — 필터+파이프라인+API (Task 2.7~2.12, 🅐 2.1~2.5 완료 후 시작)

**Task 2.7 — StyleFilter (규칙 기반 사전 필터)**
- [ ] `backend/app/services/style_filter.py` 생성
- [ ] `detect_category(title, category3)` — 키워드 → 캐시 → LLM 3단계
- [ ] `filter_outfit(items)` — 3축 가중합 계산, 55점 미만 False
- [ ] pytest 테스트: 통과 코디, 탈락 코디, 55점 경계
- [ ] 참조: 기획서 섹션 6.6

**Task 2.8 — Hard Filter 체인**
- [ ] `backend/app/services/feed_builder.py` 생성
- [ ] Hard Filter 8단계 순차 적용 (H1 성별 → H2 예산 → ... → H8 StyleFilter)
- [ ] 각 필터는 독립 함수로 분리
- [ ] pytest 테스트: 각 필터별 통과/탈락 케이스
- [ ] 참조: 기획서 섹션 5.4 (Hard Filter 상세)

**Task 2.9 — Soft Score + 리랭킹**
- [ ] feed_builder.py에 Soft Score 계산 추가 (5축 가중합)
- [ ] 리랭킹: 완성 코디 가산(+3점), dislike 제외, 톤 다양성(동일 톤 3개 제한), 메인아이템 중복 제거
- [ ] 개인화 보정 (-10 ~ +10)
- [ ] 상위 200개 반환
- [ ] 참조: 기획서 섹션 6.1

**Task 2.10 — 추천 이유 생성**
- [ ] `backend/app/services/reason_generator.py` 생성
- [ ] 5축 가중 기여도 계산 → 상위 2개 축 선택
- [ ] high(75점+) / mid(75점 미만) 템플릿 분기
- [ ] 톤별 한글 이름 매핑 ("여름쿨소프트 핵심 컬러...")
- [ ] pytest 테스트: PCF 최고 기여, OF 최고 기여, 동점 처리
- [ ] 참조: 기획서 섹션 6.4

**Task 2.11 — Feed API 엔드포인트**
- [ ] `backend/app/routers/feed.py` — GET /api/feed
- [ ] 파라미터: tone_id, tpo, gender, budget_min, budget_max, page
- [ ] Profile Load → Filter → StyleFilter → Score → Rerank → Reason 전체 파이프라인
- [ ] 응답: 코디 리스트 + 5축 스코어 + 이유 2줄
- [ ] `backend/app/routers/outfit.py` — GET /api/outfit/{id}
- [ ] Pydantic 스키마 정의 (`schemas/outfit.py`)

**Task 2.12 — 스코어 프리컴퓨팅**
- [ ] `backend/scripts/precompute_scores.py` 생성
- [ ] 전체 코디에 대해 기본 5축 스코어 사전 계산
- [ ] outfits.scores JSONB에 저장
- [ ] 런타임에는 개인화 보정만 적용

### 🅒 Lane D: 온보딩 + 피드 UI (🅐🅑와 동시 실행 가능)

**Task 2.13 — 온보딩 공통 레이아웃**
- [ ] `frontend/app/onboarding/layout.tsx` — 공통 레이아웃
- [ ] 상단 진행 바 (5단계, Marsala 채움)
- [ ] 뒤로가기 버튼
- [ ] 좌→우 슬라이드 전환 (Framer Motion AnimatePresence)
- [ ] 참조: 기획서 섹션 8.4.1

**Task 2.14 — 온보딩 Step 1: 성별 선택**
- [ ] `frontend/app/onboarding/step1/page.tsx`
- [ ] "나에 대해 알려주세요" 헤드라인 (Nanum Myeongjo 28px)
- [ ] 여성/남성 2개 카드 (가로 배치, 3:4 비율)
- [ ] 탭 시 scale 1.05 + Marsala 아웃라인 → 자동 다음 Step
- [ ] "건너뛰기" 텍스트 링크

**Task 2.15 — 온보딩 Step 2: 퍼스널컬러 선택**
- [ ] `frontend/app/onboarding/step2/page.tsx`
- [ ] 시즌별 그라데이션 스트립 4개 (봄/여름/가을/겨울)
- [ ] 각 스트립 아래 세부 톤 칩 3개
- [ ] 선택 시 다른 시즌 디밍 (opacity 0.4)
- [ ] "잘 모르겠어요" → 바텀시트 간이 진단 2문항

**Task 2.16 — 온보딩 Step 3: TPO + 무드 선택**
- [ ] `frontend/app/onboarding/step3/page.tsx`
- [ ] TPO 8종 필 버튼 (성별에 따라 다른 세트)
- [ ] 무드 태그 클라우드 (성별에 따라 다른 세트)
- [ ] 복수 선택: TPO 최대 3개, 무드 최대 5개

**Task 2.17 — 온보딩 Step 4: 예산 설정**
- [ ] `frontend/app/onboarding/step4/page.tsx`
- [ ] 듀얼 썸 레인지 슬라이더 (min/max)
- [ ] 빠른 프리셋 4개 버튼 (~3만 / 3~7만 / 7~15만 / 15만~)
- [ ] "추천 코디 보러가기" CTA (풀와이드, Marsala)

**Task 2.18 — 온보딩 Step 5: 비주얼 취향 분석**
- [ ] `frontend/app/onboarding/step5/page.tsx`
- [ ] 2x2 이미지 그리드, 4라운드
- [ ] 탭 시 선택 → 0.5s 후 다음 라운드 crossfade
- [ ] "패스" 링크, 라운드 인디케이터
- [ ] 완료 후 피드로 전환

**Task 2.19 — 온보딩 API 연동**
- [ ] `backend/app/routers/onboarding.py` — POST /api/onboarding
- [ ] 프론트에서 5 Step 결과를 모아서 전송
- [ ] users 테이블 + style_seeds 테이블에 저장
- [ ] 프론트 → API 호출 연동

**Task 2.20 — 코디 카드 컴포넌트**
- [ ] `frontend/components/OutfitCard.tsx`
- [ ] 이미지 (3:4, rounded-lg) + 아이템 수 뱃지 + 하트 아이콘
- [ ] 제목 (Nanum Myeongjo 16px) + 가격 (bold) + 추천 이유 1줄
- [ ] 스코어 뱃지 미니 필 2개 ("PCF 95" "OF 80")
- [ ] fadeInUp 등장 애니메이션

**Task 2.21 — 코디 피드 화면**
- [ ] `frontend/app/feed/page.tsx`
- [ ] 헤더 (ColorFit 로고 + 프로필 아이콘)
- [ ] TPO 탭 필터 (가로 스크롤 필 버튼)
- [ ] 예산 슬라이더 (접힌 상태, 탭 시 펼침)
- [ ] "오늘의 컬러핏" 특별 카드 (피드 최상단)
- [ ] OutfitCard 리스트 (무한 스크롤, 커서 기반 페이지네이션)
- [ ] GET /api/feed 연동
- [ ] 스켈레톤 로딩 + empty state + error state

**Task 2.22 — save/dislike 인터랙션**
- [ ] 좌 스와이프 → dislike (카드 슬라이드 아웃 + "관심없음" 토스트)
- [ ] 더블탭 → save (하트 뿅 애니메이션, Marsala 전환)
- [ ] 우상단 하트 탭 → save 토글
- [ ] POST /api/reaction 연동 (save/dislike)
- [ ] `backend/app/routers/reaction.py` — POST /api/reaction

**Task 2.23 — 코디 상세 화면**
- [ ] `frontend/app/outfit/[id]/page.tsx`
- [ ] 히어로 이미지 (풀블리드, parallax scroll)
- [ ] 5축 스코어 바 차트 (width 0% → 실제값, ease-out 0.8s)
- [ ] 추천 이유 카드 (배경 #F0EDE8)
- [ ] 아이템 캐러셀 (가로 스크롤, 80px 정사각 이미지)
- [ ] 코디 합계 가격 + 최저가 합산
- [ ] 하단 CTA ("저장" + "A vs B 비교")
- [ ] GET /api/outfit/{id} 연동

**Task 2.24 — 하단 탭바**
- [ ] `frontend/components/BottomTabBar.tsx`
- [ ] 홈/저장/Top/마이 4탭
- [ ] 활성 탭: Marsala 아이콘 + bold 라벨
- [ ] 전환 모션: 아이콘 scale 0.9→1.1→1.0

### W2 완료 기준
- [ ] 5 Step 온보딩 → 코디 피드 진입 동작
- [ ] 스코어링 기반 피드가 실제 데이터로 동작
- [ ] save/dislike 동작
- [ ] 추천 이유 2줄 노출

---

## W3: 가격비교 + 유사상품 (4/7~4/11)

### 🅐 백엔드 (Task 3.1~3.2)

**Task 3.1 — 유사 상품 매칭 서비스**
- [ ] `backend/app/services/similar_finder.py` 생성
- [ ] 색상 유사도 (가중치 0.6) + 가격 유사도 (0.4) 계산
- [ ] Exact(동일 상품 다른 판매처) / Similar(대체재) 구분
- [ ] 상위 5개 반환
- [ ] pytest 테스트
- [ ] 참조: 기획서 섹션 6.2

**Task 3.2 — 아이템 API**
- [ ] `backend/app/routers/item.py`
- [ ] GET /api/item/{id} — 아이템 상세 + 판매처별 가격
- [ ] GET /api/item/{id}/similar — 유사 상품 리스트
- [ ] Pydantic 스키마 정의

### 🅑 프론트엔드 (Task 3.3~3.7, 🅐와 동시 실행 가능)

**Task 3.3 — 아이템 상세 화면**
- [ ] `frontend/app/item/[id]/page.tsx`
- [ ] 아이템 이미지 (1:1) + 브랜드 + 상품명 + 가격
- [ ] 가격 비교 테이블 (판매처, 가격, 유형, 바로가기)
- [ ] 최저가 행 하이라이트 (#F0EDE8 + Marsala 뱃지)
- [ ] 유사 상품 섹션 (2열 그리드 + 유사도 % 뱃지)
- [ ] 하단 CTA "최저가 쇼핑몰에서 보기" (Marsala 버튼)

**Task 3.4 — 외부 쇼핑몰 링크**
- [ ] 가격 비교 행 탭 → 새 탭 열기
- [ ] 하단 CTA 탭 → 최저가 쇼핑몰 새 탭
- [ ] 유사 상품 카드 탭 → 해당 아이템 상세로 이동

**Task 3.5 — 프로필/마이페이지**
- [ ] `frontend/app/profile/page.tsx`
- [ ] 톤 카드 (그라데이션 배경 + 톤 이름, Nanum Myeongjo 28px)
- [ ] 잘 어울리는 색 스와치 6개 + 피해야 할 색 4개
- [ ] 내 정보 (성별, TPO, 예산) + "변경" 버튼 → 해당 Step 바텀시트
- [ ] 취향 관리 행 → 취향 관리 화면

**Task 3.6 — 톤 설명 화면**
- [ ] `frontend/app/tone/[id]/page.tsx`
- [ ] 톤 그라데이션 히어로 (height 200px)
- [ ] 시즌 설명 1~2문장
- [ ] 잘 어울리는 색 스와치 + 피해야 할 색 스와치
- [ ] 어울리는 코디 3개 캐러셀
- [ ] "다른 톤으로 변경하기" 버튼
- [ ] `backend/app/routers/tone.py` — GET /api/tone/{id}

**Task 3.7 — 취향 관리 화면**
- [ ] Style Seed 시각화 (무드/실루엣/색감/가격 4축 요약)
- [ ] 학습 상태 진행바 ("피드백 N건 학습됨", 30건 목표)
- [ ] "취향 다시 분석하기" → Step 5 재진행
- [ ] "취향 초기화" → 확인 다이얼로그 → 데이터 삭제

**W3 금요일 — Fallback 판단 시점**
- [ ] TASK.md 전체 진행 상황 확인
- [ ] 밀리는 항목이 있으면 Fallback 발동 (CLAUDE.md 참조)

### W3 완료 기준
- [ ] 가격 비교 테이블 동작 (Task 3.3)
- [ ] Exact/Similar 구분 표시 (Task 3.1)
- [ ] 외부 쇼핑몰 링크 동작 (Task 3.4)
- [ ] 마이페이지 동작 (Task 3.5)

---

## W4: 결정 지원 + 통합 (4/14~4/18)

### 🅐 백엔드 (Task 4.1~4.2, 4.7~4.8)

**Task 4.1 — Top Pick 서비스**
- [ ] `backend/app/services/top_pick.py`
- [ ] 저장 목록 기반: 저장 코디 중 최고 점수 1개
- [ ] 전체 DB 기반: 전체 코디 중 최고 점수 1개 (콜드스타트)
- [ ] 시간대 기반 TPO 자동 추론 (오전=출근, 오후=캐주얼, 저녁=데이트)
- [ ] `backend/app/routers/top_pick.py` — GET /api/top-pick

**Task 4.2 — A vs B 비교 서비스**
- [ ] `backend/app/services/comparator.py`
- [ ] 두 코디의 5축 점수 비교 + 결정적 차이 요인 추출
- [ ] `backend/app/routers/compare.py` — GET /api/compare?ids=a,b

### 🅑 프론트엔드 (Task 4.3~4.6, 4.9, 🅐와 동시 실행 가능)

**Task 4.3 — 저장 목록 화면**
- [ ] `frontend/app/saved/page.tsx`
- [ ] 2열 그리드 (이미지 3:4 + 1줄 제목 + 가격)
- [ ] 정렬 드롭다운 (최근/점수/가격)
- [ ] 비어있을 때: 일러스트 + "아직 저장한 코디가 없어요" + CTA
- [ ] 롱프레스 → 삭제 확인 바텀시트
- [ ] GET /api/saved 연동

**Task 4.4 — Top Pick 모달**
- [ ] "Top Pick 보기" 버튼 (저장 목록 상단)
- [ ] 풀스크린 모달: 1위 코디 확대 + 추천 이유 3줄 + 5축 바 차트
- [ ] GET /api/top-pick 연동

**Task 4.5 — A vs B 비교 화면**
- [ ] 좌우 분할 (50:50), 각 코디 이미지 + 정보
- [ ] 중앙 5축 비교 (레이더 차트 또는 바 차트 오버레이)
- [ ] 하단 1줄 결론 ("A가 퍼스널컬러에 더 잘 맞아요")
- [ ] GET /api/compare 연동

**Task 4.6 — 로그인 화면**
- [ ] `frontend/app/login/page.tsx`
- [ ] ColorFit 로고 + 서브카피
- [ ] 카카오 로그인 버튼 (#FEE500)
- [ ] 구글 로그인 버튼 (#FFFFFF + border)
- [ ] "게스트로 둘러보기" 텍스트 링크

**Task 4.7 — 소셜 로그인 백엔드**
- [ ] `backend/app/services/jwt.py` — JWT 토큰 발급/검증
- [ ] `backend/app/routers/auth.py` — 카카오/구글 OAuth 콜백
- [ ] 게스트 → 로그인 전환 (저장/Top Pick 접근 시 로그인 요구)

**Task 4.8 — 피드백 개인화 학습**
- [ ] `backend/app/services/preference_tracker.py`
- [ ] 피드백 행동별 가중치: save(+2.0), like(+1.0), click(+0.3), dislike(-1.5)
- [ ] tone/category/brand/price 선호도 누적
- [ ] 10건+ 축적 시 weight_overrides 자동 생성
- [ ] `backend/app/routers/feedback.py` — POST /api/feedback
- [ ] 참조: 기획서 섹션 6.8

**Task 4.9 — 구매 후 피드백 바텀시트**
- [ ] 외부 쇼핑몰 이동 후 복귀 시 자동 표시
- [ ] "이 추천이 도움이 됐나요?" + 3개 버튼
- [ ] 👎 선택 시 이유 태그 추가 표시
- [ ] POST /api/feedback 연동

### 단독 실행 (🅐🅑 모두 완료 후)

**Task 4.10 — 통합 테스트**
- [ ] 온보딩 → 피드 → 코디 상세 → 가격비교 → 외부 링크 전체 플로우
- [ ] 저장 → 저장 목록 → Top Pick 플로우
- [ ] Edge case: 코디 0개 결과, 예산 초과, 톤 불일치

### W4 완료 기준
- [ ] Top Pick 동작 (Task 4.4)
- [ ] A vs B 비교 동작 (Task 4.5)
- [ ] 소셜 로그인 동작 (Task 4.7)
- [ ] 전체 플로우 통합 테스트 통과 (Task 4.10)

---

## W5: 폴리싱 + 배포 (4/21~4/25)

**Task 5.1 — 반응형 QA**
- [ ] 모바일 (375px): 전체 화면 확인
- [ ] 태블릿 (768px): 레이아웃 확인
- [ ] 데스크톱 (1280px): 최대 폭 제한 확인
- [ ] 가로 스크롤 없는지 확인
- [ ] 터치 타겟 44px 이상 확인

**Task 5.2 — 다크모드**
- [ ] CSS variables 다크 테마 적용
- [ ] 다크모드 토글 구현 (마이페이지 설정)
- [ ] 웜 언더톤 유지 (#1A1714, 쿨그레이 아님)
- [ ] 스코어 축 컬러 밝기 조정

**Task 5.3 — 성능 최적화**
- [ ] 이미지 lazy loading + Cloudflare CDN 설정
- [ ] 피드 API 응답 800ms 이내 확인
- [ ] Next.js Server Components 활용
- [ ] Lighthouse 성능 점수 확인 (목표: 80+)

**Task 5.4 — 버그 수정**
- [ ] 발견된 버그 목록 정리 + 수정
- [ ] 크로스 브라우저 테스트 (Chrome, Safari)

**Task 5.5 — 프로덕션 배포**
- [ ] 프론트엔드 프로덕션 빌드 + Vercel 배포
- [ ] 백엔드 프로덕션 설정 + Railway 배포
- [ ] 프로덕션 URL 접속 확인

**Task 5.6 — 데모 준비**
- [ ] 데모 시나리오 작성 (페르소나 A 기준: 소개팅 룩 찾기)
- [ ] 데모용 샘플 데이터 확인
- [ ] 발표 자료 작성

### W5 완료 기준
- [ ] 프로덕션 URL 접속 가능 (Task 5.5)
- [ ] 주요 플로우 버그 없음 (Task 5.4)
- [ ] 데모 준비 완료 (Task 5.6)

---

## MVP 핵심 지표 (W5 기준)

| 지표 | 목표 |
|------|------|
| 온보딩 완주율 | >= 60% |
| 회원 전환율 | >= 40% |
| 첫 코디 저장 도달율 | >= 25% |

---

## Fallback 순서 (W3 금요일 판단)

밀릴 경우 아래 순서로 2차 미룸:
1. A vs B 비교 (Task 4.2, 4.5)
2. Top Pick + One-shot (Task 4.1, 4.4)
3. 가격비교 (Task 3.1~3.4, 외부 링크만 유지)
4. 스코어링 5축 → 3축(PCF+OF+SF) (Task 2.1~2.5 단순화)

**절대 미루지 않는 것:** 온보딩 → 코디 피드 → 추천 이유 → save/dislike → 외부 링크
