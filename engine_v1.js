// The Client Promise Tracker — FIRST BUILD (prompt 1), kept verbatim for the episode.
// Its sins, exactly as the naive build made them:
//   * "today" comes from the MACHINE CLOCK (new Date()) — open the same files tomorrow and
//     the report changes;
//   * clients are matched by EXACT STRING against the client list: a trailing space, a
//     lowercase name or an ALL-CAPS phone export and the row silently never lands anywhere;
//   * anything not open counts as KEPT — done rows (however late), done rows with no date,
//     cancelled rows: all "handled". Lateness does not exist;
//   * a row is overdue only when its status is exactly "Open" and its due date has passed
//     on the clock; unreadable dates and unknown clients are skipped in silence.
(function (root) {
  "use strict";
  function rows(text) { return text.split(/\r?\n/).filter(l => l.trim()).map(l => l.split(",")); }

  function build(clientsCsv, promisesCsv) {
    const c = rows(clientsCsv), p = rows(promisesCsv);
    const chh = c[0].map(x => x.trim().toLowerCase());
    const phh = p[0].map(x => x.trim().toLowerCase());
    const ci = n => chh.indexOf(n), pi = n => phh.indexOf(n);
    const clients = {};
    for (let r = 1; r < c.length; r++) {
      const name = c[r][ci("client")];
      if (name) clients[name] = { name, kept: 0, overdue: 0, open: 0 };
    }
    const today = new Date();                                   // the sin: the clock votes
    for (let r = 1; r < p.length; r++) {
      const row = p[r];
      const cl = clients[row[pi("client")]];
      if (!cl) continue;                                        // silently skipped
      const status = row[pi("status")];
      if (status !== "Open") { cl.kept++; continue; }           // done/cancelled/whatever = kept
      const due = new Date(row[pi("due")]);
      if (isNaN(due)) continue;                                 // silently skipped
      if (due < today) cl.overdue++; else cl.open++;
    }
    const people = Object.values(clients);
    const kept = people.reduce((s, x) => s + x.kept, 0);
    const overdue = people.reduce((s, x) => s + x.overdue, 0);
    const open = people.reduce((s, x) => s + x.open, 0);
    const rate = kept + overdue ? (kept / (kept + overdue)) * 100 : 100;
    return { people, clients: people.length, kept, overdue, open,
      keptRate: +rate.toFixed(1), display: rate.toFixed(1) + "% kept" };
  }
  root.CP_V1 = { build };
})(typeof window !== "undefined" ? window : (typeof module !== "undefined" ? module.exports : this));
