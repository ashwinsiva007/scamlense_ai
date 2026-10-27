"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import Link from "next/link";
import {
  Upload,
  FileText,
  Link2,
  X,
  Sparkles,
  ArrowRight,
  AlertTriangle,
  Info,
  Layers,
  ShieldAlert,
  RotateCcw,
} from "lucide-react";
import { useT, Language } from "@/context/LanguageContext";
import {
  analyzeMessage,
  loadDemoResult,
  getHealth,
  AnalyzeResponse,
  Mode,
  ApiError,
  ApiNetworkError,
  ApiRateLimitError,
} from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Tabs } from "@/components/ui/Tabs";
import { SegmentedControl } from "@/components/ui/SegmentedControl";
import { Tooltip } from "@/components/ui/Tooltip";
import { LoadingSteps } from "@/components/LoadingSteps";
import { ResultPanel } from "@/components/ResultPanel";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { Greeting } from "@/components/Greeting";
import { useToast } from "@/components/ui/Toast";
import { checkClientAuthenticity } from "@/lib/paymentScreenshot";

type SampleKey = "internship" | "payment" | "kyc" | "bank_alert";

const ALLOWED_EXTENSIONS = [
  ".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tiff", ".tif", ".heic", ".heif",
  ".pdf", ".docx", ".doc", ".txt", ".rtf", ".eml"
];

const ALLOWED_MIME_PREFIXES = [
  "image/", "application/pdf", "application/vnd.openxmlformats",
  "application/msword", "text/plain", "application/rtf", "text/rtf", "message/rfc822"
];

const isImageFile = (file: File | null, preview: string | null): boolean => {
  if (preview && preview.startsWith("data:image/")) return true;
  if (!file) return Boolean(preview);
  if (file.type.startsWith("image/")) return true;
  const ext = file.name.split(".").pop()?.toLowerCase();
  return ["png", "jpg", "jpeg", "webp", "gif", "bmp", "tiff", "tif", "heic", "heif"].includes(ext || "");
};

const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const getFileTypeLabel = (fileName: string): string => {
  const ext = fileName.split(".").pop()?.toLowerCase();
  switch (ext) {
    case "pdf": return "PDF Document";
    case "docx": return "Word Document (.docx)";
    case "doc": return "Legacy Word Document (.doc)";
    case "txt": return "Plain Text (.txt)";
    case "rtf": return "Rich Text (.rtf)";
    case "eml": return "Email Message (.eml)";
    default: return ext ? ext.toUpperCase() : "Document";
  }
};

