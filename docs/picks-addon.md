# DeepSeek Picks — a catalog addon built on the fly

`host/addon_server.py` serves a Stremio/Nuvio **catalog** addon whose rows are generated
at request time. The agent decides what belongs in a row; the player renders it as a
normal shelf; the streams come from whichever stream addon is already installed.

## Why the ids are the whole trick

Stream addons (Torrentio, Comet, AIOStreams) key their results by **IMDB id**. A catalog
row is only useful if every item carries a real `tt…`, so picks are *ids plus a reason* —
never invented titles. Name, poster, year and rating are enriched from Cinemeta at request
time, so nothing is guessed:

```
picks.json  {"movie": ["tt0111161","tt1375666"], "series": ["tt0903747"]}
                 │
                 ▼  Cinemeta → name, poster, releaseInfo, imdbRating
catalog     {"metas":[{"id":"tt0903747","type":"series","name":"Breaking Bad", …}]}
```

Edit `picks.json` while the server runs — the catalog reloads on mtime, no restart.

## Endpoints

```
GET /<token>/manifest.json
GET /<token>/catalog/<type>/<id>.json
GET /<token>/catalog/<type>/<id>/skip=N.json        # pagination: a whole extra segment
GET /<token>/meta/<type>/<id>.json
```

The `skip=` form matters: Nuvio paginates by requesting `/catalog/movie/deepseek/skip=4.json`,
which is four path segments, not three. Serving only the three-segment shape answers 404
and the row silently stops loading more.

## Run it

```bash
cd dsh-tv/host
python3 addon_server.py --port 8890 --token "$(openssl rand -hex 8)"
# then install http://<mac-ip>:8890/<token>/manifest.json in Nuvio → Addons → Install addon
```

## Verified

- Nuvio fetched the manifest from the LAN and rendered a native **DeepSeek · Series** row
  showing Breaking Bad and Game of Thrones.
- Server log is the proof, not a screenshot:
  `192.168.4.58 "GET /<token>/catalog/series/deepseek.json" 200`

## Known gaps

- **Streams need a stream addon.** With only Cinemeta installed a title opens with no
  sources. Install Torrentio or Comet and the same `tt…` ids resolve there — that is the
  half of the concept not yet exercised.
- **Catalog metadata only.** `resources: ["catalog"]`; no `meta` endpoint is exercised by
  the row, so the player falls back to its own metadata addon for details.
- **The process is not supervised.** It runs from a shell and dies with it; a LaunchAgent
  would need Removable Volumes/FDA to read the repo on the external volume (macOS blocks
  launchd-run `python3` from `/Volumes/External SSD` — `kTCCServiceSystemPolicyRemovableVolumes`).

## Status, 2026-11-11 — catalog works, install does not persist

Verified working:

- Nuvio fetched the manifest and **rendered the row** (Breaking Bad, Game of Thrones) —
  server log: `192.168.4.58 "GET /<token>/catalog/series/deepseek.json" 200`.
- The catalog serves real, confirmed IMDB ids and paginates on `/skip=N/`.

Not working:

- Re-adding it does not stick. Nuvio fetches the manifest (`200`, logged) and then never
  enters it into its manifest cache — the count stays `Loaded 17 cached manifests from disk`
  across restarts. The addon is absent from the Installed list.

Two candidate causes, neither confirmed:

1. **Nuvio validates more strictly than Stremio.** Our manifest lacks `addonCatalogs`
   (Cinemeta has it, but it should be optional). Next test: serve Cinemeta's manifest
   verbatim from this host — if *that* installs, the fault is a field in ours and can be
   bisected.
2. **HTTPS.** `stremio://<host>/<path>/manifest.json` resolves to `https://` and failed
   against this HTTP server with "error sending request". If Nuvio has the same expectation
   for persisted addons, the fix is to serve over TLS (or a tunnel), not to change the
   manifest.

Either answer is one experiment away; the addon code itself is not the suspect, since the
row rendered from it once.

## Research tool

`host/picks_research.py` turns a researched list into `picks.json`:

```bash
./picks_research.py --spec research.json
```

It resolves every title through Cinemeta and **confirms the id resolves on its own** before
writing it. Two things it caught on the first real run, which is the argument for the tool:

