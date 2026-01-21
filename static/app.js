const state = {
  providers: [],
  literatureQueries: [],
  selectedIdeaId: null,
  selectedLiteratureId: null,
  selectedReviewId: null,
  localPdfs: [],
  runFormState: {
    ideaCount: "",
    topicFocus: "",
    topicExclude: "",
    literatureQueryId: "",
    useAssessmentSeeds: "",
  },
  llmSettings: {
    provider: "",
    model: "",
  },
  synthesisCache: {
    queryId: null,
    title: "",
    content: "",
  },
  llmAssessmentState: {},
};

const MODE_COPY = {
  idea: {
    title: "Idea Lab",
    subtitle: "Generate and vet breakthrough IPE ideas with gates and dossiers.",
  },
  "review-paper": {
    title: "Paper Review",
    subtitle: "Grounded APSR-level critique with section-anchored revisions.",
  },
  "review-project": {
    title: "Project Review",
    subtitle: "Level-aware review for IC, Mestrado, Doutorado, and Research Grant.",
  },
  setup: {
    title: "Session Setup",
    subtitle: "Unlock access and save provider credentials before choosing a workflow.",
  },
};

const REVIEW_PERSONA_LABELS = {
  theory_positioning: "Theory & Positioning",
  identification_design: "Identification & Design",
  measurement_constructs: "Measurement & Constructs",
  contribution_agenda: "Contribution & Agenda",
  feasibility_clarity: "Feasibility & Clarity",
  evidence_robustness: "Evidence & Robustness",
};

function formatPersonaLabel(persona) {
  if (!persona) {
    return "Reviewer";
  }
  return REVIEW_PERSONA_LABELS[persona] || persona;
}

function formatPersonaShort(entry) {
  if (!entry) {
    return "";
  }
  const label = formatPersonaLabel(entry.persona);
  if (entry.slot) {
    return `R${entry.slot}: ${label}`;
  }
  return label;
}

function setMode(mode) {
  const normalized = MODE_COPY[mode] ? mode : "select";
  document.body.dataset.mode = normalized;

  document.querySelectorAll("[data-mode]").forEach((panel) => {
    const modes = panel.dataset.mode.split(" ");
    const shouldShow = modes.includes("all") || modes.includes(normalized);
    panel.hidden = !shouldShow;
  });

  const selector = document.getElementById("mode-select");
  const workspace = document.getElementById("mode-workspace");
  const synthesisView = document.getElementById("synthesis-view");
  if (synthesisView) {
    synthesisView.hidden = true;
  }
  if (selector && workspace) {
    const isSelect = normalized === "select";
    selector.hidden = !isSelect;
    workspace.hidden = isSelect;
  }

  const copy = MODE_COPY[normalized];
  if (copy) {
    const title = document.getElementById("mode-title");
    const subtitle = document.getElementById("mode-subtitle");
    if (title) {
      title.textContent = copy.title;
    }
    if (subtitle) {
      subtitle.textContent = copy.subtitle;
    }
  }

  const typeSelect = document.getElementById("review-type");
  if (typeSelect) {
    if (normalized === "review-paper") {
      typeSelect.value = "paper";
      typeSelect.disabled = true;
    } else if (normalized === "review-project") {
      typeSelect.value = "project";
      typeSelect.disabled = true;
    } else {
      typeSelect.disabled = false;
    }
    updateReviewLevelVisibility();
  }

  localStorage.setItem("codexcouncil-mode", normalized);
  if (normalized !== "select" && normalized !== "setup") {
    localStorage.setItem("codexcouncil-last-mode", normalized);
  }
  window.scrollTo({ top: 0, behavior: "auto" });
}

function showSynthesisView() {
  const view = document.getElementById("synthesis-view");
  const workspace = document.getElementById("mode-workspace");
  if (!view || !workspace) {
    return;
  }
  view.hidden = false;
  workspace.hidden = true;
  const title = document.getElementById("synthesis-title");
  const subtitle = document.getElementById("synthesis-subtitle");
  const content = document.getElementById("synthesis-content");
  if (title) {
    title.textContent = state.synthesisCache.title || "Synthesis";
  }
  if (subtitle) {
    subtitle.textContent = state.synthesisCache.queryId
      ? `Query #${state.synthesisCache.queryId}`
      : "Select a query to view its synthesis.";
  }
  if (content) {
    if (state.synthesisCache.content) {
      content.innerHTML = `<pre>${state.synthesisCache.content}</pre>`;
    } else {
      content.innerHTML = "<p>No synthesis loaded.</p>";
    }
  }
  window.scrollTo({ top: 0, behavior: "auto" });
}

function hideSynthesisView() {
  const view = document.getElementById("synthesis-view");
  const workspace = document.getElementById("mode-workspace");
  if (!view || !workspace) {
    return;
  }
  view.hidden = true;
  workspace.hidden = false;
  window.scrollTo({ top: 0, behavior: "auto" });
}

function initModeSwitcher() {
  document.querySelectorAll("[data-mode-target]").forEach((card) => {
    card.addEventListener("click", () => setMode(card.dataset.modeTarget));
  });
  const switcher = document.getElementById("mode-switch");
  if (switcher) {
    switcher.addEventListener("click", () => setMode("select"));
  }
  const homeLink = document.getElementById("home-link");
  if (homeLink) {
    homeLink.addEventListener("click", () => setMode("select"));
  }
  const sessionCta = document.getElementById("session-cta");
  if (sessionCta) {
    sessionCta.addEventListener("click", () => {
      const status = document.getElementById("session-status");
      const isLocked = status ? status.dataset.state !== "unlocked" : true;
      if (document.body.dataset.mode === "select") {
        setMode("setup");
      }
      const sessionPanel = document.getElementById("session-control");
      if (sessionPanel) {
        sessionPanel.scrollIntoView({ behavior: "smooth", block: "start" });
      }
      const passphraseInput = document.getElementById("passphrase");
      if (passphraseInput && isLocked) {
        setTimeout(() => passphraseInput.focus(), 250);
      }
    });
  }
  const synthesisBack = document.getElementById("synthesis-back");
  if (synthesisBack) {
    synthesisBack.addEventListener("click", hideSynthesisView);
  }
  const saved = localStorage.getItem("codexcouncil-mode");
  setMode(saved || "select");
}

