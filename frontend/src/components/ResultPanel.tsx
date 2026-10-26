"use client";

import React, { useState } from "react";
import {
  AlertOctagon,
  AlertTriangle,
  Info,
  CheckCircle2,
  PhoneCall,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Terminal,
  Check,
  Copy,
  RotateCcw,
  Shield,
  Layers,
  Link as LinkIcon,
  Phone,
  CreditCard,
  Banknote,
  Clock,
  Sparkles,
} from "lucide-react";
import { AnalyzeResponse, Band, ToolStatus } from "@/lib/api";
import { Language, useT } from "@/context/LanguageContext";
import { SemicircleGauge } from "@/components/SemicircleGauge";
import { FamilyAlertCard } from "@/components/FamilyAlertCard";
import { SpeechPlayer } from "@/components/SpeechPlayer";
import { Badge, SourceBadge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Tooltip } from "@/components/ui/Tooltip";
import { useToast } from "@/components/ui/Toast";

interface ResultPanelProps {
  result: AnalyzeResponse;
  originalImagePreview: string | null;
  onReset: () => void;
  language: Language;
}

export function ResultPanel({
  result,
  originalImagePreview,
  onReset,
  language,
}: ResultPanelProps) {
  const { t } = useT();
  const { toast } = useToast();
  const [showTechnical, setShowTechnical] = useState(false);
  const [jsonCopied, setJsonCopied] = useState(false);

  const copyJson = async () => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(result, null, 2));
      setJsonCopied(true);
      toast(t("results.jsonCopied"), "success");
      setTimeout(() => setJsonCopied(false), 2000);
    } catch {
      toast("Could not copy JSON", "error");
    }
  };

  // 1. Verdict Configuration (CRITICAL: Never green for safe!)
  const getBandConfig = (band: Band) => {
    switch (band) {
      case "likely_scam":
        return {
          icon: <AlertOctagon className="w-6 h-6 text-danger" />,
          label: t("results.bandScam"),
          cardBg: "bg-danger-light/40 border-danger/40",
          textColor: "text-danger-dark",
          badgeVariant: "danger" as const,
        };
      case "suspicious":
        return {
          icon: <AlertTriangle className="w-6 h-6 text-warning" />,
          label: t("results.bandSuspicious"),
          cardBg: "bg-warning-light/40 border-warning/40",
          textColor: "text-warning-dark",
          badgeVariant: "warning" as const,
        };
      case "insufficient_info":
        return {
          icon: <Info className="w-6 h-6 text-slate-500" />,
          label: t("results.bandInsufficient"),
          cardBg: "bg-slate-100 border-slate-300",
          textColor: "text-slate-800",
          badgeVariant: "neutral" as const,
        };
      case "low_risk":
      default:
        // INFO BLUE with explicit non-absolving label: "No major red flags found, still verify"
        return {
          icon: <CheckCircle2 className="w-6 h-6 text-info" />,
          label: t("results.bandLow"),
          cardBg: "bg-info-light/40 border-info/40",
          textColor: "text-info-dark",
          badgeVariant: "info" as const,
        };
    }
  };

  const bandConfig = getBandConfig(result.band);

  // Group signals by category
  const groupedSignals = result.signals.reduce<Record<string, typeof result.signals>>(
    (acc, sig) => {
      acc[sig.category] = acc[sig.category] || [];
      acc[sig.category].push(sig);
      return acc;
    },
    {}
  );

  // Check if payment related
  const isPayment =
    result.extracted.document_type === "payment_screenshot" ||
    result.scam_type?.toLowerCase().includes("payment") ||
    result.signals.some((s) => s.category === "payment_screenshot");

  // Tool status helper
  const getToolStatusBadge = (status: ToolStatus) => {
    switch (status) {
      case "ok":
        return {
          label: t("results.toolOk"),
          variant: "info" as const,
          tooltip: t("results.toolOkTooltip"),
        };
      case "warn":
        return {
          label: t("results.toolWarn"),
          variant: "warning" as const,
          tooltip: t("results.toolWarnTooltip"),
        };
      case "error":
        return {
          label: t("results.toolError"),
          variant: "danger" as const,
          tooltip: t("results.toolErrorTooltip"),
        };
      case "skipped":
      default:
        return {
          label: t("results.toolSkipped"),
          variant: "neutral" as const,
          tooltip: t("results.toolSkippedTooltip"),
        };
    }
  };

  return (
    <section
      id="analysis-result"
      aria-label="Analysis report results"
      className="space-y-8 animate-fadeIn"
    >
      {/* Top Bar with Reset Button and Speech */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-slate-200">
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={onReset}
          leftIcon={<RotateCcw className="w-4 h-4 text-primary" />}
        >
          {t("results.analyzeAnother")}
        </Button>

        <div className="flex items-center gap-3">
          <SpeechPlayer
            text={`${result.explanation}. ${result.family_alert.title}. ${result.family_alert.body}`}
            language={language}
            onUnavailable={(msg) => toast(msg, "info")}
            labels={{
              readAloud: t("results.readAloudBtn"),
              playing: t("results.readAloudPlaying"),
              unavailable: t("results.readAloudUnavailable"),
            }}
          />
        </div>
      </div>

      {/* 1. Verdict Banner */}
      <div
        className={`rounded-2xl border-2 p-6 sm:p-8 shadow-md transition-all ${bandConfig.cardBg}`}
      >
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-3 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-600">
                {t("results.title")}
              </span>
              <Badge variant={bandConfig.badgeVariant} size="sm" dot>
                {t(`results.conf${result.confidence.charAt(0).toUpperCase() + result.confidence.slice(1)}`)}{" "}
                {t("results.confidenceLabel")}
              </Badge>
              {result.scam_type && (
                <span className="text-[11px] font-mono px-2 py-0.5 rounded-md bg-white/80 border border-slate-200 text-slate-700">
                  {result.scam_type}
                </span>
              )}
            </div>

            <div className="flex items-start sm:items-center gap-3">
              <div className="p-2 rounded-xl bg-white/90 shadow-sm shrink-0">
                {bandConfig.icon}
              </div>
              <h2 className={`text-xl sm:text-2xl font-black ${bandConfig.textColor}`}>
                {bandConfig.label}
              </h2>
            </div>

            {result.band === "insufficient_info" ? (
              <p className="text-xs sm:text-sm text-slate-700 font-medium">
                {t("results.bandInsufficientAdvice")}
              </p>
            ) : result.band === "low_risk" ? (
              <p className="text-xs sm:text-sm text-info-dark font-medium">
                {t("results.bandLow")}
              </p>
            ) : null}
          </div>

          {/* SVG Semicircle Gauge */}
          <div className="bg-white/90 rounded-2xl p-4 border border-slate-200/80 shadow-sm flex flex-col items-center justify-center shrink-0">
            <SemicircleGauge score={result.score} band={result.band} size={170} />
          </div>
        </div>
      </div>

      {/* 2. "Why we think so" + Evidence List & Image Preview */}
      <div className="glass-panel rounded-2xl border border-slate-200/90 shadow-sm p-6 sm:p-8 space-y-6">
        <div className="border-b border-slate-200 pb-3 flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Layers className="w-5 h-5 text-primary" />
              <span>{t("results.whyHeader")}</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              {t("results.evidenceHeader")}
            </p>
          </div>
          <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-100 text-slate-700">
            {result.signals.length} {result.signals.length === 1 ? "Signal" : "Signals"}
          </span>
        </div>

        {/* Side-by-side: Image Preview & Quoted Evidence */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Quoted Evidence List */}
          <div className="lg:col-span-7 space-y-4">
            {result.signals.length === 0 ? (
              <p className="text-xs text-slate-500 italic p-4 bg-slate-50 rounded-xl border border-slate-200">
                {t("results.noSignals")}
              </p>
            ) : (
              Object.entries(groupedSignals).map(([category, sigs]) => (
                <div key={category} className="space-y-2">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">
                    {category.replace(/_/g, " ")}
                  </span>
                  <div className="space-y-2.5">
                    {sigs.map((sig) => (
                      <div
                        key={sig.id}
                        className="p-3.5 rounded-xl border border-slate-200 bg-white shadow-sm space-y-2"
                      >
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <span className="text-xs sm:text-sm font-bold text-slate-900">
                            {sig.label}
                          </span>
                          <div className="flex items-center gap-2">
                            <SourceBadge source={sig.source} />
                            <span
                              className={`text-xs font-bold px-2 py-0.5 rounded-md ${
                                sig.weight > 0
                                  ? "bg-danger-light text-danger-dark"
                                  : "bg-info-light text-info-dark"
                              }`}
                            >
                              {sig.weight > 0 ? `+${sig.weight}` : sig.weight} {t("results.pts")}
                            </span>
                          </div>
                        </div>

                        {/* Quoted Evidence highlighted */}
                        <div className="text-xs text-slate-700 bg-slate-50/80 p-2.5 rounded-lg border border-slate-200">
                          <span className="font-semibold text-slate-800">
                            {t("results.quotedEvidence")}{" "}
                          </span>
                          <mark className="bg-warning-light/80 text-warning-dark font-mono px-1.5 py-0.5 rounded font-semibold">
                            &quot;{sig.evidence}&quot;
                          </mark>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Original Uploaded Image Preview & Extraction Notes */}
          <div className="lg:col-span-5 space-y-3">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">
              {t("results.originalImage")}
            </span>

            {originalImagePreview ? (
              <div className="rounded-xl border border-slate-200 overflow-hidden bg-slate-100 shadow-sm max-h-80 flex items-center justify-center p-2">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={originalImagePreview}
                  alt="Original input"
                  className="max-h-72 w-auto object-contain rounded-lg"
                />
              </div>
            ) : (
              <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 text-xs text-slate-500 italic">
                Direct text input was analyzed without screenshot.
              </div>
            )}

            {result.extracted.visual_notes && result.extracted.visual_notes.length > 0 && (
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-1.5">
                <span className="text-[10px] font-bold uppercase text-slate-500 block">
                  Observable Visual Notes
                </span>
                <ul className="text-xs text-slate-700 space-y-1 list-disc list-inside">
                  {result.extracted.visual_notes.map((note, idx) => (
                    <li key={idx}>{note}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 3. "What we checked": Links, Phone Numbers, UPI IDs, Amounts */}
      <div className="glass-panel rounded-2xl border border-slate-200/90 shadow-sm p-6 sm:p-8 space-y-5">
        <div className="border-b border-slate-200 pb-3">
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Shield className="w-5 h-5 text-primary" />
            <span>{t("results.checkedHeader")}</span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Extracted entities and automated reputation verifications
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Links */}
          <div className="p-4 rounded-xl bg-slate-50/80 border border-slate-200 space-y-2">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-800">
              <LinkIcon className="w-4 h-4 text-info" />
              <span>{t("results.linksCount")}</span>
              <span className="ml-auto text-[11px] font-mono bg-white px-1.5 py-0.5 rounded border border-slate-200">
                {result.extracted.urls.length}
              </span>
            </div>
            {result.extracted.urls.length === 0 ? (
              <span className="text-xs text-slate-400 italic block">None detected</span>
            ) : (
              <div className="flex flex-wrap gap-1.5">
                {result.extracted.urls.map((url, i) => (
                  <span
                    key={i}
                    className="text-xs font-mono bg-white border border-slate-200 px-2 py-1 rounded-md text-slate-700 break-all"
                  >
                    {url}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Phone Numbers */}
          <div className="p-4 rounded-xl bg-slate-50/80 border border-slate-200 space-y-2">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-800">
              <Phone className="w-4 h-4 text-primary" />
              <span>{t("results.phonesCount")}</span>
              <span className="ml-auto text-[11px] font-mono bg-white px-1.5 py-0.5 rounded border border-slate-200">
                {result.extracted.phone_numbers.length}
              </span>
            </div>
            {result.extracted.phone_numbers.length === 0 ? (
              <span className="text-xs text-slate-400 italic block">None detected</span>
            ) : (
              <div className="flex flex-wrap gap-1.5">
                {result.extracted.phone_numbers.map((phone, i) => (
                  <span
                    key={i}
                    className="text-xs font-mono bg-white border border-slate-200 px-2 py-1 rounded-md text-slate-700"
                  >
                    {phone}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* UPI IDs */}
          <div className="p-4 rounded-xl bg-slate-50/80 border border-slate-200 space-y-2">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-800">
              <CreditCard className="w-4 h-4 text-warning" />
              <span>{t("results.upisCount")}</span>
              <span className="ml-auto text-[11px] font-mono bg-white px-1.5 py-0.5 rounded border border-slate-200">
                {result.extracted.upi_ids.length}
              </span>
            </div>
            {result.extracted.upi_ids.length === 0 ? (
              <span className="text-xs text-slate-400 italic block">None detected</span>
            ) : (
              <div className="flex flex-wrap gap-1.5">
                {result.extracted.upi_ids.map((upi, i) => (
                  <span
                    key={i}
                    className="text-xs font-mono bg-white border border-slate-200 px-2 py-1 rounded-md text-slate-700"
                  >
                    {upi}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Amounts */}
          <div className="p-4 rounded-xl bg-slate-50/80 border border-slate-200 space-y-2">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-800">
              <Banknote className="w-4 h-4 text-emerald-700" />
              <span>{t("results.amountsCount")}</span>
              <span className="ml-auto text-[11px] font-mono bg-white px-1.5 py-0.5 rounded border border-slate-200">
                {result.extracted.amounts.length}
              </span>
            </div>
            {result.extracted.amounts.length === 0 ? (
              <span className="text-xs text-slate-400 italic block">None detected</span>
            ) : (
              <div className="flex flex-wrap gap-1.5">
                {result.extracted.amounts.map((amt, i) => (
                  <span
                    key={i}
                    className="text-xs font-bold bg-white border border-slate-200 px-2 py-1 rounded-md text-slate-900"
                  >
                    {amt}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Tool Results list */}
        {result.tool_results.length > 0 && (
          <div className="space-y-2.5 pt-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">
              Automated Verifier Outputs
            </span>
            <div className="space-y-2">
              {result.tool_results.map((tr, idx) => {
                const badge = getToolStatusBadge(tr.status);
                return (
                  <div
                    key={idx}
                    className="flex flex-col sm:flex-row sm:items-center justify-between p-3 rounded-xl border border-slate-200 bg-white gap-2 text-xs"
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-slate-800 font-semibold">{tr.target}</span>
                      <span className="text-slate-400 font-normal">({tr.tool})</span>
                    </div>

                    <div className="flex items-center gap-3">
                      <span className="text-slate-600 font-medium">{tr.detail}</span>
                      <Tooltip content={badge.tooltip}>
                        <Badge variant={badge.variant} size="sm">
                          {badge.label}
                        </Badge>
                      </Tooltip>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* 4. "What to do now": Next steps & Indian Official Reporting Channels */}
      <div className="glass-panel rounded-2xl border border-slate-200/90 shadow-sm p-6 sm:p-8 space-y-6">
        <div>
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-primary" />
            <span>{t("results.whatToDoHeader")}</span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            {t("results.checklistHeader")}
          </p>
        </div>

        {/* Next Steps Checklist */}
        <ul className="space-y-2.5 text-xs sm:text-sm text-slate-700">
          {result.next_steps.map((step, idx) => (
            <li
              key={idx}
              className="flex items-start gap-3 p-3 rounded-xl bg-slate-50 border border-slate-200/70"
            >
              <CheckCircle2 className="w-4 h-4 text-primary shrink-0 mt-0.5" />
              <span className="leading-relaxed font-medium">{step}</span>
            </li>
          ))}
        </ul>

        {/* Indian Cybercrime Reporting Section */}
        {/* Verification note: The reporting URLs below are official Government of India portals */}
        <div className="rounded-xl border border-slate-200 bg-slate-50/90 p-5 space-y-3">
          <div className="flex items-center gap-2">
            <PhoneCall className="w-4 h-4 text-danger" />
            <span className="text-xs font-bold text-slate-900 uppercase tracking-wide">
              {t("results.reportHeader")}
            </span>
          </div>
          <p className="text-xs text-slate-600 leading-relaxed">
            {t("results.reportDescription")}
          </p>

          <div className="flex flex-wrap gap-2.5 pt-1">
            <a
              href="https://cybercrime.gov.in"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-3.5 py-2 text-xs font-semibold rounded-lg bg-white border border-slate-200 text-slate-800 hover:bg-slate-100 shadow-sm transition-all min-h-[44px]"
            >
              <ExternalLink className="w-3.5 h-3.5 text-info" />
              <span>{t("results.reportCybercrimeBtn")}</span>
            </a>

            <a
              href="tel:1930"
              className="inline-flex items-center gap-2 px-3.5 py-2 text-xs font-bold rounded-lg bg-danger text-white hover:bg-danger-dark shadow-sm transition-all min-h-[44px]"
            >
              <Phone className="w-3.5 h-3.5" />
              <span>{t("results.reportHelplineBtn")}</span>
            </a>

            <a
              href="https://sancharsaathi.gov.in"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-3.5 py-2 text-xs font-semibold rounded-lg bg-white border border-slate-200 text-slate-800 hover:bg-slate-100 shadow-sm transition-all min-h-[44px]"
            >
              <ExternalLink className="w-3.5 h-3.5 text-primary" />
              <span>{t("results.reportSancharBtn")}</span>
            </a>
          </div>
        </div>
      </div>

      {/* 5. Plain Language Explanation & Payment Screenshot Disclaimer */}
      <div className="glass-panel rounded-2xl border border-slate-200/90 shadow-sm p-6 sm:p-8 space-y-4">
        <h3 className="text-base font-bold text-slate-900">
          {t("results.explanationHeader")}
        </h3>

        <p className="text-xs sm:text-sm text-slate-700 leading-relaxed bg-slate-50/80 p-4 rounded-xl border border-slate-200 font-medium">
          {result.explanation}
        </p>

        {/* ALWAYS SHOW for payment screenshots */}
        {isPayment && (
          <div className="p-4 rounded-xl bg-amber-50 border border-warning/40 text-amber-900 flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-warning shrink-0 mt-0.5" />
            <div className="space-y-0.5 text-xs sm:text-sm">
              <span className="font-bold block">
                Crucial Payment Verification Reminder:
              </span>
              <span className="font-semibold text-warning-dark">
                {t("results.paymentScreenshotWarning")}
              </span>
            </div>
          </div>
        )}

        {/* Prominent Limitations Note */}
        <div className="p-3.5 rounded-xl bg-slate-100/90 border border-slate-200 text-xs text-slate-600 space-y-1">
          <span className="font-bold text-slate-800 block">
            {t("results.limitationsHeader")}
          </span>
          <p>{result.limitations}</p>
        </div>
      </div>

      {/* 6. Family Alert Card (Specially designed for WhatsApp sharing) */}
      <FamilyAlertCard
        alert={result.family_alert}
        language={language}
        labels={{
          header: t("results.familyAlertHeader"),
          sub: t("results.familyAlertSub"),
          watermark: t("results.familyAlertWatermark"),
          downloadPng: t("results.downloadPngBtn"),
          copyAlert: t("results.copyAlertBtn"),
          shareWhatsApp: t("results.shareWhatsAppBtn"),
          copied: t("results.alertCopied"),
        }}
      />

      {/* 8. Collapsible "Show technical details" */}
      <div className="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
        <button
          type="button"
          onClick={() => setShowTechnical(!showTechnical)}
          className="w-full min-h-[44px] p-4 flex items-center justify-between text-xs font-bold text-slate-700 hover:bg-slate-50 transition-colors select-none"
        >
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-primary" />
            <span>{t("results.technicalHeader")}</span>
            <span className="text-[10px] font-normal text-slate-400">
              (Latency: {result.timings_ms.total || 0} ms)
            </span>
          </div>
          {showTechnical ? (
            <ChevronUp className="w-4 h-4 text-slate-400" />
          ) : (
            <ChevronDown className="w-4 h-4 text-slate-400" />
          )}
        </button>

        {showTechnical && (
          <div className="p-5 border-t border-slate-200 bg-slate-900 text-slate-200 space-y-4 animate-fadeIn">
            {/* Timings row */}
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
              <div className="bg-slate-800/80 p-2.5 rounded-lg border border-slate-700 text-center">
                <span className="text-[10px] uppercase text-slate-400 block font-mono">
                  Total
                </span>
                <span className="text-sm font-bold text-primary-light font-mono">
                  {result.timings_ms.total ?? 0} ms
                </span>
              </div>
              <div className="bg-slate-800/80 p-2.5 rounded-lg border border-slate-700 text-center">
                <span className="text-[10px] uppercase text-slate-400 block font-mono">
                  Perception
                </span>
                <span className="text-sm font-bold text-slate-200 font-mono">
                  {result.timings_ms.extraction ?? 0} ms
                </span>
              </div>
              <div className="bg-slate-800/80 p-2.5 rounded-lg border border-slate-700 text-center">
                <span className="text-[10px] uppercase text-slate-400 block font-mono">
                  Verifiers
                </span>
                <span className="text-sm font-bold text-info-light font-mono">
                  {result.timings_ms.verifiers ?? 0} ms
                </span>
              </div>
              <div className="bg-slate-800/80 p-2.5 rounded-lg border border-slate-700 text-center">
                <span className="text-[10px] uppercase text-slate-400 block font-mono">
                  Rule Engine
                </span>
                <span className="text-sm font-bold text-warning font-mono">
                  {result.timings_ms.rules ?? 0} ms
                </span>
              </div>
              <div className="bg-slate-800/80 p-2.5 rounded-lg border border-slate-700 text-center">
                <span className="text-[10px] uppercase text-slate-400 block font-mono">
                  Explainer
                </span>
                <span className="text-sm font-bold text-slate-200 font-mono">
                  {result.timings_ms.explanation ?? 0} ms
                </span>
              </div>
            </div>

            {/* Copy JSON block */}
            <div className="flex items-center justify-between pt-2 border-t border-slate-800">
              <span className="text-xs font-mono text-slate-400">
                request_id: {result.request_id}
              </span>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={copyJson}
                leftIcon={
                  jsonCopied ? (
                    <Check className="w-3.5 h-3.5 text-primary-light" />
                  ) : (
                    <Copy className="w-3.5 h-3.5 text-slate-400" />
                  )
                }
                className="bg-slate-800 hover:bg-slate-700 border-slate-700 text-slate-200"
              >
                {jsonCopied ? t("results.jsonCopied") : t("results.copyJsonBtn")}
              </Button>
            </div>

            <pre className="text-xs font-mono overflow-x-auto p-3 bg-slate-950/70 rounded-xl text-emerald-300 max-h-80 border border-slate-800">
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </section>
  );
}
