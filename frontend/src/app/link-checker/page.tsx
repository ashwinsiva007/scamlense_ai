"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  ExternalLink,
  Search,
  Sparkles,
  ArrowRight,
  Info,
  CheckCircle2,
  XCircle,
  Lock,
  FileCode,
} from "lucide-react";
import { checkLink, LinkCheckResponse } from "@/lib/api";
import { Button } from "@/components/ui/Button";

// Client-side fallback analyzer implementing scam-link-checker.html logic
const BRANDS_LOCAL: Record<string, string[]> = {
  paypal: ["paypal.com"],
  amazon: ["amazon.com", "amazon.in", "amazon.co.uk", "amazon.de", "amazon.ca", "amazon.com.au"],
  google: ["google.com", "google.co.in", "gmail.com"],
  flipkart: ["flipkart.com"],
  paytm: ["paytm.com"],
  phonepe: ["phonepe.com"],
  gpay: ["pay.google.com"],
  netflix: ["netflix.com"],
  apple: ["apple.com", "icloud.com"],
  microsoft: ["microsoft.com", "live.com", "office.com"],
  facebook: ["facebook.com", "fb.com"],
  instagram: ["instagram.com"],
  whatsapp: ["whatsapp.com", "wa.me"],
  irctc: ["irctc.co.in"],
  sbi: ["sbi.co.in", "onlinesbi.sbi", "sbicard.com"],
  hdfc: ["hdfcbank.com", "hdfc.com"],
  icici: ["icicibank.com"],
  axis: ["axisbank.com"],
  kotak: ["kotak.com"],
  binance: ["binance.com"],
  coinbase: ["coinbase.com"],
  ebay: ["ebay.com"],
  dhl: ["dhl.com"],
  fedex: ["fedex.com"],
  myntra: ["myntra.com"],
  swiggy: ["swiggy.com"],
  zomato: ["zomato.com"],
  uidai: ["uidai.gov.in"],
  incometax: ["incometax.gov.in"],
  airtel: ["airtel.in"],
  jio: ["jio.com"],
  bankofindia: ["bankofindia.co.in"],
};

const BAD_TLDS_LOCAL = [
  "xyz", "top", "tk", "ml", "ga", "cf", "gq", "click", "buzz", "icu", "work",
  "rest", "loan", "zip", "mov", "cfd", "sbs", "monster", "cyou", "quest", "fit",
  "cam", "support", "bid", "win", "vip", "live", "site", "online", "store", "shop",
];

const SHORT_LOCAL = [
  "bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd", "cutt.ly", "rb.gy",
  "shorturl.at", "ow.ly", "rebrand.ly", "tiny.cc", "s.id", "t.ly",
];

const WORDS_LOCAL = [
  "login", "signin", "verify", "verification", "secure", "update", "account",
  "bonus", "prize", "winner", "free", "gift", "claim", "kyc", "refund",
  "lottery", "giveaway", "recharge", "offer", "earn", "wallet", "crypto",
  "invest", "double", "reward", "suspend", "unlock", "confirm", "cashback",
  "lucky", "airdrop", "password", "otp",
];

const TWO_LOCAL = [
  "co.in", "org.in", "net.in", "gov.in", "nic.in", "ac.in", "edu.in", "res.in",
  "co.uk", "org.uk", "ac.uk", "com.au", "co.nz", "com.br", "co.za", "co.jp", "com.sg",
];

