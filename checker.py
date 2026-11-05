#!/usr/bin/env python3
"""Independent second implementation of the Client Promise Tracker's rules (shares no code
with the tool). Reads clients.csv + promises.csv, prints a JSON report in the same shape as
engine.js's build(). Money in integer cents; rates in integer tenths of a percent."""
import csv, datetime, io, json, re, sys

DEF = {"graceWd": 0, "dueSoonWd": 5, "watchAt": 3}
MONEY = re.compile(r"^\s*\$?\s*(-?)([0-9][0-9,]*)(?:\.([0-9]{1,2}))?\s*$")
DATE = re.compile(r"^\s*(\d{4})-(\d{2})-(\d{2})\s*$")
EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
ONE = datetime.timedelta(days=1)


def half_up_div(a, b):
    return (2 * a + b) // (2 * b)


def pct_tenths(a, b):
    return half_up_div(a * 1000, b)


def cents(s):
    m = MONEY.match(s or "")
    if not m:
        return None
    frac = m.group(3) or ""
    f = int(frac) * 10 if len(frac) == 1 else (int(frac) if frac else 0)
    v = int(m.group(2).replace(",", "")) * 100 + f
    return -v if m.group(1) == "-" else v


def pdate(s):
    m = DATE.match(s or "")
    if not m:
        return None
    try:
        return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def wd_after_through(a, b):
    n, cur = 0, a + ONE
    while cur <= b:
        if cur.weekday() < 5:
            n += 1
        cur += ONE
    return n


def fmt_money(c):
    return ("-$" if c < 0 else "$") + format(abs(c) / 100, ",.2f")


def fmt_tenths(t):
    return f"{t / 10:.1f}%"


