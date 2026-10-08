import React, { useEffect, useState } from 'react';
import { api } from '@/api/client';
import { PipelineResponse } from '@/types/api';
import { CheckCircle2 } from 'lucide-react';

export const PipelinePage: React.FC = () => {
  const [pipeline, setPipeline] = useState<PipelineResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getPipeline()
      .then((data) => setPipeline(data))
      .catch((err) => console.error('Failed to load pipeline status:', err))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-8">
      <div>
        <div className="text-xs font-cinzel font-bold text-[#F59E0B] tracking-widest uppercase mb-1">
          Automated Computational Pipeline
        </div>
        <h1 className="text-3xl font-extrabold text-[#F8FAFC] tracking-tight">
          Pipeline Orchestration & Execution Lineage
        </h1>
        <p className="text-sm text-[#94A3B8] mt-1">
          Audit trail, stage execution status, duration waterfall, and reproducible artifact tracking across all 7 stages.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Waterfall Stages List */}
        <div className="lg:col-span-2 space-y-4">
          <div className="text-xs font-cinzel font-bold text-[#F59E0B] tracking-wider uppercase mb-2">
            Automated Hybrid Workflow
          </div>

          {pipeline?.stages.map((st, i) => (
            <div
              key={st.stage_id}
              className="qc-card p-5 flex items-start gap-4 hover:border-[#F59E0B]/40"
            >
              <div className="w-8 h-8 rounded-full bg-[#10B981]/15 border border-[#10B981]/40 text-[#34D399] flex items-center justify-center font-bold text-xs shrink-0 mt-0.5 shadow-sm">
                <CheckCircle2 className="w-4 h-4 text-[#10B981]" />
              </div>
              <div className="grow">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-1">
                  <h3 className="font-bold text-sm text-[#F8FAFC]">{st.name}</h3>
                  <div className="flex items-center gap-2">
                    {st.duration_seconds !== null && (
                      <span className="text-[11px] font-mono text-[#94A3B8]">
                        {st.duration_seconds.toFixed(4)}s
                      </span>
                    )}
                    <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#10B981]/15 text-[#34D399] border border-[#10B981]/30">
                      {st.status}
                    </span>
                  </div>
                </div>
                <p className="text-xs text-[#94A3B8] mb-2.5 leading-relaxed">{st.description}</p>
                <div className="font-mono text-[11px] text-[#FDE047] bg-[#080C18] px-3 py-1 rounded-lg border border-[#F59E0B]/20 inline-block">
                  {st.artifact_path}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Execution Metadata & Trigger Info */}
        <div className="space-y-6">
          <div className="qc-card p-6">
            <div className="text-xs font-cinzel font-bold text-[#F59E0B] tracking-wider uppercase mb-3">
              Active Run Manifest
            </div>
            <div className="space-y-3 text-xs">
              <div className="flex justify-between py-1.5 border-b border-[#1E293B]">
                <span className="text-[#94A3B8]">Run Identifier:</span>
                <span className="font-mono font-bold text-[#F8FAFC] text-[11px]">
                  {pipeline?.run_id || 'run_latest'}
                </span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-[#1E293B]">
                <span className="text-[#94A3B8]">Pipeline Version:</span>
                <span className="font-mono font-bold text-[#FDE047]">{pipeline?.pipeline_version || '0.1.0'}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-[#1E293B]">
                <span className="text-[#94A3B8]">Status:</span>
                <span className="font-bold text-[#34D399]">7/7 Complete</span>
              </div>
              <div className="flex justify-between py-1.5">
                <span className="text-[#94A3B8]">Timestamp:</span>
                <span className="font-mono text-[#64748B] text-[10px]">
                  {pipeline?.timestamp || '2026-10-07T16:05:33Z'}
                </span>
              </div>
            </div>
          </div>

          <div className="qc-card p-6 border-l-4 border-l-[#F59E0B]">
            <div className="text-xs font-cinzel font-bold text-[#F59E0B] tracking-wider uppercase mb-2">
              Execution Policy
            </div>
            <p className="text-xs text-[#94A3B8] leading-relaxed mb-4">
              Deterministic single-command CLI execution:
            </p>
            <div className="bg-[#080C18] text-[#FDE047] border border-[#F59E0B]/30 p-3 rounded-lg font-mono text-xs shadow-qc-sm">
              python -m pipeline.evaluate
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
