/**
 * Payment Screenshot Extractor & Authenticity Intelligence Engine
 * ---------------------------------------------------------------
 * Ported directly from external featured payment screenshot extractor.
 * Runs completely in the background without user interaction or extra buttons.
 * Extracts payment entities (transaction ID, UTR, amount, status, date, bank, payment app, UPI handles)
 * and evaluates tampering (photo editor metadata, aspect ratio, ELA compression analysis, and localStorage reuse).
 */

export interface ParsedPayment {
  transaction_id: string | null;
  amount: string | null;
  currency: string | null;
  status: "Success" | "Failed" | "Pending" | null;
  date_time: string | null;
  paid_to: string | null;
  paid_from: string | null;
  upi_ids: string[];
  phone: string | null;
  bank: string | null;
  payment_app: string | null;
}

export interface AuthenticityCheck {
  pts: number;
  text: string;
  sev: "ok" | "warn" | "bad" | "info";
}

export interface ClientAuthenticityResult {
  parsed: ParsedPayment;
  score: number;
  checks: AuthenticityCheck[];
  elaRatio: number | null;
  seenBefore: {
    exactImageDate: string | null;
    transactionIdDate: string | null;
  };
}

const EDITORS = [
  "Photoshop",
  "GIMP",
  "Canva",
  "Snapseed",
  "PicsArt",
  "Pixlr",
  "Photopea",
  "Lightroom",
  "Paint.NET",
  "Fotor",
  "Inkscape",
  "Affinity",
  "Figma",
  "PhotoRoom",
  "Remini",
  "Picsart",
];

const first = (pats: RegExp[], t: string): string | null => {
  for (const p of pats) {
    const m = t.match(p);
    if (m && m[1]) return m[1].trim();
  }
  return null;
};

export function parsePaymentFields(t: string): ParsedPayment {
  const tid = first(
    [
      /UPI\s*(?:Transaction|Txn|Ref(?:erence)?)\s*(?:ID|No\.?|Number)?\s*[:\-]?\s*([A-Za-z0-9]{10,})/i,
      /(?:Google\s*Pay\s*)?Transaction\s*(?:ID|No\.?|Number)\s*[:\-]?\s*([A-Za-z0-9]{8,})/i,
      /Txn\s*(?:ID|No\.?)\s*[:\-]?\s*([A-Za-z0-9]{8,})/i,
      /UTR\s*(?:No\.?|Number|ID)?\s*[:\-]?\s*([A-Za-z0-9]{10,})/i,
      /(?:Reference|Ref)\s*(?:ID|No\.?|Number)\s*[:\-]?\s*([A-Za-z0-9]{8,})/i,
      /(?:Order|Payment)\s*ID\s*[:\-]?\s*([A-Za-z0-9\-]{8,})/i,
      /Transaction\s*ID\s*\n\s*([A-Za-z0-9]{8,})/i,
      /\b(T\d{15,25})\b/,
      /\b(\d{12})\b/,
    ],
    t
  );

  const amt = first(
    [
      /(?:₹|Rs\.?|INR)\s*([\d,]+(?:\.\d{1,2})?)/i,
      /Amount\s*(?:Paid|Sent|Debited|Credited)?\s*[:\-]?\s*(?:₹|Rs\.?|INR)?\s*([\d,]+(?:\.\d{1,2})?)/i,
      /(?:Paid|Sent|Received|Debited|Credited)\s*(?:₹|Rs\.?|INR)?\s*([\d,]+\.\d{2})/i,
      /(?:^|\s)[^\w\s]\s?(\d[\d,]*\.\d{2})\b/m,
    ],
    t
  );

  const tl = t.toLowerCase();
  const status: "Success" | "Failed" | "Pending" | null = /\b(fail(ed|ure)?|declined|unsuccessful|rejected)\b/.test(tl)
    ? "Failed"
    : /\b(pending|processing|in progress)\b/.test(tl)
    ? "Pending"
    : /\b(success(ful(ly)?)?|completed|paid|sent|received)\b/.test(tl)
    ? "Success"
    : null;

  const date = first(
    [
      /(\d{1,2}\s+[A-Za-z]{3,9}\.?,?\s+\d{4}(?:\s*(?:,|at)?\s*\d{1,2}:\d{2}(?::\d{2})?\s*(?:[AaPp]\.?[Mm]\.?)?)?)/,
      /([A-Za-z]{3,9}\.?\s+\d{1,2},?\s+\d{4}(?:\s*(?:,|at)?\s*\d{1,2}:\d{2}(?::\d{2})?\s*(?:[AaPp]\.?[Mm]\.?)?)?)/,
      /(\d{1,2}[\/\-.]\d{1,2}[\/\-.]\d{2,4}(?:\s*,?\s*\d{1,2}:\d{2}(?::\d{2})?\s*(?:[AaPp][Mm])?)?)/,
      /(\d{1,2}:\d{2}\s*[AaPp][Mm],?\s*\d{1,2}\s+[A-Za-z]{3,9}(?:\s+\d{4})?)/,
    ],
    t
  );

  const party = (labels: string): string | null => {
    const m = t.match(
      new RegExp(
        "(?:' + labels + ')\\s*[:\\-]?\\s*\\n?\\s*([A-Za-z][A-Za-z .&'\\-]{2,40})",
        "i"
      )
    );
    return m ? m[1].split(/\s{2,}|UPI|Transaction|Banking/)[0].trim() || null : null;
  };

  const rawUpis = t.match(/\b[\w.\-]{2,}@[a-zA-Z]{2,}\b/g) || [];
  const upis = Array.from(
    new Set(rawUpis.filter((x) => !/\.(com|in|org|net)$/i.test(x)))
  );

  const ph = t.match(/(?:\+91[\s\-]?)?\b([6-9]\d{4}[\s\-]?\d{5})\b/);
  const bank = t.match(
    /\b((?:State Bank of India|SBI|HDFC|ICICI|Axis|Kotak|Canara|Union|Punjab National|PNB|Bank of Baroda|BOB|IDFC|Yes|IndusInd|Federal|Indian|Central|UCO)(?:\s+Bank)?)(?:\s*[-–]?\s*(?:[Xx*•]{2,}\s*)?(\d{4}))?/i
  );

  const apps: Record<string, string[]> = {
    "Google Pay": ["google pay", "gpay", "g pay"],
    PhonePe: ["phonepe", "phone pe"],
    Paytm: ["paytm"],
    BHIM: ["bhim"],
    "Amazon Pay": ["amazon pay"],
    CRED: ["cred"],
    "WhatsApp Pay": ["whatsapp"],
  };

  const app =
    Object.keys(apps).find((k) => apps[k].some((w) => tl.includes(w))) || null;

  return {
    transaction_id: tid,
    amount: amt ? amt.replace(/,/g, "") : null,
    currency: /₹|Rs\.?|INR/.test(t) ? "INR" : null,
    status,
    date_time: date,
    paid_to: party("Paid to|Paying to|Sent to|Transfer(?:red)? to|To"),
    paid_from: party("Paid by|Received from|Debited from|From"),
    upi_ids: upis,
    phone: ph ? ph[1].replace(/[\s\-]/g, "") : null,
    bank: bank ? bank[1] + (bank[2] ? " ••" + bank[2] : "") : null,
    payment_app: app,
  };
}