| Asked | Naive name match | Truth |
|---|---|---|
| Perfect Day (2023) | tt0491100 — a 2005 British film | tt27503384 *Perfect Days* (Wenders, 2023) |
| Balloon (2019) | tt7125774 — 2018 Germany/France/US | Pema Tseden's Balloon is not in Cinemeta; dropped |

A row with the wrong film in it is worse than a short row, so unresolved titles are
reported, never guessed. Year hints (`{"title": "Perfect Day", "year": 2023}`) filter hard,
and the output prints year + country for every hit so a wrong match is visible rather than
plausible.

## Metadata source: TMDB, not Cinemeta

Stremio ships Cinemeta, and most people hide it in favour of TMDB through AIOmetadata —
so enriching from Cinemeta would style every row with the addon they turned off. The addon
now takes a metadata base and prefers it:

```bash
python3 addon_server.py --port 8890 --token <t> \
  --aiometadata "https://aiometadata.elfhosted.com/stremio/<your-uuid>"
```

Verified: posters come back as `image.tmdb.org/t/p/w600_and_h900_bestv2/…` with director and
runtime, straight from the AIOmetadata instance already installed on the player. Cinemeta
stays only as a fallback, so the addon still works on a box with nothing else configured.
No TMDB API key is needed on our side — the instance holds it.

## Resolution source: TMDB, because Cinemeta can't surface current films

The complaint about Cinemeta is not that it is old — it is that films in cinemas never
appear. Measured, that is precise and it is not about the data:

| Title (TMDB trending, 2026) | Cinemeta search | TMDB search |
|---|---|---|
| Other Mommy | tt36586020 | tt36586020 |
| Model Citizen | tt13884466 | tt13884466 |
| The Odyssey | tt33764258 | tt33764258 |
| The Good Lawyer | tt39453578 | tt39453578 |

Cinemeta **can find** every current film by name. It cannot **surface** one: its manifest is
eight catalogs — Popular / New / Featured for movie and series — whose only extras are
`genre`, `search`, `skip`. There is no release-status, no upcoming, no "in cinemas". Unless
you already know the title, current releases never reach a row. That is why MDBList's builder
carries *Release Status*, *Has Release*, *Release From/To* and *Upcoming* as first-class
filters — vocabulary Cinemeta does not have.

So resolution now prefers TMDB on the player's own AIOmetadata instance:

```bash
./picks_research.py --spec research.json \
  --aiometadata "https://aiometadata.elfhosted.com/stremio/<uuid>"
```

Verified on four 2026 releases: all resolved with year and production country
(`The Odyssey` → tt33764258, UK/US; `The Good Lawyer` → tt39453578, France). Cinemeta stays as
the fallback when no instance is configured, and is still fine for back-catalogue work.

This also means our addon is the thing Cinemeta structurally cannot be: a row that contains
what is out *now*, because the agent supplies the ids and no filter vocabulary is required.

## Bespoke catalogs: many rows, built on request

The point is not one row — it is that the agent builds a *new* row whenever asked, and the
earlier ones stay. The store is `host/catalogs.json`:

```json
[{ "id": "chinese-new-wave", "type": "movie", "name": "Like The Breaking Ice",
   "seed": "The Breaking Ice + Perfect Days",
   "theme": "quiet contemporary East Asian cinema", "picks": ["tt17052842", "..."] },
 { "id": "in-cinemas", "type": "movie", "name": "In Cinemas Now", "picks": ["tt36586020", "..."] }]
```

The manifest is generated from that file, so every bespoke catalog becomes its own row in
the player, and adding another never touches the server code:

```bash
./picks_research.py --spec research.json --catalogs catalogs.json \
    --catalog-id japanese-slow --catalog-name "Japanese Slow Cinema" \
    --aiometadata "https://aiometadata.elfhosted.com/stremio/<uuid>"
```

Verified: two rows, served independently — `chinese-new-wave` (17 titles, 0.68s) and
`in-cinemas` (4 titles, 0.50s), each resolving its own metadata through TMDB.

### Stremio installs it; Nuvio does not

Stremio fetched the manifest and completed the install in-app (the screen switched to
Uninstall), where Nuvio fetched the manifest and then dropped it from its cache. So the
addon target is Stremio — the larger audience and the player that works — and the Nuvio
persistence problem is no longer blocking.

![Bespoke rows in Stremio](picks-rows-stremio.jpg)

**Verified working in Stremio.** Both bespoke rows render on the board — *"Like The Breaking
Ice"* (17 titles) and *"In Cinemas Now"* (4 titles) — and the server log is the proof, not a
screenshot:

```
00:43:48  192.168.4.58  GET /catalog/movie/in-cinemas.json           200
00:43:48  192.168.4.58  GET /catalog/movie/chinese-new-wave.json     200
00:43:49  192.168.4.58  GET /catalog/movie/in-cinemas/skip=4.json    200
00:44:02  192.168.4.58  GET /catalog/movie/chinese-new-wave/skip=17.json  200
```

The `skip=` lines are the pagination fix doing its job — without it the row stops growing
silently. The rows required a Stremio restart before the board rebuilt; that was the only
thing standing between "installed" and "visible".

## Deployment: local and private, by design

A bespoke catalog *is* the person's taste, so hosting it on shared infrastructure inverts the
idea — the recommendations would live on someone else's server. The addon therefore belongs
on the machine that already holds the agent, one instance per person, reachable on the LAN.

That makes the deployment problem "keep a local process alive", not "find a host". Two facts
shaped the answer:

1. **It must live on the internal disk.** launchd cannot read `/Volumes/External SSD`
   without Removable Volumes / Full Disk Access — it fails with `Operation not permitted`.
   That is precisely what killed the old `com.jp-iptv.serve` agent. So the addon is installed
   to `~/Library/Application Support/dsh-tv-addon/` and reads its catalogs from there.
2. **launchd with `KeepAlive` is enough.** No tunnel, no container, no subscription.

Template: `host/com.muen.dshtv-addon.plist.example`.

```bash
mkdir -p ~/Library/Application\ Support/dsh-tv-addon
cp host/addon_server.py host/catalogs.json host/picks.json \
   ~/Library/Application\ Support/dsh-tv-addon/
# fill in the token and AIOmetadata uuid in the example, then:
cp host/com.muen.dshtv-addon.plist.example ~/Library/LaunchAgents/com.muen.dshtv-addon.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.muen.dshtv-addon.plist
```

Verified: killing the process (`kill -9`) brings it back within seconds — pid 34084 → 34153,
manifest still `200`, both rows still listed. The URL does not change, so Stremio keeps
working across restarts.

Privacy posture, stated plainly: the token is the only credential, anyone on the LAN who has
the URL can read the picks, and Stremio accepts the plain-HTTP LAN URL (Nuvio does not
persist it). That is the right trade for a home instance and the wrong one for anything
reachable from the internet.

## Any private source, not just IMDB

A catalog full of `tt…` ids is only half the idea: IMDB ids work because Torrentio/Comet
already index them. For a source that no stream addon knows about — a personal account, a
private archive, anything you host — the addon has to carry the URL itself.

The manifest adapts: when the store holds a direct catalog, it advertises `meta` and `stream`
alongside `catalog`, and mints ids under its own prefix so they can never collide with `tt…`:

```
"resources":   ["catalog", "meta", "stream"]
"idPrefixes":  ["tt", "dsv"]
```

```bash
./catalog_add.py --catalog-id private-archive --catalog-name "My Archive" --items items.json
```

`items.json` is `[{ "name", "url", "poster"?, "description"?, "releaseInfo"? }]`. The item id is
derived (`dsv:<catalog>:<n>`), so the row is stable across restarts.

Verified with two public test assets: `catalog/movie/test-direct.json` listed them under `dsv:`
ids, `stream/movie/dsv:test-direct:0.json` returned the playable URL, and
`meta/movie/dsv:test-direct:1.json` returned its metadata. The test row was then removed.

## Logging is content-neutral by default

A private catalog is only private if its log is. The server no longer logs the request path —
that carries the token, and for direct items it would name the row. It logs the route shape
only:

```
[00:50:54] 192.168.4.57 200 manifest
[00:50:58] 192.168.4.57 200 catalog movie/test-direct
[00:50:58] 192.168.4.57 200 stream movie
```

No token, no item URL, no title. This is the default rather than a flag, because the sensitive
case is the one nobody remembers to configure.

## One command to install, on any Mac

No external SSD required — in fact the internal disk is mandatory, for the reason above.

```bash
cd dsh-tv/host
DSHTV_AIO_METADATA="https://aiometadata.elfhosted.com/stremio/<your-uuid>" \
  bash deploy.sh
```

It creates `~/Library/Application Support/dsh-tv-addon/`, copies the code, seeds an empty
catalog store, writes and loads the launchd agent, and prints the URL to paste into Stremio:

```
running — http://192.168.x.x:8890/<token>/manifest.json
manifest: DeepSeek Picks v0.1.0 · resources=['catalog']
rows: ['Like The Breaking Ice', 'In Cinemas Now']
```

Re-running it is safe: the token and metadata source are kept in `config.env` so the URL never
changes under the installed addon, and existing catalogs are left alone.

### One writable copy of each thing

| | lives | why |
|---|---|---|
| **code** | the repo, copied down by `deploy.sh` | one source of truth, and the deploy is explicit |
| **data** (`catalogs.json`) | only in `~/Library/Application Support/dsh-tv-addon/` | the server reads it, the agent's tools write it — a second copy would be the Silt defect |

`catalogs.json` is gitignored and the repo ships `catalogs.example.json` instead. The tools
default to the live path, so `catalog_add.py` with no flags writes exactly where the server
reads:

```
$ ./catalog_add.py --catalog-id deploy-test --catalog-name "Deploy Test" --items items.json
  wrote: ~/Library/Application Support/dsh-tv-addon/catalogs.json
```

And the new row appears immediately — the store is read per request, so no restart:

```
rows: ['Like The Breaking Ice', 'In Cinemas Now', 'Deploy Test']
```

## The assistant can build a row — and must prove it

The voice daemon's brain is a full DSH turn, so "make me a catalog of X" is a tool call away.
The first attempt showed why that is not enough: asked for *"a catalog of japanese slow cinema
like perfect days"*, the assistant researched 18 real films (Ozu, correctly), wrote them to
`host/catalogs.ready.json` — the wrong path — and then replied:

> "Done — the Japanese Slow Cinema row is live in Stremio with all 18 films."

The store still had two rows. The research was right; the claim was false.

`host/install_catalog.py` removes both degrees of freedom. It takes a store-shaped file,
verifies **every** id resolves (an id that starts with `tt` is not a film), merges the row into
the live store, then fetches the manifest to confirm the row is really there — and prints the
only sentence worth saying:

```
OK row=japanese-slow name="Japanese Slow Cinema" picks=18 verified=yes
```

The brief now permits one path and one claim: run that exact command, and never say a catalog
was made unless the last line starts with `OK`.

### Still broken on the TV side

- **Voice capture** — reported failing by the user; the send button only commits an in-flight
  recording, so with capture broken it is a no-op.
- **Typed entry** — the keyboard button and dialog exist and the field accepts remote typing,
  but `AlertDialog` on this overlay does not receive D-pad events, so OK/submit is unreachable.
  The fix is not another handler: put the field in the overlay layout itself so it shares the
  window that already handles D-pad focus.
- **Long turns** — a catalog build takes 3-5 minutes, which exceeds the synchronous `/ask`
  timeout (`MAX_TURN_SECONDS`, currently 300). It needs to answer "on it" immediately and
  report when done, instead of holding the request open.

## The assistant drafts; the host applies

The reason the assistant once produced a row at the wrong path and then claimed success is not
sloppiness — it is a sandbox. The voice brain runs as `dsh --profile headless`, which can only
write inside the workspace. The live store is at `~/Library/Application Support/dsh-tv-addon/`,
outside it. So:

- writing to the "right" path returned **`Operation not permitted`**
- the only writable place was the repo, which is why `catalogs.ready.json` appeared there
- and the assistant could not see the live store at all, so "it's live" was never checkable

The fix splits the job along the permission boundary:

| who | does |
|---|---|
| **assistant** (sandboxed) | drafts `.dsh-voice/pending-catalogs/<slug>.json` |
| **daemon** (ordinary process) | applies it with `install_catalog.py`, then moves it to `done/` |

The daemon appends the verdict to the spoken reply, so the sentence the household hears is
written where the permission is — not where the optimism is.

Verified end to end:

```
ask: "make me a catalog of south korean revenge films"
reply: "South Korean Revenge is queued with 15 films, from Oldboy and Lady Vengeance to
        Kill Boksoon — the host will add it to the row. (South Korean Revenge, 15 titles is live.)"
store: korean-revenge  South Korean Revenge  15 picks
```

Also raised `MAX_TURN_SECONDS` to 600 and the client read timeout to 650 s: a catalog build is
not a question, and a 3-5 minute one was returning 504.

## Conformance: Stremio's linter judges the manifest, not us

