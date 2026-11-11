# Configuring a metadata addon as JSON

`host/addon_config.py` — set up [AIOmetadata](https://aiometadata.elfhosted.com/configure/)
by writing JSON instead of clicking a configurator or typing a long URL with a remote.

AIOmetadata is what most people use for catalogs and metadata in Nuvio and Stremio. Its
configurator is a web UI over a small JSON API, and both players install the result as a
normal addon — so the whole thing is scriptable:

```
POST /api/config/save            {config, password}  -> {userUUID, installUrl}
POST /api/config/load/<uuid>     {password}          -> {config, installUrl}
PUT  /api/config/update/<uuid>   {config, password}  -> {config, installUrl}
GET  /stremio/<uuid>/manifest.json                   -> the configured addon
```

`update` is **PUT**, not POST — `POST /api/config/update/<uuid>` returns 404 against the
live instance. That cost one debugging round; noting it so it does not cost another.

## Commands

```bash
cd dsh-tv/host

./addon_config.py new   --config spec.json        # create → prints the install URL
./addon_config.py from  --out current.json        # dump the JSON (schema + your keys)
./addon_config.py apply --config edited.json      # PUT the edit → new install URL
./addon_config.py show                            # what is stored, secrets redacted
```

Credentials go to `~/.dsh/aiometadata.json` (mode 0600, outside any repo) the first time
you run `new`, so `from` and `apply` need no flags. Nothing prints the password.

`new` generates a password if you do not pass `--password`. Keep it: it is the only thing
protecting the config on a shared instance — `load` with a wrong password is a 401, with
the right one it returns your config.

## Two things it gets right

**It verifies.** After every save it fetches the `installUrl` and reports what came back:

```json
"manifest": { "ok": true, "name": "AIOMetadata | ElfHosted", "version": "3.8.3",
              "catalogs": 10, "resources": ["catalog","meta"] }
```

An empty spec still yields 10 default catalogs, so a fresh config is usable immediately.
If that block says `ok: false`, the URL is wrong and you find out here instead of on the TV.

**It never logs the password.** `show` prints `"password": "<24 chars>"`.

## The workflow that matters

The interesting path is not "create from scratch" — it is **edit an existing setup**:

```bash
./addon_config.py from --out current.json     # your real config, with its keys
# edit current.json — add catalogs, reorder providers, fix a broken source
./addon_config.py apply --config current.json
```

That is the thing a human cannot do comfortably: 20+ catalogs, providers and metadata
sources in a web form, with no way to check the result. An agent can diff the JSON, keep
the API keys untouched, and hand back one URL.

## Installing the result

Paste the `installUrl` into Nuvio (**Addons → Install addon**) or Stremio (**Addons → Install
from URL**). On the TV, the bridge's `text` command can type it into that field, and the
Addons screen is accessibility-readable afterwards — so the install can be verified rather
than assumed:

```
"Nuvio addons screen → 'Cinemeta · v3.0.14 · Catalogs: 8 · https://v3-cinemeta.strem.io'"
```

## Caveats

- **API keys travel in the config** (TMDB, TVDB, MAL, Fanart). Treat the JSON as a secret;
  never screenshot it or paste it into a post.
- **The public instance is someone else's server.** Configs live in their database. If this
  becomes part of the product, self-host [cedya77/aiometadata](https://github.com/cedya77/aiometadata)
  (Docker) — then the API is yours and the third-party dependency is gone.
- **Metadata addons only.** This configures catalogs and metadata. Stream add-ons
  (AIOStreams, Torrentio and friends) are a separate manifest each.

## Next: DeepSeek TV as an addon

Nuvio and Stremio speak the same addon protocol, so the reverse direction is available too:
DeepSeek TV could serve its own manifest and appear **inside** the player as a catalog
rather than as an overlay that drives it. Same protocol, one implementation, both apps —
and it makes the agent a first-class part of the player instead of an accessibility
automation on top of it.
