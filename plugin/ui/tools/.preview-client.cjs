var __create = Object.create;
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __getProtoOf = Object.getPrototypeOf;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
  // If the importer is in node compatibility mode or this is not an ESM
  // file that has been converted to a CommonJS file using a Babel-
  // compatible transform (i.e. "__esModule" has not been set), then set
  // "default" to the CommonJS "module.exports" for node compatibility.
  isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
  mod
));
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

// src/client.tsx
var client_exports = {};
__export(client_exports, {
  NS: () => NS,
  WhaleTvSection: () => WhaleTvSection,
  default: () => client_default,
  en: () => en,
  zh: () => zh
});
module.exports = __toCommonJS(client_exports);
var React = __toESM(require("react"), 1);
var import_jsx_runtime = require("react/jsx-runtime");
var NS = "whale-tv";
var en = {
  nav: "Whale-chan TV",
  title: "Whale-chan TV",
  subtitle: "Android TV assistant \u2014 press the TV button, talk, and DSH drives the TV.",
  sectionTvs: "Choose a TV on your network",
  sectionPair: "Pair this TV",
  scanning: "Scanning your network for Android TVs\u2026",
  scanAgain: "Scan again",
  daemonDown: "The Whale-chan daemon is not answering.",
  daemonDownHint: "Start it on the Mac: python3 host/whale_voice.py --serve \u2014 then scan again.",
  noTvs: "No TVs found on this network.",
  noTvsHint: "Turn the TV on, open Whale-chan there, then scan again.",
  running: "Daemon running",
  stopped: "Daemon not running",
  generateQr: "Generate pairing QR code",
  waiting: "Waiting for approval \u2014 scan the QR with your phone and tap Approve.",
  approved: "Paired. The TV now has this Mac.",
  qrHint: "On the TV, open \u201CPair this TV with Whale-chan\u201D, then scan this code.",
  codeLabel: "Code",
  urlLabel: "Or open",
  tvUnknown: "Android TV",
  pairFailed: "Could not create a pairing code."
};
var zh = {
  nav: "\u9CB8\u5A18\u7535\u89C6",
  title: "\u9CB8\u5A18\u7535\u89C6",
  subtitle: "\u5B89\u5353\u7535\u89C6\u52A9\u624B \u2014 \u6309\u4E0B\u7535\u89C6\u6309\u94AE\u8BF4\u8BDD\uFF0CDSH \u64CD\u4F5C\u7535\u89C6\u3002",
  sectionTvs: "\u9009\u62E9\u7F51\u7EDC\u4E0A\u7684\u7535\u89C6",
  sectionPair: "\u914D\u5BF9\u6B64\u7535\u89C6",
  scanning: "\u6B63\u5728\u626B\u63CF\u7F51\u7EDC\u4E2D\u7684\u5B89\u5353\u7535\u89C6\u2026",
  scanAgain: "\u91CD\u65B0\u626B\u63CF",
  daemonDown: "\u9CB8\u5A18\u540E\u53F0\u6CA1\u6709\u54CD\u5E94\u3002",
  daemonDownHint: "\u5148\u5728 Mac \u4E0A\u542F\u52A8\uFF1Apython3 host/whale_voice.py --serve\uFF0C\u7136\u540E\u91CD\u65B0\u626B\u63CF\u3002",
  noTvs: "\u6B64\u7F51\u7EDC\u672A\u53D1\u73B0\u7535\u89C6\u3002",
  noTvsHint: "\u6253\u5F00\u7535\u89C6\u5E76\u5728\u4E0A\u9762\u6253\u5F00\u9CB8\u5A18\uFF0C\u7136\u540E\u91CD\u65B0\u626B\u63CF\u3002",
  running: "\u540E\u53F0\u8FD0\u884C\u4E2D",
  stopped: "\u540E\u53F0\u672A\u8FD0\u884C",
  generateQr: "\u751F\u6210\u914D\u5BF9\u4E8C\u7EF4\u7801",
  waiting: "\u7B49\u5F85\u6279\u51C6 \u2014 \u7528\u624B\u673A\u626B\u63CF\u4E8C\u7EF4\u7801\u5E76\u70B9\u51FB\u6279\u51C6\u3002",
  approved: "\u5DF2\u914D\u5BF9\uFF0C\u7535\u89C6\u5DF2\u83B7\u5F97\u8FD9\u53F0 Mac \u7684\u5730\u5740\u3002",
  qrHint: "\u5728\u7535\u89C6\u4E0A\u6253\u5F00\u201CPair this TV with Whale-chan\u201D\uFF0C\u7136\u540E\u626B\u63CF\u6B64\u4E8C\u7EF4\u7801\u3002",
  codeLabel: "\u9A8C\u8BC1\u7801",
  urlLabel: "\u6216\u6253\u5F00",
  tvUnknown: "\u5B89\u5353\u7535\u89C6",
  pairFailed: "\u65E0\u6CD5\u751F\u6210\u914D\u5BF9\u7801\u3002"
};
function translatorOf(props) {
  return (key) => props && typeof props.t === "function" ? props.t(key) : en[key] ?? key;
}
var T = (name) => `var(--dsw-alias-${name})`;
var card = {
  background: T("bg-layer-2"),
  border: `1px solid ${T("border-l3")}`,
  borderRadius: 12,
  padding: 14
};
var row = (active) => ({
  display: "flex",
  flexWrap: "wrap",
  alignItems: "center",
  justifyContent: "space-between",
  gap: 8,
  width: "100%",
  textAlign: "left",
  cursor: "pointer",
  background: active ? T("bg-layer-3") : "transparent",
  border: `1px solid ${active ? T("brand-primary") : T("border-l2")}`,
  borderRadius: 10,
  padding: "10px 12px",
  color: T("label-primary")
});
var button = {
  background: T("button-primary-fill"),
  color: T("label-primary-foreground"),
  border: "none",
  borderRadius: 8,
  padding: "8px 14px",
  cursor: "pointer",
  fontSize: 13
};
var ghost = {
  ...button,
  background: "transparent",
  border: `1px solid ${T("border-l2")}`,
  color: T("label-primary")
};
function WhaleTvSection(props) {
  const t = translatorOf(props);
  const preview = props.preview;
  const [phase, setPhase] = React.useState(preview?.phase ?? "loading");
  const [devices, setDevices] = React.useState(preview?.devices ?? []);
  const [selected, setSelected] = React.useState(preview?.devices?.[0]?.host ?? null);
  const [pair, setPair] = React.useState(preview?.pair ?? null);
  const [pairState, setPairState] = React.useState(preview?.pairState ?? "idle");
  const [error, setError] = React.useState(preview?.error ?? "");
  const scan = React.useCallback(async () => {
    setPhase("loading");
    setError("");
    try {
      const [status, found] = await Promise.all([
        fetch("/whale-chan/status").then((r) => r.json()),
        fetch("/whale-chan/devices").then((r) => r.json())
      ]);
      if (status && status.daemon === false) {
        setError(String(status.error || ""));
        setPhase("error");
        return;
      }
      const list = Array.isArray(found.devices) ? found.devices : [];
      setDevices(list);
      setSelected((prev) => prev && list.some((d) => d.host === prev) ? prev : list[0]?.host ?? null);
      setPhase(list.length > 0 ? "ready" : "empty");
    } catch (err) {
      setError(String(err?.message || err));
      setPhase("error");
    }
  }, []);
  React.useEffect(() => {
    if (preview) return;
    void scan();
  }, [scan, preview]);
  const generate = React.useCallback(async () => {
    setPair(null);
    setPairState("idle");
    try {
      const info = await fetch("/whale-chan/pair/new", { method: "POST" }).then((r) => r.json());
      if (!info || info.ok === false) {
        setError(String(info?.error || t("pairFailed")));
        return;
      }
      setPair(info);
      setPairState("pending");
    } catch (err) {
      setError(String(err?.message || err));
    }
  }, [t]);
  React.useEffect(() => {
    if (preview) return;
    if (pairState !== "pending" || !pair) return;
    const timer = setInterval(async () => {
      try {
        const state = await fetch("/whale-chan/pair/status?id=" + encodeURIComponent(pair.id)).then((r) => r.json());
        if (state && state.approved) setPairState("approved");
      } catch {
      }
    }, 1500);
    return () => clearInterval(timer);
  }, [pair, pairState, preview]);
  const statusLabel = phase === "error" ? t("stopped") : t("running");
  const statusColor = phase === "error" ? T("label-error") : T("brand-primary");
  return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("section", { style: { display: "flex", flexDirection: "column", gap: 14, padding: 4, color: T("label-primary") }, children: [
    /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("header", { children: [
      /* @__PURE__ */ (0, import_jsx_runtime.jsx)("h2", { style: { margin: 0, fontSize: 16 }, children: t("title") }),
      /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", { style: { margin: "4px 0 0", color: T("label-caption"), fontSize: 12 }, children: t("subtitle") }),
      /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", { style: { margin: "6px 0 0", color: statusColor, fontSize: 12 }, "aria-live": "polite", children: [
        "\u25CF ",
        statusLabel
      ] })
    ] }),
    /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { style: card, children: [
      /* @__PURE__ */ (0, import_jsx_runtime.jsx)("h3", { style: { margin: "0 0 8px", fontSize: 13, color: T("label-caption") }, children: t("sectionTvs") }),
      phase === "loading" && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", { style: { margin: 0, color: T("label-caption"), fontSize: 13 }, "aria-live": "polite", children: t("scanning") }),
      phase === "error" && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { role: "alert", children: [
        /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", { style: { margin: 0, color: T("label-error"), fontSize: 13 }, children: t("daemonDown") }),
        /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", { style: { margin: "4px 0 10px", color: T("label-caption"), fontSize: 12 }, children: [
          error ? error + " \u2014 " : "",
          t("daemonDownHint")
        ] }),
        /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", { style: ghost, onClick: () => void scan(), children: t("scanAgain") })
      ] }),
      phase === "empty" && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [
        /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", { style: { margin: 0, fontSize: 13 }, children: t("noTvs") }),
        /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", { style: { margin: "4px 0 10px", color: T("label-caption"), fontSize: 12 }, children: t("noTvsHint") }),
        /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", { style: ghost, onClick: () => void scan(), children: t("scanAgain") })
      ] }),
      phase === "ready" && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [
        /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { role: "radiogroup", "aria-label": t("sectionTvs"), style: { display: "flex", flexDirection: "column", gap: 8 }, children: devices.map((device) => {
          const active = selected === device.host;
          return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(
            "button",
            {
              role: "radio",
              "aria-checked": active,
              style: row(active),
              onClick: () => setSelected(device.host),
              children: [
                /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", { style: { display: "flex", flexDirection: "column", gap: 2 }, children: [
                  /* @__PURE__ */ (0, import_jsx_runtime.jsx)("strong", { style: { fontSize: 13 }, children: device.label || device.model || t("tvUnknown") }),
                  /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", { style: { color: T("label-caption"), fontSize: 12 }, children: [
                    device.host,
                    ":",
                    device.port
                  ] })
                ] }),
                active && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { "aria-hidden": "true", style: { color: T("brand-primary") }, children: "\u25CF" })
              ]
            },
            device.host
          );
        }) }),
        /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { style: { marginTop: 10 }, children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", { style: ghost, onClick: () => void scan(), children: t("scanAgain") }) })
      ] })
    ] }),
    /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { style: card, children: [
      /* @__PURE__ */ (0, import_jsx_runtime.jsx)("h3", { style: { margin: "0 0 8px", fontSize: 13, color: T("label-caption") }, children: t("sectionPair") }),
      /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", { style: button, onClick: () => void generate(), disabled: !selected, children: t("generateQr") }),
      error && pair === null && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", { style: { margin: "8px 0 0", color: T("label-error"), fontSize: 12 }, children: error }),
      pair && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { style: { marginTop: 12, display: "flex", flexWrap: "wrap", gap: 14, alignItems: "flex-start" }, children: [
        pair.qr ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
          "img",
          {
            src: "data:image/png;base64," + pair.qr,
            alt: t("generateQr"),
            width: 190,
            height: 190,
            style: { background: "#fff", borderRadius: 8, padding: 8 }
          }
        ) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)("code", { style: { fontSize: 12, wordBreak: "break-all", color: T("label-caption") }, children: pair.url }),
        /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { style: { flex: "1 1 200px", minWidth: 180 }, children: [
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", { style: { margin: 0, fontSize: 12, color: T("label-caption") }, children: t("qrHint") }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", { style: { margin: "8px 0 0", fontSize: 13 }, children: [
            t("codeLabel"),
            ": ",
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)("strong", { style: { letterSpacing: 2 }, children: pair.code })
          ] }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", { style: { margin: "4px 0 0", fontSize: 12, color: T("label-caption"), wordBreak: "break-all" }, children: [
            t("urlLabel"),
            " ",
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)("a", { href: pair.url, style: { color: T("brand-primary") }, children: pair.url })
          ] }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", { style: { margin: "8px 0 0", fontSize: 12 }, "aria-live": "polite", children: pairState === "approved" ? t("approved") : t("waiting") })
        ] })
      ] })
    ] })
  ] });
}
var client_default = WhaleTvSection;
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  NS,
  WhaleTvSection,
  en,
  zh
});
