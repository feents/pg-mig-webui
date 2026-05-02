import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import api from "../lib/api";
import Layout from "../components/Layout";

interface PendingUser {
  id: number;
  email: string;
  role: string;
  status: string;
}

export default function AdminPage() {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [users, setUsers] = useState<PendingUser[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (localStorage.getItem("user_role") !== "admin") {
      navigate("/connections", { replace: true });
      return;
    }
    load();
  }, []);

  async function load() {
    const { data } = await api.get("/admin/pending-users");
    setUsers(data);
  }

  async function approve(id: number) {
    setLoading(true);
    try {
      await api.post(`/admin/users/${id}/approve`);
      await load();
    } finally {
      setLoading(false);
    }
  }

  return (
    <Layout>
      <div className="space-y-5">
        <h1 className="text-xl font-bold text-fs-900 tracking-tight">{t("admin.title")}</h1>

        {users.length === 0 ? (
          <div className="bg-white rounded-[14px] border border-fs-200 p-12 text-center">
            <p className="text-fs-400 text-sm">{t("admin.empty")}</p>
          </div>
        ) : (
          <div className="space-y-2.5">
            {users.map((u) => (
              <div
                key={u.id}
                className="bg-white border border-fs-200 rounded-[14px] p-4 flex items-center justify-between hover:border-fs-300 hover:shadow-sm transition-all duration-150"
              >
                <div className="space-y-0.5">
                  <p className="font-semibold text-fs-900 text-sm">{u.email}</p>
                  <p className="text-xs text-fs-400">{t("admin.pending_label")}</p>
                </div>
                <button
                  onClick={() => approve(u.id)}
                  disabled={loading}
                  className="text-sm bg-feents text-white px-4 py-1.5 rounded-lg hover:bg-feents-600 disabled:opacity-50 transition-colors duration-150 font-semibold"
                >
                  {t("common.approve")}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
