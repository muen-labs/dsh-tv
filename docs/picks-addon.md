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
