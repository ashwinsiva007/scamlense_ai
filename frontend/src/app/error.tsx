"use client";

import React, { useEffect } from "react";
import { AlertTriangle, RotateCcw } from "lucide-react";
import { useT } from "@/context/LanguageContext";
import { Button } from "@/components/ui/Button";

export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const { t } = useT();

  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="min-h-[60vh] flex items-center justify-center px-4 sm:px-6 py-16">
      <div className="max-w-md w-full text-center space-y-6 glass-panel p-8 sm:p-10 rounded-2xl border border-slate-200 shadow-md">
        <div className="w-16 h-16 rounded-2xl bg-warning-light/60 border border-warning/30 flex items-center justify-center mx-auto text-warning-dark">
          <AlertTriangle className="w-8 h-8" />
        </div>

        <div className="space-y-2">
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900">
            {t("errorPage.title")}
          </h1>
          <p className="text-xs sm:text-sm text-slate-600 leading-relaxed font-medium">
            {t("errorPage.desc")}
          </p>
        </div>

        <div>
          <Button
            variant="outline"
            size="md"
            onClick={() => reset()}
            leftIcon={<RotateCcw className="w-4 h-4 text-primary" />}
          >
            {t("errorPage.retryBtn")}
          </Button>
        </div>
      </div>
    </div>
  );
}
