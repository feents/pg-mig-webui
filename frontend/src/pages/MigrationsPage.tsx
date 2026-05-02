import { useState } from "react";
import { useTranslation } from "react-i18next";
import Layout from "../components/Layout";
import MigrationForm from "../components/MigrationForm";
import MigrationProgress from "../components/MigrationProgress";
import MigrationHistory from "../components/MigrationHistory";

interface SelectedJob {
  id: number;
  target_kind: string;
}

export default function MigrationsPage() {
  const { t } = useTranslation();
  const [selectedJob, setSelectedJob] = useState<SelectedJob | null>(null);
  const [historyKey, setHistoryKey] = useState(0);

  function handleStarted(jobId: number, targetKind: string) {
    setSelectedJob({ id: jobId, target_kind: targetKind });
    setHistoryKey((k) => k + 1);
  }

  function handleSelectFromHistory(job: { id: number; target_kind: string }) {
    setSelectedJob({ id: job.id, target_kind: job.target_kind });
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  return (
    <Layout>
      <div className="space-y-5">
        <h1 className="text-xl font-bold text-fs-900 tracking-tight">{t("migrations.title")}</h1>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 items-start">
          <MigrationForm onStarted={handleStarted} />

          {selectedJob !== null && (
            <MigrationProgress
              jobId={selectedJob.id}
              initialTargetKind={selectedJob.target_kind}
            />
          )}
        </div>

        <MigrationHistory refresh={historyKey} onSelect={handleSelectFromHistory} />
      </div>
    </Layout>
  );
}
