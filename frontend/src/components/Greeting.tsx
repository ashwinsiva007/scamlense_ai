"use client";

import React, { useState, useEffect } from "react";
import { useT } from "@/context/LanguageContext";

export type TimePeriod = "morning" | "afternoon" | "evening" | "night";

export function getTimePeriod(date: Date = new Date()): {
  period: TimePeriod;
  icon: string;
} {
  const hour = date.getHours();
  if (hour >= 5 && hour < 12) {
    return { period: "morning", icon: "🌅" };
  } else if (hour >= 12 && hour < 17) {
    return { period: "afternoon", icon: "☀️" };
  } else if (hour >= 17 && hour < 22) {
    return { period: "evening", icon: "🌆" };
  } else {
    return { period: "night", icon: "🌙" };
  }
}

interface GreetingProps {
  className?: string;
}

export const Greeting: React.FC<GreetingProps> = ({ className = "" }) => {
  const { t } = useT();
  const [timeInfo, setTimeInfo] = useState<{ period: TimePeriod; icon: string }>({
    period: "morning",
    icon: "🌅",
  });
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    setTimeInfo(getTimePeriod());

    const interval = setInterval(() => {
      setTimeInfo(getTimePeriod());
    }, 60000);

    return () => clearInterval(interval);
  }, []);

  const greetingText = mounted
    ? t(`greeting.${timeInfo.period}`)
    : t("greeting.morning");

  const greetingIcon = mounted ? timeInfo.icon : "🌅";

  return (
    <div
      className={`flex items-center justify-center gap-1.5 text-sm sm:text-base font-semibold text-slate-700 animate-fadeIn ${className}`}
      aria-live="polite"
    >
      <span className="text-base sm:text-lg select-none" role="img" aria-label={timeInfo.period}>
        {greetingIcon}
      </span>
      <span>{greetingText}</span>
    </div>
  );
};
