"use client";

import React from "react";
import Link from "next/link";
import { AlertCircle, ArrowLeft } from "lucide-react";
import { useT } from "@/context/LanguageContext";
import { Button } from "@/components/ui/Button";

export default function NotFound() {
  const { t } = useT();

  return (
    <div className="min-h-[60vh] flex items-center justify-center px-4 sm:px-6 py-16">
      <div className="max-w-md w-full text-center space-y-6 glass-panel p-8 sm:p-10 rounded-2xl border border-slate-200 shadow-md">
        <div className="w-16 h-16 rounded-2xl bg-danger-light/60 border border-danger/30 flex items-center justify-center mx-auto text-danger">
          <AlertCircle className="w-8 h-8" />
        </div>

        <div className="space-y-2">
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900">
            {t("notFound.title")}
          </h1>
          <p className="text-xs sm:text-sm text-slate-600 leading-relaxed font-medium">
            {t("notFound.desc")}
          </p>
        </div>

        <div>
          <Link href="/">
            <Button
              variant="primary"
              size="md"
              leftIcon={<ArrowLeft className="w-4 h-4" />}
            >
              {t("notFound.homeBtn")}
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