`host/conformance/validate.js` runs our manifest through
[`stremio-addon-linter`](https://www.npmjs.com/package/stremio-addon-linter) — MIT, maintained by
the people who define the protocol — and `deploy.sh` now fails if it objects:

```bash
cd host/conformance && npm install     # once; node_modules is gitignored
bash host/deploy.sh
# conformance: {"ok":true,"addon":"com.muen.deepseek.tv", …, "catalogs":4,"errors":[],"warnings":[]}
```

Why it matters: two of the defects this project hit — the four-segment `skip=` pagination route
and Nuvio refusing to persist the addon — were found by trial and error against a closed player.
A protocol-level check catches the class of problem that does not depend on which player is
looking.

Both shapes are verified, and the gate is verified to actually fail:

| Manifest | Result |
|---|---|
| live addon, 4 catalogs | `ok: true`, no errors, no warnings |
| private-source shape (`catalog`+`meta`+`stream`, `dsv` ids) | `ok: true` |
| deliberately broken (no `version`) | `ok: false` — *"manifest.version must be a valid semver string"*, exit 1 |

## One-command install, and the row-snapshot limit

`host/install_addon.py` installs or refreshes the addon in Stremio with no typing: it launches
Stremio, returns to the board, opens Add addons, types the URL, presses ADD and Install, and
confirms by checking the screen offers **Uninstall**. Typing goes through adb, not the bridge —
`/text` needs the accessibility service, which every APK update disables, so relying on it made
installing depend on a setting.

Verified: `{"ok": true, "confirmed_by": "the add-on screen offers Uninstall"}`. The assistant can
run it on request too — asked *"install my catalog rows in stremio"* it did, in 9.7 s, and said
so accurately.

### The limit it exposed

Adding a row after install does **not** make it appear, and this is not a caching problem:

| | |
|---|---|
| live manifest | 4 catalogs (`chinese-new-wave`, `in-cinemas`, `japanese-slow`, `korean-revenge`) |
| Stremio fetched it | `[02:42:19] 192.168.4.58 200 manifest` |
| catalogs Stremio ever requested | only `chinese-new-wave`, `in-cinemas` |
| board | the two original rows, never the two newer ones |

Stremio snapshots the catalog list when the addon is *added*; a refreshed manifest updates an
existing row's contents but not the set of rows. So "the agent builds a row, it appears" holds
only for rows that existed at install time.

Two ways out, and the trade is names vs steps:

1. **Fixed slots** — declare e.g. six rows once; the store maps bespoke catalogs into them. Rows
   then appear with no further interaction, but their names are fixed by the manifest, so the
   agent cannot title them.
2. **Automated remove + re-add** — a true rebuild of the row set, which `install_addon.py` could
   do, giving meaningful names at the cost of running a ~40 s UI sequence after each new row.

Neither is obviously right; the choice depends on whether a named row is worth 40 seconds.

## Fixed slots — the design the row snapshot forces

Because Stremio snapshots the catalog list at add time, the manifest now declares a **fixed set
of six rows** and the agent writes catalogs *into slots* instead of creating rows:

```
slot-1  DeepSeek · Tonight        (free)
slot-2  DeepSeek · More like this ← Like The Breaking Ice (17)
slot-3  DeepSeek · In cinemas     ← In Cinemas Now (4)
slot-4  DeepSeek · Deep cuts      ← Japanese Slow Cinema (18)
slot-5  DeepSeek · By theme       ← South Korean Revenge (14)
slot-6  DeepSeek · Newest         (free)
```

`install_catalog.py` assigns the first free slot (or keeps the slot a catalog already had) and
verifies by **fetching that slot** and checking it returns this catalog's ids:

```
OK slot=5 name="South Korean Revenge" picks=14 verified=yes
```

Slot names are categories, not titles, because the names live in the manifest too — that is the
price of rows appearing without touching the player. The agent picks the slot whose meaning fits
the row it built.

Verified: conformance passes with six catalogs; slots 2–5 each serve their own titles and slots
1 and 6 serve nothing (correctly, as empty rows).

### The one-time step that is still manual

Adopting the new row **ids** needs Stremio to re-read the catalog list, which it only does on a
fresh add — re-adding the same URL updates the manifest but keeps the old row set. So after this
change, the addon has to be removed and added once in Stremio. After that, filling a slot needs
no player interaction at all, which is the point of the design.
