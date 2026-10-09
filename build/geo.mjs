// Project Canada (and faint USA context) plus node points to SVG coordinates.
import fs from "fs";
import { feature } from "topojson-client";
import { geoConicConformal, geoPath } from "d3-geo";

const topo = JSON.parse(fs.readFileSync("node_modules/world-atlas/countries-50m.json", "utf8"));
const countries = feature(topo, topo.objects.countries).features;
const canada = countries.find(f => f.properties.name === "Canada");
const usa = countries.find(f => f.properties.name === "United States of America");
const data = JSON.parse(fs.readFileSync("data.json", "utf8"));

const W = 1000, H = 520;
// Southern Canada only: fit the projection to the box that holds the network, so the map reads well.
const box = { type: "Feature", geometry: { type: "MultiPoint", coordinates: [[-127, 42], [-58, 42], [-127, 57], [-58, 57]] } };
const proj = geoConicConformal().parallels([44, 54]).rotate([92, 0]).fitExtent([[20, 20], [W - 20, H - 20]], box);
proj.clipExtent([[-5, -5], [W + 5, H + 5]]);
const path = geoPath(proj).digits(0);

const nodes = {};
for (const [k, n] of Object.entries(data.nodes)) {
  const [x, y] = proj([n.lon, n.lat]);
  nodes[k] = { x: +x.toFixed(1), y: +y.toFixed(1) };
}
fs.writeFileSync("geo.json", JSON.stringify({ w: W, h: H, canada: path(canada), usa: path(usa), nodes }));
console.log("canada path chars", path(canada).length, "usa", path(usa).length, nodes.BRA, nodes.DEL);