export default function HomePage() {
  const { t, language, setLanguage } = useT();
  const { toast } = useToast();

  const [activeTab, setActiveTab] = useState<string>("upload");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [filePreview, setFilePreview] = useState<string | null>(null);
  const [activeSampleKey, setActiveSampleKey] = useState<SampleKey | null>(null);
  const [inputText, setInputText] = useState("");
  const [selectedMode, setSelectedMode] = useState<"cloud" | "local">("cloud");
  const [isOllamaAvailable, setIsOllamaAvailable] = useState<boolean>(false);
  const [isCloudAvailable, setIsCloudAvailable] = useState<boolean>(false);
  const [cloudKeyConfigured, setCloudKeyConfigured] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDemoMode, setIsDemoMode] = useState(() => process.env.NEXT_PUBLIC_DEMO_MODE === "true");
  const [result, setResult] = useState<AnalyzeResponse | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // In-memory reference to last input for language-change re-analysis
  const lastInputRef = useRef<{
    file: File | null;
    text: string;
    mode: "cloud" | "local";
    sampleKey: SampleKey | null;
  } | null>(null);

  const prevLangRef = useRef<Language>(language);

  // Re-run analysis or load translated sample when language is switched while result is showing
  useEffect(() => {
    if (prevLangRef.current !== language) {
      prevLangRef.current = language;
      if (result && lastInputRef.current) {
        const lastInput = lastInputRef.current;
        if (lastInput.sampleKey) {
          setIsLoading(true);
          loadDemoResult(lastInput.sampleKey, language)
            .then((res) => setResult(res))
            .catch(() => {})
            .finally(() => setIsLoading(false));
        } else if (lastInput.file || lastInput.text.trim()) {
          setIsLoading(true);
          analyzeMessage({
            image: lastInput.file,
            text: lastInput.text,
            language: language,
            mode: lastInput.mode,
          })
            .then((res) => setResult(res))
            .catch((err) => {
              const msg = err instanceof Error ? err.message : t("errors.generic");
              setError(msg);
            })
            .finally(() => setIsLoading(false));
        }
      }
    }
  }, [language, result, t]);

  // Validate file client-side (Images + Documents)
  const validateAndSetFile = useCallback(
    (file: File) => {
      setError(null);
      const ext = file.name.includes(".") ? `.${file.name.split(".").pop()?.toLowerCase()}` : "";
      const isAllowedExt = ALLOWED_EXTENSIONS.includes(ext);
      const isAllowedMime = ALLOWED_MIME_PREFIXES.some((prefix) => file.type.startsWith(prefix));

      if (!isAllowedExt && !isAllowedMime) {
        setError(t("form.invalidFileType"));
        toast(t("form.invalidFileType"), "error");
        return false;
      }

      // Max 8 MB
      const maxBytes = 8 * 1024 * 1024;
      if (file.size > maxBytes) {
        setError(t("form.fileTooLarge"));
        toast(t("form.fileTooLarge"), "error");
        return false;
      }

      setSelectedFile(file);
      setActiveSampleKey(null);

      if (isImageFile(file, null)) {
        const reader = new FileReader();
        reader.onload = () => setFilePreview(reader.result as string);
        reader.readAsDataURL(file);
      } else {
        setFilePreview(null);
      }
      return true;
    },
    [t, toast]
  );

  // Clipboard paste listener (Ctrl+V)
  useEffect(() => {
    const handlePaste = (e: ClipboardEvent) => {
      if (result) return; // Do not intercept paste if result is showing

      if (e.clipboardData && e.clipboardData.files && e.clipboardData.files.length > 0) {
        const file = e.clipboardData.files[0];
        e.preventDefault();
        setActiveTab("upload");
        if (validateAndSetFile(file)) {
          toast(t("form.pastedClipboard"), "info");
        }
      }
    };

    window.addEventListener("paste", handlePaste);
    return () => window.removeEventListener("paste", handlePaste);
  }, [result, validateAndSetFile, toast, t]);

  // Check backend health on mount to detect live connectivity
  useEffect(() => {
    getHealth()
      .then((health) => {
        setIsOllamaAvailable(Boolean(health.ollama_reachable));
        const keyConfigured = Boolean(health.key_configured || health.cloud_key_set);
        setCloudKeyConfigured(keyConfigured);
        setIsCloudAvailable(Boolean(keyConfigured && health.live_ok));
        // Clear demo mode if live connection is healthy
        if (keyConfigured && health.live_ok) {
          setIsDemoMode(false);
          setError(null);
        } else if (process.env.NEXT_PUBLIC_DEMO_MODE === "true") {
          setIsDemoMode(true);
        }
      })
      .catch(() => {
        // Do not silently enable demo mode on network errors
      });
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleRemoveFile = (e: React.MouseEvent) => {
    e.stopPropagation();
    setSelectedFile(null);
    setFilePreview(null);
    setActiveSampleKey(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  // Load bundled sample image
  const handleLoadSample = async (sampleKey: SampleKey) => {
    setError(null);
    setActiveSampleKey(sampleKey);
    setActiveTab("upload");

    const sampleFiles: Record<SampleKey, { path: string; name: string }> = {
      internship: {
        path: "/samples/fake_internship_offer.png",
        name: "fake_internship_offer.png",
      },
      payment: {
        path: "/samples/fake_payment_screenshot.png",
        name: "fake_payment_screenshot.png",
      },
      kyc: {
        path: "/samples/fake_kyc_otp_sms.png",
        name: "fake_kyc_otp_sms.png",
      },
      bank_alert: {
        path: "/samples/genuine_bank_alert.png",
        name: "genuine_bank_alert.png",
      },
    };

    const target = sampleFiles[sampleKey];
    setFilePreview(target.path);

    try {
      const response = await fetch(target.path);
      const blob = await response.blob();
      const file = new File([blob], target.name, { type: "image/png" });
      setSelectedFile(file);
      toast(`Loaded ${sampleKey} sample`, "info");
    } catch {
      // If fetching binary fails in static context, keep preview path
      setSelectedFile(null);
    }
  };

  const handleAnalyze = async (e?: React.FormEvent) => {
    if (e) {
      e.preventDefault();
    }
    setError(null);

    const hasInput = (selectedFile !== null) || (filePreview !== null) || (inputText.trim().length > 0);
    if (!hasInput) {
      setError(t("form.emptyInput"));
      toast(t("form.emptyInput"), "error");
      return;
    }

    lastInputRef.current = {
      file: selectedFile,
      text: inputText,
      mode: selectedMode,
      sampleKey: activeSampleKey,
    };
    setIsLoading(true);

    try {
      // Step 5 Rule: Demo mode only returns cached results for the built-in sample chips
      if (isDemoMode) {
        if (activeSampleKey) {
          const demoRes = await loadDemoResult(activeSampleKey, language);
          setResult(demoRes);
          return;
        } else {
          // Rule: For user-uploaded or pasted input, demo mode must NOT return a canned verdict
          const demoWarning = "Demo mode can only show built-in samples. Switch to Live or Local mode to analyze your own screenshot.";
          setError(demoWarning);
          toast(demoWarning, "info");
          return;
        }
      }

      // Guard against running local mode when Ollama is offline
      if (selectedMode === "local" && !isOllamaAvailable) {
        const ollamaWarning = "Cannot connect to local Ollama at http://localhost:11434. Switch to Cloud mode to analyze with your live Gemini API key.";
        setError(ollamaWarning);
        toast(ollamaWarning, "info");
        return;
      }

      // Live mode call (Cloud or Local)
      const res = await analyzeMessage({
        image: selectedFile,
        text: inputText,
        language: language,
        mode: selectedMode,
      });

      // Defensive initialization of all fields to prevent any render crash
      res.extracted = res.extracted || {
        document_type: "document",
        sender: null,
        message_text: "",
        urls: [],
        phone_numbers: [],
        upi_ids: [],
        amounts: [],
        claimed_brand: null,
        detected_language: language,
        image_quality: "sharp",
        visual_notes: [],
      };
      res.extracted.amounts = Array.isArray(res.extracted.amounts) ? res.extracted.amounts : [];
      res.extracted.upi_ids = Array.isArray(res.extracted.upi_ids) ? res.extracted.upi_ids : [];
      res.extracted.phone_numbers = Array.isArray(res.extracted.phone_numbers) ? res.extracted.phone_numbers : [];
      res.extracted.urls = Array.isArray(res.extracted.urls) ? res.extracted.urls : [];
      res.extracted.visual_notes = Array.isArray(res.extracted.visual_notes) ? res.extracted.visual_notes : [];
      res.tool_results = Array.isArray(res.tool_results) ? res.tool_results : [];
      res.signals = Array.isArray(res.signals) ? res.signals : [];
      res.next_steps = Array.isArray(res.next_steps) ? res.next_steps : [];

      // Run client-side background payment screenshot & tampering analysis using authentic extracted text
      if (selectedFile && isImageFile(selectedFile, null)) {
        try {
          const effectiveText = inputText.trim() || res.extracted.message_text;
          const clientAuth = await checkClientAuthenticity(selectedFile, effectiveText);
          if (clientAuth) {
            // Incorporate duplicate screenshot reuse warnings safely
            if (clientAuth.seenBefore.exactImageDate && !res.signals.some((s) => s.id === "PAY_REUSED_SCREENSHOT")) {
              res.tool_results.unshift({
                tool: "screenshot_reuse",
                target: "image_hash",
                status: "warn",
                detail: `This exact screenshot was previously verified in this browser on ${new Date(
                  clientAuth.seenBefore.exactImageDate
                ).toLocaleDateString()}.`,
              });
              res.signals.unshift({
                id: "PAY_REUSED_SCREENSHOT",
                label: "Previously Verified or Recycled Screenshot",
                category: "payment_screenshot",
                weight: 20.0,
                evidence: `Exact duplicate screenshot hash found in local verification history (${new Date(
                  clientAuth.seenBefore.exactImageDate
                ).toLocaleDateString()})`,
                source: "tool",
              });
            }

            // ELA compression anomaly
            if (clientAuth.elaRatio !== null && clientAuth.elaRatio > 4.0) {
              const elaExists = res.tool_results.some((tr) => tr.target === "compression_ela");
              if (!elaExists) {
                res.tool_results.push({
                  tool: "payment_authenticity",
                  target: "compression_ela",
                  status: "warn",
                  detail: `Pixel-level Error Level Analysis detects localized compression anomaly (ratio ${clientAuth.elaRatio.toFixed(
                    1
                  )} > 4.0). Editing or digital tampering suspected.`,
                });
                res.extracted.visual_notes.push(
                  `Pixel-level ELA compression anomaly (ratio ${clientAuth.elaRatio.toFixed(
                    1
                  )} > 4.0) indicates localized editing`
                );
              }
            }
          }
        } catch {
          // ignore client-side check errors
        }
      }

      setResult(res);
    } catch (err: unknown) {
      // Step 5 Rule: Never fall back silently to demo or mock results after an error in cloud or local mode
      let msg = err instanceof Error ? err.message : t("errors.generic");
      if (
        msg.includes("GEMINI_API_KEY") ||
        msg.includes("CLOUD_KEY_MISSING") ||
        msg.includes("KEY_MISSING") ||
        (err instanceof ApiError && err.errorCode === "KEY_MISSING")
      ) {
        msg = "Gemini API key is not configured in backend/.env. To analyze custom screenshots in Cloud mode, please configure GEMINI_API_KEY or test with the built-in demo samples below.";
      }
      setError(msg);
      toast(msg, "error");
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setResult(null);
    setError(null);
    setSelectedFile(null);
    setFilePreview(null);
    setActiveSampleKey(null);
    setInputText("");
    lastInputRef.current = null;
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleSwitchToLive = async () => {
    setIsLoading(true);
    try {
      const h = await getHealth();
      if (h.key_configured && h.live_ok) {
        setIsDemoMode(false);
        setSelectedMode("cloud");
        setError(null);
        toast("Connected to Live Cloud API!", "success");
      } else {
        let reason = "Live API key is not configured in backend/.env";
        if (h.key_configured && !h.live_ok) {
          reason = `Gemini key is configured (${h.model}), but model probe failed. Please verify API quotas or model access.`;
        } else if (!h.key_configured) {
          reason = "Live API key is not configured in backend/.env";
        }
        toast(reason, "error");
        setError(reason);
      }
    } catch {
      toast("Backend server unreachable. Make sure backend is running on port 8000.", "error");
      setError("Cannot connect to ScamLens API server on port 8000.");
    } finally {
      setIsLoading(false);
    }
  };

  const hasValidInput = Boolean(selectedFile || filePreview || inputText.trim());

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 sm:py-14 space-y-10">
      {/* Demo Mode Notice Banner if Active */}
      {isDemoMode && (
        <div
          role="status"
          className="rounded-xl p-3.5 bg-amber-50 border border-warning/40 text-amber-900 flex items-center justify-between text-xs sm:text-sm animate-fadeIn"
        >
          <div className="flex items-center gap-2 font-medium">
            <Info className="w-4 h-4 text-warning shrink-0" />
            <span>Demo Mode Active: Rendering verified sample intelligence offline.</span>
          </div>
          <button
            type="button"
            onClick={handleSwitchToLive}
            className="text-xs font-bold underline hover:text-amber-950 ml-2"
          >
            Switch to Live API
          </button>
        </div>
      )}

      {/* Hero Header */}
      {!result && (
        <header className="text-center space-y-3.5 max-w-2xl mx-auto">
          <Greeting />

          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-primary/10 text-primary border border-primary/20">
            <Sparkles className="w-3.5 h-3.5" />
            <span>{t("hero.badge")}</span>
          </div>

          <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight text-slate-900 leading-tight">
            {t("hero.title")}
          </h1>

          <p className="text-sm sm:text-base text-slate-600 leading-relaxed font-medium">
            {t("hero.subtitle")}
          </p>
        </header>
      )}

      {/* Main Analyzer Card (replaces with ResultPanel when result exists) */}
      {result ? (
        <ErrorBoundary onReset={handleReset} resetLabel={t("errorPage.retryBtn") || "Try Again / Reset"}>
          <ResultPanel
            result={result}
            originalImagePreview={filePreview}
            onReset={handleReset}
            language={language}
          />
        </ErrorBoundary>
      ) : isLoading ? (
        <LoadingSteps
          labels={{
            step1: t("loading.step1"),
            step2: t("loading.step2"),
            step3: t("loading.step3"),
            step4: t("loading.step4"),
          }}
        />
      ) : (
        <div className="glass-panel rounded-2xl shadow-xl shadow-slate-200/50 p-5 sm:p-8 space-y-6">
          <form onSubmit={handleAnalyze} className="space-y-6">
            {/* Tabs: Screenshot vs Paste text vs Link */}
            <Tabs
              tabs={[
                {
                  id: "upload",
                  label: t("form.uploadTab"),
                  icon: <Upload className="w-4 h-4" />,
                },
                {
                  id: "text",
                  label: t("form.pasteTab"),
                  icon: <FileText className="w-4 h-4" />,
                },
                {
                  id: "link",
                  label: t("form.linkTab") || "Check Link",
                  icon: <Link2 className="w-4 h-4" />,
                },
              ]}
              activeTab={activeTab}
              onChange={setActiveTab}
            />

            {/* Tab 1: File / Screenshot Upload Zone */}
            {activeTab === "upload" ? (
              <div className="space-y-3">
                <div
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                  tabIndex={0}
                  role="button"
                  aria-label="Upload file area"
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      fileInputRef.current?.click();
                    }
                  }}
                  className={`border-2 border-dashed rounded-2xl p-6 sm:p-10 text-center transition-all cursor-pointer group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary ${
                    filePreview || selectedFile
                      ? "border-primary/50 bg-primary/5"
                      : "border-slate-300 hover:border-primary/60 bg-slate-50/70 hover:bg-slate-50"
                  }`}
                >
                  <input
                    ref={fileInputRef}
                    id="file-upload-input"
                    type="file"
                    accept=".png,.jpg,.jpeg,.webp,.gif,.bmp,.tiff,.tif,.heic,.heif,.pdf,.docx,.doc,.txt,.rtf,.eml,image/*,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/msword,text/plain,application/rtf,text/rtf,message/rfc822"
                    className="hidden"
                    onChange={handleFileChange}
                  />

                  {filePreview ? (
                    <div className="space-y-4">
                      <div className="relative inline-block rounded-xl overflow-hidden border border-slate-200 shadow-md bg-white p-1 max-h-64 sm:max-h-80">
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img
                          src={filePreview}
                          alt="Screenshot preview"
                          className="max-h-60 sm:max-h-72 w-auto object-contain rounded-lg"
                        />
                        <button
                          type="button"
                          onClick={handleRemoveFile}
                          className="absolute top-3 right-3 p-1.5 rounded-full bg-slate-900/80 text-white hover:bg-danger shadow-md transition-colors"
                          aria-label={t("form.removeImage")}
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>

                      <div className="flex items-center justify-center gap-2">
                        <span className="text-xs font-semibold text-primary">
                          {selectedFile ? selectedFile.name : "Loaded sample image"}
                        </span>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={handleRemoveFile}
                          className="text-xs text-danger hover:text-danger-dark"
                        >
                          {t("form.removeImage")}
                        </Button>
                      </div>
                    </div>
                  ) : selectedFile ? (
                    <div className="space-y-4">
                      <div className="relative inline-flex flex-col items-center justify-center rounded-2xl border border-slate-200 shadow-md bg-white p-6 max-w-sm mx-auto w-full">
                        <button
                          type="button"
                          onClick={handleRemoveFile}
                          className="absolute top-3 right-3 p-1.5 rounded-full bg-slate-100 text-slate-600 hover:bg-danger hover:text-white shadow-sm transition-colors"
                          aria-label={t("form.removeFile")}
                        >
                          <X className="w-4 h-4" />
                        </button>

                        <div className="w-16 h-16 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary mb-3">
                          <FileText className="w-8 h-8" />
                        </div>

                        <p className="font-bold text-sm text-slate-800 break-all text-center max-w-[260px]">
                          {selectedFile.name}
                        </p>

                        <p className="text-xs text-slate-500 font-medium mt-1">
                          {getFileTypeLabel(selectedFile.name)} • {formatFileSize(selectedFile.size)}
                        </p>
                      </div>

                      <div className="flex items-center justify-center gap-2">
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={handleRemoveFile}
                          className="text-xs text-danger hover:text-danger-dark"
                        >
                          {t("form.removeFile")}
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <div className="w-14 h-14 rounded-2xl bg-white border border-slate-200 shadow-sm flex items-center justify-center mx-auto text-primary group-hover:scale-105 transition-transform">
                        <Upload className="w-7 h-7" />
                      </div>

                      <div className="space-y-1">
                        <p className="text-sm font-bold text-slate-800">
                          {t("form.dragDrop")}
                        </p>
                        <p className="text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
                          {t("form.fileHint")}
                        </p>
                      </div>
                    </div>
                  )}
                </div>

                <p className="text-[11px] text-slate-500 text-center font-medium">
                  {t("form.pasteClipboardHint")}
                </p>
              </div>
            ) : activeTab === "link" ? (
              /* Tab 3: Check Suspicious Link */
              <div className="space-y-3">
                <div className="relative">
                  <input
                    type="text"
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    placeholder="Paste link, e.g. http://paytm-kyc-update.top/verify?acc=1"
                    className="w-full rounded-xl border border-slate-200 p-4 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary bg-slate-50/70 font-mono transition-all text-slate-900 placeholder:text-slate-400"
                    aria-label="Paste website link"
                  />
                  {inputText && (
                    <button
                      type="button"
                      onClick={() => setInputText("")}
                      className="absolute top-3 right-3 text-xs text-slate-400 hover:text-slate-600 bg-white/80 px-2 py-1 rounded border border-slate-200"
                    >
                      {t("form.clearText")}
                    </button>
                  )}
                </div>
                <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500 pt-0.5">
                  <div className="flex flex-wrap items-center gap-1.5">
                    <span className="font-semibold text-slate-600">Sample links:</span>
                    <button
                      type="button"
                      onClick={() => setInputText("http://paytm-kyc-update.top/verify?acc=1")}
                      className="px-2 py-0.5 rounded-full bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 text-[11px] font-medium transition-colors"
                    >
                      paytm-kyc-update.top
                    </button>
                    <button
                      type="button"
                      onClick={() => setInputText("http://192.168.4.20/sbi/login.php")}
                      className="px-2 py-0.5 rounded-full bg-amber-50 hover:bg-amber-100 text-amber-700 border border-amber-200 text-[11px] font-medium transition-colors"
                    >
                      IP address link
                    </button>
                    <button
                      type="button"
                      onClick={() => setInputText("https://www.amazon.in")}
                      className="px-2 py-0.5 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 text-[11px] font-medium transition-colors"
                    >
                      amazon.in
                    </button>
                  </div>
                  <Link
                    href="/link-checker"
                    className="text-primary hover:underline font-semibold text-xs inline-flex items-center gap-1"
                  >
                    <span>Dedicated Link Tool</span>
                    <ArrowRight className="w-3 h-3" />
                  </Link>
                </div>
              </div>
            ) : (
              /* Tab 2: Paste Text Area */
              <div className="space-y-2">
                <div className="relative">
                  <textarea
                    rows={6}
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    placeholder={t("form.textPlaceholder")}
                    className="w-full rounded-xl border border-slate-200 p-4 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary bg-slate-50/70 font-sans transition-all text-slate-900 placeholder:text-slate-400"
                    aria-label="Paste message text"
                  />
                  {inputText && (
                    <button
                      type="button"
                      onClick={() => setInputText("")}
                      className="absolute top-3 right-3 text-xs text-slate-400 hover:text-slate-600 bg-white/80 px-2 py-1 rounded border border-slate-200"
                    >
                      {t("form.clearText")}
                    </button>
                  )}
                </div>
                <div className="flex justify-end text-[11px] text-slate-400 font-mono">
                  {inputText.length} characters
                </div>
              </div>
            )}

            {/* Controls: Language and Execution Mode */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
              {/* Language Selection */}
              <div className="space-y-1.5">
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                  {t("form.languageLabel")}
                </label>
                <SegmentedControl<Language>
                  label={t("form.languageLabel")}
                  options={[
                    { value: "en", label: "English" },
                    { value: "ta", label: "தமிழ்" },
                    { value: "hi", label: "हिन्दी" },
                  ]}
                  value={language}
                  onChange={(val) => setLanguage(val)}
                />
              </div>

              {/* Execution Mode Selection with Tooltip */}
              <div className="space-y-1.5">
                <div className="flex items-center gap-1.5">
                  <label className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                    {t("form.modeLabel")}
                  </label>
                  <Tooltip
                    content={
                      selectedMode === "cloud"
                        ? t("form.modeCloudTooltip")
                        : t("form.modeLocalTooltip")
                    }
                  />
                </div>
                <SegmentedControl<"cloud" | "local">
                  label={t("form.modeLabel")}
                  options={[
                    {
                      value: "cloud",
                      label: isCloudAvailable
                        ? t("form.modeCloudLabel")
                        : cloudKeyConfigured
                        ? `${t("form.modeCloudLabel")} (Connecting...)`
                        : `${t("form.modeCloudLabel")} (Setup Required)`,
                      title: isCloudAvailable
                        ? t("form.modeCloudTooltip")
                        : "Live Cloud inference requires GEMINI_API_KEY configured in backend/.env.",
                    },
                    {
                      value: "local",
                      label: isOllamaAvailable
                        ? t("form.modeLocalLabel")
                        : `${t("form.modeLocalLabel")} (Offline)`,
                      disabled: !isOllamaAvailable,
                      title: isOllamaAvailable
                        ? t("form.modeLocalTooltip")
                        : "Local Ollama daemon is offline (http://localhost:11434). Run `ollama serve` to enable.",
                    },
                  ]}
                  value={selectedMode}
                  onChange={(val) => {
                    if (val === "local" && !isOllamaAvailable) {
                      toast("Local Ollama is offline. Run `ollama serve` or switch to Cloud mode.", "info");
                      return;
                    }
                    setSelectedMode(val);
                    setError(null);
                  }}
                />
                {!cloudKeyConfigured && selectedMode === "cloud" && (
                  <p className="text-[11px] text-amber-800 bg-amber-50 border border-amber-200/70 rounded-lg px-2.5 py-1.5 flex items-center gap-1.5 mt-2">
                    <Sparkles className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                    <span>Set <code className="font-mono font-bold bg-amber-100 px-1 py-0.5 rounded">GEMINI_API_KEY</code> in <code className="font-mono">backend/.env</code> for live multimodal analysis. Built-in samples below work offline.</span>
                  </p>
                )}
              </div>
            </div>

            {/* "Try a sample" Chips */}
            <div className="space-y-2 pt-1 border-t border-slate-200/60">
              <span className="text-xs font-bold text-slate-700">
                {t("form.trySampleLabel")}
              </span>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => handleLoadSample("internship")}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all min-h-[44px] flex items-center gap-1.5 ${
                    activeSampleKey === "internship"
                      ? "bg-primary text-white border-primary shadow-sm"
                      : "bg-white text-slate-700 border-slate-200 hover:bg-slate-50"
                  }`}
                >
                  <span>📄</span>
                  <span>{t("form.sampleInternship")}</span>
                </button>

                <button
                  type="button"
                  onClick={() => handleLoadSample("payment")}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all min-h-[44px] flex items-center gap-1.5 ${
                    activeSampleKey === "payment"
                      ? "bg-primary text-white border-primary shadow-sm"
                      : "bg-white text-slate-700 border-slate-200 hover:bg-slate-50"
                  }`}
                >
                  <span>💳</span>
                  <span>{t("form.samplePayment")}</span>
                </button>

                <button
                  type="button"
                  onClick={() => handleLoadSample("kyc")}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all min-h-[44px] flex items-center gap-1.5 ${
                    activeSampleKey === "kyc"
                      ? "bg-primary text-white border-primary shadow-sm"
                      : "bg-white text-slate-700 border-slate-200 hover:bg-slate-50"
                  }`}
                >
                  <span>📱</span>
                  <span>{t("form.sampleKyc")}</span>
                </button>

                <button
                  type="button"
                  onClick={() => handleLoadSample("bank_alert")}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all min-h-[44px] flex items-center gap-1.5 ${
                    activeSampleKey === "bank_alert"
                      ? "bg-primary text-white border-primary shadow-sm"
                      : "bg-white text-slate-700 border-slate-200 hover:bg-slate-50"
                  }`}
                >
                  <span>🏦</span>
                  <span>{language === "ta" ? "உண்மையான வங்கி எச்சரிக்கை" : language === "hi" ? "असली बैंक सूचना" : "Genuine Bank Alert"}</span>
                </button>
              </div>
            </div>

            {/* Error Banner */}
            {error && (
              <div
                role="alert"
                className="rounded-xl bg-danger-light border border-danger/30 p-3.5 text-xs text-danger-dark flex flex-col sm:flex-row sm:items-center justify-between gap-3 animate-fadeIn"
              >
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 shrink-0 text-danger" />
                  <span className="font-semibold">{error}</span>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {(selectedMode === "local" || error.toLowerCase().includes("ollama")) && (
                    <Button
                      type="button"
                      variant="primary"
                      size="sm"
                      onClick={() => {
                        setSelectedMode("cloud");
                        setError(null);
                        toast("Switched to Live Cloud API (Gemini)", "success");
                      }}
                      className="text-xs bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm flex items-center gap-1.5 font-bold"
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>Switch to Live Cloud (Gemini)</span>
                    </Button>
                  )}
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => handleAnalyze()}
                    className="text-xs bg-white text-slate-800 hover:bg-slate-100 shrink-0 flex items-center gap-1 font-semibold"
                  >
                    <RotateCcw className="w-3.5 h-3.5 text-primary" />
                    <span>{t("errorPage.retryBtn") || "Retry"}</span>
                  </Button>
                  {!isDemoMode && (
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={async () => {
                        setIsDemoMode(true);
                        setError(null);
                        const sampleKey = activeSampleKey || "payment";
                        try {
                          setIsLoading(true);
                          const demoRes = await loadDemoResult(sampleKey, language);
                          setResult(demoRes);
                          toast("Loaded verified sample result", "info");
                        } catch {
                          toast("Failed to load demo result", "error");
                        } finally {
                          setIsLoading(false);
                        }
                      }}
                      className="text-xs bg-white text-slate-800 hover:bg-slate-100 shrink-0 font-semibold"
                    >
                      {t("errors.switchToDemoBtn")}
                    </Button>
                  )}
                </div>
              </div>
            )}

            {/* Analyze Submit Button */}
            <div className="space-y-2 pt-2">
              <Button
                type="submit"
                variant="primary"
                size="lg"
                disabled={!hasValidInput || isLoading}
                isLoading={isLoading}
                rightIcon={<ArrowRight className="w-4 h-4" />}
                className="w-full text-sm sm:text-base font-bold shadow-lg shadow-primary/25 hover:shadow-xl"
              >
                {t("form.analyzeBtn")}
              </Button>

              <p className="text-[11px] text-slate-500 text-center font-medium">
                {t("form.noStorageNote")}
              </p>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
