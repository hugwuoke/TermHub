import React, {useState, useEffect} from "react";
import {dataAccessor} from "./State";
import _ from "../supergroup/supergroup";
import * as d3Base from "d3";
import * as d3dag from "d3-dag";
// import _EDGES from '../data/wholegraph.json';
// export const EDGES = _EDGES;

//const EDGES = require('../../wholegraph.json');

const d3 = Object.assign({}, d3Base, d3dag);

export function currentConceptIds(props) {
  const concepts = props?.cset_data?.concepts ?? [];
  return concepts.map(c => c.concept_id);
}
function formatEdges(edges=[]) {
  if (!edges.length) return [];
  let etest = edges[0];
  let pairs;
  if (Array.isArray(etest)) {
    if (etest.length === 3) {
      pairs = edges.map(e => ([e[0], e[2]])); // middle item is predicate; not keeping (for now)
    }else if (etest.length === 2) {
      pairs = edges.map(e => ([e[0], e[1]]));
    } else {
      throw new Error('Unexpected array-type edge with != 3 elements', etest)
    }
  }
  // assume edges are objects if not arrays
  else if ('p' in etest) {
    pairs = edges.map(e => ([e.p, e.c]));
  }
  else if ('pred' in etest && etest.pred === 'rdfs:subClassOf') {
    pairs = edges.map(e => ([e.obj, e.sub]));   // not keeping e.pred (for now)
  }
  else {
    throw new Error('unkown edge type', etest);
  }
  return pairs.map(e => [e[0].toString(), e[1].toString()]);
}
export function ConceptGraph(props) {
  const {concept_ids, use_example=false} = props;
  const [concepts, setConcepts] = useState([]);
  const [edges, setEdges] = useState([]);
  const [svgSize, setSvgSize] = useState({width: 500, height: 500});
  const svg = React.useRef();

  var doc_height = window.innerHeight * .8;
  var doc_width = window.innerWidth * .9;
  // const doc_height = 500;
  // const doc_width = 500;

  console.log({concept_ids, concepts, props});
  window.d3 = d3;
  // console.log(EDGES);

  useEffect(() => {
    async function fetchData() {
      const _concepts = await dataAccessor.getConcepts(concept_ids, 'array');
      setConcepts(_concepts);
    }
    fetchData();
  }, []);
  useEffect(() => {
    async function fetchData() {
      if (use_example == 1) {
        const ex = [{p:'a', c:'b'}, {p:'a', c:'c'}, {p:'a', c:'d'},
          {p:'b', c:'e'}, {p:'b', c:'f'},
          {p:'c', c:'f'},
          {p:'d', c:'g'},
          {p:'e', c:'h'},
          {p:'f', c:'h'},
            /*
          {p:'b2', c:'e2'}, {p:'b2', c:'f2'},
          {p:'c2', c:'f2'},
          {p:'d2', c:'g2'},
          {p:'e2', c:'h2'},
          {p:'f2', c:'h2'} */
        ]
        setEdges(formatEdges(ex));
        return;
      }
      if (use_example == 2) {
        const ex = [
          {
            "sub": "N3C:4043671",
            "pred": "rdfs:subClassOf",
            "obj": "N3C:254068",
            "meta": null
          },
          {
            "sub": "N3C:4043671",
            "pred": "rdfs:subClassOf",
            "obj": "N3C:4180170",
            "meta": null
          },
          {
            "sub": "N3C:4180170",
            "pred": "rdfs:subClassOf",
            "obj": "N3C:4162282",
            "meta": null
          },
          {
            "sub": "N3C:4162282",
            "pred": "rdfs:subClassOf",
            "obj": "N3C:320136",
            "meta": null
          },
          {
            "sub": "N3C:4162282",
            "pred": "rdfs:subClassOf",
            "obj": "N3C:4178818",
            "meta": null
          },
          {
            "sub": "N3C:4178818",
            "pred": "rdfs:subClassOf",
            "obj": "N3C:4180169",
            "meta": null
          },
          {
            "sub": "N3C:4180169",
            "pred": "rdfs:subClassOf",
            "obj": "N3C:4027384",
            "meta": null
          },
          {
            "sub": "N3C:4027384",
            "pred": "rdfs:subClassOf",
            "obj": "N3C:4274025",
            "meta": null
          },
          {
            "sub": "N3C:4274025",
            "pred": "rdfs:subClassOf",
            "obj": "N3C:441840",
            "meta": null
          },
          {
            "sub": "N3C:320136",
            "pred": "rdfs:subClassOf",
            "obj": "N3C:4024567",
            "meta": null
          },
          {
            "sub": "N3C:4024567",
            "pred": "rdfs:subClassOf",
            "obj": "N3C:441840",
            "meta": null
          },
          {
            "sub": "N3C:254068",
            "pred": "rdfs:subClassOf",
            "obj": "N3C:320136",
            "meta": null
          },
          {
            "sub": "N3C:254068",
            "pred": "rdfs:subClassOf",
            "obj": "N3C:4103320",
            "meta": null
          },
          {
            "sub": "N3C:254068",
            "pred": "rdfs:subClassOf",
            "obj": "N3C:4339468",
            "meta": null
          },
          {
            "sub": "N3C:4339468",
            "pred": "rdfs:subClassOf",
            "obj": "N3C:4178545",
            "meta": null
          },
          {
            "sub": "N3C:4339468",
            "pred": "rdfs:subClassOf",
            "obj": "N3C:4274025",
            "meta": null
          },
          {
            "sub": "N3C:4178545",
            "pred": "rdfs:subClassOf",
            "obj": "N3C:255919",
            "meta": null
          },
          {
            "sub": "N3C:255919",
            "pred": "rdfs:subClassOf",
            "obj": "N3C:441840",
            "meta": null
          },
          {
            "sub": "N3C:4103320",
            "pred": "rdfs:subClassOf",
            "obj": "N3C:4024567",
            "meta": null
          },
          {
            "sub": "N3C:4103320",
            "pred": "rdfs:subClassOf",
            "obj": "N3C:4178545",
            "meta": null
          },
          {
            "sub": "N3C:24969",
            "pred": "rdfs:subClassOf",
            "obj": "N3C:31602",
            "meta": null
          },
          {
            "sub": "N3C:24969",
            "pred": "rdfs:subClassOf",
            "obj": "N3C:4043671",
            "meta": null
          },
          {
            "sub": "N3C:24969",
            "pred": "rdfs:subClassOf",
            "obj": "N3C:4181063",
            "meta": null
          },
          {
            "sub": "N3C:4181063",
            "pred": "rdfs:subClassOf",
            "obj": "N3C:4180169",
            "meta": null
          },
          {
            "sub": "N3C:31602",
            "pred": "rdfs:subClassOf",
            "obj": "N3C:254068",
            "meta": null
          },
          {
            "sub": "N3C:31602",
            "pred": "rdfs:subClassOf",
            "obj": "N3C:4042837",
            "meta": null
          },
          {
            "sub": "N3C:31602",
            "pred": "rdfs:subClassOf",
            "obj": "N3C:4155904",
            "meta": null
          },
          {
            "sub": "N3C:4155904",
            "pred": "rdfs:subClassOf",
            "obj": "N3C:4103320",
            "meta": null
          },
          {
            "sub": "N3C:4155904",
            "pred": "rdfs:subClassOf",
            "obj": "N3C:4184252",
            "meta": null
          },
          {
            "sub": "N3C:4184252",
            "pred": "rdfs:subClassOf",
            "obj": "N3C:255919",
            "meta": null
          },
          {
            "sub": "N3C:4042837",
            "pred": "rdfs:subClassOf",
            "obj": "N3C:4184252",
            "meta": null
          },
          {
            "sub": "N3C:4042837",
            "pred": "rdfs:subClassOf",
            "obj": "N3C:4274025",
            "meta": null
          }
        ]
        setEdges(formatEdges(ex));
        return;
      }
      const _edges = await dataAccessor.getSubgraphEdges(concept_ids, 'array');
      setEdges(formatEdges(_edges));
    }
    fetchData();
  }, []);
  useEffect(() => {
    if (!edges.length) {
      return;
    }
    const {width, height, dag } = drawGraph(svg, edges, doc_height, doc_width);
    setSvgSize({width, height});
    window.dag = dag;
    window.svgcur = svg.current;
  }, [edges.length]);


  return (
      <div>
        <h3>d3 dag</h3>
        <svg
            ref={svg}
            id="svg"
            width={doc_width}
            height={doc_height}
            // width={svgSize.width+200}
            // height={svgSize.height+200}
        ></svg>
      </div>
  );
  // debugger;
  // let tree = _.hierarchicalTableToTree(edges, 'obj', 'sub')
  // let paths = tree.flattenTree().map(d => d.namePath());
  // console.log(paths);
  // return <pre>{paths.join('\n')}</pre>;
  // if (concepts.length) {
  //   // return <pre>{JSON.stringify(concepts, null, 2)}</pre>;
  // }
  // return <pre>{JSON.stringify(concept_ids)}</pre>;
}
function graphWidth(dag) {
  return _.max(Object.values(
      _.groupBy(dag.descendants('breadth').map(d => d.value))
  ).map(d => d.length))
}
function graphHeight(dag) {
  return _.max(dag.height().descendants().map(d => d.value));
}
function drawGraph(svg, edges, doc_height, doc_width) {
  // edge looks like {
  //     "sub": "N3C:46274124",       // child
  //     "pred": "rdfs:subClassOf",
  //     "obj": "N3C:36684328",       // parent
  //     "meta": null
  //   },
  const connect = d3dag.dagConnect();
  const dag = connect(edges);
  const graphs = dag.split();
  const maxDims = {
    width: _.sum(graphs.map(g => graphWidth(g))),
    height: _.max(graphs.map(g => graphHeight(g))),
  };
  const nodeSizeWidth = 3 * doc_width / maxDims.width;
  const nodeSizeHeight = doc_height / (maxDims.height + 2) + 5;

  /* from https://observablehq.com/@erikbrinkman/d3-dag-sugiyama
  let nodeRadius = 20;
  let padding = 5;
  const base = nodeRadius * 2 * padding;
  */
  const start = performance.now();
  const layout = d3
      .sugiyama()
      // .layering(d3.layeringSimplex())
      // .layering(d3.layeringCoffmanGraham())
      // .decross(d3.decrossTwoLayer().order(d3.twolayerAgg()))
      // .coord(d3.coordSimplex())
      .nodeSize(node => node === undefined ? [0, 0] : [nodeSizeWidth, nodeSizeHeight]);
      // .nodeSize((node) => {
      //   const size = node ? base : 5;
      //   return [1.2 * size, size];
      // })
  const time = performance.now() - start;
  console.log('performance:', time)

  const {width, height} = layout(dag);
  console.log(d3dag, dag, width, height, svg.current);

  // from https://observablehq.com/@bumbeishvili/d3-dag-vert
  const line = d3.line()
      .curve(d3.curveCatmullRom)
      .x(d => d.x)
      .y(d => d.y);

  const g = d3.select(svg.current).append('g')// .attr('transform',`translate(${100},${100})`);

  g.append('g')
      .selectAll('path')
      .data(dag.links())
      .enter()
      .append('path')
      .attr('id', (source, target) => {
        return source.data.join(':');
      })
      .attr('d', ({ source, target, data }) =>
          line([
                 {
                   x: source.x,
                   y: source.y
                 }
               ].concat(
              data.points || [],
              [ {
                x: target.x,
                y: target.y
              }
              ])
          ))
      .attr('fill','none')
      .attr('stroke','black')
  console.log(g);
  /*
  const arrowSize = (nodeRadius * nodeRadius) / 5.0;
  const arrowLen = Math.sqrt((4 * arrowSize) / Math.sqrt(3));
  const arrow = d3.symbol().type(d3.symbolTriangle).size(arrowSize);
  svgSelection
    .append("g")
    .selectAll("path")
    .data(dag.links())
    .enter()
    .append("path")
    .attr("d", arrow)
    .attr("transform", ({ source, target, points }) => {
      const [end, start] = points.slice().reverse();
      // This sets the arrows the node radius (20) + a little bit (3) away from the node center, on the last line segment of the edge. This means that edges that only span ine level will work perfectly, but if the edge bends, this will be a little off.
      const dx = start.x - end.x;
      const dy = start.y - end.y;
      const scale = (nodeRadius * 1.15) / Math.sqrt(dx * dx + dy * dy);
      // This is the angle of the last line segment
      const angle = (Math.atan2(-dy, -dx) * 180) / Math.PI + 90;
      console.log(angle, dx, dy);
      return `translate(${end.x + dx * scale}, ${
        end.y + dy * scale
      }) rotate(${angle})`;
    })
    .attr("fill", ({ target }) => colorMap[target.data.id])
    .attr("stroke", "white")
    .attr("stroke-width", 1.5)
    .attr("stroke-dasharray", `${arrowLen},${arrowLen}`);

   */


  const nodes = g.append('g')
      .selectAll('g')
      .data(dag.descendants())
      .enter()
      .append('g')
      .attr('transform', ({x, y}) => {
        return `translate(${x}, ${y})`;
      });

  nodes.append('circle')
      .attr('r',4)
      .attr('fill','white')
      .attr('stroke','black')
  console.log(nodes);


  // Add text, which screws up measureement
  nodes.append('text').text(d => d.id).attr('text-anchor','middle').attr('alignment-baseline','middle');
  return {width, height, dag};
}

function _nodeSizes(nodeRadius) {
  const padding = 1.5;
  const base = nodeRadius * 2 * padding;
  return new Map([
    [
      "Less Space around Edges",
      (node) => {
        const size = node ? base : 5;
        return [1.2 * size, size];
      }
    ],
    ["Constant Separation", () => [base, base]]
  ]);
}
