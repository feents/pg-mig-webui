import { useNavigate, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";

export default function Layout({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate();
  const location = useLocation();
  const isAdmin = localStorage.getItem("user_role") === "admin";
  const { t, i18n } = useTranslation();

  function logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user_role");
    navigate("/login");
  }

  const navItems = [
    { path: "/connections", label: t("nav.connections") },
    { path: "/migrations", label: t("nav.migrations") },
    ...(isAdmin ? [{ path: "/admin", label: t("nav.admin") }] : []),
  ];

  return (
    <div className="min-h-screen bg-fs-25 font-sans">
      <nav className="bg-white border-b border-fs-200 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 bg-feents rounded-lg flex items-center justify-center flex-shrink-0">
                <span className="text-white font-extrabold text-base leading-none">F</span>
              </div>
              <span className="text-sm font-bold text-fs-900 tracking-tight">{t("app.nav_title")}</span>
            </div>
            <div className="flex gap-0.5">
              {navItems.map((item) => (
                <button
                  key={item.path}
                  onClick={() => navigate(item.path)}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors duration-150 ${
                    location.pathname === item.path
                      ? "bg-feents-50 text-feents-700"
                      : "text-fs-600 hover:bg-fs-50 hover:text-fs-900"
                  }`}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1 text-xs font-medium">
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
            <button
              onClick={logout}
              className="text-sm text-fs-500 hover:text-fs-800 px-3 py-1.5 rounded-lg hover:bg-fs-50 transition-colors duration-150"
            >
              {t("nav.logout")}
            </button>
          </div>
        </div>
      </nav>
      <main className="max-w-5xl mx-auto px-6 py-8">{children}</main>
      <footer className="border-t border-fs-100 mt-auto">
        <div className="max-w-5xl mx-auto px-6 h-10 flex items-center">
          <span className="text-xs text-fs-400">© 2026 FEENTS</span>
        </div>
      </footer>
    </div>
  );
}
