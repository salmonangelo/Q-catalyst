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
          <CartesianGrid strokeDasharray="3 3" stroke="#F0F2F5" />
          <XAxis
            dataKey="iteration"
            stroke="#7A828E"
            fontSize={11}
            tickLine={false}
            label={{ value: 'Optimizer Iteration', position: 'insideBottom', offset: -10, fill: '#6C757D', fontSize: 12 }}
          />
          <YAxis
            stroke="#7A828E"
            fontSize={11}
            tickLine={false}
            domain={['auto', 'auto']}
            tickFormatter={(val) => val.toFixed(4)}
            label={{ value: 'Energy (Hartree)', angle: -90, position: 'insideLeft', fill: '#6C757D', fontSize: 12 }}
          />
          <Tooltip
            contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#E3E5E8', borderRadius: '8px', fontSize: '12px' }}
            formatter={(val: number) => [`${val.toFixed(6)} Ha`, 'VQE Energy']}
            labelFormatter={(label) => `Iteration ${label}`}
          />
          <ReferenceLine
            y={casciEnergy}
            stroke="#121417"
            strokeDasharray="4 4"
            strokeWidth={1.5}
            label={{
              value: `CASCI Reference: ${casciEnergy.toFixed(6)} Ha`,
              position: 'insideTopRight',
              fill: '#121417',
              fontSize: 11,
            }}
          />
          <Line
            type="monotone"
            dataKey="energy"
            stroke="#C59A45"
            strokeWidth={2.5}
            dot={{ r: 3, fill: '#C59A45' }}
            activeDot={{ r: 5 }}
            name="VQE (TwoLocal/COBYLA)"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
