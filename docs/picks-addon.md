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
