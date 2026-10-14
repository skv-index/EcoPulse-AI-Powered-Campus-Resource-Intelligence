// Centralized API client for EcoPulse frontend.
// Talks to resource-service (default :5001) and ai-service (default :5002).
// Uses axios, unwraps common envelope shapes, normalizes errors, adds timeout.

import axios from "axios";

const RESOURCE_BASE = process.env.REACT_APP_RESOURCE_URL || "http://localhost:5001";
const AI_BASE = process.env.REACT_APP_AI_URL || "http://localhost:5002";
const TIMEOUT_MS = 10000;

function makeClient(baseURL) {
  const client = axios.create({ baseURL, timeout: TIMEOUT_MS });
  client.interceptors.response.use(
    (res) => res,
    (err) => {
      // Normalize to a plain Error with helpful fields
      const status = err && err.response && err.response.status;
      const d = err && err.response && err.response.data;
      const serverMsg = (d && (d.message || d.error)) || (typeof d === "string" ? d : null);
      let message = serverMsg || (err && err.message) || "Request failed";
      if (err && err.code === "ECONNABORTED") message = "Request timed out after " + TIMEOUT_MS + "ms";
      if (!err.response) message = "Network error — is the API up at " + baseURL + "? (" + message + ")";
      const norm = new Error(message);
      norm.status = status;
      norm.url = err && err.config && err.config.url;
      norm.base = baseURL;
      norm.cause = err;
      throw norm;
    }
  );
  return client;
}

export const resourceClient = makeClient(RESOURCE_BASE);
export const aiClient = makeClient(AI_BASE);
export const API_HOSTS = { RESOURCE_BASE, AI_BASE };

// Unwrap envelopes like { data: ... }, { result: ... }, { items: ... }
export function unwrap(payload) {
  if (payload == null) return payload;
  if (Array.isArray(payload)) return payload;
  if (typeof payload !== "object") return payload;
  if (payload.data !== undefined) return unwrap(payload.data);
  if (payload.result !== undefined) return unwrap(payload.result);
  if (payload.items !== undefined) return payload.items;
  return payload;
}

async function req(client, method, url, opts) {
  const cfg = { method, url };
  if (opts && opts.params) cfg.params = opts.params;
  if (opts && opts.body !== undefined) cfg.data = opts.body;
  const res = await client.request(cfg);
  return unwrap(res.data);
}

const apiFor = (client) => ({
  get: (url, params) => req(client, "get", url, { params }),
  post: (url, body) => req(client, "post", url, { body }),
  put: (url, body) => req(client, "put", url, { body }),
  patch: (url, body) => req(client, "patch", url, { body }),
  del: (url) => req(client, "delete", url),
});

// Default client = resource-service
const api = {
  ...apiFor(resourceClient),
  resource: apiFor(resourceClient),
  ai: apiFor(aiClient),
};

export default api;
