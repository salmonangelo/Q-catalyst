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
          <CartesianGrid strokeDasharray="3 3" stroke="#F0F2F5" />
          <XAxis type="number" domain={[0, 1.05]} stroke="#7A828E" fontSize={11} />
          <YAxis dataKey="name" type="category" stroke="#121417" fontSize={11} width={80} />
          <Tooltip
            contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#E3E5E8', borderRadius: '8px', fontSize: '12px' }}
            formatter={(val: number) => [`${val.toFixed(4)}`, 'Composite Score']}
          />
          <Bar dataKey="score" radius={[0, 4, 4, 0]}>
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={
                  entry.status === 'PRIORITIZE'
                    ? '#C59A45'
                    : entry.status === 'PROMISING_BUT_UNCERTAIN'
                    ? '#5B4AE4'
                    : '#D1D5DB'
                }
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