export const sha256 = async (buf: ArrayBuffer): Promise<string> => {
  if (typeof crypto !== "undefined" && crypto.subtle) {
    const hash = await crypto.subtle.digest("SHA-256", buf);
    return Array.from(new Uint8Array(hash))
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("");
  }
  return "";
};

function parseDate(s: string | null): Date | null {
  if (!s) return null;
  const m = s.match(/(\d{1,2})[\/\-.](\d{1,2})[\/\-.](\d{2,4})/);
  if (m) {
    let y = +m[3];
    if (y < 100) y += 2000;
    return new Date(y, +m[2] - 1, +m[1]);
  }
  const d = new Date(s.replace(/\bat\b/i, " ").replace(/\./g, ""));
  return isNaN(d.getTime()) ? null : d;
}

/**
 * Pixel-level Error Level Analysis (ELA) on Canvas for JPEG files.
 * Edited regions often compress differently from the rest of the image.
 */
async function computeElaRatio(img: HTMLImageElement): Promise<number | null> {
  try {
    if (typeof document === "undefined") return null;
    const w = Math.min(img.naturalWidth || img.width, 1000);
    const naturalW = img.naturalWidth || img.width || 1;
    const naturalH = img.naturalHeight || img.height || 1;
    const h = Math.round((naturalH * w) / naturalW);

    const a = document.createElement("canvas");
    a.width = w;
    a.height = h;
    const ax = a.getContext("2d");
    if (!ax) return null;
    ax.drawImage(img, 0, 0, w, h);

    const re = new Image();
    re.src = a.toDataURL("image/jpeg", 0.9);
    await re.decode();

    const b = document.createElement("canvas");
    b.width = w;
    b.height = h;
    const bx = b.getContext("2d");
    if (!bx) return null;
    bx.drawImage(re, 0, 0);

    const A = ax.getImageData(0, 0, w, h).data;
    const B = bx.getImageData(0, 0, w, h).data;

    const blk = 16;
    const bw = Math.ceil(w / blk);
    const sums = new Float64Array(bw * Math.ceil(h / blk));

    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        const i = (y * w + x) * 4;
        const d =
          (Math.abs(A[i] - B[i]) +
            Math.abs(A[i + 1] - B[i + 1]) +
            Math.abs(A[i + 2] - B[i + 2])) /
          3;
        sums[((y / blk) | 0) * bw + ((x / blk) | 0)] += d;
      }
    }

    const means = Array.from(sums)
      .map((s) => s / (blk * blk))
      .filter((m) => m > 0.3)
      .sort((p, q) => p - q);

    const ratio =
      means.length > 20
        ? means[Math.floor(means.length * 0.98)] /
          means[Math.floor(means.length / 2)]
        : 1;

    return ratio;
  } catch {
    return null;
  }
}

/**
 * Runs the complete background authenticity check on an uploaded image file.
 * Returns parsed fields, risk score, individual check outcomes, ELA ratio, and reuse history.
 */
