import React from 'react';

interface MetricCardProps {
  label: string;
  value: string | number;
  subtext?: string;
  variant?: 'default' | 'gold' | 'quantum' | 'ruby';
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  subtext,
  variant = 'default',
}) => {
  const getStyles = () => {
    switch (variant) {
      case 'gold':
        return {
          textColor: 'text-[#FDE047]',
          borderColor: 'border-[#F59E0B]/30',
          bgGlow: 'hover:border-[#F59E0B]/60 hover:shadow-qc-gold',
        };
      case 'quantum':
        return {
          textColor: 'text-[#38BDF8]',
          borderColor: 'border-[#06B6D4]/30',
          bgGlow: 'hover:border-[#06B6D4]/60 hover:shadow-qc-cyan',
        };
      case 'ruby':
        return {
          textColor: 'text-[#EF4444]',
          borderColor: 'border-[#DC2626]/30',
          bgGlow: 'hover:border-[#DC2626]/60 hover:shadow-qc-ruby',
        };
      default:
        return {
          textColor: 'text-[#F8FAFC]',
          borderColor: 'border-[#CBD5E1]/15',
          bgGlow: 'hover:border-[#CBD5E1]/30',
        };
    }
  };

  const style = getStyles();

  return (
    <div className={`bg-[#0D1222]/85 border ${style.borderColor} ${style.bgGlow} rounded-xl p-4 transition-all duration-300 shadow-qc-sm relative overflow-hidden group`}>
      <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-white/10 to-transparent group-hover:via-[#F59E0B]/40 transition-colors" />
      <div className="text-[11px] font-semibold text-[#94A3B8] uppercase tracking-wider mb-1">
        {label}
      </div>
      <div className={`text-2xl font-bold tracking-tight font-sans ${style.textColor}`}>
        {value}
      </div>
      {subtext && <div className="text-xs text-[#64748B] mt-1 font-medium">{subtext}</div>}
    </div>
  );
};
