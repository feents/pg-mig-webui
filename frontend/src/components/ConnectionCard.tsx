import { useTranslation } from "react-i18next";
import api from "../lib/api";

interface Connection {
  id: number;
  name: string;
  host: string;
  port: number;
  database: string;
  username: string;
  use_vpn: boolean;
}

interface Props {
  conn: Connection;
  onDeleted: () => void;
  onEdit: (conn: Connection) => void;
}

export default function ConnectionCard({ conn, onDeleted, onEdit }: Props) {
  const { t } = useTranslation();

  async function handleDelete() {
    if (!confirm(t("connections.delete_confirm", { name: conn.name }))) return;
    await api.delete(`/connections/${conn.id}`);
    onDeleted();
  }

  return (
    <div className="bg-white border border-fs-200 rounded-[14px] p-4 flex items-center justify-between hover:border-fs-300 hover:shadow-sm transition-all duration-150">
      <div className="space-y-1">
        <div className="flex items-center gap-2">
          <p className="font-semibold text-fs-900 text-sm">{conn.name}</p>
          {conn.use_vpn && (
            <span className="text-xs bg-feents-50 text-feents-700 px-2 py-0.5 rounded-full font-semibold">VPN</span>
          )}
        </div>
        <p className="text-xs text-fs-400">
          {conn.host}:{conn.port} &middot; <span className="font-mono">{conn.database}</span>
        </p>
      </div>
      <div className="flex gap-2">
        <button
          onClick={() => onEdit(conn)}
          className="text-fs-500 hover:text-feents-700 text-xs border border-fs-200 hover:border-feents/40 px-3 py-1.5 rounded-lg transition-colors duration-150"
        >
          {t("common.edit")}
        </button>
        <button
          onClick={handleDelete}
          className="text-fs-500 hover:text-[#E54B4B] text-xs border border-fs-200 hover:border-[#E54B4B]/40 px-3 py-1.5 rounded-lg transition-colors duration-150"
        >
          {t("common.delete")}
        </button>
      </div>
    </div>
  );
}
