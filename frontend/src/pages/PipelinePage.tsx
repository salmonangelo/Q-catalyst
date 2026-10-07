import React, { useEffect, useState } from 'react';
import { api } from '@/api/client';
import { PipelineResponse } from '@/types/api';
import { CheckCircle2, Play, Layers, Clock, ShieldCheck } from 'lucide-react';

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
        <h1 className="text-3xl font-extrabold text-[#121417] tracking-tight">
          Pipeline Orchestration & Execution Lineage
        </h1>
        <p className="text-sm text-[#6C757D] mt-1">
          Audit trail, stage execution status, duration waterfall, and reproducible artifact tracking across all 7 stages.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Waterfall Stages List */}
        <div className="lg:col-span-2 space-y-4">
          <div className="text-xs font-cinzel font-bold text-[#C59A45] tracking-wider uppercase mb-2">
            Automated Hybrid Workflow
          </div>

          {pipeline?.stages.map((st, i) => (
            <div
              key={st.stage_id}
              className="qc-card p-5 flex items-start gap-4 hover:border-[#C59A45]/40"
            >
              <div className="w-8 h-8 rounded-full bg-[#121417] text-white flex items-center justify-center font-bold text-xs shrink-0 mt-0.5">
                <CheckCircle2 className="w-4 h-4 text-[#198754]" />
              </div>
              <div className="grow">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-1">
                  <h3 className="font-bold text-sm text-[#121417]">{st.name}</h3>
                  <div className="flex items-center gap-2">
                    {st.duration_seconds !== null && (
                      <span className="text-[11px] font-mono text-[#6C757D]">
                        {st.duration_seconds.toFixed(4)}s
                      </span>
                    )}
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#EAF8EE] text-[#1E7E34]">
                      {st.status}
                    </span>
                  </div>
                </div>
                <p className="text-xs text-[#6C757D] mb-2">{st.description}</p>
                <div className="font-mono text-[11px] text-[#9E7A30] bg-[#FAF9F6] px-2.5 py-1 rounded border border-[#E3E5E8] inline-block">
                  {st.artifact_path}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Execution Metadata & Trigger Info */}
        <div className="space-y-6">
          <div className="qc-card p-6">
            <div className="text-xs font-cinzel font-bold text-[#121417] tracking-wider uppercase mb-3">
              Active Run Manifest
            </div>
            <div className="space-y-3 text-xs">
              <div className="flex justify-between py-1.5 border-b border-[#E3E5E8]">
                <span className="text-[#6C757D]">Run Identifier:</span>
                <span className="font-mono font-bold text-[#121417] text-[11px]">
                  {pipeline?.run_id || 'run_latest'}
                </span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-[#E3E5E8]">
                <span className="text-[#6C757D]">Pipeline Version:</span>
                <span className="font-mono font-bold text-[#121417]">{pipeline?.pipeline_version || '0.1.0'}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-[#E3E5E8]">
                <span className="text-[#6C757D]">Status:</span>
                <span className="font-bold text-[#198754]">7/7 Complete</span>
              </div>
              <div className="flex justify-between py-1.5">
                <span className="text-[#6C757D]">Timestamp:</span>
                <span className="font-mono text-[#6C757D] text-[10px]">
                  {pipeline?.timestamp || '2026-10-07T16:05:33Z'}
                </span>
              </div>
            </div>
          </div>

          <div className="qc-card p-6">
            <div className="text-xs font-cinzel font-bold text-[#C59A45] tracking-wider uppercase mb-2">
              Execution Policy
            </div>
            <p className="text-xs text-[#6C757D] leading-relaxed mb-4">
              Deterministic single-command CLI execution:
            </p>
            <div className="bg-[#121417] text-[#DFBD74] p-3 rounded-lg font-mono text-xs">
              python -m pipeline.evaluate
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