async function fetchJSON(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || "Request failed");
  }
  return response.json();
}

async function uploadFile(url, file) {
  const body = new FormData();
  body.append("file", file);
  const response = await fetch(url, {
    method: "POST",
    body,
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || "Upload failed");
  }
  return response.json();
}

function setSessionStatus(text, isUnlocked = false) {
  const status = document.getElementById("session-status");
  if (!status) {
    return;
  }
  status.textContent = text;
  status.dataset.state = isUnlocked ? "unlocked" : "locked";
  const passphraseInput = document.getElementById("passphrase");
  const unlockButton = document.getElementById("unlock-button");
  const sessionCta = document.getElementById("session-cta");
  if (isUnlocked) {
    if (passphraseInput) {
      passphraseInput.value = "";
      passphraseInput.placeholder = "Session unlocked";
      passphraseInput.disabled = true;
    }
    if (unlockButton) {
      unlockButton.textContent = "Unlocked";
      unlockButton.disabled = true;
    }
    if (sessionCta) {
      sessionCta.textContent = "Session unlocked";
      sessionCta.disabled = true;
    }
  } else {
    if (passphraseInput) {
      passphraseInput.disabled = false;
      passphraseInput.placeholder = "Enter passphrase";
    }
    if (unlockButton) {
      unlockButton.textContent = "Unlock";
      unlockButton.disabled = false;
    }
    if (sessionCta) {
      sessionCta.textContent = "Unlock session";
      sessionCta.disabled = false;
    }
  }
}

async function loadProviders() {
  const data = await fetchJSON("/api/providers");
  state.providers = data;
  const credentialSelect = document.getElementById("provider");
  const globalProvider = document.getElementById("global-provider");
  const globalModel = document.getElementById("global-model");
  const selectedProvider = credentialSelect?.value || "";
  const savedGlobal = state.llmSettings.provider;
  const providerSelects = [
    credentialSelect,
    globalProvider,
  ];
  providerSelects.forEach((select) => {
    if (!select) {
      return;
    }
    select.innerHTML = "";
    data.forEach((provider) => {
      const option = document.createElement("option");
      option.value = provider.name;
      option.textContent = provider.name;
      select.appendChild(option);
    });
  });

  if (selectedProvider) {
    credentialSelect.value = selectedProvider;
  }
  if (globalProvider) {
    if (savedGlobal) {
      globalProvider.value = savedGlobal;
    }
    globalProvider.addEventListener("change", () => {
      const selected = state.providers.find((p) => p.name === globalProvider.value);
      if (globalModel) {
        globalModel.placeholder = selected ? selected.default_model : "Default";
        if (!globalModel.value && selected && selected.default_model) {
          globalModel.value = selected.default_model;
        }
      }
      captureLlmSettings();
      saveLlmSettings();
    });
  }
  if (globalModel) {
    globalModel.value = state.llmSettings.model || "";
  }
  if (state.providers.length && globalProvider) {
    const selected = state.providers.find((p) => p.name === globalProvider.value) || state.providers[0];
    if (globalProvider && !globalProvider.value) {
      globalProvider.value = selected.name;
    }
    if (globalModel) {
      globalModel.placeholder = selected.default_model || "Default";
      if (!globalModel.value && selected.default_model) {
        globalModel.value = selected.default_model;
      }
    }
  }
}

async function loadCredentials() {
  const list = document.getElementById("credential-list");
  list.innerHTML = "";
  const data = await fetchJSON("/api/credentials");
  data.forEach((cred) => {
    const item = document.createElement("div");
    item.className = "list-item";
    item.innerHTML = `<strong>${cred.provider}</strong>${cred.name || ""} <span>${cred.created_at}</span>`;
    list.appendChild(item);
  });
}

async function loadRuns() {
  const list = document.getElementById("run-list");
  list.innerHTML = "";
  const data = await fetchJSON("/api/runs");
  data.forEach((run) => {
    const item = document.createElement("div");
    item.className = "list-item";
    const excludedCount = run.topic_exclude
      ? run.topic_exclude.split(";").map((entry) => entry.trim()).filter(Boolean).length
      : 0;
    const focusLine = run.topic_focus || (excludedCount ? `Excluded topics: ${excludedCount}` : "No topic focus");
    item.innerHTML = `
      <strong>Run #${run.id} - ${run.status}</strong>
      <div>${run.provider} / ${run.model}</div>
      <div>${run.created_at}</div>
      <div>${focusLine}</div>
    `;
    list.appendChild(item);
  });
}

async function loadIdeas() {
  const list = document.getElementById("idea-list");
  list.innerHTML = "";
  const statusFilter = document.getElementById("idea-status-filter");
  const filterValue = statusFilter ? statusFilter.value : "all";
  const data = await fetchJSON("/api/ideas");
  const filtered = data.filter((idea) => {
    if (filterValue === "all") {
      return true;
    }
    if (filterValue === "resubmitted") {
      return idea.status === "resubmitted";
    }
    if (filterValue === "none") {
      return !idea.status;
    }
    if (filterValue === "other") {
      return idea.status && idea.status !== "resubmitted";
    }
    return true;
  });
  filtered.forEach((idea) => {
    const item = document.createElement("div");
    item.className = "list-item";
    if (idea.id === state.selectedIdeaId) {
      item.classList.add("selected");
    }
    const statusPill = idea.status ? `<span class="status-pill">${idea.status}</span>` : "";
    item.innerHTML = `
      <div class="list-title"><strong>${idea.title || "Untitled Idea"}</strong>${statusPill}</div>
      <div>Run #${idea.run_id} | ${idea.lane_primary || "No lane"} | ${idea.breakthrough_type || "No breakthrough type"}</div>
      <div>${idea.big_claim || ""}</div>
    `;
    item.addEventListener("click", () => loadIdeaDetail(idea.id));
    list.appendChild(item);
  });
}

function updateReviewLevelVisibility() {
  const typeSelect = document.getElementById("review-type");
  const levelWrapper = document.getElementById("review-level-wrapper");
  if (!typeSelect || !levelWrapper) {
    return;
  }
  const isProject = typeSelect.value === "project";
  levelWrapper.style.display = isProject ? "block" : "none";
}

