# UI JSON configuration

UI scenes are defined as a JSON object where each key is an element id
and the value is an element definition.

Example element definitions:

- Text element

```json
"title": {
  "type": "text",
  "text": "Layout Trainer",
  "pos": [20, 20],
  "size": 24,
  "font": "Arial",
  "color": "#ffffff"
}
```

- Button element

```json
"start_button": {
  "type": "button",
  "text": "Start Training",
  "pos": [20, 80],
  "size": 18,
  "font": "Arial",
  "color": "#ffffff",
  "bg_color": "#333333",
  "border_color": "#666666",
  "padding": 8
}
```

Notes
- Colors may be hex strings (e.g. `"#RRGGBB"`) or RGB tuples.
- `pos` is the top-left position for the element in pixels.
- Buttons automatically size themselves to fit their text plus `padding`.
- To attach behavior, use `Scene.on_click(element_id, callback)` from
  Python code after creating the `Scene`.
