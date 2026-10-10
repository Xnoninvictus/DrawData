// js/model.js
//
// The original drawdata widgets are anywidget `render({ model, el })` modules:
// `model` is a Backbone-style object synced to a Python traitlets object over
// a Jupyter comm. Outside a notebook there is no Python kernel, so this file
// provides a tiny drop-in replacement that implements exactly the surface
// area the widgets use:
//
//   model.get(key)                 -> current value
//   model.set(key, value)          -> stage + broadcast a change
//   model.on("change:key", fn)     -> subscribe (fires synchronously, like Backbone)
//   model.save_changes()           -> no-op here (nothing to sync to a kernel),
//                                      but still emitted as an event so the app
//                                      shell can hook "a batch just finished".
//
// Everything else (drawing, undo, brush math, axes...) is the original,
// unmodified widget code in scatter_render.js / bar_render.js.

class LocalModel {
  constructor(initialState = {}) {
    this._state = { ...initialState };
    this._listeners = new Map();
  }

  get(key) {
    return this._state[key];
  }

  set(key, value) {
    this._state[key] = value;
    this._emit(`change:${key}`, value);
  }

  on(eventName, handler) {
    if (!this._listeners.has(eventName)) this._listeners.set(eventName, []);
    this._listeners.get(eventName).push(handler);
  }

  off(eventName, handler) {
    if (!this._listeners.has(eventName)) return;
    if (!handler) {
      this._listeners.delete(eventName);
      return;
    }
    const next = this._listeners.get(eventName).filter((fn) => fn !== handler);
    this._listeners.set(eventName, next);
  }

  save_changes() {
    this._emit("save_changes");
  }

  _emit(eventName, ...args) {
    const handlers = this._listeners.get(eventName);
    if (!handlers) return;
    // copy in case a handler mutates the listener list
    [...handlers].forEach((fn) => fn(...args));
  }
}
