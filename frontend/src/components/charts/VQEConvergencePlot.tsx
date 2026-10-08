import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { QuantumHistoryPoint } from '@/types/api';

interface VQEConvergencePlotProps {
  history: QuantumHistoryPoint[];
  casciEnergy: number;
  finalVqeEnergy: number;
}

export const VQEConvergencePlot: React.FC<VQEConvergencePlotProps> = ({
  history,
  casciEnergy,
}) => {
  return (
    <div className="w-full h-80">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={history} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(203, 213, 225, 0.08)" />
          <XAxis
            dataKey="iteration"
            stroke="#64748B"
            fontSize={11}
            tickLine={false}
            label={{ value: 'Optimizer Iteration', position: 'insideBottom', offset: -10, fill: '#94A3B8', fontSize: 12 }}
          />
          <YAxis
            stroke="#64748B"
            fontSize={11}
            tickLine={false}
            domain={['auto', 'auto']}
            tickFormatter={(val) => val.toFixed(4)}
            label={{ value: 'Energy (Hartree)', angle: -90, position: 'insideLeft', fill: '#94A3B8', fontSize: 12 }}
          />
          <Tooltip
            contentStyle={{ 
              backgroundColor: '#0D1222', 
              borderColor: 'rgba(245, 158, 11, 0.4)', 
              borderRadius: '8px', 
              fontSize: '12px',
              color: '#F8FAFC',
              boxShadow: '0 8px 24px rgba(0,0,0,0.6)'
            }}
            formatter={(val: number) => [`${val.toFixed(6)} Ha`, 'VQE Energy']}
            labelFormatter={(label) => `Iteration ${label}`}
          />
          <ReferenceLine
            y={casciEnergy}
            stroke="#DC2626"
            strokeDasharray="4 4"
            strokeWidth={1.5}
            label={{
              value: `CASCI Reference: ${casciEnergy.toFixed(6)} Ha`,
              position: 'insideTopRight',
              fill: '#EF4444',
              fontSize: 11,
            }}
          />
          <Line
            type="monotone"
            dataKey="energy"
            stroke="#F59E0B"
            strokeWidth={2.5}
            dot={{ r: 3, fill: '#F59E0B' }}
            activeDot={{ r: 6, fill: '#FDE047' }}
            name="VQE (TwoLocal/COBYLA)"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
