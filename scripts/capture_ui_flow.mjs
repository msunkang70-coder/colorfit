/**
 * ColorFit UI E2E 캡쳐 → PDF
 *
 * 실행: node scripts/capture_ui_flow.mjs
 */

import { chromium } from "playwright";
import fs from "fs";
import path from "path";

const BASE = "http://localhost:3000";
const OUT = path.resolve("ui화면/captures");
const PDF = path.resolve("ui화면/colorfit_ui_flow.pdf");

const TABS = ["전체","출근","면접","캠퍼스","데이트","주말","여행","행사","운동"];

// 온보딩 데이터
const ONBOARDING = JSON.stringify({
  gender: "female",
  tone_id: "summer_cool_light",
  tpo_list: ["commute","date"],
  style_moods: ["minimal","classic"],
  budget_min: 30000,
  budget_max: 300000,
  style_seed_choices: [],
});

async function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function main() {
  fs.mkdirSync(OUT, { recursive: true });

  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({
    viewport: { width: 390, height: 844 },
    deviceScaleFactor: 2,
    bypassCSP: true,
  });

  // referrer 정책 우회 — 네이버 이미지 로딩용
  await ctx.route("**/*pstatic.net/**", async (route) => {
    const req = route.request();
    await route.continue({ headers: { ...req.headers(), referer: "https://search.shopping.naver.com/" } });
  });

  const page = await ctx.newPage();

  // 온보딩 설정
  await page.goto(BASE + "/feed", { waitUntil: "networkidle" });
  await page.evaluate((data) => localStorage.setItem("colorfit_onboarding", data), ONBOARDING);

  const shots = [];
  let num = 0;

  for (let tabIdx = 0; tabIdx < TABS.length; tabIdx++) {
    const tabName = TABS[tabIdx];
    const prefix = String(tabIdx + 1).padStart(2, "0");
    console.log(`[${tabName}]`);

    // 페이지 새로고침 + 탭 클릭
    await page.goto(BASE + "/feed", { waitUntil: "networkidle" });
    await sleep(1500);

    // 탭 클릭 (전체=0번째)
    const tabBtns = page.locator("header button.shrink-0");
    const tabCount = await tabBtns.count();

    // 스크롤해서 탭 보이게
    if (tabIdx > 0 && tabIdx < tabCount) {
      await tabBtns.nth(tabIdx).scrollIntoViewIfNeeded();
      await tabBtns.nth(tabIdx).click();
      await sleep(2500); // API 응답 대기
    } else {
      await sleep(1500);
    }

    // 이미지 로딩 대기
    await sleep(2000);

    // === Step 1: 메인 화면 (풀페이지) ===
    num++;
    const f1 = path.join(OUT, `${prefix}_${tabName}_step1_main.png`);
    await page.screenshot({ path: f1, fullPage: true });
    shots.push({ path: f1, label: `[${tabName}] Step 1 — 메인 화면` });
    console.log("  step1 메인");

    // === Step 2: 뷰포트 (Top1 중심) ===
    await page.evaluate(() => window.scrollTo(0, 0));
    await sleep(300);
    num++;
    const f2 = path.join(OUT, `${prefix}_${tabName}_step2_top1.png`);
    await page.screenshot({ path: f2, fullPage: false });
    shots.push({ path: f2, label: `[${tabName}] Step 2 — Top1 코디 (뷰포트)` });
    console.log("  step2 Top1");

    // === Step 3: 스크롤 다운 — CTA + evidence 영역 ===
    await page.evaluate(() => window.scrollBy(0, 400));
    await sleep(500);
    num++;
    const f3 = path.join(OUT, `${prefix}_${tabName}_step3_cta.png`);
    await page.screenshot({ path: f3, fullPage: false });
    shots.push({ path: f3, label: `[${tabName}] Step 3 — CTA + 코디 구성` });
    console.log("  step3 CTA");

    // === Step 4: "비슷한 선택 보기" 클릭 ===
    const exploreBtn = page.locator('button:has-text("비슷한 선택 보기")');
    let hasExplore = false;
    try {
      hasExplore = await exploreBtn.isVisible({ timeout: 1000 });
    } catch { hasExplore = false; }

    if (hasExplore) {
      await exploreBtn.click();
      await sleep(1500);
      num++;
      const f4 = path.join(OUT, `${prefix}_${tabName}_step4_explore.png`);
      await page.screenshot({ path: f4, fullPage: true });
      shots.push({ path: f4, label: `[${tabName}] Step 4 — Explore Mode` });
      console.log("  step4 Explore");

      // 스크롤해서 compact 카드 보기
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
      await sleep(500);
      num++;
      const f5 = path.join(OUT, `${prefix}_${tabName}_step5_explore_bottom.png`);
      await page.screenshot({ path: f5, fullPage: false });
      shots.push({ path: f5, label: `[${tabName}] Step 5 — Explore 하단 (compact 카드)` });
      console.log("  step5 Explore 하단");
    } else {
      console.log("  step4 Explore 없음 (코디 부족)");
    }
  }

  // ====== PDF 생성 ======
  console.log(`\nPDF 생성 (${shots.length}장)...`);

  const imgTags = shots.map(s => {
    const b64 = fs.readFileSync(s.path).toString("base64");
    return `
      <div style="page-break-after:always;text-align:center;padding:16px 12px;">
        <h3 style="font-family:-apple-system,sans-serif;font-size:14px;color:#333;margin:0 0 10px;">${s.label}</h3>
        <img src="data:image/png;base64,${b64}" style="max-width:100%;max-height:88vh;border:1px solid #eee;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.1);" />
      </div>`;
  });

  const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><title>ColorFit UI Flow</title></head>
<body style="margin:0;padding:0;">
  <div style="text-align:center;padding:60px 20px;page-break-after:always;">
    <h1 style="font-family:-apple-system,sans-serif;font-size:32px;color:#964F4C;margin:0;">ColorFit</h1>
    <p style="font-family:-apple-system,sans-serif;font-size:16px;color:#666;margin:12px 0;">UI Flow — ${new Date().toISOString().slice(0,10)}</p>
    <p style="font-family:-apple-system,sans-serif;font-size:14px;color:#999;">${shots.length}장 · ${TABS.length}개 TPO</p>
  </div>
  ${imgTags.join("\n")}
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
  console.log(`   ${shots.length}장 · ${TABS.length} TPO`);

  await browser.close();
}

main().catch(e => { console.error(e); process.exit(1); });
