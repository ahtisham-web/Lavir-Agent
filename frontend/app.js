document.addEventListener("DOMContentLoaded", () => {
  const chatForm = document.getElementById("chat-form");
  const userInput = document.getElementById("user-input");
  const chatHistory = document.getElementById("chat-history");
  const stepsContainer = document.getElementById("steps-container");
  const emailList = document.getElementById("email-list");
  const calendarList = document.getElementById("calendar-list");
  const inboxCount = document.getElementById("inbox-count");
  const mockToggle = document.getElementById("mock-toggle");
  const resetBtn = document.getElementById("reset-btn");
  const googleAuthBtn = document.getElementById("google-auth-btn");
  
  // In-Line HITL Banner Elements
  const inlineHitlBanner = document.getElementById("inline-hitl-banner");
  const bannerActionType = document.getElementById("banner-action-type");
  const bannerAgentRole = document.getElementById("banner-agent-role");
  const bannerDescription = document.getElementById("banner-description");
  const bannerDetailsJson = document.getElementById("banner-details-json");
  const bannerApproveBtn = document.getElementById("banner-approve-btn");
  const bannerRejectBtn = document.getElementById("banner-reject-btn");

  // Modal Elements
  const modal = document.getElementById("confirmation-modal");
  const modalActionType = document.getElementById("modal-action-type");
  const modalAgentRole = document.getElementById("modal-agent-role");
  const modalDescription = document.getElementById("modal-description");
  const modalDetailsJson = document.getElementById("modal-details-json");
  const modalApproveBtn = document.getElementById("modal-approve-btn");
  const modalRejectBtn = document.getElementById("modal-reject-btn");

  let activeConfirmationId = null;
  let activeSessionId = "session_" + Math.random().toString(36).substr(2, 9);
  let ws = null;

  // Initialize WebSocket connection for streaming agent updates
  function connectWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/agent`;
    ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.type === "agent_execution" || payload.type === "confirmation_processed") {
          renderSteps(payload.data.steps);
        }
      } catch (e) {
        console.error("WS Parse error:", e);
      }
    };

    ws.onclose = () => {
      setTimeout(connectWebSocket, 3000);
    };
  }

  connectWebSocket();

  // Check Google Auth Status
  async function checkAuthStatus() {
    try {
      const res = await fetch("/api/auth/status");
      const data = await res.json();
      if (mockToggle.value === "false") {
        if (!data.authenticated) {
          googleAuthBtn.classList.remove("hidden");
        } else {
          googleAuthBtn.classList.add("hidden");
        }
      } else {
        googleAuthBtn.classList.add("hidden");
      }
      return data;
    } catch (e) {
      console.error("Auth status check failed:", e);
    }
  }

  mockToggle.addEventListener("change", async () => {
    await checkAuthStatus();
    loadDataFeeds();
  });

  googleAuthBtn.addEventListener("click", async () => {
    googleAuthBtn.disabled = true;
    googleAuthBtn.textContent = "⏳ Waiting for Login...";
    appendAgentBubble("🔑 Opening Google OAuth consent window in your browser. Please log in and authorize access.");
    try {
      const res = await fetch("/api/auth/login", { method: "POST" });
      const data = await res.json();
      if (data.success) {
        appendAgentBubble("✅ **Google Account Connected!** Successfully authenticated with Gmail & Google Calendar.");
        await checkAuthStatus();
        loadDataFeeds();
      } else {
        appendAgentBubble("⚠️ Authentication failed: " + (data.error || data.detail || "Unknown error"));
      }
    } catch (e) {
      appendAgentBubble("⚠️ Error during Google OAuth login: " + e.message);
    } finally {
      googleAuthBtn.disabled = false;
      googleAuthBtn.textContent = "🔑 Connect Google Account";
    }
  });

  // Load Data Feeds with cache prevention query string
  async function loadDataFeeds() {
    const useMock = mockToggle.value;
    const cacheBuster = `&_t=${Date.now()}`;
    try {
      // Fetch Emails
      const emailRes = await fetch(`/api/emails?use_mock=${useMock}${cacheBuster}`);
      const emailData = await emailRes.json();
      if (emailData.success) {
        renderEmails(emailData.data || []);
      }

      // Fetch Calendar Events
      const calRes = await fetch(`/api/calendar?use_mock=${useMock}${cacheBuster}`);
      const calData = await calRes.json();
      if (calData.success) {
        renderCalendar(calData.data || []);
      }
    } catch (e) {
      console.error("Error loading feeds:", e);
    }
  }

  function renderEmails(emails) {
    inboxCount.textContent = emails.length;
    if (emails.length === 0) {
      emailList.innerHTML = `<div class="placeholder-text">No emails found.</div>`;
      return;
    }
    emailList.innerHTML = emails.map(m => `
      <div class="data-item">
        <h4>✉️ ${escapeHtml(m.subject)}</h4>
        <p><strong>From:</strong> ${escapeHtml(m.sender)}</p>
        <p>${escapeHtml(m.snippet)}</p>
      </div>
    `).join("");
  }

  function renderCalendar(events) {
    if (events.length === 0) {
      calendarList.innerHTML = `<div class="placeholder-text">No calendar events scheduled.</div>`;
      return;
    }
    calendarList.innerHTML = events.map(e => `
      <div class="data-item">
        <h4>📅 ${escapeHtml(e.title)}</h4>
        <p><strong>Time:</strong> ${escapeHtml(e.start_time)} to ${escapeHtml(e.end_time)}</p>
        <p><strong>Location:</strong> ${escapeHtml(e.location || 'N/A')}</p>
      </div>
    `).join("");
  }

  // Render Steps Trace in Left Sidebar
  function renderSteps(steps) {
    if (!steps || steps.length === 0) return;

    // Highlight Active Node in Graph
    const lastStep = steps[steps.length - 1];
    document.querySelectorAll(".graph-node").forEach(n => n.classList.remove("active"));
    if (lastStep.agent_role.includes("Master")) {
      document.getElementById("node-master").classList.add("active");
    } else if (lastStep.agent_role.includes("Email")) {
      document.getElementById("node-email").classList.add("active");
    } else if (lastStep.agent_role.includes("Calendar")) {
      document.getElementById("node-calendar").classList.add("active");
    }

    stepsContainer.innerHTML = steps.map(s => `
      <div class="step-card ${getRoleClass(s.agent_role)} ${s.status}">
        <div class="step-header">
          <span>${escapeHtml(s.agent_role)}</span>
          <span class="step-status">${escapeHtml(s.status)}</span>
        </div>
        <div class="step-thought">${escapeHtml(s.thought)}</div>
        ${s.tool_call ? `<div class="step-tool">⚡ ${escapeHtml(s.tool_call.tool_name)}</div>` : ''}
      </div>
    `).join("");

    stepsContainer.scrollTop = stepsContainer.scrollHeight;
  }

  function getRoleClass(role) {
    if (role.includes("Email")) return "email";
    if (role.includes("Calendar")) return "calendar";
    return "master";
  }

  // Handle Form Submit
  chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const prompt = userInput.value.trim();
    if (!prompt) return;

    hideHitlGuard();
    appendUserBubble(prompt);
    userInput.value = "";

    const useMock = mockToggle.value === "true";

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Cache-Control": "no-cache"
        },
        body: JSON.stringify({
          prompt: prompt,
          session_id: activeSessionId,
          use_mock: useMock
        })
      });

      const data = await res.json();
      renderSteps(data.steps);

      if (data.status === "requires_confirmation" && data.pending_confirmation) {
        showHitlGuard(data.pending_confirmation);
      }

      appendAgentBubble(data.final_output);
      loadDataFeeds();
    } catch (e) {
      appendAgentBubble("⚠️ Error executing request: " + e.message);
    }
  });

  function showHitlGuard(conf) {
    activeConfirmationId = conf.confirmation_id;

    // Show In-Line Center Banner
    bannerActionType.textContent = conf.action_type;
    bannerAgentRole.textContent = conf.agent_role;
    bannerDescription.textContent = conf.description;
    bannerDetailsJson.textContent = JSON.stringify(conf.details, null, 2);
    inlineHitlBanner.classList.remove("hidden");

    // Also populate Modal
    modalActionType.textContent = conf.action_type;
    modalAgentRole.textContent = conf.agent_role;
    modalDescription.textContent = conf.description;
    modalDetailsJson.textContent = JSON.stringify(conf.details, null, 2);
    modal.classList.remove("hidden");
  }

  function hideHitlGuard() {
    inlineHitlBanner.classList.add("hidden");
    modal.classList.add("hidden");
  }

  // Banner & Modal Button Action Listeners
  bannerApproveBtn.addEventListener("click", () => handleConfirmationResponse(true));
  bannerRejectBtn.addEventListener("click", () => handleConfirmationResponse(false));
  modalApproveBtn.addEventListener("click", () => handleConfirmationResponse(true));
  modalRejectBtn.addEventListener("click", () => handleConfirmationResponse(false));

  async function handleConfirmationResponse(approved) {
    hideHitlGuard();
    const useMock = mockToggle.value === "true";

    try {
      const res = await fetch(`/api/confirm?session_id=${activeSessionId}&use_mock=${useMock}`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Cache-Control": "no-cache"
        },
        body: JSON.stringify({
          confirmation_id: activeConfirmationId,
          approved: approved,
          user_feedback: approved ? "Approved by user" : "Cancelled by user"
        })
      });

      const data = await res.json();
      renderSteps(data.steps);
      appendAgentBubble(data.final_output);
      loadDataFeeds();
    } catch (e) {
      appendAgentBubble("⚠️ Confirmation processing failed: " + e.message);
    }
  }

  // Quick Action Chips
  document.querySelectorAll(".chip").forEach(chip => {
    chip.addEventListener("click", () => {
      userInput.value = chip.getAttribute("data-prompt");
      chatForm.dispatchEvent(new Event("submit"));
    });
  });

  // Sidebar Tab Switching
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById(btn.getAttribute("data-tab")).classList.add("active");
    });
  });

  resetBtn.addEventListener("click", async () => {
    await fetch("/api/reset", { method: "POST" });
    hideHitlGuard();
    loadDataFeeds();
    appendAgentBubble("🔄 Mock Sandbox reset to default state.");
  });

  function appendUserBubble(text) {
    const bubble = document.createElement("div");
    bubble.className = "chat-bubble user-bubble";
    bubble.innerHTML = `<div class="bubble-header"><span>You</span></div><div class="bubble-content">${escapeHtml(text)}</div>`;
    chatHistory.appendChild(bubble);
    chatHistory.scrollTop = chatHistory.scrollHeight;
  }

  function appendAgentBubble(text) {
    const bubble = document.createElement("div");
    bubble.className = "chat-bubble agent-bubble";
    bubble.innerHTML = `<div class="bubble-header"><span class="agent-name">🤖 Larvi Master Agent</span></div><div class="bubble-content">${formatMarkdown(text)}</div>`;
    chatHistory.appendChild(bubble);
    chatHistory.scrollTop = chatHistory.scrollHeight;
  }

  function escapeHtml(text) {
    if (!text) return "";
    return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function formatMarkdown(text) {
    if (!text) return "";
    let formatted = escapeHtml(text);
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
    formatted = formatted.replace(/\n/g, '<br>');
    return formatted;
  }

  checkAuthStatus();
  loadDataFeeds();
});
