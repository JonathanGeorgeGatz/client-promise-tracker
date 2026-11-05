// The Client Promise Tracker — SECOND BUILD (after prompt 2), kept verbatim for the episode.
// Prompt 2 fixed the bookkeeping: trimmed, case-insensitive matching; done-without-a-date,
// unknown clients and unreadable dates refused out loud; kept split into on-time and late by
// working days; cancelled rows separated. What the independent checker later caught, still in
// here exactly as built:
//   * "today" is STILL the machine clock — no as-of date exists;
//   * a row due exactly TODAY falls through every test (not before today, not after) and
//     lands in no bucket at all — the day's own promises are invisible;
//   * a Done date is believed wherever it falls, including the future of the day you are
//     reading — a completion that has not happened yet is credited as kept;
//   * the client list is read row by row with no duplicate check, so a client pasted twice
//     gets two ledgers and the totals count her promises twice.
(function (root) {
  "use strict";
  function rows(text) { return text.split(/\r?\n/).filter(l => l.trim()).map(l => l.split(",")); }
  const DATE = /^\s*(\d{4})-(\d{2})-(\d{2})\s*$/;
  function pd(s) {
    const m = DATE.exec(s || "");
    if (!m) return null;
    return Date.UTC(+m[1], +m[2] - 1, +m[3]);
  }
  const DAY = 86400000;
  const isWork = t => { const w = new Date(t).getUTCDay(); return w >= 1 && w <= 5; };
  function wdAfter(a, b) { let n = 0; for (let t = a + DAY; t <= b; t += DAY) if (isWork(t)) n++; return n; }

  function build(clientsCsv, promisesCsv) {
    const now = new Date();                                     // the sin that survived
    const today = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate());
    const c = rows(clientsCsv), p = rows(promisesCsv);
    const chh = c[0].map(x => x.trim().toLowerCase());
    const phh = p[0].map(x => x.trim().toLowerCase());
    const ci = n => chh.indexOf(n), pi = n => phh.indexOf(n);
    const refused = [];
    const ledgers = [];                                         // one per client ROW (the dup sin)
    for (let r = 1; r < c.length; r++) {
      const name = (c[r][ci("client")] || "").trim();
      if (!name) { refused.push({ file: "clients", line: r + 1, reason: "no name" }); continue; }
      ledgers.push({ name, key: name.toLowerCase(), onTime: 0, late: 0, overdue: 0, upcoming: 0, cancelled: 0 });
    }
    for (let r = 1; r < p.length; r++) {
      const row = p[r];
      const key = (row[pi("client")] || "").trim().toLowerCase();
      const mine = ledgers.filter(l => l.key === key);          // a dup matches twice
      if (!mine.length) { refused.push({ file: "promises", line: r + 1, reason: "unknown client" }); continue; }
      const made = pd(row[pi("made")]), due = pd(row[pi("due")]);
      if (made === null || due === null) { refused.push({ file: "promises", line: r + 1, reason: "bad date" }); continue; }
      if (due < made) { refused.push({ file: "promises", line: r + 1, reason: "due before made" }); continue; }
      const status = (row[pi("status")] || "").trim().toLowerCase();
      if (status === "cancelled") { mine.forEach(l => l.cancelled++); continue; }
      if (status !== "open" && status !== "done") { refused.push({ file: "promises", line: r + 1, reason: "bad status" }); continue; }
      if (status === "done") {
        const done = pd(row[pi("done")]);
        if (done === null) { refused.push({ file: "promises", line: r + 1, reason: "done without a date" }); continue; }
        const late = wdAfter(due, done);                        // the future is believed
        mine.forEach(l => { if (late > 0) l.late++; else l.onTime++; });
        continue;
      }
      if (due < today) mine.forEach(l => l.overdue++);          // strictly before today
      else if (due > today) mine.forEach(l => l.upcoming++);    // strictly after today
      // due === today: falls through — the day's own promises land nowhere
    }
    const sum = k => ledgers.reduce((s, l) => s + l[k], 0);
    const came = sum("onTime") + sum("late") + sum("overdue");
    return { ledgers, refused, clients: ledgers.length,
      onTime: sum("onTime"), late: sum("late"), overdue: sum("overdue"), upcoming: sum("upcoming"),
      keptRate: came ? +((sum("onTime") / came) * 100).toFixed(1) : 100 };
  }
  root.CP_V2 = { build };
})(typeof window !== "undefined" ? window : (typeof module !== "undefined" ? module.exports : this));
