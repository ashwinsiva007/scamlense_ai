"use client";

import React from "react";
import { Band } from "@/lib/api";

interface SemicircleGaugeProps {
  score: number;
  band: Band;
  size?: number;
}

export function SemicircleGauge({ score, band, size = 180 }: SemicircleGaugeProps) {
  // Clamped score 0 to 100
  const clampedScore = Math.max(0, Math.min(100, score));

  // Determine track and fill color based on band (NEVER GREEN)
  const getColor = () => {
    switch (band) {
      case "likely_scam":
        return "#DC2626"; // danger red
      case "suspicious":
        return "#D97706"; // warning amber
      case "low_risk":
        return "#0369A1"; // info blue (NEVER GREEN)
      case "insufficient_info":
      default:
        return "#64748B"; // slate grey
    }
  };

  const activeColor = getColor();

  // SVG dimensions
  const strokeWidth = 14;
  const radius = (size - strokeWidth) / 2;
  const cx = size / 2;
  const cy = size / 2 + 10;

  // Arc calculations (180 degrees from -180 to 0)
  const circumference = Math.PI * radius;
  const strokeDashoffset = circumference - (clampedScore / 100) * circumference;

  // Angle in radians for pointer needle
  const angle = Math.PI * (1 - clampedScore / 100);
  const needleLength = radius - 16;
  const nx = cx - needleLength * Math.cos(angle);
  const ny = cy - needleLength * Math.sin(angle);

  return (
    <div
      className="flex flex-col items-center justify-center select-none"
      role="img"
      aria-label={`Risk score gauge: ${score} out of 100`}
    >
      <svg
        width={size}
        height={size / 2 + 25}
        viewBox={`0 0 ${size} ${size / 2 + 25}`}
        className="overflow-visible"
      >
        {/* Background Arc */}
        <path
          d={`M ${strokeWidth / 2} ${cy} A ${radius} ${radius} 0 0 1 ${size - strokeWidth / 2} ${cy}`}
          fill="none"
          stroke="#E2E8F0"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        />

        {/* Foreground Progress Arc */}
        <path
          d={`M ${strokeWidth / 2} ${cy} A ${radius} ${radius} 0 0 1 ${size - strokeWidth / 2} ${cy}`}
          fill="none"
          stroke={activeColor}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          className="transition-all duration-1000 ease-out"
        />

        {/* Needle Line */}
        <line
          x1={cx}
          y1={cy}
          x2={nx}
          y2={ny}
          stroke={activeColor}
          strokeWidth="3.5"
          strokeLinecap="round"
          className="transition-all duration-1000 ease-out"
        />

        {/* Pivot Hub */}
        <circle cx={cx} cy={cy} r="6" fill="#0F172A" />
        <circle cx={cx} cy={cy} r="2.5" fill="#FFFFFF" />

        {/* Score Text */}
        <text
          x={cx}
          y={cy - 20}
          textAnchor="middle"
          className="font-black text-2xl fill-slate-900"
          style={{ fontVariantNumeric: "tabular-nums" }}
        >
          {score}
        </text>
        <text
          x={cx}
          y={cy - 6}
          textAnchor="middle"
          className="text-[10px] font-semibold uppercase tracking-wider fill-slate-400"
        >
          Score / 100
        </text>
      </svg>
    </div>
  );
}
