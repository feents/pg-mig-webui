import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import api from "../lib/api";

export default function LoginPage() {
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const form = new URLSearchParams();
      form.append("username", email);
      form.append("password", password);
      const { data } = await api.post("/auth/login", form, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });
      localStorage.setItem("access_token", data.access_token);
      const { data: me } = await api.get("/auth/me");
      localStorage.setItem("user_role", me.role);
      navigate("/connections");
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setError(detail ? t(`errors.${detail}`, { defaultValue: detail }) : t("auth.error_login_failed"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-fs-25 font-sans">
      <div className="fixed top-4 right-4 flex items-center gap-1 text-xs font-medium">
        <button
          onClick={() => i18n.changeLanguage("en")}
          className={`px-1.5 py-0.5 rounded transition-colors duration-150 ${
            i18n.language === "en" ? "text-feents-700 font-bold" : "text-fs-400 hover:text-fs-700"
          }`}
        >
          EN
        </button>
        <span className="text-fs-300">|</span>
        <button
          onClick={() => i18n.changeLanguage("ko")}
          className={`px-1.5 py-0.5 rounded transition-colors duration-150 ${
            i18n.language === "ko" ? "text-feents-700 font-bold" : "text-fs-400 hover:text-fs-700"
          }`}
        >
          KO
        </button>
      </div>

      <div className="w-full max-w-md px-4">
        <div className="flex flex-col items-center mb-8 gap-3">
          <div className="w-12 h-12 bg-feents rounded-xl flex items-center justify-center">
            <span className="text-white font-extrabold text-2xl leading-none">F</span>
          </div>
          <div className="text-center">
            <h1 className="text-lg font-bold text-fs-900 tracking-tight">{t("app.title")}</h1>
            <p className="text-xs text-fs-400 mt-0.5">{t("app.subtitle")}</p>
          </div>
        </div>

        <div className="bg-white rounded-[14px] border border-fs-200 p-8 space-y-5">
          <h2 className="text-base font-semibold text-fs-900">{t("auth.login")}</h2>

          {error && (
            <div className="text-sm text-[#E54B4B] bg-[#FCE9E9] border border-[#E54B4B]/30 px-3 py-2.5 rounded-lg">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-fs-600 uppercase tracking-wide mb-1.5">{t("common.email")}</label>
              <input
                type="email"
                className="w-full border border-fs-200 rounded-lg px-3 py-2.5 text-sm text-fs-900 placeholder:text-fs-400 focus:outline-none focus:border-feents focus:ring-2 focus:ring-feents/20 transition-colors"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="example@email.com"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-fs-600 uppercase tracking-wide mb-1.5">{t("common.password")}</label>
              <input
                type="password"
                className="w-full border border-fs-200 rounded-lg px-3 py-2.5 text-sm text-fs-900 placeholder:text-fs-400 focus:outline-none focus:border-feents focus:ring-2 focus:ring-feents/20 transition-colors"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-feents text-white py-2.5 rounded-lg text-sm font-semibold hover:bg-feents-600 disabled:opacity-50 transition-colors duration-150 mt-1"
            >
              {loading ? t("auth.login_loading") : t("auth.login")}
            </button>
          </form>

          <p className="text-xs text-center text-fs-400">
            {t("auth.no_account")}{" "}
            <Link to="/register" className="text-feents-700 hover:text-feents font-medium">
              {t("auth.register")}
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
