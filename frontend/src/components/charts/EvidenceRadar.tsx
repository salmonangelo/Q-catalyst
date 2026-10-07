import React from 'react';
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from 'recharts';
import { RadarScoreProfile } from '@/types/api';

interface EvidenceRadarProps {
  scores: RadarScoreProfile;
  candidateId: string;
  quantumAvailable: boolean;
}

export const EvidenceRadar: React.FC<EvidenceRadarProps> = ({
  scores,
  candidateId,
  quantumAvailable,
}) => {
  const data = [
    { subject: 'Sequence AI', value: scores.protein_ai, fullMark: 1.0 },
    { subject: 'Uncertainty', value: scores.uncertainty_quality, fullMark: 1.0 },
    { subject: 'Mechanism', value: scores.mechanism_proximity, fullMark: 1.0 },
    { subject: 'Chemistry', value: scores.chemistry, fullMark: 1.0 },
    { subject: 'Quantum', value: quantumAvailable ? scores.quantum : 0.0, fullMark: 1.0 },
    { subject: 'Diversity', value: scores.diversity, fullMark: 1.0 },
  ];

  return (
    <div className="w-full h-80">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="70%" data={data}>
          <PolarGrid stroke="#E3E5E8" />
          <PolarAngleAxis
            dataKey="subject"
            tick={{ fill: '#121417', fontSize: 11, fontWeight: 600 }}
          />
          <PolarRadiusAxis
            angle={30}
            domain={[0, 1.0]}
            tick={{ fill: '#6C757D', fontSize: 10 }}
            stroke="#E3E5E8"
          />
          <Radar
            name={candidateId}
            dataKey="value"
            stroke="#C59A45"
            fill="#C59A45"
            fillOpacity={0.25}
            strokeWidth={2}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
};
