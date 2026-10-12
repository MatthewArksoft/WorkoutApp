// Run: node test.js
const assert = require("assert");
const { streak, week, shareText } = require("./track.js");
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
console.log("ok");
