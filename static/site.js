// Theme toggle: flips light/dark and remembers the choice.
document.querySelector(".theme-toggle").addEventListener("click", () => {
  const root = document.documentElement;
  const current = root.dataset.theme ||
    (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  const next = current === "dark" ? "light" : "dark";
  root.dataset.theme = next;
  try { localStorage.setItem("theme", next); } catch (e) {}
});

// Copy buttons on code blocks.
document.querySelectorAll(".code .copy").forEach((btn) => {
  btn.addEventListener("click", async () => {
    const code = btn.closest(".code").querySelector("pre").innerText;
    try {
      await navigator.clipboard.writeText(code);
      btn.textContent = "Copied";
    } catch (e) {
      btn.textContent = "Failed";
    }
    setTimeout(() => (btn.textContent = "Copy"), 1500);
  });
});

// Contact form: submit in place instead of leaving the page.
const form = document.querySelector(".contact-form");
if (form) {
  const status = form.querySelector(".form-status");
  const button = form.querySelector("button[type=submit]");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const data = new FormData(form);
    if (data.get("botcheck")) return;   // honeypot ticked: a bot, drop it silently
    if (form.querySelector(".h-captcha") && !data.get("h-captcha-response")) {
      status.textContent = "Please complete the captcha.";
      return;
    }
    button.disabled = true;
    status.className = "form-status muted";
    status.textContent = "Sending…";
    try {
      const res = await fetch(form.action, {
        method: "POST",
        headers: { Accept: "application/json" },
        body: data,
      });
      const json = await res.json();
      if (!json.success) throw new Error(json.message);
      form.reset();
      if (window.hcaptcha) hcaptcha.reset();
      status.className = "form-status ok";
      status.textContent = "Thanks! Your message was sent.";
    } catch (err) {
      status.textContent = "Something went wrong. Please try again in a minute.";
    } finally {
      button.disabled = false;
    }
  });
}

// Filter pills: tags on the blog index, kinds on projects.
document.querySelectorAll("[data-filter]").forEach((group) => {
  const attr = group.dataset.filter;   // "tags" or "kind"
  const items = document.querySelectorAll(`[data-${attr}]:not([data-filter])`);
  const pick = (value) => {
    group.querySelectorAll(".pill").forEach((p) =>
      p.setAttribute("aria-pressed", String(p.dataset.value === value)));
    items.forEach((el) => {
      const values = el.dataset[attr].split(" ");
      el.hidden = value !== "" && !values.includes(value);
    });
    document.querySelectorAll("[data-group]").forEach((g) => {
      g.hidden = !g.querySelector(`[data-${attr}]:not([hidden])`);
    });
  };
  group.addEventListener("click", (e) => {
    const pill = e.target.closest(".pill");
    if (!pill) return;
    pick(pill.dataset.value);
    if (attr === "tags") history.replaceState(null, "", pill.dataset.value ? "#" + pill.dataset.value : location.pathname);
  });
  // Tag links on posts point to /blog/#tag
  const hash = decodeURIComponent(location.hash.slice(1));
  if (attr === "tags" && hash && group.querySelector(`[data-value="${CSS.escape(hash)}"]`)) pick(hash);
});
