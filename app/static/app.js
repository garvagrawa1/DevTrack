const $ = (id) => document.getElementById(id);
const form = $("search-form");
const input = $("repo-input");
const dashboard = $("dashboard");
const message = $("message");

function number(value) { return new Intl.NumberFormat().format(value ?? 0); }
function date(value) {
  if (!value) return "date unavailable";
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(new Date(value));
}
function safeText(value, fallback = "Not provided") { return value || fallback; }
function clear(node) { node.replaceChildren(); }
function addEmpty(node, text) {
  const p = document.createElement("p"); p.className = "empty"; p.textContent = text; node.append(p);
}
function activityRow(container, title, subtitle, when, url) {
  const row = document.createElement("div"); row.className = "activity-item";
  const main = document.createElement("div"); main.className = "activity-main";
  const link = document.createElement("a"); link.href = url; link.target = "_blank"; link.rel = "noreferrer"; link.textContent = title;
  const sub = document.createElement("div"); sub.className = "activity-sub"; sub.textContent = subtitle;
  const time = document.createElement("div"); time.className = "activity-date"; time.textContent = date(when);
  main.append(link, sub); row.append(main, time); container.append(row);
}
function renderList(id, items, makeRow, emptyText) {
  const node = $(id); clear(node);
  if (!items.length) return addEmpty(node, emptyText);
  items.forEach(item => makeRow(node, item));
}
async function getJSON(url) {
  const response = await fetch(url);
  const body = await response.json();
  if (!response.ok) throw new Error(body.detail || `Request failed (${response.status})`);
  return body;
}
async function explore(repo) {
  const clean = repo.trim().replace(/^https?:\/\/github\.com\//, "").replace(/\/$/, "");
  const parts = clean.split("/");
  if (parts.length !== 2 || parts.some(p => !p || p.includes(" "))) {
    message.textContent = "Please enter a repository in owner/name format.";
    return;
  }
  message.textContent = "Connecting to GitHub and collecting repository signals…";
  dashboard.classList.add("hidden");
  try {
    const [summary, activity] = await Promise.all([
      getJSON(`/api/repository/${encodeURIComponent(parts[0])}/${encodeURIComponent(parts[1])}`),
      getJSON(`/api/repository/${encodeURIComponent(parts[0])}/${encodeURIComponent(parts[1])}/activity?per_page=8`)
    ]);
    $("owner-avatar").src = summary.owner.avatar_url;
    $("owner-avatar").alt = `${summary.owner.login} avatar`;
    $("repo-name").textContent = summary.full_name;
    $("repo-link").href = summary.html_url;
    $("repo-description").textContent = safeText(summary.description, "This repository has no description.");
    $("stars").textContent = number(summary.stars);
    $("forks").textContent = number(summary.forks);
    $("open-issues").textContent = number(summary.open_issues);
    $("watchers").textContent = number(summary.watchers);
    const topics = $("topics"); clear(topics);
    (summary.topics || []).slice(0, 10).forEach(topic => {
      const span = document.createElement("span"); span.className = "topic"; span.textContent = topic; topics.append(span);
    });
    $("meta-strip").innerHTML = "";
    const metadata = [
      ["LANGUAGE", summary.language], ["LICENSE", summary.license],
      ["DEFAULT BRANCH", summary.default_branch], ["LAST PUSH", date(summary.pushed_at)]
    ];
    metadata.forEach(([label, value]) => {
      const span = document.createElement("span");
      const b = document.createElement("b"); b.textContent = `${label}: `;
      span.append(b, document.createTextNode(safeText(value))); $("meta-strip").append(span);
    });
    $("export-link").href = `/api/export/${encodeURIComponent(parts[0])}/${encodeURIComponent(parts[1])}`;
    renderList("commits", activity.commits, (node, c) =>
      activityRow(node, c.message, `${c.sha} · ${c.author}`, c.date, c.url), "No recent commits found.");
    renderList("pulls", activity.pull_requests, (node, p) =>
      activityRow(node, `#${p.number} ${p.title}`, `${p.state} · ${p.user}`, p.updated_at, p.url), "No pull requests found.");
    renderList("issues", activity.issues, (node, i) =>
      activityRow(node, `#${i.number} ${i.title}`, `${i.state} · ${i.user}`, i.updated_at, i.url), "No issues found.");
    const people = $("contributors"); clear(people);
    if (!activity.contributors.length) addEmpty(people, "Contributor data is unavailable.");
    activity.contributors.forEach(person => {
      const row = document.createElement("div"); row.className = "person";
      const img = document.createElement("img"); img.src = person.avatar_url; img.alt = "";
      const link = document.createElement("a"); link.href = person.url; link.target = "_blank"; link.rel = "noreferrer"; link.textContent = person.login;
      const count = document.createElement("span"); count.textContent = `${number(person.contributions)} commits`;
      row.append(img, link, count); people.append(row);
    });
    $("commit-count").textContent = activity.commits.length;
    $("contributor-count").textContent = activity.contributors.length;
    $("pr-count").textContent = activity.pull_requests.length;
    $("issue-count").textContent = activity.issues.length;
    dashboard.classList.remove("hidden");
    message.textContent = "Repository loaded. A local snapshot has been saved.";
    dashboard.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    message.textContent = error.message;
  }
}
form.addEventListener("submit", event => { event.preventDefault(); explore(input.value); });
document.querySelectorAll(".example").forEach(button => button.addEventListener("click", () => {
  input.value = button.dataset.repo; explore(input.value);
}));