function localAnalyze(raw: string): LinkCheckResponse | null {
  let s = raw.trim();
  const had = /^[a-z][a-z0-9+.-]*:\/\//i.test(s);
  if (!had) s = "https://" + s;
  let u: URL;
  try {
    u = new URL(s);
  } catch {
    return null;
  }
  if (u.protocol !== "http:" && u.protocol !== "https:") return null;
  const host = u.hostname.toLowerCase().replace(/\.$/, "");
  const full = (host + u.pathname + u.search).toLowerCase();

  const findings: { level: "bad" | "warn" | "good"; title: string; description: string; points: number }[] = [];
  let score = 0;

  function add(level: "bad" | "warn" | "good", title: string, description: string, points: number) {
    findings.push({ level, title, description, points });
    score += points;
  }

  // regDomain
  const parts = host.split(".");
  let reg = host;
  if (parts.length > 2) {
    const last2 = parts.slice(-2).join(".");
    if (TWO_LOCAL.includes(last2)) {
      reg = parts.slice(-3).join(".");
    } else {
      reg = last2;
    }
  }

  const label = reg.split(".")[0];
  const tld = host.split(".").pop() || "";

  let trustedBrand: string | null = null;
  for (const b of Object.keys(BRANDS_LOCAL)) {
    if (BRANDS_LOCAL[b].includes(reg)) {
      trustedBrand = b;
      break;
    }
  }

  if (u.protocol === "http:") {
    add("bad", "Not encrypted (http)", "The page doesn't use a secure connection. Real shops and banks use https.", 20);
  } else {
    add("good", "Uses https", "The connection is encrypted. Note: Scam sites can have https too.", 0);
  }

  if (/^\d{1,3}(\.\d{1,3}){3}$/.test(host) || /^\[.*\]$/.test(host) || /^0x[0-9a-f]+$/i.test(host)) {
    add("bad", "Address is a number, not a name", "Legitimate companies almost never ask you to log in or pay at a raw IP address.", 40);
  }

  if (host.includes("xn--")) {
    add("bad", "Look-alike characters in the name", "The domain uses special characters that imitate letters.", 35);
  }

  if (/@/.test(s.replace(/^https?:\/\//, "").split("/")[0])) {
    add("bad", "Contains '@' before the site name", "Everything before @ is ignored by the browser to obscure destination.", 35);
  }

  if (SHORT_LOCAL.includes(host)) {
    add("warn", "Shortened link", "You cannot see where it leads until expanded.", 25);
  }

  if (u.port && u.port !== "80" && u.port !== "443") {
    add("warn", "Unusual port number", `Port ${u.port} is rarely used by genuine websites.`, 15);
  }

  if (trustedBrand) {
    add("good", `Matches the official domain for ${trustedBrand.toUpperCase()}`, `Main domain is ${reg}, official for ${trustedBrand.toUpperCase()}.`, -30);
    const extra = host.slice(0, host.length - reg.length - 1);
    if (extra && /(login|secure|verify|account|update)/.test(extra) && extra.split(".").length > 1) {
      add("warn", "Odd sub-domain wording", "Official address, but sub-domain contains security words.", 10);
    }
  } else {
    let hit: string | null = null;
    for (const b of Object.keys(BRANDS_LOCAL)) {
      if (!hit && host.includes(b)) hit = b;
    }
    if (hit) {
      add("bad", `Uses the name '${hit.toUpperCase()}' but isn't their domain`, `The real ${hit} site lives at ${BRANDS_LOCAL[hit][0]}. This is on ${reg}.`, 40);
    } else {
      const norm = label.replace(/rn/g, "m").replace(/vv/g, "w").replace(/0/g, "o").replace(/1/g, "l").replace(/3/g, "e").replace(/5/g, "s").replace(/\$/g, "s");
      if (norm !== label) {
        for (const b of Object.keys(BRANDS_LOCAL)) {
          if (!hit && norm.includes(b)) hit = b;
        }
        if (hit) {
          add("bad", `Looks like a misspelt copy of '${hit.toUpperCase()}'`, "Swapped characters (like 0 for o or rn for m) are used to imitate real brands.", 40);
        }
      }
    }
  }

  if (BAD_TLDS_LOCAL.includes(tld)) {
    add("warn", `Ending '.${tld}' is common on throw-away sites`, "Cheap domain endings are heavily used for scams.", 15);
  }

  const dots = host.split(".").length - 1;
  if (dots >= 4) {
    add("warn", "Many sub-domains", `The address has ${dots + 1} parts to bury the real domain.`, 15);
  }

  const hy = (host.match(/-/g) || []).length;
  if (hy >= 3) {
    add("warn", "Lots of hyphens in the name", "Names like 'secure-login-bank-offer' are typical of fake sites.", 15);
  } else if (hy >= 1 && !trustedBrand) {
    add("warn", "Hyphenated domain", "Hyphens are a mild warning indicator.", 5);
  }

  const digits = (label.match(/\d/g) || []).length;
  if (digits >= 4) {
    add("warn", "Many digits in the name", "Auto-generated domains often contain strings of numbers.", 10);
  }

  const found = WORDS_LOCAL.filter((w) => full.includes(w));
  if (found.length && !trustedBrand) {
    add(found.length >= 2 ? "bad" : "warn", `Pressure or bait words: ${found.slice(0, 5).join(", ")}`, "Words about gifts, KYC, refunds or account blocks push urgent action.", Math.min(30, found.length * 12));
  }

  if (s.length > 120) {
    add("warn", "Very long link", "Long addresses are sometimes used to hide the real destination.", 10);
  }

  if (/\.(apk|exe|scr|msi|bat|jar)(\?|$)/i.test(u.pathname)) {
    add("bad", "Link downloads an app or program", "Never install an APK or program from a link you were sent.", 40);
  }

  const finalScore = Math.max(0, Math.min(100, score));
  const level = finalScore >= 45 ? "bad" : finalScore >= 20 ? "warn" : "good";
  const title = level === "bad" ? "Very likely fake or unsafe" : level === "warn" ? "Suspicious: be careful" : "No obvious red flags";
  const advice = level === "good"
    ? "Still, don't enter passwords, card details, or OTPs unless you reached the site from the company's official app or by typing its address yourself."
    : "Don't enter any personal details, passwords, card numbers, or OTPs, and do not pay anything. Treat the sender with extreme suspicion.";

  return {
    url: u.href,
    host,
    reg_domain: reg,
    score: finalScore,
    level,
    title,
    trusted: Boolean(trustedBrand),
    trusted_brand: trustedBrand,
    findings,
    advice,
    second_opinions: [
      { name: "Google Safe Browsing", url: `https://transparencyreport.google.com/safe-browsing/search?url=${encodeURIComponent(u.href)}` },
      { name: "VirusTotal", url: "https://www.virustotal.com/gui/home/url" },
      { name: "Domain Age (WHOIS)", url: `https://who.is/whois/${encodeURIComponent(reg)}` },
    ],
  };
}

export default function LinkCheckerPage() {
  const [urlInput, setUrlInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<LinkCheckResponse | null>(null);

  const handleCheck = async (e?: React.FormEvent, overrideUrl?: string) => {
    if (e) e.preventDefault();
    const target = (overrideUrl || urlInput).trim();
    if (!target) {
      setError("Please paste a link first.");
      return;
    }
    setError(null);
    setLoading(true);

    try {
      // Try backend endpoint first
      const res = await checkLink(target);
      setResult(res);
    } catch {
      // Fallback to local heuristic engine
      const localRes = localAnalyze(target);
      if (localRes) {
        setResult(localRes);
      } else {
        setError("That doesn't look like a valid web address. Ensure it starts with http://, https://, or a valid domain.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSelectExample = (ex: string) => {
    setUrlInput(ex);
    handleCheck(undefined, ex);
  };

  const getBadgeStyle = (level: "bad" | "warn" | "good") => {
    if (level === "bad") return "bg-rose-50 border-rose-200 text-rose-700";
    if (level === "warn") return "bg-amber-50 border-amber-200 text-amber-700";
    return "bg-emerald-50 border-emerald-200 text-emerald-700";
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 sm:py-14 space-y-8 animate-fadeIn">
      {/* Header */}
      <header className="text-center space-y-3 max-w-2xl mx-auto">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-primary/10 text-primary border border-primary/20">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Real-time Link Intelligence</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-900">
          Is this website a scam?
        </h1>
        <p className="text-sm sm:text-base text-slate-600 leading-relaxed">
          Paste a link before you pay, log in, or share an OTP. The checker evaluates the domain,
          unmasks impersonated brands, flags suspicious TLDs, and detects phishing tricks.
        </p>
      </header>

      {/* Main Form Card */}
      <div className="glass-panel rounded-2xl shadow-xl shadow-slate-200/50 p-6 sm:p-8 space-y-6">
        <form onSubmit={handleCheck} className="space-y-4">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="w-5 h-5 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={urlInput}
                onChange={(e) => setUrlInput(e.target.value)}
                placeholder="Paste link, e.g. http://paytm-kyc-update.top/verify?acc=1"
                className="w-full pl-11 pr-4 py-3.5 text-sm sm:text-base rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-white shadow-inner font-mono text-slate-800"
              />
            </div>
            <Button
              type="submit"
              disabled={loading}
              className="py-3.5 px-6 font-bold flex items-center justify-center gap-2 whitespace-nowrap shadow-md"
            >
              {loading ? (
                <span>Checking...</span>
              ) : (
                <>
                  <span>Check link</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </Button>
          </div>

          {/* Quick Examples */}
          <div className="flex items-center gap-2 flex-wrap text-xs text-slate-500 pt-1">
            <span className="font-semibold text-slate-600">Try an example:</span>
            <button
              type="button"
              onClick={() => handleSelectExample("https://www.amazon.in")}
              className="px-2.5 py-1 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 font-medium transition-colors"
            >
              amazon.in
            </button>
            <button
              type="button"
              onClick={() => handleSelectExample("http://paytm-kyc-update.top/verify?acc=1")}
              className="px-2.5 py-1 rounded-full bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 font-medium transition-colors"
            >
              paytm-kyc-update.top
            </button>
            <button
              type="button"
              onClick={() => handleSelectExample("http://192.168.4.20/sbi/login.php")}
              className="px-2.5 py-1 rounded-full bg-amber-50 hover:bg-amber-100 text-amber-700 border border-amber-200 font-medium transition-colors"
            >
              IP address link
            </button>
            <button
              type="button"
              onClick={() => handleSelectExample("https://fake-lottery-gift.xyz/claim")}
              className="px-2.5 py-1 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 font-medium transition-colors"
            >
              .xyz bait link
            </button>
          </div>

          {error && (
            <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs sm:text-sm font-medium flex items-center gap-2">
              <XCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}
        </form>

        {/* Results Presentation */}
        {result && (
          <div className="space-y-6 pt-4 border-t border-slate-200 animate-fadeIn">
            {/* Verdict Banner */}
            <div
              className={`rounded-2xl p-6 border-2 transition-all ${
                result.level === "bad"
                  ? "bg-rose-50/70 border-rose-300 text-rose-950"
                  : result.level === "warn"
                  ? "bg-amber-50/70 border-amber-300 text-amber-950"
                  : "bg-emerald-50/70 border-emerald-300 text-emerald-950"
              }`}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    {result.level === "bad" ? (
                      <ShieldAlert className="w-6 h-6 text-rose-600" />
                    ) : result.level === "warn" ? (
                      <AlertTriangle className="w-6 h-6 text-amber-600" />
                    ) : (
                      <ShieldCheck className="w-6 h-6 text-emerald-600" />
                    )}
                    <h2 className="text-xl sm:text-2xl font-black">{result.title}</h2>
                  </div>
                  <p className="text-sm font-mono text-slate-600 break-all">{result.host}</p>
                </div>
                <span
                  className={`px-3 py-1 text-xs font-extrabold uppercase rounded-full border ${getBadgeStyle(
                    result.level
                  )}`}
                >
                  {result.level === "bad" ? "High Risk" : result.level === "warn" ? "Caution" : "Low Risk"}
                </span>
              </div>

              {/* Progress Meter */}
              <div className="mt-5 space-y-1.5">
                <div className="w-full bg-slate-200/80 rounded-full h-3 overflow-hidden">
                  <div
                    className={`h-full transition-all duration-700 rounded-full ${
                      result.level === "bad"
                        ? "bg-rose-600"
                        : result.level === "warn"
                        ? "bg-amber-500"
                        : "bg-emerald-500"
                    }`}
                    style={{ width: `${result.score}%` }}
                  />
                </div>
                <div className="flex justify-between text-xs font-semibold text-slate-600">
                  <span>Risk score: {result.score} / 100</span>
                  <span>{result.score >= 45 ? "Danger" : result.score >= 20 ? "Suspicious" : "Clean"}</span>
                </div>
              </div>
            </div>

            {/* Findings List */}
            <div className="space-y-3">
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700">What We Found</h3>
              <div className="grid gap-2.5">
                {result.findings.map((f, i) => (
                  <div
                    key={i}
                    className={`p-3.5 rounded-xl border flex items-start gap-3 bg-white ${
                      f.level === "bad"
                        ? "border-l-4 border-l-rose-500 border-slate-200"
                        : f.level === "warn"
                        ? "border-l-4 border-l-amber-500 border-slate-200"
                        : "border-l-4 border-l-emerald-500 border-slate-200"
                    }`}
                  >
                    <div className="mt-0.5">
                      {f.level === "bad" ? (
                        <XCircle className="w-4 h-4 text-rose-500" />
                      ) : f.level === "warn" ? (
                        <AlertTriangle className="w-4 h-4 text-amber-500" />
                      ) : (
                        <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                      )}
                    </div>
                    <div className="space-y-0.5 flex-1">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-bold text-slate-900">{f.title}</span>
                        {f.points !== 0 && (
                          <span
                            className={`text-xs font-mono font-bold ${
                              f.points > 0 ? "text-rose-600" : "text-emerald-600"
                            }`}
                          >
                            {f.points > 0 ? `+${f.points}` : f.points}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-600 leading-relaxed">{f.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Safety Advice */}
            <div className="p-4 rounded-xl border border-dashed border-slate-300 bg-slate-50/70 text-xs sm:text-sm text-slate-700 leading-relaxed flex items-start gap-2.5">
              <Info className="w-4 h-4 text-primary shrink-0 mt-0.5" />
              <div>
                <strong className="text-slate-900">Safety Guidance: </strong>
                {result.advice}
              </div>
            </div>

            {/* Second Opinions */}
            <div className="space-y-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">Get A Second Opinion</h4>
              <div className="flex flex-wrap gap-2">
                {result.second_opinions.map((op, i) => (
                  <a
                    key={i}
                    href={op.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-xs font-semibold text-primary hover:text-primary-dark transition-colors shadow-sm"
                  >
                    <span>{op.name}</span>
                    <ExternalLink className="w-3 h-3 text-slate-400" />
                  </a>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Footer & Direct HTML tool link */}
        <div className="pt-6 border-t border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <div>
            Need to report a digital scam? In India, dial <strong>1930</strong> or file a report at{" "}
            <a
              href="https://cybercrime.gov.in"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary font-semibold underline"
            >
              cybercrime.gov.in
            </a>
            .
          </div>
          <a
            href="/scam-link-checker.html"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium transition-colors shrink-0"
          >
            <FileCode className="w-3.5 h-3.5" />
            <span>Open Standalone HTML Tool</span>
          </a>
        </div>
      </div>
    </div>
  );
}
