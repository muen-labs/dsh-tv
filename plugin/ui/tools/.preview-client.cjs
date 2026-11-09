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
function focusRing(active) {
  return active ? { outline: "2px solid var(--dsw-alias-brand-primary)", outlineOffset: 2 } : { outline: "none" };
}
var surface = {
  background: "var(--dsw-alias-bg-layer-3)",
  border: "1px solid var(--dsw-alias-border-l2)",
  borderRadius: 12
};
var nestedSurface = {
  background: "var(--dsw-alias-bg-layer-2)",
  border: "1px solid var(--dsw-alias-border-l3)",
  borderRadius: 10
};
function Card(props) {
  return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { style: { ...surface, padding: 16, ...props.style }, children: props.children });
}
function CardHeader(props) {
  return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { style: { display: "flex", flexWrap: "wrap", alignItems: "baseline", gap: 8, marginBottom: 10 }, children: [
    /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { style: { display: "flex", flexDirection: "column", gap: 2, flex: "1 1 220px", minWidth: 0 }, children: [
      /* @__PURE__ */ (0, import_jsx_runtime.jsx)("h3", { style: { margin: 0, fontSize: 14, fontWeight: 600, lineHeight: "20px", color: "var(--dsw-alias-label-primary)" }, children: props.title }),
      props.hint !== void 0 ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", { style: { margin: 0, fontSize: 12, lineHeight: "18px", color: "var(--dsw-alias-label-tertiary)" }, children: props.hint }) : null
    ] }),
    props.trailing
  ] });
}
function Muted(props) {
  const Tag = props.as === "span" ? "span" : "p";
  return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Tag, { style: { margin: 0, fontSize: 12.5, lineHeight: "19px", color: "var(--dsw-alias-label-tertiary)" }, children: props.children });
}
var toneColor = {
  ok: "var(--dsw-alias-state-success-primary)",
  warn: "var(--dsw-alias-state-warn-primary)",
  error: "var(--dsw-alias-state-error-primary)",
  neutral: "var(--dsw-alias-label-tertiary)"
};
function Dot(props) {
  return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
    "span",
    {
      "aria-hidden": "true",
      style: {
        width: 7,
        height: 7,
        borderRadius: 999,
        flex: "none",
        display: "inline-block",
        background: toneColor[props.tone]
      }
    }
  );
}
function Chip(props) {
  return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
    "span",
    {
      style: {
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        height: 22,
        padding: "0 9px",
        borderRadius: 999,
        border: `1px solid color-mix(in srgb, ${toneColor[props.tone]} 38%, transparent)`,
        background: `color-mix(in srgb, ${toneColor[props.tone]} 12%, transparent)`,
        color: toneColor[props.tone],
        fontSize: 11.5,
        fontWeight: 600,
        lineHeight: "16px",
        whiteSpace: "nowrap"
      },
      children: props.children
    }
  );
}
function buttonStyle(variant) {
  if (variant === "primary") {
    return {
      background: "var(--dsw-alias-label-primary)",
      color: "var(--dsw-alias-bg-layer-3)",
      border: "1px solid transparent"
    };
  }
  if (variant === "secondary") {
    return {
      background: "transparent",
      color: "var(--dsw-alias-label-primary)",
      border: "1px solid var(--dsw-alias-border-l2)"
    };
  }
  return { background: "transparent", color: "var(--dsw-alias-label-secondary)", border: "1px solid transparent" };
}
function Button(props) {
  const { variant = "secondary", small = false, style, disabled, onFocus, onBlur, ...rest } = props;
  const [focused, setFocused] = React.useState(false);
  return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
    "button",
    {
      ...rest,
      type: "button",
      disabled,
      onFocus: (event) => {
        setFocused(true);
        onFocus?.(event);
      },
      onBlur: (event) => {
        setFocused(false);
        onBlur?.(event);
      },
      style: {
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        gap: 6,
        height: small ? 28 : 32,
        padding: small ? "0 10px" : "0 14px",
        borderRadius: 8,
        font: "inherit",
        fontSize: 13,
        fontWeight: 500,
        lineHeight: 1,
        whiteSpace: "nowrap",
        cursor: disabled ? "default" : "pointer",
        opacity: disabled ? 0.45 : 1,
        ...buttonStyle(variant),
        ...focusRing(focused),
        ...style
      }
    }
  );
}
function Code(props) {
  return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
    "code",
    {
      style: {
        display: "inline-block",
        fontFamily: "var(--ds-font-family-code)",
        fontSize: 20,
        fontWeight: 600,
        letterSpacing: ".2em",
        lineHeight: "26px",
        color: "var(--dsw-alias-label-primary)",
        background: "var(--dsw-alias-bg-module-platform)",
        border: "1px solid var(--dsw-alias-border-l2)",
        borderRadius: 8,
        padding: "3px 4px 3px 10px",
        whiteSpace: "nowrap"
      },
      children: props.children
    }
  );
}
function StateRow(props) {
  return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { style: { display: "flex", flexWrap: "wrap", alignItems: "center", gap: "4px 8px", minWidth: 0 }, children: [
    /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Dot, { tone: props.tone }),
    /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { style: { fontSize: 13, fontWeight: 500, color: "var(--dsw-alias-label-primary)" }, children: props.label }),
    /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { style: { fontSize: 13, color: "var(--dsw-alias-label-secondary)" }, children: props.value }),
    props.detail !== void 0 ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
      "span",
      {
        style: {
          fontSize: 12,
          color: "var(--dsw-alias-label-tertiary)",
          fontFamily: "var(--ds-font-family-code)",
          overflowWrap: "anywhere",
          minWidth: 0
        },
        children: props.detail
      }
    ) : null
  ] });
}
function Callout(props) {
  const error = props.tone === "error";
  return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(
    "div",
    {
      role: error ? "alert" : void 0,
      style: {
        ...nestedSurface,
        borderColor: error ? "color-mix(in srgb, var(--dsw-alias-state-error-primary) 40%, transparent)" : "var(--dsw-alias-border-l3)",
        background: error ? "color-mix(in srgb, var(--dsw-alias-state-error-primary) 8%, var(--dsw-alias-bg-layer-3))" : "var(--dsw-alias-bg-layer-2)",
        padding: "10px 12px",
        display: "flex",
        flexDirection: "column",
        gap: 4
      },
      children: [
        props.title !== void 0 ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("strong", { style: { fontSize: 13, fontWeight: 600, color: "var(--dsw-alias-label-primary)" }, children: props.title }) : null,
        props.children
      ]
    }
  );
}
function Command(props) {
  return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
    "code",
    {
      style: {
        display: "block",
        fontFamily: "var(--ds-font-family-code)",
        fontSize: 12,
        lineHeight: "18px",
        color: "var(--dsw-alias-label-secondary)",
        background: "var(--dsw-alias-bg-layer-1)",
        border: "1px solid var(--dsw-alias-border-l2)",
        borderRadius: 6,
        padding: "6px 8px",
        overflowWrap: "anywhere"
      },
      children: props.children
    }
  );
}

