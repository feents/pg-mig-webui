import { useState } from "react";
import { useTranslation } from "react-i18next";
import api from "../lib/api";

interface ExistingConnection {
  id: number;
  name: string;
  host: string;
  port: number;
  database: string;
  username: string;
  use_vpn: boolean;
}

interface Props {
  onSaved: () => void;
  onCancel: () => void;
  existing?: ExistingConnection;
}

export default function ConnectionForm({ onSaved, onCancel, existing }: Props) {
  const { t } = useTranslation();
  const isEdit = !!existing;

  const [form, setForm] = useState({
    name: existing?.name ?? "",
    host: existing?.host ?? "",
    port: String(existing?.port ?? "5432"),
    database: existing?.database ?? "",
    username: existing?.username ?? "",
    password: "",
    use_vpn: existing?.use_vpn ?? false,
    ovpn_content: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [testStatus, setTestStatus] = useState<null | "testing" | "ok" | "error">(null);
  const [testMessage, setTestMessage] = useState("");

  function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => setForm((f) => ({ ...f, ovpn_content: ev.target?.result as string }));
    reader.readAsText(file);
  }

  async function handleTest() {
    setTestStatus("testing");
    setTestMessage("");
    try {
      let res;
      if (isEdit && !form.password) {
        res = await api.post(`/connections/${existing!.id}/test`);
      } else {
        if (!form.password) {
          setTestStatus("error");
          setTestMessage(t("connections.test_error_password_required"));
          return;
        }
        res = await api.post("/connections/test", {
          host: form.host,
          port: Number(form.port),
          database: form.database,
          username: form.username,
          password: form.password,
        });
      }
      if (res.data.ok) {
        setTestStatus("ok");
      } else {
        setTestStatus("error");
        setTestMessage(res.data.detail ?? "");
      }
    } catch (err: any) {
      setTestStatus("error");
      setTestMessage(err.response?.data?.detail ?? "");
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (isEdit) {
        const body: Record<string, unknown> = {
          name: form.name,
          host: form.host,
          port: Number(form.port),
          database: form.database,
          username: form.username,
          use_vpn: form.use_vpn,
        };
        if (form.password) body.password = form.password;
        if (form.use_vpn && form.ovpn_content) body.ovpn_content = form.ovpn_content;
        await api.put(`/connections/${existing!.id}`, body);
      } else {
        await api.post("/connections", {
          ...form,
          port: Number(form.port),
          ovpn_content: form.use_vpn ? form.ovpn_content : undefined,
        });
      }
      onSaved();
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setError(detail ? t(`errors.${detail}`, { defaultValue: detail }) : t("connections.error_save_failed"));
    } finally {
      setLoading(false);
    }
  }

  const field = (label: string, key: keyof typeof form, type = "text", placeholder?: string) => (
    <div>
      <label className="block text-xs font-semibold text-fs-600 uppercase tracking-wide mb-1.5">{label}</label>
      <input
        type={type}
        className="w-full border border-fs-200 rounded-lg px-3 py-2 text-sm text-fs-900 placeholder:text-fs-400 focus:outline-none focus:border-feents focus:ring-2 focus:ring-feents/20 transition-colors"
        value={form[key] as string}
        onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
        required={key !== "ovpn_content" && key !== "password"}
        placeholder={placeholder}
      />
    </div>
  );

  return (
    <div className="fixed inset-0 bg-fs-900/40 flex items-center justify-center z-50 px-4">
      <div className="bg-white rounded-[14px] shadow-lg w-full max-w-lg p-6 space-y-4">
        <h2 className="text-base font-bold text-fs-900">
          {isEdit ? t("connections.form_title_edit") : t("connections.form_title_add")}
        </h2>
        {error && (
          <p className="text-sm text-[#E54B4B] bg-[#FCE9E9] border border-[#E54B4B]/30 px-3 py-2.5 rounded-lg">{error}</p>
        )}
        <form onSubmit={handleSubmit} className="space-y-3">
          {field(t("connections.field_name"), "name")}
          {field(t("connections.field_host"), "host")}
          {field(t("connections.field_port"), "port", "number")}
          {field(t("connections.field_database"), "database")}
          {field(t("connections.field_username"), "username")}
          {field(
            isEdit ? t("connections.field_password_edit") : t("connections.field_password"),
            "password",
            "password",
            isEdit ? t("connections.field_password_edit_placeholder") : undefined,
          )}
          <div className="flex items-center gap-2 py-1">
            <input
              id="use_vpn"
              type="checkbox"
              checked={form.use_vpn}
              onChange={(e) => setForm((f) => ({ ...f, use_vpn: e.target.checked }))}
              className="w-4 h-4 accent-feents rounded"
            />
            <label htmlFor="use_vpn" className="text-sm font-medium text-fs-700">{t("connections.vpn_label")}</label>
          </div>
          {form.use_vpn && (
            <div>
              <label className="block text-xs font-semibold text-fs-600 uppercase tracking-wide mb-1.5">
                {isEdit ? t("connections.ovpn_label_edit") : t("connections.ovpn_label")}
              </label>
              <input
                type="file"
                accept=".ovpn,.conf"
                onChange={handleFile}
                className="text-sm text-fs-600 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-feents-50 file:text-feents-700 hover:file:bg-feents-100 file:cursor-pointer"
              />
            </div>
          )}
          <div className="pt-2 space-y-2">
            <button
              type="button"
              onClick={handleTest}
              disabled={testStatus === "testing"}
              className="w-full border border-feents text-feents py-2 rounded-lg text-sm font-semibold hover:bg-feents/5 disabled:opacity-50 transition-colors duration-150"
            >
              {testStatus === "testing" ? t("connections.test_testing") : t("connections.test_btn")}
            </button>
            {testStatus === "ok" && (
              <p className="text-sm text-[#22863A] bg-[#E6F4EA] border border-[#22863A]/30 px-3 py-2 rounded-lg">
                ✓ {t("connections.test_ok")}
              </p>
            )}
            {testStatus === "error" && (
              <p className="text-sm text-[#E54B4B] bg-[#FCE9E9] border border-[#E54B4B]/30 px-3 py-2 rounded-lg break-all">
                ✗ {t("connections.test_fail")}{testMessage ? `: ${testMessage}` : ""}
              </p>
            )}
            <div className="flex gap-2">
              <button
                type="submit"
                disabled={loading}
                className="flex-1 bg-feents text-white py-2 rounded-lg text-sm font-semibold hover:bg-feents-600 disabled:opacity-50 transition-colors duration-150"
              >
                {loading ? t("common.saving") : t("common.save")}
              </button>
              <button
                type="button"
                onClick={onCancel}
                className="flex-1 border border-fs-200 py-2 rounded-lg text-sm font-semibold hover:bg-fs-50 text-fs-700 transition-colors duration-150"
              >
                {t("common.cancel")}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
