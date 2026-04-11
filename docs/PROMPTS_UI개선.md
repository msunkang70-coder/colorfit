# ColorFit UI 개선 — Claude Code 실행 프롬프트

## 실행 순서

```
Prompt A (데이터 클렌징) → Prompt B (이미지 표시) → Prompt C (탭바+레이아웃) → Prompt D (텍스트 차별화)
      │                        │                        │                        │
  아동복/이상 데이터 제거    멀티 아이템 표시       4탭→2탭 축소          core 문구 개선
  카테고리-이미지 불일치     아이템 리스트 영역     evidence 위치 조정     evidence 다양화
```

---

## Prompt A. 아동복/이상 데이터 클렌징 (P0)

```
outfits_scored.json에서 아동복이나 성인 여성 코디에 부적절한 데이터를 찾아서 제거해줘.

파일: backend/scripts/clean_invalid_outfits.py

다음 기준으로 필터링:

1. 아동복 감지:
   - 아이템 name에 다음 키워드 포함 시 제거: 키즈, 아동, 유아, 주니어, kids, baby, 베이비, 아기
   - 아이템 brand/mall_name에 아동복 브랜드 포함 시 제거: 밍크뮤, 래핑차일드, 블루독, 모이몰른, 알로봇

2. 가격 이상치:
   - 코디 total_price > 2,000,000원인 코디 제거 (또는 별도 리스트로 분리)
   - 코디 total_price < 10,000원인 코디 제거

3. 이미지 유효성:
   - items[].image_url이 비어있는 아이템이 있는 코디 제거

4. 카테고리 일관성:
   - 아이템이 1개뿐인 코디 중 원피스/점프수트가 아닌 것은 제거 (코디가 아님)

실행 후 출력:
- 제거된 코디 수 (사유별)
- 제거된 코디 샘플 5개 (outfit_id + 제거 사유)
- 남은 코디 수
- TPO별 분포 (제거 후)

outfits_scored.json 업데이트.
원본은 outfits_scored_backup.json으로 백업해줘.
```

---

## Prompt B. 멀티 아이템 이미지 표시 (P1)

```
현재 OutfitCard.tsx에서 코디의 첫 번째 아이템(items[0]) 이미지만 표시하고 있어.
코디는 2~4개 아이템인데 상의 사진만 보여서 사용자가 전체 조합을 판단할 수 없어.

frontend/components/OutfitCard.tsx를 수정해줘.

변경 내용 (full variant만):

1. 메인 이미지 (기존 3:4)는 유지 — items[0] 이미지

2. 메인 이미지 아래에 아이템 리스트 행 추가:
   - 가로 스크롤 가능한 작은 썸네일 리스트
   - 각 아이템: 48x48 rounded-md 썸네일 + 아이템명(truncate) + 가격
   - 스타일: Surface bg(#F0EDE8), gap 8px, padding 8px 12px
   - 현재 메인 이미지에 표시된 아이템(items[0])에 Marsala 테두리 강조

3. 썸네일 탭 시:
   - 메인 이미지가 해당 아이템 이미지로 교체 (state로 관리)
   - 탭한 썸네일에 Marsala 테두리

이렇게 하면 사용자가 코디에 포함된 모든 아이템을 확인할 수 있어.

Props 변경:
- 기존 imageUrl: string → items: { image_url: string; name: string; price: number }[] 추가
  (imageUrl도 호환성 위해 유지)

feed/page.tsx에서 OutfitCard 호출 시 items prop 전달하도록 수정.

compact variant는 변경 없음 (썸네일만 표시).

DESIGN.md의 컬러/스페이싱 규칙 준수.
수정 후 npm run build 확인.
```

---

## Prompt C-1. 하단 탭바 4탭→2탭 축소 (P1)

