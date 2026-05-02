import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import api from "../lib/api";
import Layout from "../components/Layout";
import ConnectionCard from "../components/ConnectionCard";
import ConnectionForm from "../components/ConnectionForm";

interface Connection {
  id: number;
  name: string;
  host: string;
  port: number;
  database: string;
  username: string;
  use_vpn: boolean;
}

export default function ConnectionsPage() {
  const { t } = useTranslation();
  const [connections, setConnections] = useState<Connection[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [editTarget, setEditTarget] = useState<Connection | null>(null);

  async function load() {
    const { data } = await api.get("/connections");
    setConnections(data);
  }

  useEffect(() => { load(); }, []);

  function handleEdit(conn: Connection) {
    setEditTarget(conn);
    setShowForm(true);
  }

  function handleFormClose() {
    setShowForm(false);
    setEditTarget(null);
  }

  return (
    <Layout>
      <div className="space-y-5">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold text-fs-900 tracking-tight">{t("connections.title")}</h1>
          <button
            onClick={() => { setEditTarget(null); setShowForm(true); }}
            className="bg-feents text-white text-sm px-4 py-2 rounded-lg hover:bg-feents-600 transition-colors duration-150 font-semibold"
          >
            {t("connections.add")}
          </button>
        </div>

        {connections.length === 0 ? (
          <div className="bg-white rounded-[14px] border border-fs-200 p-12 text-center">
            <p className="text-fs-400 text-sm">{t("connections.empty")}</p>
            <button
              onClick={() => { setEditTarget(null); setShowForm(true); }}
              className="mt-4 text-feents-700 text-sm font-medium hover:text-feents"
            >
              {t("connections.add_first")}
            </button>
          </div>
        ) : (
          <div className="space-y-2.5">
            {connections.map((c) => (
              <ConnectionCard key={c.id} conn={c} onDeleted={load} onEdit={handleEdit} />
            ))}
          </div>
        )}
      </div>

      {showForm && (
        <ConnectionForm
          existing={editTarget ?? undefined}
          onSaved={() => { handleFormClose(); load(); }}
          onCancel={handleFormClose}
        />
      )}
    </Layout>
  );
}
