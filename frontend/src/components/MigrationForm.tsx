import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import api from "../lib/api";

interface Connection {
  id: number;
  name: string;
  host: string;
}

interface Props {
  onStarted: (jobId: number, targetKind: string) => void;
}

type Kind = "db" | "file";

export default function MigrationForm({ onStarted }: Props) {
  const { t } = useTranslation();
  const [connections, setConnections] = useState<Connection[]>([]);
  const [sourceKind, setSourceKind] = useState<Kind>("db");
  const [targetKind, setTargetKind] = useState<Kind>("db");
  const [sourceId, setSourceId] = useState("");
  const [targetId, setTargetId] = useState("");
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    api.get("/connections").then(({ data }) => setConnections(data));
  }, []);

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) setUploadFile(f);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    if (sourceKind === "file" && targetKind === "file") {
      setError(t("migrations.error_both_file"));
      return;
    }

    if (sourceKind === "db" && targetKind === "db" && sourceId === targetId) {
      setError(t("migrations.error_same"));
      return;
    }

    setLoading(true);
    try {
      let data: { id: number };

      if (sourceKind === "file") {
        if (!uploadFile) { setError(t("migrations.error_no_file")); setLoading(false); return; }
        if (!targetId) { setError(t("migrations.error_no_target")); setLoading(false); return; }
        const form = new FormData();
        form.append("file", uploadFile);
        form.append("target_conn_id", targetId);
        ({ data } = await api.post("/migrations/from-file", form, {
          headers: { "Content-Type": "multipart/form-data" },
        }));
      } else {
        ({ data } = await api.post("/migrations", {
          source_kind: sourceKind,
          target_kind: targetKind,
          source_conn_id: sourceId ? Number(sourceId) : undefined,
          target_conn_id: targetId ? Number(targetId) : undefined,
        }));
      }

      onStarted(data.id, sourceKind === "file" ? "db" : targetKind);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setError(detail ? t(`errors.${detail}`, { defaultValue: detail }) : t("migrations.error_start_failed"));
    } finally {
      setLoading(false);
    }
  }

  const kindBtn = (current: Kind, value: Kind, label: string, setter: (v: Kind) => void) => (
    <button
      type="button"
      onClick={() => setter(value)}
      className={`flex-1 py-1.5 text-xs rounded-lg font-semibold transition-colors duration-150 ${
        current === value
          ? "bg-feents text-white"
          : "bg-fs-100 text-fs-600 hover:bg-fs-200"
      }`}
    >
      {label}
    </button>
  );

  return (
    <div className="bg-white rounded-[14px] border border-fs-200 p-6 space-y-5">
      <h2 className="text-sm font-bold text-fs-900 tracking-tight">{t("migrations.form_title")}</h2>

      {error && (
        <div className="text-sm text-[#E54B4B] bg-[#FCE9E9] border border-[#E54B4B]/30 px-3 py-2.5 rounded-lg">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="space-y-2">
          <label className="block text-xs font-semibold text-fs-600 uppercase tracking-wide">{t("migrations.source")}</label>
          <div className="flex gap-2">
            {kindBtn(sourceKind, "db", t("migrations.kind_db"), setSourceKind)}
            {kindBtn(sourceKind, "file", t("migrations.kind_file_upload"), setSourceKind)}
          </div>

          {sourceKind === "db" ? (
            <select
              className="w-full border border-fs-200 rounded-lg px-3 py-2 text-sm text-fs-900 focus:outline-none focus:border-feents focus:ring-2 focus:ring-feents/20 transition-colors"
              value={sourceId}
              onChange={(e) => setSourceId(e.target.value)}
              required
            >
              <option value="">{t("migrations.select_connection")}</option>
              {connections.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} ({c.host})
                </option>
              ))}
            </select>
          ) : (
            <div
              className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors duration-150 ${
                dragging ? "border-feents bg-feents-50" : "border-fs-300 hover:border-fs-400 hover:bg-fs-50"
              }`}
              onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <p className="text-sm text-fs-500">
                {uploadFile
                  ? <span className="text-feents-700 font-semibold">{uploadFile.name}</span>
                  : t("migrations.file_drop")}
              </p>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pgdump,.dump,.backup"
                className="hidden"
                onChange={(e) => setUploadFile(e.target.files?.[0] ?? null)}
              />
            </div>
          )}
        </div>

        <div className="space-y-2">
          <label className="block text-xs font-semibold text-fs-600 uppercase tracking-wide">{t("migrations.target")}</label>
          <div className="flex gap-2">
            {kindBtn(targetKind, "db", t("migrations.kind_db"), setTargetKind)}
            {kindBtn(targetKind, "file", t("migrations.kind_file_download"), setTargetKind)}
          </div>

          {targetKind === "db" && sourceKind !== "file" && (
            <select
              className="w-full border border-fs-200 rounded-lg px-3 py-2 text-sm text-fs-900 focus:outline-none focus:border-feents focus:ring-2 focus:ring-feents/20 transition-colors"
              value={targetId}
              onChange={(e) => setTargetId(e.target.value)}
              required
            >
              <option value="">{t("migrations.select_connection")}</option>
              {connections
                .filter((c) => String(c.id) !== sourceId)
                .map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} ({c.host})
                  </option>
                ))}
            </select>
          )}

          {targetKind === "db" && sourceKind === "file" && (
            <select
              className="w-full border border-fs-200 rounded-lg px-3 py-2 text-sm text-fs-900 focus:outline-none focus:border-feents focus:ring-2 focus:ring-feents/20 transition-colors"
              value={targetId}
              onChange={(e) => setTargetId(e.target.value)}
              required
            >
              <option value="">{t("migrations.select_connection")}</option>
              {connections.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} ({c.host})
                </option>
              ))}
            </select>
          )}

          {targetKind === "file" && (
            <p className="text-xs text-fs-500 bg-fs-50 border border-fs-200 rounded-lg px-3 py-2.5">
              {t("migrations.download_note")}
            </p>
          )}
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-feents text-white py-2.5 rounded-lg text-sm font-semibold hover:bg-feents-600 disabled:opacity-50 transition-colors duration-150"
        >
          {loading ? t("migrations.starting") : t("migrations.start")}
        </button>
      </form>
    </div>
  );
}
