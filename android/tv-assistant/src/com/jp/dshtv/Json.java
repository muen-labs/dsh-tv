package com.jp.dshtv;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Tiny dependency-free JSON writer used by the HTTP API. Only handles the
 * subset we emit: objects, arrays, strings, numbers, booleans and null.
 */
public final class Json {

    private Json() {
    }

    public static String escape(String s) {
        if (s == null) {
            return "null";
        }
        StringBuilder sb = new StringBuilder(s.length() + 16);
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            switch (c) {
                case '"':
                    sb.append("\\\"");
                    break;
                case '\\':
                    sb.append("\\\\");
                    break;
                case '\b':
                    sb.append("\\b");
                    break;
                case '\f':
                    sb.append("\\f");
                    break;
                case '\n':
                    sb.append("\\n");
                    break;
                case '\r':
                    sb.append("\\r");
                    break;
                case '\t':
                    sb.append("\\t");
                    break;
                default:
                    if (c < 0x20 || c == 0x7f) {
                        sb.append(String.format("\\u%04x", Integer.valueOf(c)));
                    } else {
                        sb.append(c);
                    }
            }
        }
        return sb.toString();
    }

    private static void writeValue(StringBuilder sb, Object value) {
        if (value == null) {
            sb.append("null");
        } else if (value instanceof String) {
            sb.append('"').append(escape((String) value)).append('"');
        } else if (value instanceof Boolean) {
            sb.append(((Boolean) value).booleanValue() ? "true" : "false");
        } else if (value instanceof Number) {
            sb.append(value.toString());
        } else if (value instanceof Obj) {
            ((Obj) value).writeTo(sb);
        } else if (value instanceof Arr) {
            ((Arr) value).writeTo(sb);
        } else {
            sb.append('"').append(escape(value.toString())).append('"');
        }
    }

    /** Ordered JSON object. */
    public static final class Obj {
        private final Map<String, Object> map = new LinkedHashMap<String, Object>();

        public Obj put(String key, Object value) {
            map.put(key, value);
            return this;
        }

        public String toString() {
            StringBuilder sb = new StringBuilder(128);
            writeTo(sb);
            return sb.toString();
        }

        void writeTo(StringBuilder sb) {
            sb.append('{');
            boolean first = true;
            for (Map.Entry<String, Object> e : map.entrySet()) {
                if (!first) {
                    sb.append(',');
                }
                first = false;
                sb.append('"').append(escape(e.getKey())).append("\":");
                writeValue(sb, e.getValue());
            }
            sb.append('}');
        }
    }

    /** JSON array. */
    public static final class Arr {
        private final List<Object> list = new ArrayList<Object>();

        public Arr add(Object value) {
            list.add(value);
            return this;
        }

        public int size() {
            return list.size();
        }

        public String toString() {
            StringBuilder sb = new StringBuilder(128);
            writeTo(sb);
            return sb.toString();
        }

        void writeTo(StringBuilder sb) {
            sb.append('[');
            boolean first = true;
            for (Object value : list) {
                if (!first) {
                    sb.append(',');
                }
                first = false;
                writeValue(sb, value);
            }
            sb.append(']');
        }
    }
}
