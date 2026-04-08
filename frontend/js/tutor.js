// FIXED SEND MESSAGE
async function sendMessage() {
  const input = document.getElementById("chat-input");
  const msg   = input.value.trim();
  if (!msg) return;

  input.value = "";
  addMessage("user", msg);
  showTyping();
  document.getElementById("send-btn").disabled = true;

  try {
    const d = await apiPost("/api/tutor/chat", { message: msg }); // FIXED
    removeTyping();
    addMessage("ai", d.reply);
  } catch(e) {
    removeTyping();
    addMessage("ai", e.message || "Connection error");
  }

  document.getElementById("send-btn").disabled = false;
  input.focus();
}

// FIXED CLEAR CHAT
async function clearChat() {
  await apiPost("/api/tutor/clear", {}); // FIXED
  document.getElementById("chat-messages").innerHTML = `
    <div class="msg ai">
      <div class="msg-avatar">EN</div>
      <div class="msg-bubble">Chat cleared! Let's start fresh. 😊</div>
    </div>`;
}

// FIXED LOAD TOPICS
async function loadTopics() {
  try {
    const d = await apiGet("/api/dashboard/data"); // FIXED
    const list = document.getElementById("topic-list");
    list.innerHTML = "";

    if (!d.mastery_scores) return;

    for (const [topic, score] of Object.entries(d.mastery_scores)) {
      const cls = score < 70 ? "weak" : "ok";
      list.innerHTML += `<button class="topic-chip ${cls}" onclick="quickAsk('Help me with ${topic}')">
        ${topic} — ${score}%</button>`;
    }
  } catch(e) {}
}