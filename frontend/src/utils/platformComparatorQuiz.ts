import type { CatalogPlatform } from "../data/platformCatalog";
import { getCatalogPlatform } from "../data/platformCatalog";

export type QuizAnswers = {
  q1: string | null;
  q2: string | null;
  q3: string | null;
  q4: string | null;
  q5: string | null;
};

const SCORE_IDS = [
  "bitvavo",
  "okx",
  "bybit",
  "bitpanda",
  "degiro",
  "ibkr",
  "trading212",
  "bux",
  "goldrepublic",
  "hollandgold",
] as const;

export function scorePlatformQuiz(ans: QuizAnswers): CatalogPlatform | null {
  const scores: Record<string, number> = {};
  for (const id of SCORE_IDS) scores[id] = 0;

  if (ans.q1 === "crypto") {
    scores.bitvavo += 3;
    scores.okx += 3;
    scores.bybit += 3;
    scores.bitpanda += 2;
  } else if (ans.q1 === "stocks") {
    scores.degiro += 3;
    scores.ibkr += 3;
    scores.trading212 += 3;
    scores.bux += 3;
    scores.bitpanda += 1;
  } else if (ans.q1 === "metals") {
    scores.goldrepublic += 4;
    scores.hollandgold += 4;
  } else if (ans.q1 === "mix") {
    scores.bitpanda += 4;
  }

  if (ans.q2 === "beginner") {
    scores.bitvavo += 2;
    scores.bux += 2;
    scores.trading212 += 2;
    scores.bitpanda += 2;
    scores.hollandgold += 1;
  } else if (ans.q2 === "intermediate") {
    scores.degiro += 2;
    scores.bitvavo += 1;
    scores.trading212 += 1;
    scores.goldrepublic += 1;
  } else if (ans.q2 === "advanced") {
    scores.ibkr += 3;
    scores.okx += 2;
    scores.bybit += 2;
    scores.degiro += 1;
  }

  if (ans.q3 === "simple") {
    scores.bux += 2;
    scores.bitvavo += 2;
    scores.trading212 += 2;
    scores.bitpanda += 1;
    scores.hollandgold += 1;
  } else if (ans.q3 === "cheap") {
    scores.okx += 2;
    scores.trading212 += 2;
    scores.ibkr += 2;
    scores.degiro += 1;
  } else if (ans.q3 === "features") {
    scores.ibkr += 3;
    scores.okx += 2;
    scores.bybit += 2;
  } else if (ans.q3 === "dutch") {
    scores.bitvavo += 3;
    scores.bux += 3;
    scores.goldrepublic += 2;
  }

  if (ans.q4 === "dca") {
    scores.trading212 += 3;
    scores.bitvavo += 2;
    scores.bux += 1;
    scores.bitpanda += 1;
  } else if (ans.q4 === "occasional") {
    scores.degiro += 1;
    scores.bux += 1;
    scores.goldrepublic += 1;
    scores.hollandgold += 1;
  } else if (ans.q4 === "frequent") {
    scores.ibkr += 2;
    scores.okx += 2;
    scores.bybit += 2;
  }

  if (ans.q5 === "api") {
    scores.bitvavo += 2;
    scores.okx += 2;
    scores.bybit += 2;
    scores.bitpanda += 2;
    scores.ibkr += 2;
  }

  let best: string | null = null;
  let bestScore = -1;
  for (const [id, s] of Object.entries(scores)) {
    if (s > bestScore) {
      bestScore = s;
      best = id;
    }
  }
  return best ? getCatalogPlatform(best) ?? null : null;
}

export function quizReasonForPlatform(platform: CatalogPlatform): string {
  const reasons: Record<string, string> = {
    bitvavo: "Nederlandstalig, AFM-vergund en toegankelijk voor crypto-starters.",
    okx: "Zeer lage fees en uitgebreid aanbod voor actieve crypto-traders.",
    bybit: "Advanced trading features voor ervaren crypto-gebruikers.",
    bitpanda: "Crypto, ETF's en edelmetaal in één eenvoudige app.",
    degiro: "Lage kosten en grote asset-keuze voor lange-termijn beleggers.",
    ibkr: "Professioneel platform met wereldwijde markten en API-koppeling.",
    trading212: "Geen commissies, fractioneel beleggen en uitstekend voor DCA.",
    bux: "Nederlandse AFM-vergunning, simpele mobiele app.",
    goldrepublic: "AFM-vergund edelmetaalplatform met Zwitserse opslag.",
    hollandgold: "Fysieke levering en grote productkeuze zonder beheerkosten.",
  };
  return reasons[platform.id] ?? platform.idealFor;
}
