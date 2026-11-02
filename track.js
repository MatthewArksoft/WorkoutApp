// Workout log helpers. log = {"YYYY-MM-DD": {d: dayId, n: done, t: total}}, keyed by the PLANNED
// weekday's date in the week the session was done (so a Monday workout finished on Tuesday still
// fills Monday, and any number of different days can be logged on the same real date).
const dkey = d => d.toLocaleDateString("en-CA");
const addDays = (d, n) => { const x = new Date(d); x.setDate(x.getDate() + n); return x; };
const monday = d => addDays(d, -((d.getDay() + 6) % 7));
const isDone = e => !!e && e.n >= e.t;
const WEEK = ["Mon", "Tue", "Wed", "Thu", "Fri"];
const DAYIDX = { mon: 0, tue: 1, wed: 2, thu: 3, fri: 4 };
const slotKey = (id, today = new Date()) => dkey(addDays(monday(today), DAYIDX[id]));

// Consecutive completed slot-days counting back from this week's Friday. A later-in-the-week slot
// done early still counts; weekends are always skipped; an unfinished slot of the CURRENT week (past
// or not yet reached) is skipped too, not a break — only a weekday in an earlier, already-closed week
// that's undone stops the count.
function streak(log, today = new Date()) {
  const mon = monday(today);
  let n = 0;
  for (let d = addDays(mon, 4); ; d = addDays(d, -1)) {
    if (isDone(log[dkey(d)])) n++;
    else if (d.getDay() % 6 === 0 || d >= mon) continue;
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

// Record day `id` at n/t ticks, filed under its planned slot for the week `today` falls in.
// Any number of different days can be logged for the same real date.
function logSession(log, id, n, t, today = new Date()) {
  const k = slotKey(id, today);
  if (n) log[k] = { d: id, n, t }; else delete log[k];
  return log;
}

// One-time migration: old logs were keyed by the date actually touched. Refile each entry under
// its planned slot for that date's week; on collision (two entries land on the same slot) keep the
// more complete one (done beats partial, then higher n/t). An entry whose day id isn't a known
// weekday keeps its original key; a malformed (non-object) entry is left untouched, not thrown on.
function refile(log) {
  const out = {};
  for (const k in log) {
    const e = log[k];
    if (!e || typeof e !== "object") { out[k] = e; continue; }
    const nk = DAYIDX.hasOwnProperty(e.d) ? slotKey(e.d, new Date(k + "T00:00")) : k;
    const cur = out[nk];
    if (!cur || (isDone(e) !== isDone(cur) ? isDone(e) : e.n > cur.n || (e.n === cur.n && e.t > cur.t))) out[nk] = e;
  }
  return out;
}

const total = log => Object.values(log).filter(isDone).length;

function shareText(name, log, today = new Date()) {
  const w = week(log, today), s = streak(log, today);
  const icon = { done: "✅", partial: "🟡", "": "⬜" };
  const we = [5, 6].reduce((a, i) => a + ((log[dkey(addDays(monday(today), i))] || {}).items || []).length, 0); // logged Sat/Sun activities
  return `💪 ${name || "Me"} · Desk Reset\n` +
    `This week: ${w.map(x => x.label + " " + icon[x.state]).join("  ")} (${w.filter(x => x.state === "done").length}/5)\n` +
    (we ? `Weekend: ${we} extra activit${we === 1 ? "y" : "ies"}\n` : "") +
    `Streak: ${s} session${s === 1 ? "" : "s"} · Total: ${total(log)}`;
}

if (typeof module !== "undefined") module.exports = { dkey, streak, week, total, shareText, logSession, slotKey, refile };
