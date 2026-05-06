import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { createMigrationWS } from "../lib/ws";
import api from "../lib/api";

interface Props {
  jobId: number;
  initialTargetKind?: string;
}

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-fs-100 text-fs-500",
  running: "bg-[#E8F0FF] text-[#4C8BFF]",
  success: "bg-[#E5F6F0] text-[#16A37B]",
  success_with_warnings: "bg-[#FFF4E0] text-[#B8770C]",
  failed: "bg-[#FCE9E9] text-[#E54B4B]",
};

const BAR_COLORS: Record<string, string> = {
  pending: "bg-fs-300",
  running: "bg-feents",
  success: "bg-[#16A37B]",
  success_with_warnings: "bg-[#E89B2C]",
  failed: "bg-[#E54B4B]",
};

export default function MigrationProgress({ jobId, initialTargetKind }: Props) {
  const { t } = useTranslation();
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState("pending");
  const [logs, setLogs] = useState<string[]>([]);
  const [targetKind, setTargetKind] = useState(initialTargetKind ?? "db");
  const logRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setProgress(0);
    setStatus("pending");
    setLogs([]);

    const ws = createMigrationWS(jobId, (data) => {
      setProgress(data.progress_pct);
      setStatus(data.status);
      if ((data as any).target_kind) setTargetKind((data as any).target_kind);
      if (data.log) setLogs((prev) => [...prev, data.log]);
    });

    return () => ws.close();
  }, [jobId]);

  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [logs]);

  const isDone = status === "success" || status === "success_with_warnings" || status === "failed";
  const showDownload = isDone && (status === "success" || status === "success_with_warnings") && targetKind === "file";

  async function handleDownload() {
    const { data } = await api.get(`/migrations/${jobId}/download`, { responseType: "blob" });
    const url = URL.createObjectURL(data);
    const a = document.createElement("a");
    a.href = url;
    a.download = `migration_${jobId}.pgdump`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="bg-white rounded-[14px] border border-fs-200 p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-fs-900">{t("progress.title", { id: jobId })}</h3>
        <span className={`text-xs px-2.5 py-1 rounded-full font-semibold ${STATUS_COLORS[status] ?? STATUS_COLORS.pending}`}>
          {t(`progress.status_${status}`, { defaultValue: status })}
        </span>
      </div>

      <div>
        <div className="w-full bg-fs-100 rounded-full h-1.5 overflow-hidden">
          <div
            className={`h-1.5 rounded-full transition-all duration-500 ${BAR_COLORS[status] ?? BAR_COLORS.pending}`}
            style={{ width: `${progress}%` }}
          />
        </div>
        <p className="text-xs text-fs-400 text-right mt-1 font-mono">{progress.toFixed(0)}%</p>
      </div>

      <div
        ref={logRef}
        className="bg-fs-900 text-[#00D1B2] text-xs font-mono rounded-lg p-4 h-56 overflow-y-auto leading-relaxed"
      >
        {logs.length === 0 ? (
          <span className="text-fs-400">{t("progress.log_waiting")}</span>
        ) : (
          logs.map((line, i) => <p key={i}>{line}</p>)
        )}
      </div>

      {showDownload && (
        <button
          onClick={handleDownload}
          className="flex items-center justify-center gap-2 w-full bg-feents text-white py-2.5 rounded-lg text-sm font-semibold hover:bg-feents-600 transition-colors duration-150"
        >
          {t("progress.download")}
        </button>
      )}
    </div>
  );
}
