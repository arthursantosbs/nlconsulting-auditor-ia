const uploadForm = document.getElementById("upload-form");
const fileInput = document.getElementById("file-input");
const feedback = document.getElementById("form-feedback");
const progressFill = document.getElementById("progress-fill");
const progressMessage = document.getElementById("progress-message");
const downloadLinks = document.getElementById("download-links");
const resultsBody = document.getElementById("results-body");
const searchInput = document.getElementById("search-input");
const anomalyFilter = document.getElementById("anomaly-filter");

const metrics = {
  documents: document.getElementById("metric-documents"),
  anomalies: document.getElementById("metric-anomalies"),
  encoding: document.getElementById("metric-encoding"),
  status: document.getElementById("metric-status"),
};

let currentJobId = null;
let currentDocuments = [];
let pollTimer = null;

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!fileInput.files.length) {
    feedback.textContent = "Selecione ao menos um arquivo .zip ou .txt.";
    return;
  }

  const formData = new FormData();
  [...fileInput.files].forEach((file) => formData.append("files", file));
  feedback.textContent = "Enviando arquivos e criando lote...";
  downloadLinks.innerHTML = "";

  try {
    const response = await fetch("/api/jobs", {
      method: "POST",
      body: formData,
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "Nao foi possivel criar o job.");
    }
    currentJobId = payload.job_id;
    currentDocuments = payload.documents || [];
    renderJob(payload);
    startPolling();
    feedback.textContent = "Lote criado com sucesso.";
  } catch (error) {
    feedback.textContent = error.message;
  }
});

searchInput.addEventListener("input", renderDocuments);
anomalyFilter.addEventListener("change", renderDocuments);

function startPolling() {
  if (pollTimer) {
    clearInterval(pollTimer);
  }
  pollTimer = setInterval(async () => {
    if (!currentJobId) {
      return;
    }
    const response = await fetch(`/api/jobs/${currentJobId}`);
    const payload = await response.json();
    renderJob(payload);
    if (payload.status === "completed" || payload.status === "failed") {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  }, 1500);
}

function renderJob(job) {
  currentDocuments = job.documents || [];
  const ratio = job.total_files ? (job.processed_files / job.total_files) * 100 : 0;
  progressFill.style.width = `${ratio}%`;
  progressMessage.textContent = job.error_message || job.progress_message || "Sem atualizacoes.";
  metrics.documents.textContent = job.summary.documents;
  metrics.anomalies.textContent = job.summary.anomalies;
  metrics.encoding.textContent = job.summary.encoding_issues;
  metrics.status.textContent = humanizeStatus(job.status);
  renderDownloads(job.downloads || {});
  populateAnomalyFilter(currentDocuments);
  renderDocuments();
}

function renderDownloads(downloadMap) {
  downloadLinks.innerHTML = "";
  Object.entries(downloadMap).forEach(([label, href]) => {
    const anchor = document.createElement("a");
    anchor.href = href;
    anchor.textContent = formatDownloadLabel(label);
    downloadLinks.appendChild(anchor);
  });
}

function populateAnomalyFilter(documents) {
  const previous = anomalyFilter.value;
  const options = new Set();
  documents.forEach((document) => {
    (document.anomalies || []).forEach((anomaly) => options.add(anomaly.label));
  });
  anomalyFilter.innerHTML = '<option value="">Todas as anomalias</option>';
  [...options].sort().forEach((label) => {
    const option = document.createElement("option");
    option.value = label;
    option.textContent = label;
    anomalyFilter.appendChild(option);
  });
  anomalyFilter.value = previous;
}

function renderDocuments() {
  const term = searchInput.value.toLowerCase().trim();
  const anomaly = anomalyFilter.value;
  const filtered = currentDocuments.filter((document) => {
    const haystack = [
      document.file_name,
      document.fields?.fornecedor,
      document.fields?.numero_documento,
      document.fields?.status,
    ]
      .join(" ")
      .toLowerCase();
    const termMatch = !term || haystack.includes(term);
    const anomalyMatch =
      !anomaly || (document.anomalies || []).some((item) => item.label === anomaly);
    return termMatch && anomalyMatch;
  });

  if (!filtered.length) {
    resultsBody.innerHTML =
      '<tr><td colspan="7" class="empty-state">Nenhum documento corresponde aos filtros atuais.</td></tr>';
    return;
  }

  resultsBody.innerHTML = filtered
    .map((document) => {
      const anomalies = (document.anomalies || [])
        .map((item) => `<span class="badge danger">${item.label}</span>`)
        .join(" ");
      const warnings = (document.warnings || [])
        .slice(0, 3)
        .map((item) => `<span class="badge warning">${escapeHtml(item)}</span>`)
        .join(" ");

      return `
        <tr>
          <td>${escapeHtml(document.file_name)}</td>
          <td>${escapeHtml(document.fields?.fornecedor || "nao extraido")}</td>
          <td>${escapeHtml(document.fields?.numero_documento || "nao extraido")}</td>
          <td><span class="badge">${escapeHtml(humanizeStatus(document.process_status))}</span></td>
          <td>${escapeHtml(document.provider || document.extraction_source)}</td>
          <td>${anomalies || '<span class="badge">Sem flags</span>'}</td>
          <td>${warnings || '<span class="badge">Sem warnings</span>'}</td>
        </tr>
      `;
    })
    .join("");
}

function humanizeStatus(status) {
  const map = {
    queued: "Na fila",
    processing: "Processando",
    completed: "Concluido",
    failed: "Falhou",
    processed: "Processado",
    warning: "Com alerta",
  };
  return map[status] || status || "Desconhecido";
}

function formatDownloadLabel(raw) {
  const labels = {
    results_csv: "Baixar CSV principal",
    anomalies_csv: "Baixar CSV de anomalias",
    audit_log_csv: "Baixar log de auditoria",
    results_xlsx: "Baixar Excel completo",
  };
  return labels[raw] || raw;
}

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
