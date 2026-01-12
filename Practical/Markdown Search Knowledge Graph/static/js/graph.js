(function () {
  const container = d3.select("#graph");
  if (!container.node() || !GRAPH_DATA) return;

  const width = container.node().clientWidth || 400;
  const height = 400;

  const svg = container
    .append("svg")
    .attr("viewBox", [0, 0, width, height])
    .attr("role", "img")
    .attr("aria-label", "Graph of Markdown links");

  const color = d3.scaleOrdinal(d3.schemeTableau10);

  const simulation = d3
    .forceSimulation(GRAPH_DATA.nodes)
    .force(
      "link",
      d3
        .forceLink(GRAPH_DATA.links)
        .id((d) => d.id)
        .distance(120),
    )
    .force("charge", d3.forceManyBody().strength(-350))
    .force("center", d3.forceCenter(width / 2, height / 2));

  const link = svg
    .append("g")
    .attr("stroke", "#aaa")
    .attr("stroke-opacity", 0.6)
    .selectAll("line")
    .data(GRAPH_DATA.links)
    .join("line")
    .attr("class", "link")
    .attr("marker-end", "url(#arrow)");

  const node = svg
    .append("g")
    .attr("stroke", "#fff")
    .attr("stroke-width", 1.5)
    .selectAll("circle")
    .data(GRAPH_DATA.nodes)
    .join("circle")
    .attr("r", 18)
    .attr("fill", (d) => color(d.id))
    .attr("class", "node")
    .call(
      d3
        .drag()
        .on("start", (event) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          event.subject.fx = event.subject.x;
          event.subject.fy = event.subject.y;
        })
        .on("drag", (event) => {
          event.subject.fx = event.x;
          event.subject.fy = event.y;
        })
        .on("end", (event) => {
          if (!event.active) simulation.alphaTarget(0);
          event.subject.fx = null;
          event.subject.fy = null;
        }),
    )
    .append("title")
    .text((d) => d.title);

  const labels = svg
    .append("g")
    .selectAll("text")
    .data(GRAPH_DATA.nodes)
    .join("text")
    .attr("text-anchor", "middle")
    .attr("dy", 4)
    .attr("font-size", 10)
    .attr("pointer-events", "none")
    .text((d) => d.title);

  svg
    .append("defs")
    .append("marker")
    .attr("id", "arrow")
    .attr("viewBox", "0 -5 10 10")
    .attr("refX", 14)
    .attr("refY", 0)
    .attr("markerWidth", 6)
    .attr("markerHeight", 6)
    .attr("orient", "auto")
    .append("path")
    .attr("d", "M0,-5L10,0L0,5")
    .attr("fill", "#bbb");

  simulation.on("tick", () => {
    link
      .attr("x1", (d) => d.source.x)
      .attr("y1", (d) => d.source.y)
      .attr("x2", (d) => d.target.x)
      .attr("y2", (d) => d.target.y);

    node.attr("cx", (d) => d.x).attr("cy", (d) => d.y);
    labels.attr("x", (d) => d.x).attr("y", (d) => d.y + 25);
  });
})();
