// Run: node test.js
const assert = require("assert");
const { streak, week, shareText, logSession } = require("./track.js");
const done = { d: "mon", n: 8, t: 8 }, half = { d: "mon", n: 3, t: 8 };

// Wed 2026-10-14. Fri+Mon+Tue done, weekend in between, today not started -> 3
const log = { "2026-10-09": done, "2026-10-12": done, "2026-10-13": done };
const wed = new Date(2026, 9, 14);
assert.strictEqual(streak(log, wed), 3);
// Missing Thu 2026-10-08 stops the count; a missed weekday tomorrow breaks it
assert.strictEqual(streak(log, new Date(2026, 9, 15)), 0);
// Today done counts
assert.strictEqual(streak({ ...log, "2026-10-14": done }, wed), 4);
assert.strictEqual(streak({}, wed), 0);

assert.deepStrictEqual(week({ ...log, "2026-10-14": half }, wed).map(x => x.state), ["done", "done", "partial", "", ""]);
assert.ok(shareText("Matt", log, wed).includes("(2/5)"));
// logSession: another day's ticks must not clobber a completed session
const k = "2026-10-12", L = {};
logSession(L, k, "mon", 8, 8);
logSession(L, k, "tue", 1, 8); assert.deepStrictEqual(L[k], { d: "mon", n: 8, t: 8 });
logSession(L, k, "tue", 0, 8); assert.deepStrictEqual(L[k], { d: "mon", n: 8, t: 8 });
logSession(L, k, "mon", 7, 8); assert.deepStrictEqual(L[k], { d: "mon", n: 7, t: 8 }); // same day can untick
logSession(L, k, "tue", 2, 8); assert.deepStrictEqual(L[k], { d: "tue", n: 2, t: 8 }); // partial: last touched wins
logSession(L, k, "mon", 0, 8); assert.deepStrictEqual(L[k], { d: "tue", n: 2, t: 8 }); // other day's untick ignored
logSession(L, k, "tue", 0, 8); assert.strictEqual(L[k], undefined);
console.log("ok");

// Reminder codes pasted back-to-back (with or without commas/newlines) parse as a list
const { parseSubs } = require("./.github/remind.js");
const sub = n => JSON.stringify({ endpoint: "https://push/" + n, expirationTime: null, keys: { p256dh: "p", auth: "a" } });
assert.strictEqual(parseSubs(sub(1) + "\n" + sub(2)).length, 2);
assert.strictEqual(parseSubs(sub(1) + "," + sub(2)).length, 2);
assert.strictEqual(parseSubs("[" + sub(1) + "]").length, 1);
assert.strictEqual(parseSubs(sub(1)).length, 1);
assert.deepStrictEqual(parseSubs(""), []);
console.log("ok remind");
