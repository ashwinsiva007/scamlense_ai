import React from "react";

export type BadgeVariant =
  | "danger"
  | "warning"
  | "info"
  | "primary"
  | "neutral";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  size?: "sm" | "md";
  dot?: boolean;
}

export function Badge({
  children,
  className = "",
  variant = "neutral",
  size = "md",
  dot = false,
  ...props
}: BadgeProps) {
  const variantStyles: Record<BadgeVariant, string> = {
    danger: "bg-danger-light text-danger-dark border-danger/30",
    warning: "bg-warning-light text-warning-dark border-warning/30",
    info: "bg-info-light text-info-dark border-info/30",
    primary: "bg-primary-light text-primary border-primary/30",
    neutral: "bg-slate-100 text-slate-700 border-slate-200",
  };

  const dotColors: Record<BadgeVariant, string> = {
    danger: "bg-danger",
    warning: "bg-warning",
    info: "bg-info",
    primary: "bg-primary",
    neutral: "bg-slate-400",
  };

  const sizeStyles = {
    sm: "px-2 py-0.5 text-[11px] gap-1",
    md: "px-2.5 py-1 text-xs gap-1.5",
  };

  return (
    <span
      className={`inline-flex items-center font-semibold rounded-lg border leading-none tracking-wide select-none ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
      {...props}
    >
      {dot && (
        <span
          className={`w-1.5 h-1.5 rounded-full shrink-0 ${dotColors[variant]}`}
          aria-hidden="true"
        />
      )}
      <span>{children}</span>
    </span>
  );
}

export function SourceBadge({
  source,
  className = "",
}: {
  source: "rule" | "tool" | "model";
  className?: string;
}) {
  switch (source) {
    case "rule":
      return (
        <Badge variant="primary" size="sm" className={className}>
          YAML Rule
        </Badge>
      );
    case "tool":
      return (
        <Badge variant="info" size="sm" className={className}>
          Live Tool
        </Badge>
      );
    case "model":
      return (
        <Badge variant="neutral" size="sm" className={className}>
          AI Perception
        </Badge>
      );
  }
}
