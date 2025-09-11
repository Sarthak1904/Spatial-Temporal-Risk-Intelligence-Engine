import React, { useEffect, useMemo, useRef } from "react";
import maplibregl, { Map } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

import { tileUrl } from "../api/client";

interface RiskMapProps {
  selectedDate: string;
  riskLevels: string[];
}

export function RiskMap({ selectedDate, riskLevels }: RiskMapProps): React.JSX.Element {
  const mapRef = useRef<Map | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const tileSourceUrl = useMemo(() => tileUrl(selectedDate, riskLevels), [riskLevels, selectedDate]);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) {
      return;
    }

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: {
        version: 8,
        glyphs: "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
        sources: {
          basemap: {
            type: "raster",
            tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
            tileSize: 256
          }
        },
        layers: [
          { id: "basemap", type: "raster", source: "basemap" }
        ]
      },
      center: [-97.0, 38.5],
      zoom: 4
    });

    map.on("load", () => {
      map.addSource("risk_source", {
        type: "vector",
        tiles: [tileSourceUrl],
        minzoom: 0,
        maxzoom: 14
      });
      map.addLayer({
        id: "risk-fill",
        type: "fill",
        source: "risk_source",
        "source-layer": "risk",
        paint: {
          "fill-color": [
            "match",
            ["get", "risk_level"],
            "low",
            "#2E7D32",
            "medium",
            "#F9A825",
            "high",
            "#EF6C00",
            "#B71C1C"
          ],
          "fill-opacity": 0.6
        }
      });
      map.addLayer({
        id: "risk-outline",
        type: "line",
        source: "risk_source",
        "source-layer": "risk",
        paint: {
          "line-color": "#0b1220",
          "line-width": 0.8
        }
      });

      map.on("click", "risk-fill", (event) => {
        const feature = event.features?.[0];
        if (!feature || !feature.geometry || feature.geometry.type !== "Polygon") {
          return;
        }
        const coordinates = event.lngLat;
        const properties = feature.properties ?? {};
        const popupHtml = `
          <strong>Risk Cell</strong><br/>
          <small>H3: ${properties.h3_index ?? "n/a"}</small><br/>
          Event Count: ${properties.event_count ?? "n/a"}<br/>
          Growth Rate: ${Number(properties.growth_rate ?? 0).toFixed(2)}<br/>
          Risk Score: ${Number(properties.risk_score ?? 0).toFixed(2)}<br/>
          Anomaly: ${properties.flagged === true || properties.flagged === "true" ? "Yes" : "No"}
        `;
        new maplibregl.Popup().setLngLat(coordinates).setHTML(popupHtml).addTo(map);
      });
    });

    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [tileSourceUrl]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) {
      return;
    }

    const source = map.getSource("risk_source");
    if (!source) {
      return;
    }
    map.removeLayer("risk-fill");
    map.removeLayer("risk-outline");
    map.removeSource("risk_source");
    map.addSource("risk_source", {
      type: "vector",
      tiles: [tileSourceUrl],
      minzoom: 0,
      maxzoom: 14
    });
    map.addLayer({
      id: "risk-fill",
      type: "fill",
      source: "risk_source",
      "source-layer": "risk",
      paint: {
        "fill-color": [
          "match",
          ["get", "risk_level"],
          "low",
          "#2E7D32",
          "medium",
          "#F9A825",
          "high",
          "#EF6C00",
          "#B71C1C"
        ],
        "fill-opacity": 0.6
      }
    });
    map.addLayer({
      id: "risk-outline",
      type: "line",
      source: "risk_source",
      "source-layer": "risk",
      paint: {
        "line-color": "#0b1220",
        "line-width": 0.8
      }
    });
  }, [tileSourceUrl]);

  return <div className="map-container" ref={containerRef} />;
}
