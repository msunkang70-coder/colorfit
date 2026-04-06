# ColorFit 데모 시나리오

**프로덕션 URL:**
- 프론트: https://frontend-msunkang70-1055s-projects.vercel.app
- 백엔드: https://colorfit-api-production.up.railway.app

---

## 시나리오 A: 출근 코디 즉시 결정 (Decision Mode)

**페르소나:** 김지은 (25세, 여름쿨소프트, 대학원생)
**목표 TTD:** < 15초

```
1. ColorFit 접속 → 온보딩 시작
2. Step 1: 여성 선택
3. Step 2: 여름쿨소프트 선택
4. Step 3: 출근 TPO 선택
5. Step 4: 예산 3~10만원 설정
6. Step 5: 취향 이미지 4라운드 선택 (또는 패스)
7. 피드 진입 → Top1 코디 확인
   - core: "XX + YY — 여름쿨소프트 출근룩"
   - evidence: 축 기반 근거 문장
   - risk_guard: 실패 가능성 낮은 이유
8. "이 코디로 결정" CTA 탭
9. 설문: 신뢰도 5점, 확신 Yes
10. 쇼핑몰 이동

측정: expanded=false, expand_level=0, selected_rank=1, TTD < 15초
```

---

## 시나리오 B: 데이트 코디 비교 후 결정 (Explore Mode)

**페르소나:** 박민준 (32세, 가을웜딥, IT 팀장)
**목표 TTD:** < 30초

```
1. 피드에서 TPO "데이트" 탭 선택
2. Top1 코디 확인 → "다른 것도 볼까?"
3. "비슷한 선택 보기" 탭
4. Top3 표시:
   - [1위 추천] 또는 [컬러 매칭형] — Top1
   - [실루엣형] 또는 [상황 최적형] — Top2
   - [가성비형] — Top3
5. Top2 compact 카드 탭 → Decision Mode 복귀 (Top2가 메인)
6. "이 코디로 결정" → 설문 (신뢰도 4, 확신 Yes) → 이동

측정: expanded=true, expand_level=1, selected_rank=2, TTD < 30초
```

---

## 시나리오 C: TPO 변경 → 재결정

```
1. 시나리오 A 또는 B 이후
2. TPO 탭에서 "주말" 선택
3. 새 코디 로드 확인 (expandLevel 리셋)
4. Top1 확인 → 즉시 결정 또는 비교 후 결정
5. 설문 → 이동

측정: TPO 변경 시 expandLevel=0 리셋, 새 코디 ID
```

---

## 데모 시 강조 포인트

1. **Decision Mode (8초):** "코디 1개 + 왜 이건지 + 왜 괜찮은지 → 즉시 결정"
2. **Explore Mode (22초):** "비교 후 확신 → 후회 없는 결정"
3. **evidence + risk_guard:** "추천 이유를 설명하는 유일한 서비스"
4. **축 기반 다양성:** "Top3가 각각 다른 강점 — 의미 있는 비교"
5. **측정:** "TTD/CTR/신뢰도/확신 — 결정 품질을 측정하는 서비스"