async function loadReviews() {
  const list = document.getElementById("review-list");
  if (!list) {
    return;
  }
  list.innerHTML = "";
  const data = await fetchJSON("/api/reviews");
  data.forEach((review) => {
    const item = document.createElement("div");
    item.className = "list-item";
    if (review.id === state.selectedReviewId) {
      item.classList.add("selected");
    }
    const level = review.level ? ` | ${review.level}` : "";
    const personaLine = (review.personas || []).length
      ? `<div>${review.personas.map(formatPersonaShort).join(" | ")}</div>`
      : "";
    item.innerHTML = `
      <strong>${review.title || "Untitled Review"}</strong>
      <div>${review.review_type}${level}</div>
      ${personaLine}
      <div>${review.created_at}</div>
    `;
    item.addEventListener("click", () => loadReviewDetail(review.id));
    list.appendChild(item);
  });
}

async function loadReviewDetail(reviewId) {
  state.selectedReviewId = reviewId;
  const detail = document.getElementById("review-detail");
  const warning = document.getElementById("review-warning");
  if (!detail) {
    return;
  }
  detail.innerHTML = "<p>Loading review...</p>";
  if (warning) {
    warning.textContent = "";
  }
  const data = await fetchJSON(`/api/reviews/${reviewId}`);
  const review = data.review;
  const sections = (data.sections || [])
    .map((section) => `${section.section_id} ${section.title} (p${section.page_start}-${section.page_end})`)
    .join("\n");
  const artifactText = (data.artifacts || []).map((a) => a.content).join("\n");
  if (warning && artifactText.includes("VALIDATION_NOTES")) {
    warning.textContent = "Review output failed validation; see notes in checklist.";
  }

  const formatKind = (kind) =>
    kind
      .toLowerCase()
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");

  const stripArtifactHeading = (content, kind) => {
    if (!content) {
      return "";
    }
    const lines = content.split(/\r?\n/);
    let start = 0;
    while (start < lines.length && !lines[start].trim()) {
      start += 1;
    }
    const first = (lines[start] || "").trim();
    const normalizedKind = kind.replace(/_/g, " ").toUpperCase();
    const normalizedFirst = first.replace(/\s+/g, " ").toUpperCase();
    if (normalizedFirst.startsWith(normalizedKind)) {
      start += 1;
    }
    const cleaned = lines.slice(start).join("\n").trim();
    return cleaned || content.trim();
  };

  const grouped = new Map();
  (data.artifacts || []).forEach((artifact) => {
    const key = `${artifact.slot || 0}|${artifact.persona || ""}`;
    if (!grouped.has(key)) {
      grouped.set(key, {
        slot: artifact.slot,
        persona: artifact.persona,
        items: [],
      });
    }
    grouped.get(key).items.push(artifact);
  });

  const sortKinds = (items) => {
    const order = {
      REFEREE_MEMO: 1,
      REVISION_CHECKLIST: 2,
    };
    return items.sort((a, b) => (order[a.kind] || 99) - (order[b.kind] || 99));
  };

  const artifactBlocks = Array.from(grouped.values())
    .sort((a, b) => (a.slot || 0) - (b.slot || 0))
    .map((group) => {
      const personaLabel = group.persona ? formatPersonaLabel(group.persona) : "Review Output";
      const heading = group.slot ? `Reviewer ${group.slot} — ${personaLabel}` : personaLabel;
      const items = sortKinds(group.items)
        .map((artifact) => {
          const label = formatKind(artifact.kind);
          const content = stripArtifactHeading(artifact.content || "", artifact.kind);
          return `<div class="artifact-block"><h4>${label}</h4><pre>${content || "No content yet."}</pre></div>`;
        })
        .join("");
      return `<div class="artifact-group"><h4>${heading}</h4>${items}</div>`;
    })
    .join("");

  const levelLine = review.level ? `<div>Level: ${review.level}</div>` : "";
  detail.innerHTML = `
    <h4>${review.title || "Untitled Review"}</h4>
    <div>Type: ${review.review_type}</div>
    ${levelLine}
    <div>Language: ${review.language || "en"}</div>
    <h4>Section Index</h4>
    <div class="hint">Used to anchor checklist quotes and validation.</div>
    <pre>${sections || "No sections yet."}</pre>
    <h4>Artifacts</h4>
    ${artifactBlocks || "<p>No artifacts yet.</p>"}
  `;
}

async function loadLiteratureQueries() {
  const list = document.getElementById("literature-list");
  if (!list) {
    return;
  }
  list.innerHTML = "";
  const data = await fetchJSON("/api/literature/queries");
  state.literatureQueries = data;
  const runLiterature = document.getElementById("run-literature");
  if (runLiterature) {
    const selected = runLiterature.value;
    runLiterature.innerHTML = `<option value="">No synthesis</option>`;
    data.forEach((query) => {
      const option = document.createElement("option");
      option.value = query.id;
      option.textContent = `#${query.id} ${query.query}`;
      runLiterature.appendChild(option);
    });
    if (selected) {
      runLiterature.value = selected;
    }
  }
  data.forEach((query) => {
    const item = document.createElement("div");
    item.className = "list-item";
    if (query.id === state.selectedLiteratureId) {
      item.classList.add("selected");
    }
    item.innerHTML = `
      <strong>${query.query}</strong>
      <div>${query.sources}</div>
      <div>Status: ${query.status}</div>
    `;
    item.addEventListener("click", () => {
      if (state.selectedLiteratureId === query.id) {
        clearLiteratureDetail();
        loadLiteratureQueries();
        return;
      }
      loadLiteratureDetail(query.id);
    });
    list.appendChild(item);
  });
}

