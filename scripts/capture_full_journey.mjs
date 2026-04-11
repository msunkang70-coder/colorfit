/**
 * ColorFit 전체 유저 여정 캡쳐 → PDF 1장
 * 온보딩 Step1~5 → 피드 (전체/출근/면접/데이트/운동) → Explore → CTA → 설문
 */

import { chromium } from "playwright";
import fs from "fs";
import path from "path";

const BASE = "http://localhost:3000";
const OUT = path.resolve("ui화면/journey");
const PDF = path.resolve("ui화면/colorfit_full_journey.pdf");

async function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function main() {
  fs.mkdirSync(OUT, { recursive: true });

  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({
    viewport: { width: 390, height: 844 },
    deviceScaleFactor: 2,
  });

  await ctx.route("**/*pstatic.net/**", async (route) => {
    await route.continue({ headers: { ...route.request().headers(), referer: "https://search.shopping.naver.com/" } });
  });

  const page = await ctx.newPage();
  const shots = [];
  let n = 0;

  async function capture(label, fullPage = true) {
    n++;
    const f = path.join(OUT, `${String(n).padStart(2, "0")}_${label.replace(/[^a-zA-Z0-9가-힣_]/g, "_")}.png`);
    await page.screenshot({ path: f, fullPage });
    shots.push({ path: f, label });
    console.log(`  [${n}] ${label}`);
  }

  // ──────────────────────────────
  // 온보딩 Step 1: 성별 선택
  // ──────────────────────────────
  console.log("온보딩...");
  await page.goto(`${BASE}/onboarding/step1`, { waitUntil: "networkidle" });
  await sleep(1000);
  await capture("온보딩 Step1 — 성별 선택");

  // 여성 선택
  const genderCards = page.locator("main button, main div[role=button]").first();
  try { await genderCards.click({ timeout: 2000 }); } catch {}
  await sleep(1500);

  // ──────────────────────────────
  // 온보딩 Step 2: 퍼스널컬러
  // ──────────────────────────────
  await page.goto(`${BASE}/onboarding/step2`, { waitUntil: "networkidle" });
  await sleep(1000);
  await capture("온보딩 Step2 — 퍼스널컬러 선택");

  // 봄웜라이트 선택 시도
  try {
    const toneBtn = page.locator("text=봄웜라이트").first();
    if (await toneBtn.isVisible({ timeout: 1000 })) await toneBtn.click();
  } catch {}
  await sleep(1000);

  // ──────────────────────────────
  // 온보딩 Step 3: TPO + 무드
  // ──────────────────────────────
  await page.goto(`${BASE}/onboarding/step3`, { waitUntil: "networkidle" });
  await sleep(1000);
  await capture("온보딩 Step3 — TPO + 무드 선택");

  // ──────────────────────────────
  // 온보딩 Step 4: 예산
  // ──────────────────────────────
  await page.goto(`${BASE}/onboarding/step4`, { waitUntil: "networkidle" });
  await sleep(1000);
  await capture("온보딩 Step4 — 예산 설정");

  // ──────────────────────────────
  // 온보딩 Step 5: 취향
  // ──────────────────────────────
  await page.goto(`${BASE}/onboarding/step5`, { waitUntil: "networkidle" });
  await sleep(1000);
  await capture("온보딩 Step5 — 스타일 취향");

  // localStorage에 온보딩 데이터 설정
  await page.evaluate(() => {
    localStorage.setItem("colorfit_onboarding", JSON.stringify({
      gender: "female",
      tone_id: "summer_cool_light",
      tpo_list: ["commute", "date"],
      style_moods: ["minimal", "classic"],
      budget_min: 30000,
      budget_max: 300000,
      style_seed_choices: [],
    }));
  });

  // ──────────────────────────────
  // 피드: TPO별 순회
  // ──────────────────────────────
  const TABS = [
    { label: "전체", idx: 0 },
    { label: "출근", idx: 1 },
    { label: "면접", idx: 2 },
    { label: "데이트", idx: 4 },
    { label: "운동", idx: 8 },
  ];

  for (const tab of TABS) {
    console.log(`피드: ${tab.label}...`);
    await page.goto(`${BASE}/feed`, { waitUntil: "networkidle" });
    await sleep(1500);

    // 탭 클릭
    if (tab.idx > 0) {
      const btns = page.locator("header button.shrink-0");
      const cnt = await btns.count();
      if (tab.idx < cnt) {
        await btns.nth(tab.idx).scrollIntoViewIfNeeded();
        await btns.nth(tab.idx).click();
        await sleep(2500);
      }
    }
    await sleep(2000);

    // 메인 화면
    await capture(`피드 ${tab.label}탭 — 메인 화면 (Top1)`, false);

    // 스크롤 → CTA 영역
    await page.evaluate(() => window.scrollBy(0, 400));
    await sleep(500);
    await capture(`피드 ${tab.label}탭 — CTA + 코디 구성`, false);

    // Explore Mode
    const exploreBtn = page.locator('button:has-text("비슷한 선택 보기")');
    try {
      if (await exploreBtn.isVisible({ timeout: 1000 })) {
        await exploreBtn.click();
        await sleep(1500);
        await capture(`피드 ${tab.label}탭 — Explore Mode`, true);
      }
    } catch {}

    await page.evaluate(() => window.scrollTo(0, 0));
  }

  // ──────────────────────────────
  // CTA + 설문 팝업
  // ──────────────────────────────
  console.log("CTA + 설문...");
  await page.goto(`${BASE}/feed`, { waitUntil: "networkidle" });
  await sleep(2500);

  const ctaBtn = page.locator('button:has-text("이 코디로 결정")');
  try {
    if (await ctaBtn.isVisible({ timeout: 2000 })) {
      await ctaBtn.click();
      await sleep(1000);
      await capture("설문 팝업 — 신뢰도 + 확신", false);
    }
  } catch {}

  // ──────────────────────────────
  // 데모 페이지
  // ──────────────────────────────
  console.log("데모...");
  await page.goto(`${BASE}/demo`, { waitUntil: "networkidle" });
  await sleep(3000);
  await page.setViewportSize({ width: 1280, height: 800 });
  await sleep(500);
  await capture("데모 페이지 — 아이폰 프레임", false);

  // ──────────────────────────────
  // PDF 생성
  // ──────────────────────────────
  console.log(`\nPDF 생성 (${shots.length}장)...`);

  const pages = shots.map(s => {
    const b64 = fs.readFileSync(s.path).toString("base64");
    return `
      <div style="page-break-after:always;text-align:center;padding:12px;">
        <h3 style="font-family:-apple-system,sans-serif;font-size:13px;color:#333;margin:0 0 8px;">${s.label}</h3>
        <img src="data:image/png;base64,${b64}" style="max-width:100%;max-height:90vh;border:1px solid #eee;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.08);" />
      </div>`;
  });

  const html = `<!DOCTYPE html><html><head><meta charset="utf-8"></head>
<body style="margin:0;">
  <div style="text-align:center;padding:50px 20px;page-break-after:always;">
    <h1 style="font-family:-apple-system,sans-serif;font-size:32px;color:#964F4C;">ColorFit</h1>
    <p style="font-size:18px;color:#666;margin:16px 0;">Full User Journey</p>
    <p style="font-size:14px;color:#999;">${shots.length}pages · ${new Date().toISOString().slice(0,10)}</p>
    <p style="font-size:13px;color:#999;margin-top:24px;">온보딩 → 피드 (5 TPO) → Explore → CTA → 설문 → 데모</p>
  </div>
  ${pages.join("\n")}
</body></html>`;

  const pdfPage = await ctx.newPage();
  await pdfPage.setContent(html, { waitUntil: "load" });
  await pdfPage.pdf({
    path: PDF,
    format: "A4",
    printBackground: true,
    margin: { top: "8mm", bottom: "8mm", left: "8mm", right: "8mm" },
  });

  console.log(`\n✅ ${PDF}`);
  console.log(`   ${shots.length}장`);

  await browser.close();
}

main().catch(e => { console.error(e); process.exit(1); });