```
TASK_v2.md의 Task 2.24v2를 진행해줘.

frontend/components/BottomTabBar.tsx를 수정:

현재: 홈 / 저장 / Top / 마이 (4탭)
변경: 홈 / 마이 (2탭)

작업:
1. 저장 탭, Top 탭 제거
2. 홈 아이콘 + "홈" 라벨
3. 마이 아이콘 + "마이" 라벨
4. 홈 → /feed, 마이 → /profile
5. 활성 탭: Marsala(#964F4C) 색상
6. 비활성 탭: Warm Gray(#8C8578)
7. 탭바 높이 56px, bg #F8F6F3, 상단 보더 #E5E1DA

기존 /saved, /top-pick 페이지는 제거하지 말고 라우팅만 제거.

수정 후 TASK_v2.md에서 Task 2.24v2를 완료 체크해줘.
```

---

## Prompt C-2. evidence/risk_guard 가독성 개선 (P1)

```
현재 피드 화면에서 이미지가 3:4로 크게 차지하고,
evidence와 risk_guard 텍스트가 스크롤 아래로 밀려서 바로 안 보여.

"결정 지원" 서비스인데 결정 근거가 즉시 보여야 해.

frontend/components/OutfitCard.tsx의 full variant 레이아웃을 조정해줘:

변경 방향:
1. 이미지 비율을 3:4 → 4:5로 약간 줄임 (또는 max-height 60vh 적용)
2. core 텍스트를 이미지 하단에 오버레이 (반투명 그라데이션 배경)
   - 위치: 이미지 bottom, padding 12px 16px
   - 배경: linear-gradient(transparent, rgba(0,0,0,0.5))
   - core 텍스트: white, Nanum Myeongjo 16px, font-weight 700
   - 가격: white, 15px, font-weight 700
3. evidence와 risk_guard를 이미지 바로 아래에 배치 (기존보다 위로)
   - evidence: #8C8578, 13px
   - risk_guard: #6B7F5E, 13px
   - 둘 다 줄바꿈 없이 2줄 이내

이렇게 하면 스크롤 없이 이미지 + core + evidence + risk_guard + CTA가 한 화면에 보여.

DESIGN.md 컬러/서체 규칙 준수.
수정 후 npm run build 확인.
```

---

## Prompt D. core/evidence 텍스트 차별화 (P2)

```
현재 모든 코디의 core가 "아이템A + 아이템B — 여름쿨라이트 XX룩" 동일 패턴이야.
evidence도 톤 관련 문장이 반복돼.

backend/app/services/reason_generator.py를 개선해줘:

1. core 다양화:
   현재: "니트 + 슬랙스 — 여름쿨라이트 출근룩"
   변경: 축 1순위에 따라 표현 변경
   - pcf 1위: "여름쿨라이트에 딱 맞는 출근 코디"
   - of 1위: "출근에 최적화된 깔끔한 조합"
   - ch 1위: "색감 조화가 돋보이는 출근 코디"
   - pe 1위: "가성비 좋은 출근 코디"
   - sf 1위: "실루엣이 깔끔한 출근 조합"

2. evidence 다양화:
   현재 5개 축별 high/low 2패턴 = 10가지
   각 패턴을 3가지 변형으로 확대 = 30가지
   예) pcf + high:
   - "니트의 색감이 여름쿨라이트 톤과 자연스럽게 어울려서 피부가 밝아 보여요"
   - "여름쿨라이트의 시원한 톤에 맞춘 색상이라 얼굴이 화사해 보여요"
   - "피부 톤과 조화로운 색상 선택으로 자연스러운 분위기가 나요"

3. risk_guard는 현재 패턴 유지 (충분함)

_build_core()에 scores 파라미터 추가 (축 1순위 판단용).
generate_reasons()에서 scores를 _build_core()에 전달.

기존 테스트 호환성 유지.
수정 후 pytest 실행.
```

---

## 실행 체크리스트

```
□ Prompt A: 아동복/이상 데이터 제거 완료 (제거 건수 확인)
□ Prompt B: 멀티 아이템 썸네일 리스트 표시 + build 성공
□ Prompt C-1: 하단 탭바 2탭으로 축소
□ Prompt C-2: evidence 가독성 개선 (한 화면에 보이는지 확인)
□ Prompt D: core/evidence 텍스트 다양화 + pytest 통과
□ 브라우저에서 최종 확인
```
