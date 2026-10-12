// Sends the weekday gym reminder to every subscribed phone. Run by .github/workflows/reminder.yml.
// SUBSCRIPTIONS: a JSON array, or reminder codes pasted one after another.
function parseSubs(raw) {
  raw = (raw || "").trim();
  if (!raw) return [];
  return JSON.parse(raw.startsWith("[") ? raw : "[" + raw.replace(/}\s*,?\s*{"endpoint"/g, '},{"endpoint"') + "]");
}

async function main() {
  const webpush = require("web-push");
  webpush.setVapidDetails("https://matthewarksoft.github.io/WorkoutApp/", process.env.VAPID_PUBLIC_KEY, process.env.VAPID_PRIVATE_KEY);
  const subs = parseSubs(process.env.SUBSCRIPTIONS);
  if (!subs.length) throw new Error("SUBSCRIPTIONS secret is empty");
  const payload = JSON.stringify({ title: "Gym time 💪", body: "Today's Desk Reset session is ready. Tap to start." });
  let failed = 0;
  for (const s of subs) {
    try { await webpush.sendNotification(s, payload, { TTL: 3600 }); console.log("sent", s.endpoint.slice(0, 50)); }
    catch (e) { failed++; console.error("failed", e.statusCode, e.body || e.message); } // 404/410 = phone unsubscribed: remove that code
  }
  if (failed) process.exitCode = 1;
}

if (require.main === module) main().catch(e => { console.error(e.message); process.exit(1); });
module.exports = { parseSubs };
