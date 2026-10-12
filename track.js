// Workout log helpers. log = {"YYYY-MM-DD": {d: dayId, n: done, t: total}}
const dkey = d => d.toLocaleDateString("en-CA");
const addDays = (d, n) => { const x = new Date(d); x.setDate(x.getDate() + n); return x; };
const monday = d => addDays(d, -((d.getDay() + 6) % 7));
const isDone = e => !!e && e.n >= e.t;
const WEEK = ["Mon", "Tue", "Wed", "Thu", "Fri"];

// Consecutive completed sessions counting back from today. Weekends and an unfinished today don't break it.
function streak(log, today = new Date()) {
  let n = 0;
  for (let d = new Date(today), first = true; ; d = addDays(d, -1), first = false) {
    if (isDone(log[dkey(d)])) n++;
    else if (first || d.getDay() % 6 === 0) continue;
    else return n;
  }
}

// Mon–Fri of the current week: "done" | "partial" | "".
function week(log, today = new Date()) {
  const m = monday(today);
  return WEEK.map((label, i) => {
    const e = log[dkey(addDays(m, i))];
    return { label, state: isDone(e) ? "done" : e && e.n ? "partial" : "" };
  });
}

// Record day `id` at n/t ticks for date key k. One entry per date: the last-touched day wins,
// except ticks on another day never overwrite or delete a session already completed today.
function logSession(log, k, id, n, t) {
  const cur = log[k];
  if (cur && cur.d !== id && (isDone(cur) || !n)) return log;
  if (n) log[k] = { d: id, n, t }; else delete log[k];
  return log;
}

const total = log => Object.values(log).filter(isDone).length;

function shareText(name, log, today = new Date()) {
  const w = week(log, today), s = streak(log, today);
  const icon = { done: "✅", partial: "🟡", "": "⬜" };
  return `💪 ${name || "Me"} · Desk Reset\n` +
    `This week: ${w.map(x => x.label + " " + icon[x.state]).join("  ")} (${w.filter(x => x.state === "done").length}/5)\n` +
    `Streak: ${s} session${s === 1 ? "" : "s"} · Total: ${total(log)}`;
}

if (typeof module !== "undefined") module.exports = { dkey, streak, week, total, shareText, logSession };
