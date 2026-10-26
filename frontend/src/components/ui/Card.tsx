import React from "react";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "glass" | "subtle" | "warning" | "danger" | "info";
}

export function Card({
  children,
  className = "",
  variant = "default",
  ...props
}: CardProps) {
  const variantStyles = {
    default: "bg-white border-slate-200/80 shadow-md shadow-slate-100",
    glass: "glass-panel shadow-lg shadow-slate-200/50",
    subtle: "bg-slate-50/80 border-slate-200 shadow-sm",
    warning: "bg-warning-light/40 border-warning/30 text-slate-900 shadow-sm",
    danger: "bg-danger-light/30 border-danger/30 text-slate-900 shadow-sm",
    info: "bg-info-light/40 border-info/30 text-slate-900 shadow-sm",
  };

  return (
    <div
      className={`rounded-2xl border transition-all ${variantStyles[variant]} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({
  children,
  className = "",
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={`p-5 sm:p-6 pb-0 ${className}`} {...props}>
      {children}
    </div>
  );
}

export function CardBody({
  children,
  className = "",
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={`p-5 sm:p-6 ${className}`} {...props}>
      {children}
    </div>
  );
}

export function CardFooter({
  children,
  className = "",
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={`p-5 sm:p-6 pt-0 border-t border-slate-100 mt-4 ${className}`} {...props}>
      {children}
    </div>
  );
}
