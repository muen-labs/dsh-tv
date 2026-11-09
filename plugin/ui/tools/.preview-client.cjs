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
var React2 = __toESM(require("react"), 1);

// src/ui.tsx
var React = __toESM(require("react"), 1);
var import_jsx_runtime = require("react/jsx-runtime");
var evaTheme = {
  // Eva dark theme (UI Kitten dark.json) mapped to shadcn semantic names.
  ["--background"]: "#101426",
  ["--foreground"]: "#FFFFFF",
  ["--card"]: "#1A2138",
  ["--card-foreground"]: "#FFFFFF",
  ["--popover"]: "#222B45",
  ["--primary"]: "#3366FF",
  ["--primary-foreground"]: "#FFFFFF",
  ["--secondary"]: "#222B45",
  ["--secondary-foreground"]: "#FFFFFF",
  ["--muted"]: "#151A30",
  ["--muted-foreground"]: "#8F9BB3",
  ["--destructive"]: "#FF3D71",
  ["--success"]: "#00E096",
  ["--warning"]: "#FFAA00",
  ["--border"]: "#2E3A59",
  ["--input"]: "#2E3A59",
  ["--ring"]: "#598BFF",
  ["--radius"]: "8px",
  color: "var(--foreground)",
  background: "var(--background)"
};
var buttonBase = {
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  gap: 8,
  borderRadius: "var(--radius)",
  border: "1px solid transparent",
  font: "inherit",
  fontWeight: 500,
  lineHeight: 1,
  cursor: "pointer",
  transition: "background-color .15s ease, box-shadow .15s ease, border-color .15s ease",
  whiteSpace: "nowrap",
  outline: "none"
};
var buttonVariants = {
  default: { background: "var(--primary)", color: "var(--primary-foreground)", borderColor: "var(--primary)" },
  secondary: { background: "var(--secondary)", color: "var(--secondary-foreground)", borderColor: "var(--border)" },
  outline: { background: "transparent", color: "var(--foreground)", borderColor: "var(--border)" },
  ghost: { background: "transparent", color: "var(--foreground)", borderColor: "transparent" },
  destructive: { background: "var(--destructive)", color: "var(--primary-foreground)", borderColor: "var(--destructive)" }
};
var buttonSizes = {
  sm: { height: 32, padding: "0 12px", fontSize: 13 },
  default: { height: 38, padding: "0 16px", fontSize: 14 },
  lg: { height: 44, padding: "0 22px", fontSize: 15 }
};
function Button(props) {
  const { variant = "default", size = "default", style, onFocus, onBlur, ...rest } = props;
  const [focus, setFocus] = React.useState(false);
  return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
    "button",
    {
      ...rest,
      onFocus: (event) => {
        setFocus(true);
        onFocus?.(event);
      },
      onBlur: (event) => {
        setFocus(false);
        onBlur?.(event);
      },
      style: {
        ...buttonBase,
        ...buttonVariants[variant],
        ...buttonSizes[size],
        ...rest.disabled ? { opacity: 0.5, cursor: "not-allowed" } : null,
        ...focus ? { boxShadow: "0 0 0 2px var(--background), 0 0 0 4px var(--ring)" } : null,
        ...style
      }
    }
  );
}
function Card(props) {
  return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
    "div",
    {
      ...props,
      style: {
        background: "var(--card)",
        color: "var(--card-foreground)",
        border: "1px solid var(--border)",
        borderRadius: 12,
        ...props.style
      }
    }
  );
}
function CardHeader(props) {
  return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { ...props, style: { padding: "16px 16px 0", display: "flex", flexDirection: "column", gap: 4, ...props.style } });
}
function CardTitle(props) {
  return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("h3", { ...props, style: { margin: 0, fontSize: 14, fontWeight: 600, letterSpacing: "-.01em", ...props.style } });
}
function CardDescription(props) {
  return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", { ...props, style: { margin: 0, fontSize: 12.5, color: "var(--muted-foreground)", lineHeight: 1.45, ...props.style } });
}
function CardContent(props) {
  return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { ...props, style: { padding: 16, ...props.style } });
}
function Badge(props) {
  const { variant = "secondary", style, ...rest } = props;
  const variants = {
    default: { background: "var(--primary)", color: "var(--primary-foreground)", borderColor: "var(--primary)" },
    secondary: { background: "var(--secondary)", color: "var(--secondary-foreground)", borderColor: "var(--border)" },
    outline: { background: "transparent", color: "var(--foreground)", borderColor: "var(--border)" },
    success: { background: "color-mix(in srgb, var(--success) 16%, transparent)", color: "var(--success)", borderColor: "color-mix(in srgb, var(--success) 40%, transparent)" },
    destructive: { background: "color-mix(in srgb, var(--destructive) 16%, transparent)", color: "var(--destructive)", borderColor: "color-mix(in srgb, var(--destructive) 40%, transparent)" }
  };
  return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
    "span",
    {
      ...rest,
      style: {
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        height: 22,
        padding: "0 8px",
        borderRadius: 999,
        border: "1px solid",
        fontSize: 11,
        fontWeight: 600,
        letterSpacing: ".02em",
        whiteSpace: "nowrap",
        ...variants[variant],
        ...style
      }
    }
  );
}
function Separator(props) {
  return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { role: "separator", ...props, style: { height: 1, background: "var(--border)", ...props.style } });
}
function Alert(props) {
  const { variant = "default", style, ...rest } = props;
  return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
    "div",
    {
      role: "alert",
      ...rest,
      style: {
        border: "1px solid",
        borderColor: variant === "destructive" ? "color-mix(in srgb, var(--destructive) 45%, transparent)" : "var(--border)",
        background: variant === "destructive" ? "color-mix(in srgb, var(--destructive) 10%, transparent)" : "color-mix(in srgb, var(--muted) 70%, transparent)",
        borderRadius: 10,
        padding: "10px 12px",
        fontSize: 12.5,
        lineHeight: 1.45,
        ...style
      }
    }
  );
}
function AlertTitle(props) {
  return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("h4", { ...props, style: { margin: "0 0 4px", fontSize: 13, fontWeight: 600, ...props.style } });
}
function AlertDescription(props) {
  return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", { ...props, style: { margin: 0, color: "var(--muted-foreground)", ...props.style } });
}