def build(clients_csv, promises_csv, settings=None):
    S = dict(DEF)
    S.update(settings or {})
    as_of = pdate(S.get("asOf"))
    if as_of is None:
        raise ValueError("The Promise Tracker never reads the clock — type the as-of date.")
    cr = [r for r in csv.reader(io.StringIO(clients_csv)) if len(r) > 1 or (r and r[0].strip())]
    pr = [r for r in csv.reader(io.StringIO(promises_csv)) if len(r) > 1 or (r and r[0].strip())]
    chh = [c.strip().lower() for c in cr[0]]
    phh = [c.strip().lower() for c in pr[0]]
    ci = {n: chh.index(n) for n in chh}
    pi = {n: phh.index(n) for n in phh}
    for n in ("client", "contact", "email"):
        if n not in ci:
            raise ValueError("The client file is missing a column.")
    for n in ("client", "promise", "made", "due", "owner", "status", "done", "at stake"):
        if n not in pi:
            raise ValueError("The promise file is missing a column.")
    refused_clients, refused_promises = [], []
    clients, order = {}, []
    client_rows = 0
    for ln, row in enumerate(cr[1:], start=2):
        client_rows += 1
        g = lambda n: (row[ci[n]] if ci[n] < len(row) else "").strip()
        name = g("client")
        if not name:
            refused_clients.append({"line": ln, "name": "(blank)"}); continue
        if name.lower() in clients:
            refused_clients.append({"line": ln, "name": name}); continue
        email = g("email")
        if email and not EMAIL.match(email):
            refused_clients.append({"line": ln, "name": name}); continue
        clients[name.lower()] = {"name": name, "contact": g("contact"), "email": email}
        order.append(name.lower())
    promises = []
    promise_rows = 0
    for ln, row in enumerate(pr[1:], start=2):
        promise_rows += 1
        g = lambda n: (row[pi[n]] if pi[n] < len(row) else "").strip()
        raw = g("client")
        if not raw:
            refused_promises.append({"line": ln, "name": "(blank)"}); continue
        key = raw.lower()
        if key not in clients:
            refused_promises.append({"line": ln, "name": raw}); continue
        promise = g("promise")
        if not promise:
            refused_promises.append({"line": ln, "name": raw}); continue
        made, due = pdate(g("made")), pdate(g("due"))
        if made is None or due is None:
            refused_promises.append({"line": ln, "name": raw}); continue
        if due < made:
            refused_promises.append({"line": ln, "name": raw}); continue
        status = g("status").lower()
        if status not in ("open", "done", "cancelled"):
            refused_promises.append({"line": ln, "name": raw}); continue
        done = None
        if status == "done":
            dv = g("done")
            if not dv:
                refused_promises.append({"line": ln, "name": raw}); continue
            done = pdate(dv)
            if done is None:
                refused_promises.append({"line": ln, "name": raw}); continue
            if done < made:
                refused_promises.append({"line": ln, "name": raw}); continue
        sv = g("at stake")
        stake_c = 0
        if sv:
            c = cents(sv)
            if c is None or c < 0:
                refused_promises.append({"line": ln, "name": raw}); continue
            stake_c = c
        promises.append({"line": ln, "key": key, "name": clients[key]["name"], "promise": promise,
                         "made": made, "due": due, "owner": g("owner") or "(unassigned)",
                         "status": status, "done": done, "stakeC": stake_c, "note": g("note") if "note" in pi else ""})

    buckets = {k: 0 for k in ("keptOnTime", "keptLate", "overdue", "dueToday", "dueSoon", "upcoming", "notYet", "cancelled")}
    for p in promises:
        if p["status"] == "cancelled":
            p["bucket"] = "cancelled"
        elif p["made"] > as_of:
            p["bucket"] = "notYet"
        else:
            eff = p["done"] if (p["status"] == "done" and p["done"] and p["done"] <= as_of) else None
            if eff:
                p["lateWd"] = wd_after_through(p["due"], eff)
                p["bucket"] = "keptOnTime" if p["lateWd"] <= S["graceWd"] else "keptLate"
            elif p["due"] < as_of:
                p["ageWd"] = wd_after_through(p["due"], as_of)
                p["bucket"] = "overdue"
            elif p["due"] == as_of:
                p["bucket"] = "dueToday"
            elif wd_after_through(as_of, p["due"]) <= S["dueSoonWd"]:
                p["bucket"] = "dueSoon"
            else:
                p["bucket"] = "upcoming"
        buckets[p["bucket"]] += 1

    ledgers = []
    for key in order:
        c = clients[key]
        mine = sorted([p for p in promises if p["key"] == key], key=lambda p: (p["due"], p["line"]))
        n = {k: 0 for k in buckets}
        at_stake = oldest = 0
        rows = []
        for p in mine:
            n[p["bucket"]] += 1
            if p["bucket"] == "overdue":
                at_stake += p["stakeC"]
                oldest = max(oldest, p["ageWd"])
            rows.append({"line": p["line"], "promise": p["promise"], "made": p["made"].isoformat(),
                         "due": p["due"].isoformat(), "owner": p["owner"], "bucket": p["bucket"],
                         "lateWd": p.get("lateWd", 0), "ageWd": p.get("ageWd", 0),
                         "stakeC": p["stakeC"], "note": p["note"]})
        came_due = n["keptOnTime"] + n["keptLate"] + n["overdue"]
        rel = pct_tenths(n["keptOnTime"], came_due) if came_due > 0 else None
        flags = ["WATCH"] if n["keptLate"] + n["overdue"] >= S["watchAt"] else []
        ledgers.append({"name": c["name"], "contact": c["contact"], "email": c["email"], "counts": n,
                        "cameDue": came_due, "reliabilityTenths": rel, "atStakeOverdueC": at_stake,
                        "oldestOverdueWd": oldest, "flags": flags, "rows": rows})
    ledgers.sort(key=lambda l: (-l["counts"]["overdue"], -l["counts"]["keptLate"], l["name"].lower()))

    owners_m = {}
    for p in promises:
        if p["bucket"] in ("cancelled", "notYet"):
            continue
        o = owners_m.setdefault(p["owner"], {"owner": p["owner"], "keptOnTime": 0, "keptLate": 0, "overdue": 0, "open": 0})
        if p["bucket"] in ("keptOnTime", "keptLate", "overdue"):
            o[p["bucket"]] += 1
        else:
            o["open"] += 1
    owners = []
    for o in owners_m.values():
        came = o["keptOnTime"] + o["keptLate"] + o["overdue"]
        owners.append({**o, "cameDue": came,
                       "reliabilityTenths": pct_tenths(o["keptOnTime"], came) if came > 0 else None})
    owners.sort(key=lambda o: (-(o["cameDue"] + o["open"]), o["owner"].lower()))

    docket = sorted([p for p in promises if p["bucket"] in ("overdue", "dueToday")],
                    key=lambda p: (p["due"], p["line"]))
    docket = [{"line": p["line"], "name": p["name"], "promise": p["promise"], "owner": p["owner"],
               "due": p["due"].isoformat(), "ageWd": p.get("ageWd", 0), "stakeC": p["stakeC"]} for p in docket]

    b_docket = b_overdue = b_stake = b_kot = b_came = 0
    for p in promises:
        if p["bucket"] == "overdue":
            b_overdue += 1; b_docket += 1; b_stake += p["stakeC"]
        if p["bucket"] == "dueToday":
            b_docket += 1
        if p["bucket"] == "keptOnTime":
            b_kot += 1
        if p["bucket"] in ("keptOnTime", "keptLate", "overdue"):
            b_came += 1
    t_overdue = sum(l["counts"]["overdue"] for l in ledgers)
    t_docket = sum(l["counts"]["overdue"] + l["counts"]["dueToday"] for l in ledgers)
    t_stake = sum(l["atStakeOverdueC"] for l in ledgers)
    t_kot = sum(l["counts"]["keptOnTime"] for l in ledgers)
    t_came = sum(l["cameDue"] for l in ledgers)

    counts = {"clientRows": client_rows, "promiseRows": promise_rows, "clients": len(clients),
              "refusedClients": len(refused_clients), "refusedPromises": len(refused_promises),
              **buckets, "watch": sum(1 for l in ledgers if l["flags"])}
    client_tie = counts["clientRows"] == counts["clients"] + counts["refusedClients"]
    promise_tie = counts["promiseRows"] == sum(buckets.values()) + counts["refusedPromises"]
    board_tie = (b_docket == t_docket and b_overdue == t_overdue and b_stake == t_stake
                 and b_kot == t_kot and b_came == t_came)
    share_c = pct_tenths(counts["refusedClients"], counts["clientRows"]) if counts["clientRows"] else 0
    share_p = pct_tenths(counts["refusedPromises"], counts["promiseRows"]) if counts["promiseRows"] else 0
    trusted = client_tie and promise_tie and board_tie and share_c <= 250 and share_p <= 250
    banner = ""
    if not trusted:
        if not client_tie:
            banner = "DO NOT TRUST THIS DOCKET — the client rows do not tie."
        elif not promise_tie:
            banner = "DO NOT TRUST THIS DOCKET — the promise rows do not tie."
        elif not board_tie:
            banner = "DO NOT TRUST THIS DOCKET — the board does not re-total from the ledgers."
        else:
            banner = ("DO NOT TRUST THIS DOCKET — too many rows refused (clients "
                      + f"{share_c / 10:.1f}" + "%, promises " + f"{share_p / 10:.1f}"
                      + "%). Fix the export and run it again.")

    return {"settings": {"asOf": S["asOf"], "graceWd": S["graceWd"], "dueSoonWd": S["dueSoonWd"], "watchAt": S["watchAt"]},
            "counts": counts,
            "company": {"docket": t_docket, "overdue": t_overdue, "atStakeOverdueC": t_stake,
                        "keptOnTime": t_kot, "cameDue": t_came,
                        "reliabilityTenths": pct_tenths(b_kot, b_came) if b_came > 0 else None,
                        "boardDocket": b_docket, "boardOverdue": b_overdue, "boardStakeC": b_stake,
                        "boardKot": b_kot, "boardCameDue": b_came},
            "docket": docket, "ledgers": ledgers, "owners": owners,
            "notYet": [{"line": p["line"], "name": p["name"], "promise": p["promise"],
                        "made": p["made"].isoformat(), "due": p["due"].isoformat(), "owner": p["owner"]}
                       for p in promises if p["bucket"] == "notYet"],
            "cancelled": [{"line": p["line"], "name": p["name"], "promise": p["promise"],
                           "due": p["due"].isoformat(), "note": p["note"]}
                          for p in promises if p["bucket"] == "cancelled"],
            "refusedClients": [[r["line"], r["name"]] for r in refused_clients],
            "refusedPromises": [[r["line"], r["name"]] for r in refused_promises],
            "historiesWithheld": not trusted,
            "recon": {"clientTie": client_tie, "promiseTie": promise_tie, "boardTie": board_tie,
                      "shareClients_tenths": share_c, "sharePromises_tenths": share_p, "trusted": trusted,
                      "banner": banner}}


if __name__ == "__main__":
    clients = open(sys.argv[1]).read()
    promises = open(sys.argv[2]).read()
    st = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {"asOf": "2026-11-05"}
    print(json.dumps(build(clients, promises, st), indent=1))