async function loadLiteratureDetail(queryId) {
  state.selectedLiteratureId = queryId;
  const detail = document.getElementById("literature-detail");
  const worksOutput = document.getElementById("literature-works-output");
  const existingDocs = detail.querySelector("#llm-docs")?.value || "";
  const existingTokens = detail.querySelector("#llm-tokens")?.value || "";
  state.llmAssessmentState[queryId] = {
    maxDocs: existingDocs,
    tokenBudget: existingTokens,
  };
  detail.innerHTML = "";
  if (worksOutput) {
    worksOutput.innerHTML = "<p>Loading works...</p>";
  }
  await loadLocalPdfs(queryId);
  const data = await fetchJSON(`/api/literature/queries/${queryId}`);
  const header = document.createElement("div");
  header.innerHTML = `
    <h4>${data.query.query}</h4>
    <p>Status: ${data.query.status} | Query ID: ${data.query.id}</p>
  `;
  detail.appendChild(header);

  const actionRow = document.createElement("div");
  actionRow.className = "attach-row";
  actionRow.innerHTML = `
    <button type="button" data-view>View Synthesis</button>
    <button type="button" data-delete class="button-secondary">Delete Query</button>
    <button type="button" data-cleanup class="button-secondary">Remove Books/Chapters</button>
  `;
  const viewButton = actionRow.querySelector("[data-view]");
  viewButton.addEventListener("click", () => {
    showSynthesisView();
  });
  const deleteButton = actionRow.querySelector("[data-delete]");
  deleteButton.addEventListener("click", async () => {
    if (!confirm("Delete this query and its stored metadata/PDF links?")) {
      return;
    }
    try {
      await fetchJSON(`/api/literature/queries/${queryId}`, { method: "DELETE" });
      clearLiteratureDetail();
      await loadLiteratureQueries();
    } catch (error) {
      alert(error.message);
    }
  });
  detail.appendChild(actionRow);

  const llmRow = document.createElement("div");
  llmRow.className = "action-row llm-row";
  const llmButton = document.createElement("button");
  llmButton.type = "button";
  llmButton.textContent = "Run Synthesis";
  const docInput = document.createElement("input");
  docInput.type = "number";
  docInput.min = "1";
  docInput.max = "20";
  docInput.value = "8";
  docInput.title = "Max docs";
  docInput.id = "llm-docs";
  const tokenInput = document.createElement("input");
  tokenInput.type = "number";
  tokenInput.min = "10000";
  tokenInput.max = "200000";
  tokenInput.value = "100000";
  tokenInput.title = "Token budget";
  tokenInput.id = "llm-tokens";
  const savedState = state.llmAssessmentState[queryId];
  if (savedState) {
    if (savedState.maxDocs) {
      docInput.value = savedState.maxDocs;
    }
    if (savedState.tokenBudget) {
      tokenInput.value = savedState.tokenBudget;
    }
  }
  const llmMeta = document.createElement("div");
  llmMeta.className = "hint";
  const llmSettings = getLlmSettings();
  llmMeta.textContent = llmSettings.provider
    ? `Uses LLM: ${llmSettings.provider}${llmSettings.model ? ` (${llmSettings.model})` : ""}`
    : "Select an LLM provider in Session Control.";
  llmButton.addEventListener("click", async () => {
    if (!confirm("Run LLM synthesis on available abstracts/full text?")) {
      return;
    }
    try {
      const llm = getLlmSettings();
      if (!llm.provider) {
        alert("Select an LLM provider in Session Control.");
        return;
      }
      const payload = {
        provider: llm.provider,
        model: llm.model || null,
        max_docs: parseInt(docInput.value, 10) || 8,
        max_tokens_budget: parseInt(tokenInput.value, 10) || 100000,
      };
      await fetchJSON(`/api/literature/queries/${queryId}/assessment/llm`, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      await loadLiteratureDetail(queryId);
    } catch (error) {
      alert(error.message);
    }
  });
  llmRow.appendChild(llmButton);
  llmRow.appendChild(docInput);
  llmRow.appendChild(tokenInput);
  llmRow.appendChild(llmMeta);
  detail.appendChild(llmRow);

  [docInput, tokenInput].forEach((field) => {
    field.addEventListener("input", () => {
      state.llmAssessmentState[queryId] = {
        maxDocs: docInput.value,
        tokenBudget: tokenInput.value,
      };
    });
    field.addEventListener("change", () => {
      state.llmAssessmentState[queryId] = {
        maxDocs: docInput.value,
        tokenBudget: tokenInput.value,
      };
    });
  });

  const cleanupButton = actionRow.querySelector("[data-cleanup]");
  cleanupButton.addEventListener("click", async () => {
    if (!confirm("Remove all book/chapter results from this query?")) {
      return;
    }
    try {
      await fetchJSON(`/api/literature/queries/${queryId}/cleanup`, { method: "POST" });
      await loadLiteratureDetail(queryId);
    } catch (error) {
      alert(error.message);
    }
  });

  state.synthesisCache = {
    queryId: data.query.id,
    title: data.query.query,
    content: data.assessment || "",
  };

  if (worksOutput) {
    if (data.works.length) {
      worksOutput.innerHTML = "<h4>Works</h4>";
      data.works.forEach((work) => {
        const block = document.createElement("div");
        block.className = "list-item";
        const pdfStatus = work.pdf_path
          ? "PDF ingested"
          : work.open_access_url
            ? "OA link available"
            : "No PDF";
        const yearLabel = work.year ? `Year: ${work.year}` : "Year: unknown";
        const venueLabel = work.venue ? `Journal: ${work.venue}` : "Journal: unknown";
        const sourceLabel = work.source ? `Source: ${work.source}` : "";
        const typeLabel = work.work_type ? `Type: ${work.work_type}` : "";
        block.innerHTML = `
          <strong>${work.title}</strong>
          <div>${work.authors || ""}</div>
          <div>${[yearLabel, venueLabel].join(" | ")}</div>
          <div>${[sourceLabel, typeLabel].filter(Boolean).join(" | ")}</div>
          <div>${work.doi || ""}</div>
          <div>${pdfStatus}</div>
        `;
        if (work.pdf_path) {
          const detachRow = document.createElement("div");
          detachRow.className = "attach-row";
          detachRow.innerHTML = `
            <button type="button" data-detach class="button-secondary">Detach PDF</button>
          `;
          detachRow.querySelector("[data-detach]").addEventListener("click", async () => {
            if (!confirm("Detach the PDF from this work?")) {
              return;
            }
            try {
              await fetchJSON(`/api/literature/works/${work.id}/attach-pdf`, { method: "DELETE" });
              await loadLiteratureDetail(queryId);
            } catch (error) {
              alert(error.message);
            }
          });
          block.appendChild(detachRow);
        } else if (state.localPdfs.length) {
          const attachWrap = document.createElement("div");
          attachWrap.className = "attach-row";
          attachWrap.innerHTML = `
            <select data-attach-select></select>
            <button type="button" data-attach-button>Attach PDF</button>
          `;
          const select = attachWrap.querySelector("[data-attach-select]");
          state.localPdfs.forEach((name) => {
            const option = document.createElement("option");
            option.value = name;
            option.textContent = name;
            select.appendChild(option);
          });
          const button = attachWrap.querySelector("[data-attach-button]");
          button.addEventListener("click", async () => {
            try {
              await fetchJSON(`/api/literature/works/${work.id}/attach-pdf`, {
                method: "POST",
                body: JSON.stringify({ filename: select.value }),
              });
              await loadLiteratureDetail(queryId);
            } catch (error) {
              alert(error.message);
            }
          });
          block.appendChild(attachWrap);
        }
        const removeRow = document.createElement("div");
        removeRow.className = "attach-row";
        removeRow.innerHTML = `
          <button type="button" data-remove class="button-secondary">Remove Result</button>
        `;
        removeRow.querySelector("[data-remove]").addEventListener("click", async () => {
          if (!confirm("Remove this result from the query?")) {
            return;
          }
          try {
            await fetchJSON(`/api/literature/works/${work.id}`, { method: "DELETE" });
            await loadLiteratureDetail(queryId);
          } catch (error) {
            alert(error.message);
          }
        });
        block.appendChild(removeRow);
        worksOutput.appendChild(block);
      });
    } else {
      worksOutput.innerHTML = "<p>No works loaded.</p>";
    }
  }
}

function clearLiteratureDetail() {
  state.selectedLiteratureId = null;
  const detail = document.getElementById("literature-detail");
  if (detail) {
    detail.innerHTML = "<p>No query selected.</p>";
  }
  const worksOutput = document.getElementById("literature-works-output");
  if (worksOutput) {
    worksOutput.innerHTML = "<p>No works loaded.</p>";
  }
  state.synthesisCache = { queryId: null, title: "", content: "" };
}

async function loadLocalPdfs(queryId) {
  try {
    state.localPdfs = await fetchJSON(`/api/literature/queries/${queryId}/local-pdfs`);
  } catch (error) {
    state.localPdfs = [];
  }
}

async function loadIdeaDetail(ideaId) {
  state.selectedIdeaId = ideaId;
  const detail = document.getElementById("idea-detail");
  detail.innerHTML = "";
  const data = await fetchJSON(`/api/ideas/${ideaId}`);
  const header = document.createElement("div");
  const headerStatus = data.idea.status ? `<span class="status-pill">${data.idea.status}</span>` : "";
  header.innerHTML = `<div class="detail-title"><h3>${data.idea.title || "Untitled Idea"}</h3>${headerStatus}</div>`;
  detail.appendChild(header);
  if (data.idea.status === "resubmitted") {
    const statusMeta = document.createElement("div");
    statusMeta.className = "status-meta";
    statusMeta.textContent = `Last resubmitted: ${data.idea.updated_at}`;
    detail.appendChild(statusMeta);
  }

  if (data.gates && data.gates.length) {
    const gateSection = document.createElement("div");
    gateSection.innerHTML = "<h4>Gate Status</h4>";
    const gateGrid = document.createElement("div");
    gateGrid.className = "gate-grid";
    data.gates.sort((a, b) => a.gate - b.gate).forEach((gate) => {
      const gateCard = document.createElement("div");
      gateCard.className = "gate-card";
      gateCard.innerHTML = `
        <div class="gate-title">Gate ${gate.gate}</div>
        <label>Status</label>
        <select data-gate-status>
          <option value="passed">passed</option>
          <option value="failed">failed</option>
          <option value="needs_revision">needs_revision</option>
        </select>
        <label>Notes</label>
        <textarea data-gate-notes rows="3" placeholder="Add notes..."></textarea>
        <button type="button" data-gate-save>Save</button>
      `;
      const statusSelect = gateCard.querySelector("[data-gate-status]");
      statusSelect.value = gate.status;
      const notesField = gateCard.querySelector("[data-gate-notes]");
      notesField.value = gate.notes || "";
      const saveButton = gateCard.querySelector("[data-gate-save]");
      saveButton.addEventListener("click", async () => {
        try {
          const payload = {
            status: statusSelect.value,
            notes: notesField.value || null,
          };
          await fetchJSON(`/api/ideas/${ideaId}/gates/${gate.gate}`, {
            method: "PUT",
            body: JSON.stringify(payload),
          });
        } catch (error) {
          alert(error.message);
        }
      });
      gateGrid.appendChild(gateCard);
    });
    gateSection.appendChild(gateGrid);
    detail.appendChild(gateSection);
  }

  const councilActions = document.createElement("div");
  councilActions.innerHTML = "<h4>Council Actions</h4>";
  const actionRow = document.createElement("div");
  actionRow.className = "action-row";
  const reviseButton = document.createElement("button");
  reviseButton.type = "button";
  reviseButton.className = "button-secondary";
  reviseButton.textContent = "Resubmit to Council";
  const reviewToggle = document.createElement("label");
  reviewToggle.className = "inline-toggle";
  reviewToggle.innerHTML = `<input type="checkbox" id="council-review-toggle" /> Run council re-review`;
  const providerSelect = document.createElement("select");
  providerSelect.id = "council-provider";
  state.providers.forEach((provider) => {
    const option = document.createElement("option");
    option.value = provider.name;
    option.textContent = provider.name;
    providerSelect.appendChild(option);
  });
  const modelInput = document.createElement("input");
  modelInput.type = "text";
  modelInput.id = "council-model";
  modelInput.placeholder = state.providers[0]?.default_model || "Default";
  providerSelect.addEventListener("change", () => {
    const selected = state.providers.find((p) => p.name === providerSelect.value);
    modelInput.placeholder = selected ? selected.default_model : "Default";
  });
  reviseButton.addEventListener("click", async () => {
    if (!confirm("Apply council revisions and resubmit this idea?")) {
      return;
    }
    try {
      const runReview = document.getElementById("council-review-toggle").checked;
      const payload = {
        run_review: runReview,
        apply_revisions: true,
        provider: runReview ? providerSelect.value : null,
        model: runReview ? (modelInput.value || null) : null,
      };
      const result = await fetchJSON(`/api/ideas/${ideaId}/council/resubmit`, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      const reviewStatus = result.review_ran ? "Council review updated." : "Council review not run.";
      alert(`Resubmitted (version ${result.version_id}). ${reviewStatus}`);
      await loadIdeaDetail(ideaId);
    } catch (error) {
      alert(error.message);
    }
  });
  actionRow.appendChild(reviseButton);
  actionRow.appendChild(reviewToggle);
  actionRow.appendChild(providerSelect);
  actionRow.appendChild(modelInput);
  councilActions.appendChild(actionRow);
  detail.appendChild(councilActions);

  const versionSection = document.createElement("div");
  versionSection.innerHTML = "<h4>Version History</h4>";
  const versionRow = document.createElement("div");
  versionRow.className = "action-row";
  const versions = await fetchJSON(`/api/ideas/${ideaId}/versions`);
  const versionSelect = document.createElement("select");
  versionSelect.id = "idea-version-select";
  versions.forEach((version) => {
    const option = document.createElement("option");
    const label = version.label ? ` - ${version.label}` : "";
    const created = version.created_at ? ` (${version.created_at})` : "";
    option.value = version.id;
    option.textContent = `${version.id}${label}${created}`;
    versionSelect.appendChild(option);
  });
  const viewButton = document.createElement("button");
  viewButton.type = "button";
  viewButton.textContent = "View Version";
  viewButton.addEventListener("click", async () => {
    if (!versionSelect.value) {
      return;
    }
    const versionData = await fetchJSON(`/api/ideas/${ideaId}/versions/${versionSelect.value}`);
    const versionDetail = document.getElementById("version-detail");
    versionDetail.innerHTML = `<h4>Version ${versionData.id}</h4><pre>${versionData.metadata || ""}</pre>`;
    versionData.dossier_parts.forEach((part) => {
      const block = document.createElement("div");
      block.innerHTML = `<h5>${part.kind}</h5><pre>${part.content}</pre>`;
      versionDetail.appendChild(block);
    });
    if (versionData.council_memos.length) {
      const memoHeader = document.createElement("h5");
      memoHeader.textContent = "Council Memos (Snapshot)";
      versionDetail.appendChild(memoHeader);
      versionData.council_memos.forEach((memo) => {
        const block = document.createElement("div");
        block.innerHTML = `<h6>${memo.referee}</h6><pre>${memo.content}</pre>`;
        versionDetail.appendChild(block);
      });
    }
  });
  if (versions.length) {
    versionRow.appendChild(versionSelect);
    versionRow.appendChild(viewButton);
    versionSection.appendChild(versionRow);
  } else {
    const empty = document.createElement("div");
    empty.className = "hint";
    empty.textContent = "No version snapshots yet.";
    versionSection.appendChild(empty);
  }
  const versionDetail = document.createElement("div");
  versionDetail.id = "version-detail";
  versionDetail.className = "detail version-detail";
  versionSection.appendChild(versionDetail);
  detail.appendChild(versionSection);

  const compactKinds = new Set(["PITCH", "DATA_PLAN", "POSITIONING", "NEXT_STEPS"]);
  data.dossier_parts.forEach((part) => {
    const block = document.createElement("div");
    block.className = "dossier-block";

    const headerRow = document.createElement("div");
    headerRow.className = "dossier-header";
    const title = document.createElement("h4");
    title.textContent = part.kind;
    headerRow.appendChild(title);

    const content = document.createElement("div");
    content.className = "dossier-content";
    content.textContent = part.content;

    if (compactKinds.has(part.kind)) {
      content.classList.add("collapsed");
      const toggle = document.createElement("button");
      toggle.type = "button";
      toggle.className = "button-ghost";
      toggle.textContent = "Expand";
      toggle.addEventListener("click", () => {
        const expanded = content.classList.toggle("expanded");
        content.classList.toggle("collapsed", !expanded);
        toggle.textContent = expanded ? "Collapse" : "Expand";
      });
      headerRow.appendChild(toggle);
    }

    block.appendChild(headerRow);
    block.appendChild(content);
    detail.appendChild(block);
  });

  const memoHeader = document.createElement("h4");
  memoHeader.textContent = "Council Memos";
  detail.appendChild(memoHeader);
  const rounds = await fetchJSON(`/api/ideas/${ideaId}/council/rounds`);
  if (rounds.length) {
    const roundRow = document.createElement("div");
    roundRow.className = "action-row";
    const roundSelect = document.createElement("select");
    rounds.forEach((round) => {
      const option = document.createElement("option");
      const status = round.status ? ` - ${round.status}` : "";
      option.value = round.id;
      option.textContent = `Round ${round.round_number}${status} (${round.created_at})`;
      roundSelect.appendChild(option);
    });
    const roundNote = document.createElement("div");
    roundNote.className = "hint";
    roundNote.textContent = rounds[0].notes || "";
    roundSelect.addEventListener("change", async () => {
      const roundData = await fetchJSON(`/api/ideas/${ideaId}/council/rounds/${roundSelect.value}`);
      roundNote.textContent = roundData.round.notes || "";
      renderCouncilMemos(roundData.memos, detail);
    });
    roundRow.appendChild(roundSelect);
    roundRow.appendChild(roundNote);
    detail.appendChild(roundRow);
    const roundData = await fetchJSON(`/api/ideas/${ideaId}/council/rounds/${rounds[0].id}`);
    renderCouncilMemos(roundData.memos, detail);
  } else if (data.council_memos.length) {
    renderCouncilMemos(data.council_memos, detail);
  }
}

function renderCouncilMemos(memos, container) {
  const existing = container.querySelectorAll(".council-memo");
  existing.forEach((node) => node.remove());
  memos.forEach((memo) => {
    const block = document.createElement("div");
    block.className = "council-memo";
    block.innerHTML = `<h5>${memo.referee}</h5><pre>${memo.content}</pre>`;
    container.appendChild(block);
  });
}

function captureLlmSettings() {
  const provider = document.getElementById("global-provider");
  const model = document.getElementById("global-model");
  if (!provider || !model) {
    return;
  }
  state.llmSettings = {
    provider: provider.value,
    model: model.value,
  };
}

function saveLlmSettings() {
  try {
    localStorage.setItem("llmSettings", JSON.stringify(state.llmSettings));
  } catch (error) {
    console.warn("Could not save LLM settings", error);
  }
}

function loadLlmSettings() {
  try {
    const raw = localStorage.getItem("llmSettings");
    if (raw) {
      state.llmSettings = JSON.parse(raw);
    }
  } catch (error) {
    console.warn("Could not load LLM settings", error);
  }
}

function restoreLlmSettings() {
  const provider = document.getElementById("global-provider");
  const model = document.getElementById("global-model");
  if (!provider || !model) {
    return;
  }
  if (state.llmSettings.provider) {
    provider.value = state.llmSettings.provider;
  }
  model.value = state.llmSettings.model || "";
}

function getLlmSettings() {
  const provider = document.getElementById("global-provider")?.value || "";
  const model = document.getElementById("global-model")?.value || "";
  return { provider, model };
}

function captureRunFormState() {
  const ideaCount = document.getElementById("idea-count");
  const topicFocus = document.getElementById("topic-focus");
  const topicExclude = document.getElementById("topic-exclude");
  const literatureQuery = document.getElementById("run-literature");
  const useAssessmentSeeds = document.getElementById("use-assessment-seeds");
  if (!ideaCount || !topicFocus || !topicExclude || !literatureQuery || !useAssessmentSeeds) {
    return;
  }
  state.runFormState = {
    ideaCount: ideaCount.value,
    topicFocus: topicFocus.value,
    topicExclude: topicExclude.value,
    literatureQueryId: literatureQuery.value,
    useAssessmentSeeds: useAssessmentSeeds.value,
  };
}

function saveRunFormState() {
  try {
    localStorage.setItem("runFormState", JSON.stringify(state.runFormState));
  } catch (error) {
    console.warn("Could not save form state", error);
  }
}

function loadRunFormState() {
  try {
    const raw = localStorage.getItem("runFormState");
    if (raw) {
      state.runFormState = JSON.parse(raw);
    }
  } catch (error) {
    console.warn("Could not load form state", error);
  }
}

function restoreRunFormState() {
  const ideaCount = document.getElementById("idea-count");
  const topicFocus = document.getElementById("topic-focus");
  const topicExclude = document.getElementById("topic-exclude");
  const literatureQuery = document.getElementById("run-literature");
  const useAssessmentSeeds = document.getElementById("use-assessment-seeds");
  if (!ideaCount || !topicFocus || !topicExclude || !literatureQuery || !useAssessmentSeeds) {
    return;
  }
  if (state.runFormState.ideaCount) {
    ideaCount.value = state.runFormState.ideaCount;
  }
  topicFocus.value = state.runFormState.topicFocus;
  topicExclude.value = state.runFormState.topicExclude || "";
  if (state.runFormState.literatureQueryId) {
    literatureQuery.value = state.runFormState.literatureQueryId;
  }
  if (state.runFormState.useAssessmentSeeds) {
    useAssessmentSeeds.value = state.runFormState.useAssessmentSeeds;
  }
}

function isFormActive() {
  const active = document.activeElement;
  if (!active) {
    return false;
  }
  return Boolean(active.closest && active.closest("form"));
}

function wireForms() {
  document.getElementById("unlock-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const passphrase = document.getElementById("passphrase").value;
    try {
      await fetchJSON("/api/session/unlock", {
        method: "POST",
        body: JSON.stringify({ passphrase }),
      });
      setSessionStatus("Session unlocked", true);
    } catch (error) {
      alert(error.message);
    }
  });

  document.getElementById("credentials-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const provider = document.getElementById("provider").value;
    const name = document.getElementById("provider-name").value;
    const apiKey = document.getElementById("api-key").value;
    try {
      await fetchJSON("/api/credentials", {
        method: "POST",
        body: JSON.stringify({ provider, name, api_key: apiKey }),
      });
      document.getElementById("api-key").value = "";
      await loadCredentials();
    } catch (error) {
      alert(error.message);
    }
  });

  const restartButton = document.getElementById("restart-server");
  if (restartButton) {
    restartButton.addEventListener("click", async () => {
      if (!confirm("Restart the server now?")) {
        return;
      }
      const message = document.getElementById("server-message");
      try {
        const port = window.location.port ? parseInt(window.location.port, 10) : 8000;
        await fetchJSON("/api/server/restart", {
          method: "POST",
          body: JSON.stringify({ port }),
        });
        message.textContent = "Server restarting...";
        setTimeout(() => window.location.reload(), 2000);
      } catch (error) {
        message.textContent = error.message;
      }
    });
  }

  document.getElementById("run-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const llm = getLlmSettings();
    const provider = llm.provider;
    const model = llm.model;
    const ideaCount = parseInt(document.getElementById("idea-count").value, 10);
    const topicFocus = document.getElementById("topic-focus").value;
    const topicExclude = document.getElementById("topic-exclude").value;
    const literatureQueryId = document.getElementById("run-literature").value;
    const useAssessmentSeeds = document.getElementById("use-assessment-seeds").value === "yes";
    const message = document.getElementById("run-message");
    if (!provider) {
      message.textContent = "Select an LLM provider in Session Control.";
      return;
    }
    try {
      const result = await fetchJSON("/api/runs", {
        method: "POST",
        body: JSON.stringify({
          provider,
          model: model || null,
          idea_count: ideaCount,
          topic_focus: topicFocus || null,
          topic_exclude: topicExclude || null,
          literature_query_id: literatureQueryId ? parseInt(literatureQueryId, 10) : null,
          use_assessment_seeds: useAssessmentSeeds,
        }),
      });
      message.textContent = `Run started: #${result.run_id}`;
      await loadRuns();
    } catch (error) {
      message.textContent = error.message;
    }
  });

  const literatureForm = document.getElementById("literature-form");
  if (literatureForm) {
    literatureForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const query = document.getElementById("literature-query").value;
      const openalexEmail = document.getElementById("openalex-email").value;
      const semanticKey = document.getElementById("semantic-key").value;
      const limit = parseInt(document.getElementById("literature-limit").value, 10);
      const sources = [];
      if (document.getElementById("source-openalex").checked) {
        sources.push("openalex");
      }
      if (document.getElementById("source-crossref").checked) {
        sources.push("crossref");
      }
      if (document.getElementById("source-semantic").checked) {
        sources.push("semantic_scholar");
      }
      const includeNonArticle = document.getElementById("include-non-article").checked;
      const message = document.getElementById("literature-message");
      try {
        const result = await fetchJSON("/api/literature/queries", {
          method: "POST",
          body: JSON.stringify({
            query,
            sources,
            per_source_limit: limit,
            include_non_article: includeNonArticle,
            openalex_email: openalexEmail || null,
            semantic_scholar_key: semanticKey || null,
          }),
        });
        message.textContent = `Literature query started: #${result.query_id}`;
        await loadLiteratureQueries();
      } catch (error) {
        message.textContent = error.message;
      }
    });
  }

  const ideaStatusFilter = document.getElementById("idea-status-filter");
  if (ideaStatusFilter) {
    ideaStatusFilter.addEventListener("change", async () => {
      await loadIdeas();
    });
  }

  const reviewForm = document.getElementById("review-form");
  if (reviewForm) {
    updateReviewLevelVisibility();
    const typeSelect = document.getElementById("review-type");
    typeSelect.addEventListener("change", updateReviewLevelVisibility);

    reviewForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const message = document.getElementById("review-message");
      const runButton = document.getElementById("review-run");
      const originalRunLabel = runButton ? runButton.textContent : "";
      message.textContent = "";
      const reviewType = document.getElementById("review-type").value;
      const level = document.getElementById("review-level").value;
      const title = document.getElementById("review-title").value;
      const language = document.getElementById("review-language").value;
      const fileInput = document.getElementById("review-pdf-upload");
      const file = fileInput ? fileInput.files[0] : null;
      const personas = [
        document.getElementById("review-persona-1")?.value,
        document.getElementById("review-persona-2")?.value,
        document.getElementById("review-persona-3")?.value,
      ].filter(Boolean);
      const duplicates = personas.filter((persona, index) => personas.indexOf(persona) !== index);
      if (duplicates.length) {
        const labels = [...new Set(duplicates)].map(formatPersonaLabel).join(", ");
        const confirmed = confirm(
          `You selected the same persona more than once (${labels}). Run duplicate personas anyway?`
        );
        if (!confirmed) {
          return;
        }
      }

      const llm = getLlmSettings();
      const provider = llm.provider;
      const model = llm.model;
      if (!provider) {
        message.textContent = "Select an LLM provider in Session Control.";
        return;
      }

      if (runButton) {
        runButton.disabled = true;
        runButton.textContent = "Running review...";
      }
      message.textContent = "Running review...";

      let reviewId = state.selectedReviewId;
      if (!reviewId) {
        if (!file) {
          message.textContent = "Choose a PDF to run the review.";
          if (runButton) {
            runButton.disabled = false;
            runButton.textContent = originalRunLabel;
          }
          return;
        }
        const payload = {
          review_type: reviewType,
          title: title || null,
          language: language || "en",
        };
        if (reviewType === "project") {
          payload.level = level;
        }
        try {
          const result = await fetchJSON("/api/reviews", {
            method: "POST",
            body: JSON.stringify(payload),
          });
          reviewId = result.review_id;
          state.selectedReviewId = reviewId;
          await loadReviews();
        } catch (error) {
          message.textContent = error.message;
          if (runButton) {
            runButton.disabled = false;
            runButton.textContent = originalRunLabel;
          }
          return;
        }
      }

      if (file) {
        try {
          await uploadFile(`/api/reviews/${reviewId}/upload-pdf`, file);
        } catch (error) {
          message.textContent = error.message;
          if (runButton) {
            runButton.disabled = false;
            runButton.textContent = originalRunLabel;
          }
          return;
        }
      } else {
        try {
          const detail = await fetchJSON(`/api/reviews/${reviewId}`);
          if (!detail.sections || detail.sections.length === 0) {
            message.textContent = "Upload a PDF to index sections before running.";
            if (runButton) {
              runButton.disabled = false;
              runButton.textContent = originalRunLabel;
            }
            return;
          }
        } catch (error) {
          message.textContent = error.message;
          if (runButton) {
            runButton.disabled = false;
            runButton.textContent = originalRunLabel;
          }
          return;
        }
      }

      try {
        await fetchJSON(`/api/reviews/${reviewId}/run`, {
          method: "POST",
          body: JSON.stringify({
            provider,
            model: model || null,
            personas,
          }),
        });
        message.textContent = "Review completed.";
        await loadReviewDetail(reviewId);
      } catch (error) {
        message.textContent = error.message;
      } finally {
        if (runButton) {
          runButton.disabled = false;
          runButton.textContent = originalRunLabel;
        }
      }
    });
  }

  ["idea-count", "topic-focus", "topic-exclude", "run-literature", "use-assessment-seeds"].forEach((id) => {
    const field = document.getElementById(id);
    if (field) {
      field.addEventListener("input", captureRunFormState);
      field.addEventListener("change", captureRunFormState);
      field.addEventListener("input", saveRunFormState);
      field.addEventListener("change", saveRunFormState);
    }
  });

  ["global-provider", "global-model"].forEach((id) => {
    const field = document.getElementById(id);
    if (field) {
      field.addEventListener("input", captureLlmSettings);
      field.addEventListener("change", captureLlmSettings);
      field.addEventListener("input", saveLlmSettings);
      field.addEventListener("change", saveLlmSettings);
    }
  });
}

async function refreshLoop() {
  const scrollY = window.scrollY;
  if (isFormActive()) {
    setTimeout(refreshLoop, 8000);
    return;
  }
  captureRunFormState();
  await loadRuns();
  await loadIdeas();
  await loadLiteratureQueries();
  await loadReviews();
  restoreRunFormState();
  if (state.selectedLiteratureId) {
    await loadLiteratureDetail(state.selectedLiteratureId);
  }
  if (state.selectedReviewId) {
    await loadReviewDetail(state.selectedReviewId);
  }
  window.scrollTo(0, scrollY);
  setTimeout(refreshLoop, 8000);
}

async function init() {
  loadLlmSettings();
  await loadProviders();
  await loadCredentials();
  loadRunFormState();
  restoreLlmSettings();
  restoreRunFormState();
  wireForms();
  initModeSwitcher();
  await refreshLoop();
}

init().catch((error) => {
  console.error(error);
});
