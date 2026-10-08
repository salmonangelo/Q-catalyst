import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { CandidateSummary } from '@/types/api';

interface RankingBarChartProps {
  candidates: CandidateSummary[];
}

export const RankingBarChart: React.FC<RankingBarChartProps> = ({ candidates }) => {
  const data = [...candidates]
    .sort((a, b) => b.rank - a.rank)
    .map((c) => ({
      name: c.candidate_id,
      score: c.fusion_score,
      status: c.decision_status,
      rank: c.rank,
    }));

  return (
    <div className="w-full h-72">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 10, right: 30, left: 40, bottom: 10 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(203, 213, 225, 0.08)" />
          <XAxis type="number" domain={[0, 1.05]} stroke="#64748B" fontSize={11} />
          <YAxis dataKey="name" type="category" stroke="#CBD5E1" fontSize={11} width={80} />
          <Tooltip
            contentStyle={{ 
              backgroundColor: '#0D1222', 
              borderColor: 'rgba(245, 158, 11, 0.4)', 
              borderRadius: '8px', 
              fontSize: '12px',
              color: '#F8FAFC',
              boxShadow: '0 8px 24px rgba(0,0,0,0.6)'
            }}
            itemStyle={{ color: '#FDE047' }}
            formatter={(val: number) => [`${val.toFixed(4)}`, 'Composite Score']}
          />
          <Bar dataKey="score" radius={[0, 4, 4, 0]}>
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={
                  entry.status === 'PRIORITIZE'
                    ? '#F59E0B'
                    : entry.status === 'PROMISING_BUT_UNCERTAIN'
                    ? '#06B6D4'
                    : '#475569'
                }
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