// src/client.tsx
var import_jsx_runtime2 = require("react/jsx-runtime");
var NS = "whale-tv";
var en = {
  nav: "Whale-chan TV",
  title: "Whale-chan TV",
  subtitle: "Your Android TV, driven by DSH. Pair it once, then press the TV button and talk.",
  chipChecking: "Checking connection",
  chipRouteError: "Pane unavailable",
  chipDaemonDown: "Daemon offline",
  chipBridgeUnset: "No TV configured",
  chipBridgeDown: "TV bridge offline",
  chipOk: "Daemon and TV bridge online",
  sectionConnection: "Connection",
  daemonLabel: "Daemon",
  bridgeLabel: "TV bridge",
  stateRunning: "Running",
  stateNotRunning: "Not running",
  stateAnswering: "Answering",
  stateNoAnswer: "No answer",
  stateNotConfigured: "Not configured",
  tokenMissing: "The daemon token was not found, so pairing cannot be approved from DSH.",
  sectionDevices: "Android TVs on this network",
  devicesHint: "The TV runs the Whale-chan bridge app. Choose the one DSH should drive.",
  scanning: "Scanning this network for Android TVs\u2026",
  scanningShort: "Scanning\u2026",
  scanAgain: "Scan again",
  routeErrorTitle: "The pane could not reach its host routes",
  routeErrorBody: "The plugin host half is not answering. Reinstall it and restart DSH, then retry.",
  retry: "Retry",
  daemonDownTitle: "The Whale-chan daemon is not answering",
  daemonDownBody: "Start it on the Mac from the repository, then retry:",
  startCommand: "python3 host/whale_voice.py --serve --port 8766",
  noTvsTitle: "No Android TVs answered",
  noTvsBody: "Turn the TV on, open Whale-chan there, and scan again.",
  noTarget: "No TV is configured yet: host/config.json has no bridge address. Pair the TV once from the TV first.",
  sectionPair: "Pairing requests",
  pairHint: "On the TV, open \u201CPair this TV with Whale-chan\u201D. When the code appears here, confirm it matches the TV before approving.",
  pairPolling: "Live \xB7 every 2s",
  pairPaused: "Not live",
  pairEmpty: "No pairing requests right now.",
  codeLabel: "Pairing code",
  tvUnknown: "Android TV",
  ageSuffix: "s ago",
  deviceFoundOne: "TV found",
  deviceFoundMany: "TVs found",
  requestWaitingOne: "1 pairing request waiting",
  requestWaitingMany: "pairing requests waiting",
  approve: "Approve TV",
  deny: "Deny",
  approving: "Approving\u2026",
  approved: "Approved. The TV has this Mac now and will finish pairing by itself.",
  denied: "Request dismissed. The TV keeps waiting until its code expires.",
  approvalError: "Could not approve that request. It may have expired \u2014 ask the TV to show a new code."
};
var zh = {
  nav: "\u9CB8\u5A18\u7535\u89C6",
  title: "\u9CB8\u5A18\u7535\u89C6",
  subtitle: "\u7528 DSH \u64CD\u4F5C\u7684\u5B89\u5353\u7535\u89C6\u3002\u914D\u5BF9\u4E00\u6B21\uFF0C\u4E4B\u540E\u6309\u4E0B\u7535\u89C6\u6309\u94AE\u8BF4\u8BDD\u5373\u53EF\u3002",
  chipChecking: "\u6B63\u5728\u68C0\u67E5\u8FDE\u63A5",
  chipRouteError: "\u9762\u677F\u4E0D\u53EF\u7528",
  chipDaemonDown: "\u540E\u53F0\u672A\u8FD0\u884C",
  chipBridgeUnset: "\u672A\u914D\u7F6E\u7535\u89C6",
  chipBridgeDown: "\u7535\u89C6\u6865\u672A\u54CD\u5E94",
  chipOk: "\u540E\u53F0\u4E0E\u7535\u89C6\u6865\u5DF2\u8FDE\u63A5",
  sectionConnection: "\u8FDE\u63A5\u72B6\u6001",
  daemonLabel: "\u540E\u53F0",
  bridgeLabel: "\u7535\u89C6\u6865",
  stateRunning: "\u8FD0\u884C\u4E2D",
  stateNotRunning: "\u672A\u8FD0\u884C",
  stateAnswering: "\u54CD\u5E94\u4E2D",
  stateNoAnswer: "\u65E0\u54CD\u5E94",
  stateNotConfigured: "\u672A\u914D\u7F6E",
  tokenMissing: "\u6CA1\u6709\u627E\u5230\u540E\u53F0\u4EE4\u724C\uFF0C\u56E0\u6B64\u65E0\u6CD5\u5728 DSH \u91CC\u6279\u51C6\u914D\u5BF9\u3002",
  sectionDevices: "\u6B64\u7F51\u7EDC\u4E0A\u7684\u5B89\u5353\u7535\u89C6",
  devicesHint: "\u7535\u89C6\u4E0A\u8FD0\u884C\u7740\u9CB8\u5A18\u7535\u89C6\u6865\u5E94\u7528\u3002\u8BF7\u9009\u62E9\u8981\u7531 DSH \u63A7\u5236\u7684\u7535\u89C6\u3002",
  scanning: "\u6B63\u5728\u626B\u63CF\u7F51\u7EDC\u4E2D\u7684\u5B89\u5353\u7535\u89C6\u2026",
  scanningShort: "\u626B\u63CF\u4E2D\u2026",
  scanAgain: "\u91CD\u65B0\u626B\u63CF",
  routeErrorTitle: "\u9762\u677F\u65E0\u6CD5\u8FDE\u63A5\u81EA\u5DF1\u7684\u540E\u53F0\u63A5\u53E3",
  routeErrorBody: "\u63D2\u4EF6\u7684\u4E3B\u673A\u7AEF\u6CA1\u6709\u54CD\u5E94\u3002\u8BF7\u91CD\u65B0\u5B89\u88C5\u5E76\u91CD\u542F DSH\uFF0C\u7136\u540E\u91CD\u8BD5\u3002",
  retry: "\u91CD\u8BD5",
  daemonDownTitle: "\u9CB8\u5A18\u540E\u53F0\u6CA1\u6709\u54CD\u5E94",
  daemonDownBody: "\u8BF7\u5728 Mac \u4E0A\u7684\u4ED3\u5E93\u76EE\u5F55\u91CC\u542F\u52A8\u5B83\uFF0C\u7136\u540E\u91CD\u8BD5\uFF1A",
  startCommand: "python3 host/whale_voice.py --serve --port 8766",
  noTvsTitle: "\u6CA1\u6709\u5B89\u5353\u7535\u89C6\u54CD\u5E94",
  noTvsBody: "\u6253\u5F00\u7535\u89C6\uFF0C\u5E76\u5728\u7535\u89C6\u4E0A\u6253\u5F00\u9CB8\u5A18\uFF0C\u7136\u540E\u91CD\u65B0\u626B\u63CF\u3002",
  noTarget: "\u8FD8\u6CA1\u6709\u914D\u7F6E\u7535\u89C6\uFF1Ahost/config.json \u91CC\u6CA1\u6709\u7535\u89C6\u6865\u5730\u5740\u3002\u8BF7\u5148\u5728\u7535\u89C6\u4E0A\u5B8C\u6210\u4E00\u6B21\u914D\u5BF9\u3002",
  sectionPair: "\u914D\u5BF9\u8BF7\u6C42",
  pairHint: "\u5728\u7535\u89C6\u4E0A\u6253\u5F00\u201CPair this TV with Whale-chan\u201D\u3002\u8FD9\u91CC\u51FA\u73B0\u9A8C\u8BC1\u7801\u540E\uFF0C\u5148\u786E\u8BA4\u4E0E\u7535\u89C6\u4E0A\u7684\u4E00\u81F4\uFF0C\u518D\u6279\u51C6\u3002",
  pairPolling: "\u5B9E\u65F6 \xB7 \u6BCF 2 \u79D2",
  pairPaused: "\u672A\u5B9E\u65F6",
  pairEmpty: "\u5F53\u524D\u6CA1\u6709\u914D\u5BF9\u8BF7\u6C42\u3002",
  codeLabel: "\u914D\u5BF9\u7801",
  tvUnknown: "\u5B89\u5353\u7535\u89C6",
  ageSuffix: "\u79D2\u524D",
  deviceFoundOne: "\u53F0\u7535\u89C6\u5DF2\u627E\u5230",
  deviceFoundMany: "\u53F0\u7535\u89C6\u5DF2\u627E\u5230",
  requestWaitingOne: "1 \u4E2A\u914D\u5BF9\u8BF7\u6C42\u7B49\u5F85\u4E2D",
  requestWaitingMany: "\u4E2A\u914D\u5BF9\u8BF7\u6C42\u7B49\u5F85\u4E2D",
  approve: "\u6279\u51C6\u7535\u89C6",
  deny: "\u62D2\u7EDD",
  approving: "\u6B63\u5728\u6279\u51C6\u2026",
  approved: "\u5DF2\u6279\u51C6\u3002\u7535\u89C6\u73B0\u5728\u5DF2\u83B7\u5F97\u8FD9\u53F0 Mac \u7684\u5730\u5740\uFF0C\u4F1A\u81EA\u52A8\u5B8C\u6210\u914D\u5BF9\u3002",
  denied: "\u8BF7\u6C42\u5DF2\u5FFD\u7565\u3002\u7535\u89C6\u4F1A\u7EE7\u7EED\u7B49\u5F85\uFF0C\u76F4\u5230\u9A8C\u8BC1\u7801\u8FC7\u671F\u3002",
  approvalError: "\u65E0\u6CD5\u6279\u51C6\u8BE5\u8BF7\u6C42\uFF0C\u53EF\u80FD\u5DF2\u7ECF\u8FC7\u671F\u3002\u8BF7\u5728\u7535\u89C6\u4E0A\u91CD\u65B0\u663E\u793A\u9A8C\u8BC1\u7801\u3002"
};
function translatorOf(props) {
  return (key) => props && typeof props.t === "function" ? props.t(key) : en[key] ?? key;
}
function ageText(entry, t) {
  const fresh = Number.isFinite(entry.ageSeconds) ? entry.ageSeconds : Math.max(0, Math.round((Date.now() - entry.createdAt) / 1e3));
  return `${Math.max(0, Math.round(fresh))}${t("ageSuffix")}`;
}
function chipFor(status, phase, t) {
  if (phase === "error") return { tone: "error", label: t("chipRouteError") };
  if (status === null) return { tone: "neutral", label: t("chipChecking") };
  if (!status.daemon || status.daemon.reachable !== true) return { tone: "error", label: t("chipDaemonDown") };
  if (!status.target) return { tone: "warn", label: t("chipBridgeUnset") };
  if (!status.bridge || status.bridge.alive !== true) return { tone: "warn", label: t("chipBridgeDown") };
  return { tone: "ok", label: t("chipOk") };
}
function DeviceRow(props) {
  const { device, active, t, onSelect, onKeyDown, tabIndex } = props;
  const [focused, setFocused] = React2.useState(false);
  const name = device.model || t("tvUnknown");
  const bridgeLine = device.app ? `${device.app}${device.version ? ` v${device.version}` : ""}` : "";
  return /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)(
    "button",
    {
      type: "button",
      id: `whale-tv-device-${device.host.replace(/\./g, "-")}`,
      role: "radio",
      "aria-checked": active,
      tabIndex,
      onClick: onSelect,
      onKeyDown,
      onFocus: () => setFocused(true),
      onBlur: () => setFocused(false),
      style: {
        display: "flex",
        alignItems: "center",
        gap: 10,
        width: "100%",
        boxSizing: "border-box",
        padding: "10px 12px",
        textAlign: "left",
        font: "inherit",
        cursor: "pointer",
        borderRadius: 10,
        border: `1px solid ${active ? "var(--dsw-alias-brand-primary)" : "var(--dsw-alias-border-l2)"}`,
        background: active ? "var(--dsw-alias-bg-layer-2)" : "transparent",
        outline: focused ? "2px solid var(--dsw-alias-brand-primary)" : "none",
        outlineOffset: 2
      },
      children: [
        /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Dot, { tone: device.alive ? "ok" : "neutral" }),
        /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)("span", { style: { display: "flex", flexDirection: "column", gap: 2, minWidth: 0, flex: "1 1 auto" }, children: [
          /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("span", { style: { fontSize: 13.5, fontWeight: 600, color: "var(--dsw-alias-label-primary)", overflowWrap: "anywhere" }, children: name }),
          /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)("span", { style: { fontSize: 12, color: "var(--dsw-alias-label-tertiary)", overflowWrap: "anywhere" }, children: [
            device.host,
            ":",
            device.port,
            bridgeLine ? ` \xB7 ${bridgeLine}` : ""
          ] })
        ] }),
        /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(
          "span",
          {
            "aria-hidden": "true",
            style: {
              width: 16,
              height: 16,
              flex: "none",
              borderRadius: 999,
              border: `1px solid ${active ? "var(--dsw-alias-brand-primary)" : "var(--dsw-alias-border-l3)"}`,
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center"
            },
            children: active ? /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("span", { style: { width: 8, height: 8, borderRadius: 999, background: "var(--dsw-alias-brand-primary)" } }) : null
          }
        )
      ]
    }
  );
}
function WhaleTvSection(props) {
  const t = translatorOf(props);
  const preview = props.preview;
  const [phase, setPhase] = React2.useState(preview?.phase ?? "loading");
  const [status, setStatus] = React2.useState(preview?.status ?? null);
  const [devices, setDevices] = React2.useState(preview?.devices ?? []);
  const [scanned, setScanned] = React2.useState(preview?.scanned ?? null);
  const [selected, setSelected] = React2.useState(preview?.devices?.[0]?.host ?? null);
  const [pending, setPending] = React2.useState(preview?.pending ?? []);
  const [pendingDaemon, setPendingDaemon] = React2.useState(preview?.pendingDaemon ?? true);
  const [approval, setApproval] = React2.useState(preview?.approval ?? null);
  const [busyId, setBusyId] = React2.useState(preview?.busyId ?? null);
  const [error, setError] = React2.useState(preview?.error ?? "");
  const [scanning, setScanning] = React2.useState(false);
  const load = React2.useCallback(async (initial) => {
    if (initial) setPhase("loading");
    setScanning(true);
    setError("");
    try {
      const statusRes = await fetch("/whale-chan/status", { headers: { accept: "application/json" } });
      const nextStatus = await statusRes.json();
      if (!nextStatus || typeof nextStatus !== "object") throw new Error("bad status response");
      setStatus(nextStatus);
      const pendingRes = await fetch("/whale-chan/pending", { headers: { accept: "application/json" } });
      const pendingBody = await pendingRes.json();
      setPending(Array.isArray(pendingBody?.pending) ? pendingBody.pending : []);
      setPendingDaemon(pendingBody?.daemon !== false);
      if (nextStatus.daemon?.reachable !== true) {
        setDevices([]);
        setPhase("down");
        return;
      }
      if (!nextStatus.target) {
        setDevices([]);
        setPhase("empty");
        return;
      }
      const deviceRes = await fetch("/whale-chan/devices?fresh=1", { headers: { accept: "application/json" } });
      const deviceBody = await deviceRes.json();
      const list = Array.isArray(deviceBody?.devices) ? deviceBody.devices : [];
      setDevices(list);
      setScanned(deviceBody?.scanned ?? null);
      setSelected((previous) => previous && list.some((device) => device.host === previous) ? previous : list[0]?.host ?? null);
      setPhase(list.length > 0 ? "ready" : "empty");
    } catch (cause) {
      setError(String(cause?.message || cause));
      setPhase("error");
    } finally {
      setScanning(false);
    }
  }, []);
  React2.useEffect(() => {
    if (preview) return;
    void load(true);
  }, [load, preview]);
  React2.useEffect(() => {
    if (preview) return;
    let cancelled = false;
    const timer = setInterval(async () => {
      try {
        const res = await fetch("/whale-chan/pending", { headers: { accept: "application/json" } });
        const body = await res.json();
        if (cancelled) return;
        setPending(Array.isArray(body?.pending) ? body.pending : []);
        setPendingDaemon(body?.daemon !== false);
      } catch {
        if (!cancelled) setPendingDaemon(false);
      }
    }, 2e3);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [preview]);
  const act = React2.useCallback(
    async (entry, kind) => {
      setBusyId(entry.id);
      setApproval(null);
      try {
        const res = await fetch(`/whale-chan/pair/${kind}`, {
          method: "POST",
          headers: { accept: "application/json", "content-type": "application/json" },
          body: JSON.stringify({ id: entry.id })
        });
        const body = await res.json();
        if (body && body.ok === true) {
          setApproval({ id: entry.id, kind: kind === "approve" ? "approved" : "denied" });
          setPending((previous) => previous.filter((item) => item.id !== entry.id));
        } else {
          setApproval({ id: entry.id, kind: "error" });
          setError(String(body?.error || "request failed"));
        }
      } catch (cause) {
        setApproval({ id: entry.id, kind: "error" });
        setError(String(cause?.message || cause));
      } finally {
        setBusyId(null);
      }
    },
    []
  );
  const chip = chipFor(status, phase, t);
  const daemonOk = status?.daemon?.reachable === true;
  const daemonDetail = status?.daemon ? [status.daemon.url, status.daemon.reachable ? null : status.daemon.error].filter(Boolean).join(" \xB7 ") : void 0;
  const bridgeOk = status?.bridge?.alive === true;
  const bridgeValue = !status?.target ? t("stateNotConfigured") : bridgeOk ? t("stateAnswering") : t("stateNoAnswer");
  const bridgeDetail = status?.target ? `${status.target.host}:${status.target.port}${status.bridge?.app ? ` \xB7 ${status.bridge.app}${status.bridge.version ? ` v${status.bridge.version}` : ""}` : ""}` : void 0;
  const approvalText = approval ? approval.kind === "approved" ? t("approved") : approval.kind === "denied" ? t("denied") : t("approvalError") : null;
  const onDeviceKeyDown = (event, index) => {
    const keys = ["ArrowDown", "ArrowRight", "ArrowUp", "ArrowLeft", "Home", "End"];
    if (!keys.includes(event.key)) return;
    event.preventDefault();
    const last = devices.length - 1;
    let next = index;
    if (event.key === "ArrowDown" || event.key === "ArrowRight") next = index >= last ? 0 : index + 1;
    if (event.key === "ArrowUp" || event.key === "ArrowLeft") next = index <= 0 ? last : index - 1;
    if (event.key === "Home") next = 0;
    if (event.key === "End") next = last;
    const target = devices[next];
    if (target) {
      setSelected(target.host);
      const node = document.getElementById(`whale-tv-device-${target.host.replace(/\./g, "-")}`);
      if (node instanceof HTMLElement) node.focus();
    }
  };
  return /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)(
    "section",
    {
      "aria-labelledby": "whale-tv-heading",
      style: {
        display: "flex",
        flexDirection: "column",
        gap: 14,
        width: "100%",
        maxWidth: 760,
        color: "var(--dsw-alias-label-primary)"
      },
      children: [
        /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)("header", { style: { display: "flex", flexDirection: "column", gap: 4 }, children: [
          /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)("div", { style: { display: "flex", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between", gap: 8 }, children: [
            /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("h2", { id: "whale-tv-heading", style: { margin: 0, fontSize: 18, fontWeight: 600, lineHeight: "26px" }, children: t("title") }),
            /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)(Chip, { tone: chip.tone, children: [
              /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Dot, { tone: chip.tone }),
              chip.label
            ] })
          ] }),
          /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Muted, { children: t("subtitle") })
        ] }),
        /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)(Card, { children: [
          /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(CardHeader, { title: t("sectionConnection"), hint: status?.token?.present === false ? t("tokenMissing") : void 0 }),
          /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)("div", { style: { display: "flex", flexDirection: "column", gap: 8 }, children: [
            /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(
              StateRow,
              {
                tone: daemonOk ? "ok" : "error",
                label: t("daemonLabel"),
                value: daemonOk ? t("stateRunning") : t("stateNotRunning"),
                detail: daemonDetail
              }
            ),
            /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(
              StateRow,
              {
                tone: bridgeOk ? "ok" : status?.target ? "warn" : "neutral",
                label: t("bridgeLabel"),
                value: bridgeValue,
                detail: bridgeDetail
              }
            )
          ] })
        ] }),
        /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)(Card, { children: [
          /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(
            CardHeader,
            {
              title: t("sectionDevices"),
              hint: t("devicesHint"),
              trailing: /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Button, { small: true, onClick: () => void load(false), disabled: scanning, children: scanning ? t("scanningShort") : t("scanAgain") })
            }
          ),
          phase === "loading" ? /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("p", { role: "status", "aria-live": "polite", style: { margin: 0, fontSize: 13, color: "var(--dsw-alias-label-tertiary)" }, children: t("scanning") }) : null,
          phase === "error" ? /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)("div", { style: { display: "flex", flexDirection: "column", gap: 10 }, children: [
            /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Callout, { tone: "error", title: t("routeErrorTitle"), children: /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)(Muted, { children: [
              error ? `${error} \u2014 ` : "",
              t("routeErrorBody")
            ] }) }),
            /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("div", { children: /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Button, { onClick: () => void load(true), children: t("retry") }) })
          ] }) : null,
          phase === "down" ? /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)("div", { style: { display: "flex", flexDirection: "column", gap: 10 }, children: [
            /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)(Callout, { tone: "error", title: t("daemonDownTitle"), children: [
              /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Muted, { children: t("daemonDownBody") }),
              /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Command, { children: t("startCommand") })
            ] }),
            /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("div", { children: /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Button, { onClick: () => void load(true), children: t("retry") }) })
          ] }) : null,
          phase === "empty" ? /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)("div", { style: { display: "flex", flexDirection: "column", gap: 8 }, children: [
            /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("strong", { style: { fontSize: 13.5, fontWeight: 600 }, children: t("noTvsTitle") }),
            /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Muted, { children: t("noTvsBody") }),
            status && !status.target ? /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Muted, { children: t("noTarget") }) : null
          ] }) : null,
          phase === "ready" ? /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)("div", { role: "radiogroup", "aria-label": t("sectionDevices"), style: { display: "flex", flexDirection: "column", gap: 8 }, children: [
            devices.map((device, index) => /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(
              DeviceRow,
              {
                device,
                active: selected === device.host,
                t,
                onSelect: () => setSelected(device.host),
                onKeyDown: (event) => onDeviceKeyDown(event, index),
                tabIndex: selected === device.host ? 0 : -1
              },
              device.host
            )),
            scanned && typeof scanned.tookMs === "number" ? /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("span", { style: { fontSize: 12, color: "var(--dsw-alias-label-tertiary)" }, children: `${devices.length} ${devices.length === 1 ? t("deviceFoundOne") : t("deviceFoundMany")} \xB7 ${scanned.tookMs}ms` }) : null
          ] }) : null
        ] }),
        /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)(Card, { children: [
          /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(
            CardHeader,
            {
              title: t("sectionPair"),
              hint: t("pairHint"),
              trailing: /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)(Chip, { tone: pendingDaemon ? "ok" : "warn", children: [
                /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Dot, { tone: pendingDaemon ? "ok" : "warn" }),
                pendingDaemon ? t("pairPolling") : t("pairPaused")
              ] })
            }
          ),
          /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(
            "div",
            {
              role: "status",
              "aria-live": "polite",
              style: {
                marginBottom: 8,
                fontSize: 13,
                lineHeight: "19px",
                fontWeight: approvalText !== null ? 500 : 400,
                color: approval ? approval.kind === "error" ? "var(--dsw-alias-state-error-primary)" : "var(--dsw-alias-state-success-primary)" : "var(--dsw-alias-label-tertiary)"
              },
              children: approvalText !== null ? approvalText : pending.length > 0 ? pending.length === 1 ? t("requestWaitingOne") : `${pending.length} ${t("requestWaitingMany")}` : t("pairEmpty")
            }
          ),
          /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("div", { style: { display: "flex", flexDirection: "column", gap: 8 }, children: pending.map((entry) => {
            const address = entry.host ? `${entry.host}${status?.target ? `:${status.target.port}` : ""}` : t("tvUnknown");
            const busy = busyId === entry.id;
            return /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)(
              "div",
              {
                style: { ...nestedSurface, padding: 12, display: "flex", flexDirection: "column", gap: 10 },
                children: [
                  /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)("div", { style: { display: "flex", flexWrap: "wrap", alignItems: "center", gap: "6px 10px" }, children: [
                    /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("span", { style: { fontSize: 11, letterSpacing: ".08em", textTransform: "uppercase", color: "var(--dsw-alias-label-tertiary)" }, children: t("codeLabel") }),
                    /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Code, { children: entry.code }),
                    /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("span", { style: { fontSize: 12.5, color: "var(--dsw-alias-label-secondary)", overflowWrap: "anywhere" }, children: address }),
                    /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("span", { style: { fontSize: 12, color: "var(--dsw-alias-label-tertiary)" }, children: ageText(entry, t) })
                  ] }),
                  /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)("div", { style: { display: "flex", flexWrap: "wrap", gap: 8 }, children: [
                    /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(
                      Button,
                      {
                        variant: "primary",
                        "aria-label": `${t("approve")} \u2014 ${t("codeLabel")} ${entry.code}`,
                        disabled: busyId !== null,
                        onClick: () => void act(entry, "approve"),
                        children: busy ? t("approving") : t("approve")
                      }
                    ),
                    /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(
                      Button,
                      {
                        "aria-label": `${t("deny")} \u2014 ${t("codeLabel")} ${entry.code}`,
                        disabled: busyId !== null,
                        onClick: () => void act(entry, "deny"),
                        children: t("deny")
                      }
                    )
                  ] })
                ]
              },
              entry.id
            );
          }) })
        ] })
      ]
    }
  );
}
var client_default = WhaleTvSection;
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  NS,
  WhaleTvSection,
  en,
  zh
});
