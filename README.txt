THE CLIENT PROMISE TRACKER — free giveaway from "Build It With AI" (Episode 22)

What your business said it would do, for whom, by when — the morning docket, a per-client
kept-on-time rate, the dollars sitting behind the overdue ones, and a printable promise
history for the "you said Tuesday" phone call. All from two files you already keep.

WHAT'S IN THIS FOLDER
- Promise_Tracker.html ... THE TOOL — the finished, tested build. One file. Open it in any
                           browser. No internet, no account, nothing you paste leaves your
                           machine, and it never reads the clock — you type the date.
- sample/clients.csv ..... the episode's sample client list (Stonebriar Kitchen & Bath —
                           fictional; every address is @example.com)
- sample/promises.csv .... the episode's sample promise log
- PROMPTS.txt ............ the exact three prompts from the episode, word for word
- checker.py ............. the independent second implementation (Python) used to verify the
                           tool — run: python3 checker.py clients.csv promises.csv
- engine_v1.js ........... FIRST DRAFT, NOT THE TOOL — kept verbatim, bugs and all (asks your
                           computer what day it is, drops typo'd names silently, calls
                           anything that isn't open "kept")
- engine_v2.js ........... SECOND DRAFT, NOT THE TOOL — kept verbatim (still reads the clock,
                           loses the rows due today, believes completion dates from the
                           future, counts a duplicated client twice)

HOW TO USE IT ON YOUR OWN PROMISES
1. Open Promise_Tracker.html. Press "Try the sample business" to see it work.
2. Make your client list a CSV with columns: Client, Contact, Email.
3. Make your promise log a CSV with columns: Client, Promise, Made, Due, Owner, Status, Done,
   At Stake, Note. Status is open / done / cancelled; At Stake is optional — what the job or
   relationship behind the promise is worth, so the overdue pile gets a price tag.
4. Drop in (or paste) both files, type the as-of date, set your grace and horizon, and read the refusals panel before you
   trust anything. The tool sends nothing and stores nothing.

If your export names its columns differently, hand your file and PROMPTS.txt's first prompt to
an AI assistant and tell it what your software calls things.

HONEST LIMITS
- It keeps the ledger; it does not send the emails, make the calls, or write the apologies.
- Working days are Monday to Friday, with no holiday calendar — be consistent about holidays.
- At Stake prices the relationship behind a promise; it is your estimate, not an invoice.
- The sample studio is fictional. Any resemblance is coincidence.

Found a bug? Ask the AI to fix it — and make it prove the fix against the checker and the
sample files, the way the episode does, not with reassurance.
