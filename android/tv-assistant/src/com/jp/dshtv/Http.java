package com.jp.dshtv;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.URLDecoder;
import java.nio.charset.Charset;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;

/**
 * Very small HTTP/1.1 request parser and response holder. No external
 * libraries: the bridge only needs GET requests and simple query strings.
 */
public final class Http {

    public static final Charset UTF8 = Charset.forName("UTF-8");
    private static final int MAX_LINE = 8192;

    private Http() {
    }

    /** A parsed HTTP request. Header names are stored lower-case. */
    public static final class Request {
        public String method = "GET";
        public String path = "/";
        public String rawQuery;
        public final Map<String, String> query = new LinkedHashMap<String, String>();
        public final Map<String, String> headers = new LinkedHashMap<String, String>();

        public String header(String name) {
            if (name == null) {
                return null;
            }
            return headers.get(name.toLowerCase(Locale.US));
        }

        public String q(String name) {
            return query.get(name);
        }

        public String q(String name, String def) {
            String v = query.get(name);
            return v != null ? v : def;
        }
    }

    /** A response ready to be written to the socket. */
    public static final class Response {
        public final int status;
        public final String contentType;
        public final byte[] body;

        private Response(int status, String contentType, byte[] body) {
            this.status = status;
            this.contentType = contentType;
            this.body = body;
        }

        public static Response json(int status, Json.Obj obj) {
            return new Response(status, "application/json; charset=utf-8",
                    obj.toString().getBytes(UTF8));
        }

        public static Response bytes(int status, String contentType, byte[] body) {
            return new Response(status, contentType, body != null ? body : new byte[0]);
        }

        public static Response error(int status, String error) {
            return json(status, new Json.Obj().put("ok", Boolean.FALSE).put("error", error));
        }
    }

    /** Parse a request from a socket stream. Returns null for an empty request. */
    public static Request parse(InputStream in) throws IOException {
        String line = readLine(in);
        if (line == null || line.length() == 0) {
            return null;
        }
        String[] parts = line.split(" ");
        if (parts.length < 2) {
            throw new IOException("bad request line");
        }
        Request req = new Request();
        req.method = parts[0].toUpperCase(Locale.US);
        String target = parts[1];

        // Tolerate absolute-form request targets ("GET http://host/x HTTP/1.1").
        int scheme = target.indexOf("://");
        if (scheme >= 0) {
            int slash = target.indexOf('/', scheme + 3);
            target = slash >= 0 ? target.substring(slash) : "/";
        }

        int qmark = target.indexOf('?');
        if (qmark >= 0) {
            req.path = target.substring(0, qmark);
            req.rawQuery = target.substring(qmark + 1);
        } else {
            req.path = target;
            req.rawQuery = null;
        }
        if (req.path.length() == 0) {
            req.path = "/";
        } else if (req.path.length() > 1 && req.path.endsWith("/")) {
            req.path = req.path.substring(0, req.path.length() - 1);
        }
        parseQuery(req.rawQuery, req.query);

        String header;
        while ((header = readLine(in)) != null) {
            if (header.length() == 0) {
                break;
            }
            int colon = header.indexOf(':');
            if (colon <= 0) {
                continue;
            }
            String name = header.substring(0, colon).trim().toLowerCase(Locale.US);
            String value = header.substring(colon + 1).trim();
            if (!req.headers.containsKey(name)) {
                req.headers.put(name, value);
            }
        }
        return req;
    }

    private static String readLine(InputStream in) throws IOException {
        ByteArrayOutputStream buf = new ByteArrayOutputStream(128);
        int b;
        boolean any = false;
        while ((b = in.read()) != -1) {
            any = true;
            if (b == '\n') {
                break;
            }
            if (b != '\r') {
                buf.write(b);
            }
            if (buf.size() > MAX_LINE) {
                throw new IOException("line too long");
            }
        }
        if (!any) {
            return null;
        }
        return new String(buf.toByteArray(), UTF8);
    }

    private static void parseQuery(String raw, Map<String, String> out) {
        if (raw == null || raw.length() == 0) {
            return;
        }
        String[] pairs = raw.split("&");
        for (int i = 0; i < pairs.length; i++) {
            String pair = pairs[i];
            if (pair.length() == 0) {
                continue;
            }
            int eq = pair.indexOf('=');
            String key = eq >= 0 ? pair.substring(0, eq) : pair;
            String value = eq >= 0 ? pair.substring(eq + 1) : "";
            key = decode(key);
            if (!out.containsKey(key)) {
                out.put(key, decode(value));
            }
        }
    }

    /** URL-decode a query component ("+" means space, as in application/x-www-form-urlencoded). */
    public static String decode(String s) {
        if (s == null) {
            return null;
        }
        try {
            return URLDecoder.decode(s, "UTF-8");
        } catch (Exception e) {
            return s;
        }
    }

    public static String reason(int status) {
        switch (status) {
            case 200:
                return "OK";
            case 204:
                return "No Content";
            case 400:
                return "Bad Request";
            case 401:
                return "Unauthorized";
            case 403:
                return "Forbidden";
            case 404:
                return "Not Found";
            case 405:
                return "Method Not Allowed";
            case 409:
                return "Conflict";
            case 500:
                return "Internal Server Error";
            case 501:
                return "Not Implemented";
            case 503:
                return "Service Unavailable";
            default:
                return "OK";
        }
    }
}
