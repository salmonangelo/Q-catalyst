import React from 'react';

interface MetricCardProps {
  label: string;
  value: string | number;
  subtext?: string;
  variant?: 'default' | 'gold' | 'quantum';
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  subtext,
  variant = 'default',
}) => {
  const valueColor =
    variant === 'gold'
      ? 'text-[#C59A45]'
      : variant === 'quantum'
      ? 'text-[#5B4AE4]'
      : 'text-[#121417]';

  return (
    <div className="bg-[#FAF9F6] border border-[#E3E5E8] rounded-xl p-4 shadow-qc-sm">
      <div className="text-[11px] font-semibold text-[#6C757D] uppercase tracking-wider mb-1">
        {label}
      </div>
      <div className={`text-2xl font-bold tracking-tight font-sans ${valueColor}`}>
        {value}
      </div>
      {subtext && <div className="text-xs text-[#6C757D] mt-1">{subtext}</div>}
    </div>
  );
};