export async function checkClientAuthenticity(
  file: File,
  ocrText = ""
): Promise<ClientAuthenticityResult> {
  const checks: AuthenticityCheck[] = [];
  const add = (pts: number, text: string) =>
    checks.push({
      pts,
      text,
      sev: pts >= 30 ? "bad" : pts >= 10 ? "warn" : "info",
    });
  const ok = (text: string) => checks.push({ pts: 0, text, sev: "ok" });

  const buf = await file.arrayBuffer();
  const parsed = parsePaymentFields(ocrText);

  // 1. Photo editor traces in metadata
  try {
    const rawText = new TextDecoder("latin1").decode(buf);
    const ed = rawText.match(new RegExp(EDITORS.join("|"), "i"));
    if (ed) {
      add(40, `File metadata mentions editing software (“${ed[0]}”)`);
    } else {
      ok("No photo-editor traces in the file metadata");
    }
  } catch {
    // metadata decode skipped
  }

  // 2. Image dimensions & aspect ratio
  let elaRatio: number | null = null;
  if (typeof window !== "undefined" && file.type.startsWith("image/")) {
    try {
      const url = URL.createObjectURL(file);
      const img = new Image();
      img.src = url;
      await img.decode();
      const w = img.naturalWidth;
      const h = img.naturalHeight;
      const ar = h / (w || 1);

      if (w < 500) {
        add(
          8,
          `Very low resolution (${w}×${h}); small text may have been altered or re-compressed`
        );
      }
      if (ar < 1.6 || ar > 2.6) {
        add(
          8,
          `Unusual shape (${w}×${h}) for a phone screenshot; it may have been cropped`
        );
      } else if (w >= 500) {
        ok("Size and shape look like a normal phone screenshot");
      }

      // 3. Pixel-level ELA test (JPEG files only)
      if (/jpe?g/i.test(file.type)) {
        elaRatio = await computeElaRatio(img);
        if (elaRatio !== null) {
          if (elaRatio > 4) {
            add(
              20,
              `Some regions compress differently from the rest (ELA ratio ${elaRatio.toFixed(
                1
              )} > 4.0), indicating localized edits`
            );
          } else {
            ok("Compression pattern looks uniform");
          }
        }
      }
      URL.revokeObjectURL(url);
    } catch {
      // image decode fallback
    }
  }

  // 4. Field format & validity
  const tid = parsed.transaction_id;
  if (!tid) {
    add(25, "No transaction ID found");
  } else {
    ok(`Transaction ID detected: ${tid}`);
    if (parsed.payment_app && /^\d+$/.test(tid) && tid.length !== 12) {
      add(
        20,
        `UPI reference numbers are normally 12 digits; found '${tid}' (${tid.length} digits)`
      );
    } else if (!/^T/i.test(tid) && tid.length < 10) {
      add(10, `Transaction ID '${tid}' is unusually short`);
    }
  }

  if (!parsed.amount) {
    add(25, "No amount found");
  } else {
    ok(`Amount detected: ₹${parsed.amount}`);
  }

  if (!parsed.date_time) {
    add(10, "No date or time found");
  } else {
    ok(`Date and time detected: ${parsed.date_time}`);
    const d = parseDate(parsed.date_time);
    if (d && d.getTime() > Date.now() + 864e5) {
      add(40, `The payment date ('${parsed.date_time}') is in the future`);
    }
  }

  if (parsed.status === "Failed" || parsed.status === "Pending") {
    add(
      30,
      `The screenshot itself shows the payment as ${parsed.status.toLowerCase()}`
    );
  } else if (!parsed.status) {
    add(10, "No clear 'success' status found");
  } else {
    ok("Status shows success");
  }

  // 5. Duplicate screenshot / Transaction ID reuse in this browser
  let exactImageDate: string | null = null;
  let transactionIdDate: string | null = null;

  if (typeof window !== "undefined" && window.localStorage) {
    try {
      const hash = await sha256(buf);
      const key = "seenPayments";
      const db = JSON.parse(localStorage.getItem(key) || "{}");
      const now = new Date().toISOString();

      const pi = db["img:" + hash];
      const pt = tid ? db["tid:" + tid] : null;

      if (pi) {
        exactImageDate = pi;
        add(
          30,
          `This exact screenshot was already checked on ${new Date(
            pi
          ).toLocaleDateString()}`
        );
      } else if (pt) {
        transactionIdDate = pt;
        add(
          40,
          `This transaction ID appeared in a different screenshot on ${new Date(
            pt
          ).toLocaleDateString()}`
        );
      } else {
        ok("Not seen before in this browser");
      }

      // Persist to local database
      db["img:" + hash] = pi || now;
      if (tid) db["tid:" + tid] = pt || now;
      localStorage.setItem(key, JSON.stringify(db));
    } catch {
      // localStorage write error fallback
    }
  }

  const score = Math.min(
    100,
    checks.reduce((s, c) => s + c.pts, 0)
  );

  return {
    parsed,
    score,
    checks,
    elaRatio,
    seenBefore: {
      exactImageDate,
      transactionIdDate,
    },
  };
}