// src/client.tsx
var import_jsx_runtime2 = require("react/jsx-runtime");
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
function DeviceRow(props) {
  const { device, active, label, onSelect } = props;
  return /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)(
    "button",
    {
      role: "radio",
      "aria-checked": active,
      onClick: onSelect,
      style: {
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: 12,
        width: "100%",
        textAlign: "left",
        cursor: "pointer",
        font: "inherit",
        background: active ? "var(--secondary)" : "transparent",
        border: "1px solid " + (active ? "var(--ring)" : "var(--border)"),
        borderRadius: "var(--radius)",
        padding: "10px 12px",
        color: "var(--foreground)"
      },
      children: [
        /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)("span", { style: { display: "flex", flexDirection: "column", gap: 2 }, children: [
          /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("strong", { style: { fontSize: 13 }, children: device.label || device.model || label }),
          /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)("span", { style: { color: "var(--muted-foreground)", fontSize: 12 }, children: [
            device.host,
            ":",
            device.port
          ] })
        ] }),
        active && /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("span", { "aria-hidden": "true", style: { width: 8, height: 8, borderRadius: 999, background: "var(--ring)" } })
      ]
    }
  );
}
function WhaleTvSection(props) {
  const t = translatorOf(props);
  const preview = props.preview;
  const [phase, setPhase] = React2.useState(preview?.phase ?? "loading");
  const [devices, setDevices] = React2.useState(preview?.devices ?? []);
  const [selected, setSelected] = React2.useState(preview?.devices?.[0]?.host ?? null);
  const [pair, setPair] = React2.useState(preview?.pair ?? null);
  const [pairState, setPairState] = React2.useState(preview?.pairState ?? "idle");
  const [error, setError] = React2.useState(preview?.error ?? "");
  const scan = React2.useCallback(async () => {
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
  React2.useEffect(() => {
    if (preview) return;
    void scan();
  }, [scan, preview]);
  const generate = React2.useCallback(async () => {
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
  React2.useEffect(() => {
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
  return /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)("section", { style: { ...evaTheme, display: "flex", flexDirection: "column", gap: 12, padding: 4, background: "transparent", color: "var(--foreground)" }, children: [
    /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)("header", { style: { display: "flex", flexDirection: "column", gap: 4 }, children: [
      /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("h2", { style: { margin: 0, fontSize: 16, fontWeight: 600, letterSpacing: "-.01em" }, children: t("title") }),
      /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("p", { style: { margin: 0, color: "var(--muted-foreground)", fontSize: 12.5 }, children: t("subtitle") }),
      /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("div", { style: { marginTop: 2 }, children: /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Badge, { variant: phase === "error" ? "destructive" : "success", children: phase === "error" ? t("stopped") : t("running") }) })
    ] }),
    /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)(Card, { children: [
      /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)(CardHeader, { children: [
        /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(CardTitle, { children: t("sectionTvs") }),
        /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(CardDescription, { children: phase === "ready" ? `${devices.length} found` : "" })
      ] }),
      /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)(CardContent, { style: { display: "flex", flexDirection: "column", gap: 10 }, children: [
        phase === "loading" && /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("p", { style: { margin: 0, color: "var(--muted-foreground)", fontSize: 13 }, "aria-live": "polite", children: t("scanning") }),
        phase === "error" && /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)(Alert, { variant: "destructive", children: [
          /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(AlertTitle, { children: t("daemonDown") }),
          /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)(AlertDescription, { children: [
            error ? error + " \u2014 " : "",
            t("daemonDownHint")
          ] })
        ] }),
        phase === "empty" && /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)("div", { style: { display: "flex", flexDirection: "column", gap: 6 }, children: [
          /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("p", { style: { margin: 0, fontSize: 13 }, children: t("noTvs") }),
          /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("p", { style: { margin: 0, color: "var(--muted-foreground)", fontSize: 12.5 }, children: t("noTvsHint") })
        ] }),
        phase === "ready" && /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("div", { role: "radiogroup", "aria-label": t("sectionTvs"), style: { display: "flex", flexDirection: "column", gap: 8 }, children: devices.map((device) => /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(
          DeviceRow,
          {
            device,
            active: selected === device.host,
            label: t("tvUnknown"),
            onSelect: () => setSelected(device.host)
          },
          device.host
        )) }),
        (phase === "ready" || phase === "empty") && /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Button, { variant: "outline", size: "sm", onClick: () => void scan(), children: t("scanAgain") })
      ] })
    ] }),
    /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)(Card, { children: [
      /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)(CardHeader, { children: [
        /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(CardTitle, { children: t("sectionPair") }),
        /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(CardDescription, { children: t("qrHint") })
      ] }),
      /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)(CardContent, { style: { display: "flex", flexDirection: "column", gap: 12 }, children: [
        /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Button, { onClick: () => void generate(), disabled: !selected, children: t("generateQr") }),
        pair && /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)("div", { style: { display: "flex", flexWrap: "wrap", gap: 14, alignItems: "flex-start" }, children: [
          pair.qr ? /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(
            "img",
            {
              src: "data:image/png;base64," + pair.qr,
              alt: t("generateQr"),
              width: 190,
              height: 190,
              style: { background: "#fff", borderRadius: 8, padding: 8 }
            }
          ) : /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("code", { style: { fontSize: 12, wordBreak: "break-all", color: "var(--muted-foreground)" }, children: pair.url }),
          /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)("div", { style: { flex: "1 1 180px", minWidth: 160, display: "flex", flexDirection: "column", gap: 8 }, children: [
            /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)("div", { style: { display: "flex", alignItems: "baseline", gap: 8 }, children: [
              /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("span", { style: { fontSize: 11, letterSpacing: ".12em", textTransform: "uppercase", color: "var(--muted-foreground)" }, children: t("codeLabel") }),
              /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("strong", { style: { fontFamily: "ui-monospace, monospace", fontSize: 22, letterSpacing: ".22em" }, children: pair.code })
            ] }),
            /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("a", { href: pair.url, style: { fontSize: 12, color: "var(--ring)", wordBreak: "break-all" }, children: pair.url }),
            /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Separator, {}),
            /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("p", { style: { margin: 0, fontSize: 12.5 }, "aria-live": "polite", children: pairState === "approved" ? t("approved") : t("waiting") })
          ] })
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
