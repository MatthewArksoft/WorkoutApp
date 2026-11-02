// Run: node test.js
const assert = require("assert");
const { streak, week, shareText, logSession, slotKey, refile } = require("./track.js");
const done = { d: "mon", n: 8, t: 8 }, half = { d: "mon", n: 3, t: 8 };

// Wed 2026-10-14. Fri+Mon+Tue done, weekend in between, today not started -> 3
const log = { "2026-10-09": done, "2026-10-12": done, "2026-10-13": done };
const wed = new Date(2026, 9, 14);
assert.strictEqual(streak(log, wed), 3);
// Thu 2026-10-15: Wed (this week, already passed) is unfinished but still in the CURRENT week, so it's
// skipped, not a break; Thu 2026-10-08 (a previous, closed week) being unfinished is what stops it
assert.strictEqual(streak(log, new Date(2026, 9, 15)), 3);
// Today done counts
assert.strictEqual(streak({ ...log, "2026-10-14": done }, wed), 4);
assert.strictEqual(streak({}, wed), 0);
// Sat/Sun with Friday (this week) still open: skipped, not a break
const log2 = { "2026-10-12": done, "2026-10-13": done, "2026-10-14": done, "2026-10-15": done }; // Mon-Thu done, Fri open
assert.strictEqual(streak(log2, new Date(2026, 9, 17)), 4); // Sat
assert.strictEqual(streak(log2, new Date(2026, 9, 18)), 4); // Sun
// Tue with Monday (this week) still open: skipped, not a break
const log3 = { "2026-10-09": done }; // previous week's Friday done
assert.strictEqual(streak(log3, new Date(2026, 9, 13)), 1); // Tue, Mon open
// A missed weekday in a previous, already-closed week still stops the count
const log4 = { "2026-10-12": done, "2026-10-13": done, "2026-10-05": done }; // this week's Mon/Tue done, but prior week's Fri (10-09) missing
assert.strictEqual(streak(log4, wed), 2);

assert.deepStrictEqual(week({ ...log, "2026-10-14": half }, wed).map(x => x.state), ["done", "done", "partial", "", ""]);
assert.ok(shareText("Matt", log, wed).includes("(2/5)"));

// logSession: a workout is credited to its planned weekday of the week it's done in, not the calendar date.
// Two workouts logged the same real day (Mon then Tue) land at different keys and both count.
const L = {};
logSession(L, "mon", 8, 8, wed);
logSession(L, "tue", 8, 8, wed);
assert.strictEqual(Object.keys(L).length, 2);
assert.deepStrictEqual(week(L, wed).map(x => x.state), ["done", "done", "", "", ""]);
// Mon's workout done late, on Tue, still fills Mon's dot
const L2 = {}; logSession(L2, "mon", 8, 8, new Date(2026, 9, 13)); // Tue
assert.strictEqual(week(L2, wed)[0].state, "done");
// Sat session of Thu fills Thu
const L3 = {}; logSession(L3, "thu", 8, 8, new Date(2026, 9, 17)); // Sat, same week
assert.strictEqual(week(L3, wed)[3].state, "done");
// Untick removes the slot entry
logSession(L3, "thu", 0, 8, new Date(2026, 9, 17));
assert.strictEqual(week(L3, wed)[3].state, "");
// streak counts a future-dated (later weekday) workout done early
const L4 = {}; logSession(L4, "fri", 8, 8, wed);
assert.strictEqual(streak(L4, wed), 1);
console.log("ok");

// refile: migrate old date-keyed entries (keyed by the day actually touched) to the planned-day key
const old = { "2026-10-13": { d: "mon", n: 8, t: 8 } }; // Tue-dated Monday session
assert.deepStrictEqual(refile(old), { "2026-10-12": { d: "mon", n: 8, t: 8 } });
// collision: keep the better (higher n) entry
const old2 = { "2026-10-12": { d: "mon", n: 3, t: 8 }, "2026-10-13": { d: "mon", n: 8, t: 8 } };
assert.deepStrictEqual(refile(old2), { "2026-10-12": { d: "mon", n: 8, t: 8 } });
// unknown day id keeps its own key
const old3 = { "2026-10-13": { d: "xyz", n: 1, t: 1 } };
assert.deepStrictEqual(refile(old3), old3);
// weekend-dated key ("sat" isn't a known weekday id): left as-is
const old4 = { "2026-10-11": { d: "sat", n: 1, t: 1 } };
assert.deepStrictEqual(refile(old4), old4);
// tie-break: a done entry beats a merely-partial one even with lower raw n/t
const old5 = { "2026-10-12": { d: "mon", n: 3, t: 4 }, "2026-10-13": { d: "mon", n: 3, t: 3 } }; // Mon-dated partial(3/4), Tue-dated done(3/3)
assert.deepStrictEqual(refile(old5), { "2026-10-12": { d: "mon", n: 3, t: 3 } });
// null entry must not throw
const old6 = { "2026-10-13": null };
assert.deepStrictEqual(refile(old6), old6);
console.log("ok refile");

// Reminder codes pasted back-to-back (with or without commas/newlines) parse as a list
const { parseSubs } = require("./.github/remind.js");
const sub = n => JSON.stringify({ endpoint: "https://push/" + n, expirationTime: null, keys: { p256dh: "p", auth: "a" } });
assert.strictEqual(parseSubs(sub(1) + "\n" + sub(2)).length, 2);
assert.strictEqual(parseSubs(sub(1) + "," + sub(2)).length, 2);
assert.strictEqual(parseSubs("[" + sub(1) + "]").length, 1);
assert.strictEqual(parseSubs(sub(1)).length, 1);
assert.deepStrictEqual(parseSubs(""), []);
console.log("ok remind");
