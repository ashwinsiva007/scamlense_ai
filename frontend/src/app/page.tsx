"use client";

import React, { useState } from "react";
import {
  Upload,
  FileText,
  ShieldCheck,
  AlertTriangle,
  AlertOctagon,
  Info,
  CheckCircle2,
  Copy,
  Check,
  Sparkles,
  ArrowRight,
  Terminal,
  ExternalLink,
} from "lucide-react";
import { useT, Language } from "@/context/LanguageContext";
import { analyzeMessage, AnalyzeResponse, Mode } from "@/lib/api";

export default function HomePage() {
  const { t, language, setLanguage } = useT();

  const [activeTab, setActiveTab] = useState<"upload" | "text">("upload");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [filePreview, setFilePreview] = useState<string | null>(null);
  const [inputText, setInputText] = useState("");
  const [selectedMode, setSelectedMode] = useState<Mode>("mock");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [alertCopied, setAlertCopied] = useState(false);
  const [jsonCopied, setJsonCopied] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setError(null);
      if (file.type.startsWith("image/")) {
        const reader = new FileReader();
        reader.onload = () => setFilePreview(reader.result as string);
        reader.readAsDataURL(file);
      }
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      setSelectedFile(file);
      setError(null);
      if (file.type.startsWith("image/")) {
        const reader = new FileReader();
        reader.onload = () => setFilePreview(reader.result as string);
        reader.readAsDataURL(file);
      }
    }
  };

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!selectedFile && !inputText.trim()) {
      setError(
        language === "ta"
          ? "தயவுசெய்து ஒரு படத்தை பதிவேற்றவும் அல்லது செய்தியை உள்ளிடவும்."
          : language === "hi"
          ? "कृपया एक स्क्रीनशॉट अपलोड करें या टेक्स्ट संदेश पेस्ट करें।"
          : "Please upload an image or paste a message to analyze."
      );
      return;
    }

    setIsLoading(true);
    try {
      const res = await analyzeMessage({
        image: selectedFile,
        text: inputText,
        language: language,
        mode: selectedMode,
      });
      setResult(res);
      // Scroll to result smoothly
      setTimeout(() => {
        document.getElementById("analysis-result")?.scrollIntoView({ behavior: "smooth" });
      }, 100);
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred during analysis.");
    } finally {
      setIsLoading(false);
    }
  };

  const copyFamilyAlert = () => {
    if (!result) return;
    const text = `${result.family_alert.title}\n\n${result.family_alert.body}\n\nTips:\n${result.family_alert.tips
      .map((t) => `• ${t}`)
      .join("\n")}\n\n— Analyzed with ScamLens (Open Source Fraud Defense)`;
    navigator.clipboard.writeText(text);
    setAlertCopied(true);
    setTimeout(() => setAlertCopied(false), 2000);
  };

  const copyJson = () => {
    if (!result) return;
    navigator.clipboard.writeText(JSON.stringify(result, null, 2));
    setJsonCopied(true);
    setTimeout(() => setJsonCopied(false), 2000);
  };

  const getBandBadge = (band: string) => {
    switch (band) {
      case "likely_scam":
        return {
          icon: <AlertOctagon className="w-5 h-5" />,
          label: t("results.bandScam"),
          bg: "bg-danger-light text-danger-dark border-danger/30",
          barColor: "bg-danger",
        };
      case "suspicious":
        return {
          icon: <AlertTriangle className="w-5 h-5" />,
          label: t("results.bandSuspicious"),
          bg: "bg-warning-light text-warning-dark border-warning/30",
          barColor: "bg-warning",
        };
      case "insufficient_info":
        return {
          icon: <Info className="w-5 h-5" />,
          label: t("results.bandInsufficient"),
          bg: "bg-slate-100 text-slate-800 border-slate-300",
          barColor: "bg-slate-500",
        };
      case "low_risk":
      default:
        return {
          icon: <CheckCircle2 className="w-5 h-5" />,
          label: t("results.bandLow"),
          bg: "bg-emerald-50 text-emerald-800 border-emerald-300",
          barColor: "bg-emerald-500",
        };
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-10 sm:py-16 space-y-12">
      {/* Hero Header */}
      <div className="text-center space-y-4 max-w-3xl mx-auto">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-primary/10 text-primary border border-primary/20">
          <Sparkles className="w-3.5 h-3.5" />
          <span>{t("hero.badge")}</span>
        </div>
        <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-slate-900 leading-tight">
          {t("hero.title")}
        </h1>
        <p className="text-base sm:text-lg text-slate-600 leading-relaxed">
          {t("hero.subtitle")}
        </p>
      </div>

      {/* Main Analysis Form Card */}
      <div className="glass-panel rounded-2xl shadow-xl shadow-slate-200/60 p-6 sm:p-8">
        <form onSubmit={handleAnalyze} className="space-y-6">
          {/* Tabs: Upload vs Paste */}
          <div className="flex border-b border-slate-200">
            <button
              type="button"
              onClick={() => setActiveTab("upload")}
              className={`pb-3 px-4 text-sm font-semibold flex items-center gap-2 border-b-2 transition-all ${
                activeTab === "upload"
                  ? "border-primary text-primary"
                  : "border-transparent text-slate-500 hover:text-slate-800"
              }`}
            >
              <Upload className="w-4 h-4" />
              {t("form.uploadTab")}
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("text")}
              className={`pb-3 px-4 text-sm font-semibold flex items-center gap-2 border-b-2 transition-all ${
                activeTab === "text"
                  ? "border-primary text-primary"
                  : "border-transparent text-slate-500 hover:text-slate-800"
              }`}
            >
              <FileText className="w-4 h-4" />
              {t("form.pasteTab")}
            </button>
          </div>

          {/* Upload Area */}
          {activeTab === "upload" ? (
            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              className="border-2 border-dashed border-slate-300 hover:border-primary/60 rounded-xl p-8 text-center bg-slate-50/50 hover:bg-slate-50 transition-colors cursor-pointer group"
              onClick={() => document.getElementById("file-upload")?.click()}
            >
              <input
                id="file-upload"
                type="file"
                accept="image/png,image/jpeg,image/webp"
                className="hidden"
                onChange={handleFileChange}
              />
              <div className="w-14 h-14 rounded-2xl bg-white border border-slate-200 shadow-sm flex items-center justify-center mx-auto text-primary group-hover:scale-105 transition-transform">
                <Upload className="w-7 h-7" />
              </div>
              <p className="mt-4 text-sm font-medium text-slate-800">
                {selectedFile ? (
                  <span className="text-primary font-semibold">
                    {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
                  </span>
                ) : (
                  t("form.dragDrop")
                )}
              </p>
              <p className="mt-1 text-xs text-slate-500">{t("form.fileHint")}</p>

              {filePreview && (
                <div className="mt-4 inline-block max-h-48 rounded-lg overflow-hidden border border-slate-200 shadow-sm">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={filePreview}
                    alt="Preview"
                    className="max-h-48 object-contain"
                  />
                </div>
              )}
            </div>
          ) : (
            <div>
              <textarea
                rows={5}
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder={t("form.textPlaceholder")}
                className="w-full rounded-xl border border-slate-200 p-4 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary bg-slate-50/50 transition-all font-sans"
              />
            </div>
          )}

          {/* Configuration Controls (Language & Mode) */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                {t("form.languageLabel")}
              </label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { code: "en", label: "English" },
                  { code: "ta", label: "தமிழ்" },
                  { code: "hi", label: "हिन्दी" },
                ].map((l) => (
                  <button
                    type="button"
                    key={l.code}
                    onClick={() => setLanguage(l.code as Language)}
                    className={`py-2 px-3 text-xs font-semibold rounded-lg border transition-all ${
                      language === l.code
                        ? "bg-primary text-white border-primary shadow-sm"
                        : "bg-white text-slate-700 border-slate-200 hover:bg-slate-50"
                    }`}
                  >
                    {l.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                {t("form.modeLabel")}
              </label>
              <select
                value={selectedMode}
                onChange={(e) => setSelectedMode(e.target.value as Mode)}
                className="w-full rounded-lg border border-slate-200 p-2 text-xs font-medium bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
              >
                <option value="mock">{t("form.modeMock")}</option>
                <option value="cloud">{t("form.modeCloud")}</option>
                <option value="local">{t("form.modeLocal")}</option>
              </select>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="rounded-lg bg-danger-light border border-danger/30 p-3 text-xs text-danger-dark flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Submit Action */}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3.5 px-6 rounded-xl bg-primary hover:bg-primary-hover text-white font-semibold text-sm shadow-lg shadow-primary/25 hover:shadow-xl transition-all disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2 group"
          >
            {isLoading ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>{t("form.analyzing")}</span>
              </>
            ) : (
              <>
                <span>{t("form.analyzeBtn")}</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </>
            )}
          </button>
        </form>
      </div>

      {/* Analysis Results Display */}
      {result && (
        <section id="analysis-result" className="space-y-8 animate-fadeIn">
          {/* Verdict Overview Card */}
          {(() => {
            const badge = getBandBadge(result.band);
            return (
              <div className="glass-panel rounded-2xl p-6 sm:p-8 border border-slate-200 shadow-xl space-y-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200">
                  <div>
                    <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                      {t("results.title")}
                    </span>
                    <div className="flex items-center gap-3 mt-1.5">
                      <div
                        className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-xl text-sm font-bold border ${badge.bg}`}
                      >
                        {badge.icon}
                        <span>{badge.label}</span>
                      </div>
                      {result.scam_type && (
                        <span className="text-xs font-medium px-2.5 py-1 rounded-md bg-slate-100 text-slate-600">
                          {result.scam_type}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Score Gauge */}
                  <div className="flex items-center gap-4 bg-slate-50 px-4 py-3 rounded-xl border border-slate-200">
                    <div>
                      <span className="text-[10px] uppercase font-semibold text-slate-500 block">
                        {t("results.scoreLabel")}
                      </span>
                      <span className="text-2xl font-black text-slate-900">
                        {result.score}
                        <span className="text-xs font-normal text-slate-400">/100</span>
                      </span>
                    </div>
                    <div className="w-24 h-2.5 rounded-full bg-slate-200 overflow-hidden">
                      <div
                        className={`h-full ${badge.barColor} transition-all duration-700`}
                        style={{ width: `${result.score}%` }}
                      />
                    </div>
                  </div>
                </div>

                {/* Plain-Language Explanation */}
                <div className="space-y-2">
                  <h3 className="text-sm font-semibold text-slate-800">
                    Plain-Language Assessment:
                  </h3>
                  <p className="text-sm text-slate-700 leading-relaxed bg-slate-50/70 p-4 rounded-xl border border-slate-200">
                    {result.explanation}
                  </p>
                </div>

                {/* Quoted Red Flags & Signals */}
                {result.signals.length > 0 && (
                  <div className="space-y-3">
                    <h3 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
                      <AlertOctagon className="w-4 h-4 text-danger" />
                      {t("results.evidenceHeader")}
                    </h3>
                    <div className="space-y-2">
                      {result.signals.map((sig, idx) => (
                        <div
                          key={idx}
                          className="p-3.5 rounded-xl border border-slate-200 bg-white shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-2"
                        >
                          <div className="space-y-1">
                            <div className="flex items-center gap-2">
                              <span className="text-xs font-bold text-slate-900">
                                {sig.label}
                              </span>
                              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-100 text-slate-600">
                                {sig.category}
                              </span>
                            </div>
                            <p className="text-xs text-slate-600">
                              <span className="font-semibold text-slate-700">Quoted Evidence:</span>{" "}
                              <code className="text-danger font-mono bg-danger-light/50 px-1.5 py-0.5 rounded">
                                &quot;{sig.evidence}&quot;
                              </code>
                            </p>
                          </div>
                          <span
                            className={`text-xs font-bold px-2 py-1 rounded-md shrink-0 self-start sm:self-auto ${
                              sig.weight > 0
                                ? "text-danger bg-danger-light"
                                : "text-emerald-700 bg-emerald-50"
                            }`}
                          >
                            {sig.weight > 0 ? `+${sig.weight}` : sig.weight} pts
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Shareable Family Alert Card */}
                <div className="rounded-2xl border-2 border-warning/40 bg-gradient-to-br from-amber-50/60 to-orange-50/40 p-5 space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                      <ShieldCheck className="w-4 h-4 text-warning" />
                      {t("results.familyAlertHeader")}
                    </h3>
                    <button
                      onClick={copyFamilyAlert}
                      className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 shadow-sm transition-all"
                    >
                      {alertCopied ? (
                        <>
                          <Check className="w-3.5 h-3.5 text-emerald-600" />
                          <span>{t("results.alertCopied")}</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3.5 h-3.5 text-slate-500" />
                          <span>{t("results.copyAlert")}</span>
                        </>
                      )}
                    </button>
                  </div>

                  <p className="text-sm font-semibold text-slate-800">
                    {result.family_alert.title}
                  </p>
                  <p className="text-xs text-slate-700 leading-relaxed">
                    {result.family_alert.body}
                  </p>
                  <ul className="space-y-1 text-xs text-slate-600 list-disc list-inside">
                    {result.family_alert.tips.map((tip, i) => (
                      <li key={i}>{tip}</li>
                    ))}
                  </ul>
                </div>

                {/* Next Steps Checklist */}
                {result.next_steps.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="text-sm font-semibold text-slate-800">
                      {t("results.nextStepsHeader")}
                    </h3>
                    <ul className="space-y-1.5 text-xs text-slate-700">
                      {result.next_steps.map((step, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <CheckCircle2 className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                          <span>{step}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            );
          })()}

          {/* Raw JSON Code Block (Explicitly Required by User Request) */}
          <div className="rounded-2xl glass-panel-dark text-slate-200 p-6 space-y-3 shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-700/80 pb-3">
              <div className="flex items-center gap-2">
                <Terminal className="w-4 h-4 text-primary-light" />
                <span className="text-xs font-mono font-semibold tracking-wide text-slate-300">
                  {t("results.rawJson")}
                </span>
              </div>
              <button
                onClick={copyJson}
                className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-all font-mono"
              >
                {jsonCopied ? (
                  <>
                    <Check className="w-3 h-3 text-emerald-400" />
                    <span>Copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3 h-3 text-slate-400" />
                    <span>Copy JSON</span>
                  </>
                )}
              </button>
            </div>
            <pre className="text-xs font-mono overflow-x-auto p-2 bg-slate-950/60 rounded-xl text-emerald-300 max-h-96">
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        </section>
      )}
    </div>
  );
}
