import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import api from "../lib/api";

interface Job {
  id: number;
  source_conn_id: number | null;
  target_conn_id: number | null;
  source_conn_name: string | null;
  target_conn_name: string | null;
  source_kind: string;
  target_kind: string;
  status: string;
  progress_pct: number;
  started_at: string | null;
  finished_at: string | null;
}

const STATUS_COLORS: Record<string, string> = {
  pending: "text-fs-500 bg-fs-100",
  running: "text-[#4C8BFF] bg-[#E8F0FF]",
  success: "text-[#16A37B] bg-[#E5F6F0]",
  success_with_warnings: "text-[#B8770C] bg-[#FFF4E0]",
  failed: "text-[#E54B4B] bg-[#FCE9E9]",
};

interface Props {
  refresh: number;
  onSelect: (job: Job) => void;
}

export default function MigrationHistory({ refresh, onSelect }: Props) {
  const { t } = useTranslation();
  const [jobs, setJobs] = useState<Job[]>([]);

  async function load() {
    const { data } = await api.get("/migrations");
    setJobs(data);
  }

  useEffect(() => { load(); }, [refresh]);

  if (jobs.length === 0) return null;

  function elapsed(started: string | null, finished: string | null): string {
    if (!started) return "-";
    const s = new Date(started);
    const e = finished ? new Date(finished) : new Date();
    const sec = Math.floor((e.getTime() - s.getTime()) / 1000);
    if (sec < 60) return t("history.duration_sec", { sec });
    return t("history.duration_min", { min: Math.floor(sec / 60), sec: sec % 60 });
  }

  function sourceLabel(job: Job) {
    if (job.source_kind === "file") return t("history.file_upload");
    return job.source_conn_name ?? t("history.deleted");
  }

  function targetLabel(job: Job) {
    if (job.target_kind === "file") return t("history.file_download");
    return job.target_conn_name ?? t("history.deleted");
  }

  return (
    <div className="bg-white rounded-[14px] border border-fs-200 p-6">
      <h2 className="text-sm font-bold text-fs-900 tracking-tight mb-4">{t("history.title")}</h2>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-fs-100 text-left text-fs-400 text-xs uppercase tracking-wide">
              <th className="pb-3 pr-4 font-semibold">#</th>
              <th className="pb-3 pr-4 font-semibold">{t("history.col_source")}</th>
              <th className="pb-3 pr-4 font-semibold">{t("history.col_target")}</th>
              <th className="pb-3 pr-4 font-semibold">{t("history.col_status")}</th>
              <th className="pb-3 pr-4 font-semibold">{t("history.col_progress")}</th>
              <th className="pb-3 pr-4 font-semibold">{t("history.col_duration")}</th>
              <th className="pb-3"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-fs-100">
            {jobs.map((j) => (
              <tr key={j.id} className="hover:bg-fs-25 transition-colors">
                <td className="py-3 pr-4 text-fs-400 font-mono text-xs">{j.id}</td>
                <td className="py-3 pr-4 text-fs-800 font-medium truncate max-w-[120px] text-xs">{sourceLabel(j)}</td>
                <td className="py-3 pr-4 text-fs-700 truncate max-w-[120px] text-xs">{targetLabel(j)}</td>
                <td className="py-3 pr-4">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${STATUS_COLORS[j.status] ?? ""}`}>
                    {t(`progress.status_${j.status}`, { defaultValue: j.status })}
                  </span>
                </td>
                <td className="py-3 pr-4 text-fs-500 text-xs font-mono">{j.progress_pct.toFixed(0)}%</td>
                <td className="py-3 pr-4 text-fs-400 text-xs font-mono">{elapsed(j.started_at, j.finished_at)}</td>
                <td className="py-3">
                  <button
                    onClick={() => onSelect(j)}
                    className="text-xs text-feents-700 hover:text-feents font-semibold"
                  >
                    {t("history.view_log")}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
