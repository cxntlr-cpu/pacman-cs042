"use strict";
const $ = id => document.getElementById(id);
const descriptions = {
  play: ["You choose each move. Collect the dots and keep away from ghosts.", "Can you collect every dot?"],
  west: ["A simple rule: keep going west. Watch what happens when a wall gets in the way.", "What is missing from a rule that only says ‘go west’?"],
  dfs: ["Follow one route as far as it goes, then backtrack. It finds a route, but may take a long one.", "Did finding a route quickly also make it a short route?"],
  bfs: ["Explore nearby squares before farther ones. It finds the fewest moves when all steps cost the same.", "What changes when some squares cost more to enter?"],
  ucs: ["Explore the cheapest total journey so far. Extra moves can be worthwhile if they avoid costly squares.", "Is the route with the fewest moves also the cheapest?"],
  astar: ["Balance cost so far with an estimate of cost left. A useful estimate can reduce the search.", "How does your estimate change how many squares are explored?"],
  custom: ["Your rule in my_pacman_behavior.py chooses each move. The starter favors west and can get stuck in a loop.", "What would you change after watching this round?"],
  compare: ["Run the four searches on the same maze. Compare their routes, travel costs, and search effort.", "Which approach explores less while still finding a cheap route?"],
};
const mazeLabels = {tiny:"Tiny maze", medium:"Medium maze", costly:"Cost maze · orange squares cost 6", classic:"Classic · food & ghosts", west:"Go-west demo"};
const promptNumbers = {dfs:"04_depth_first_search", bfs:"05_breadth_first_search", ucs:"06_uniform_cost_search", astar:"07_astar_search"};
const displayName = mode => mode === "astar" ? "A*" : mode.toUpperCase();
let config, trace = null, manual = null, session = null, position = 0, playing = false;
let busy = false, moving = false, lastTick = 0, activeMode = "play";
const canvas = $("game"), ctx = canvas.getContext("2d");

function message(text, error=false) {
  $("status").textContent = text;
  $("message").classList.toggle("error", error);
}
async function api(path, body) {
  const response = await fetch(path, body === undefined ? {cache:"no-store"} : {
    method:"POST", headers:{"Content-Type":"application/json", "X-Lab-Token":config.token}, body:JSON.stringify(body)
  });
  const data = await response.json();
  if (!response.ok || data.error) throw new Error(data.error || "The game could not connect. Reload the page.");
  return data;
}
function configure(maze) {
  const mode = $("mode").value;
  const allowed = ["dfs","bfs","ucs","astar","compare"].includes(mode) ? ["tiny","medium","costly"] : mode === "west" ? ["west","tiny","medium","costly"] : ["classic","tiny","medium","costly","west"];
  const old = maze || $("maze").value;
  $("maze").replaceChildren(...allowed.map(value => new Option(mazeLabels[value], value)));
  $("maze").value = allowed.includes(old) ? old : mode === "compare" ? "costly" : mode === "west" ? "west" : allowed[0];
  $("description").textContent = descriptions[mode][0];
  $("question").textContent = descriptions[mode][1];
  $("heuristic-group").hidden = !["astar","compare"].includes(mode);
  $("run").firstChild.textContent = mode === "play" ? "New game " : "Run experiment ";
  const missing = Object.hasOwn(config.ready, mode) && !config.ready[mode];
  $("build-hint").hidden = !missing;
  $("build-hint").textContent = missing ? `Build this search first: copy ${promptNumbers[mode]}.prompt.md from prompts/ into your AI chat.` : "";
  mazeNote();
}
function mazeNote() {
  const costly = $("maze").value === "costly";
  $("maze-note").textContent = costly ? "Entering an orange square costs 6. Every other step costs 1. Travel cost is separate from game score." : "Each step costs 1. Search mazes have one food dot; Classic has many.";
  $("mud-key").hidden = !costly;
}
function setBusy(value) {
  busy = value;
  for (const id of ["run","mode","maze","heuristic"]) $(id).disabled = value;
}
function stopPlayback() { playing = false; $("toggle").textContent = "▶"; $("toggle").setAttribute("aria-label", "Play playback"); }
function total() { return trace ? trace.visits.length + trace.frames.length - 1 : 0; }
function currentFrame() { return trace ? trace.frames[Math.max(0, Math.min(trace.frames.length-1, position-trace.visits.length))] : manual; }
function draw() {
  const board = trace || manual;
  if (!board) return;
  const frame = currentFrame();
  if (!frame) return;
  const w = 880, h = 530;
  const ratio = Math.min(window.devicePixelRatio || 1, 2);
  if (canvas.width !== w*ratio || canvas.height !== h*ratio) {canvas.width=w*ratio;canvas.height=h*ratio;}
  ctx.setTransform(ratio,0,0,ratio,0,0);
  ctx.fillStyle = "#111d27";ctx.fillRect(0,0,w,h);
  const cell = Math.min((w-34)/board.width,(h-30)/board.height,55);
  const ox=(w-board.width*cell)/2, oy=(h-board.height*cell)/2;
  const xy=([x,y]) => [ox+(x+.5)*cell, oy+(board.height-y-.5)*cell];
  const square=(p,color,inset=1) => {const [x,y]=xy(p);ctx.fillStyle=color;ctx.fillRect(x-cell/2+inset,y-cell/2+inset,cell-inset*2,cell-inset*2);};
  for (const p of board.mud) square(p,"#634a2a",1.5);
  if (trace && $("explored").checked) {
    trace.visits.slice(0,position).forEach((p,i) => square(p, i < position-1 ? "#214453" : "#3d8c9e",2));
  }
  // Keep expensive terrain identifiable even after the search explores it.
  for(const p of board.mud){const [x,y]=xy(p);square(p,"rgba(176,124,49,.22)",2);ctx.strokeStyle="#a77e3c";ctx.lineWidth=1;ctx.strokeRect(x-cell/2+2,y-cell/2+2,cell-4,cell-4);}
  if (trace) {
    const count=Math.max(0,position-trace.visits.length);
    const route=trace.frames.slice(0,count+1).map(f=>f.position);
    if(route.length>1){ctx.strokeStyle="#65d3aa";ctx.lineWidth=Math.max(2,cell*.09);ctx.lineJoin="round";ctx.lineCap="round";ctx.beginPath();route.forEach((p,i)=>{const [x,y]=xy(p);i?ctx.lineTo(x,y):ctx.moveTo(x,y);});ctx.stroke();}
  }
  for(const p of board.walls){const [x,y]=xy(p);ctx.fillStyle="#162c4e";ctx.strokeStyle="#3665b0";ctx.lineWidth=1.1;ctx.beginPath();ctx.roundRect(x-cell/2+1.5,y-cell/2+1.5,cell-3,cell-3,Math.max(2,cell*.12));ctx.fill();ctx.stroke();}
  for(const p of frame.food){const [x,y]=xy(p);ctx.fillStyle="#f5e9bd";ctx.beginPath();ctx.arc(x,y,Math.max(2,cell*.075),0,Math.PI*2);ctx.fill();}
  for(const p of frame.capsules){const [x,y]=xy(p);ctx.fillStyle="#ffecbc";ctx.beginPath();ctx.arc(x,y,cell*.2,0,Math.PI*2);ctx.fill();}
  frame.ghosts.forEach((g,i)=>{
    const [x,y]=xy(g.position),r=cell*.34;
    ctx.fillStyle=g.scared?"#6a8cde":["#fb7d86","#c096e6","#72d5d2","#f6b55c"][i%4];
    ctx.beginPath();ctx.arc(x,y-r*.12,r,Math.PI,0);ctx.lineTo(x+r,y+r);ctx.lineTo(x+r*.5,y+r*.65);ctx.lineTo(x,y+r);ctx.lineTo(x-r*.5,y+r*.65);ctx.lineTo(x-r,y+r);ctx.closePath();ctx.fill();
    for(const d of [-1,1]){ctx.fillStyle="#fff";ctx.beginPath();ctx.ellipse(x+d*r*.36,y-r*.08,r*.23,r*.3,0,0,Math.PI*2);ctx.fill();ctx.fillStyle="#233c61";ctx.beginPath();ctx.arc(x+d*r*.36+r*.06,y-r*.04,r*.12,0,Math.PI*2);ctx.fill();}
  });
  const [px,py]=xy(frame.position),radius=cell*.37;
  const angles={East:0,South:Math.PI/2,West:Math.PI,North:-Math.PI/2,Stop:0};
  const angle=angles[frame.direction]??0, mouth=.19*Math.PI;
  ctx.fillStyle=frame.lost?"#e3a33c":"#ffdc52";ctx.beginPath();ctx.moveTo(px,py);ctx.arc(px,py,radius,angle+mouth,angle+Math.PI*2-mouth);ctx.closePath();ctx.fill();
  const moves=trace?Math.max(0,position-trace.visits.length):manual.moves;
  $("moves").textContent=moves;
  const mudSet=new Set(board.mud.map(p=>p.join(",")));
  $("cost").textContent=trace?trace.frames.slice(1,moves+1).reduce((n,f)=>n+(mudSet.has(f.position.join(","))?6:1),0):"—";
  $("expanded").textContent=trace&&trace.mode in promptNumbers?Math.min(position,trace.visits.length):"—";
  $("score").textContent=frame.score;
  if(trace){$("timeline").value=position;$("progress-label").textContent=position<trace.visits.length?`Search ${position} / ${trace.visits.length}`:`Move ${moves} / ${trace.moves}`;}
}
function showTrace(result, autoplay=true) {
  trace=result;manual=null;session=null;activeMode=result.mode;position=0;
  $("manual-controls").hidden=true;$("playback").hidden=false;
  $("timeline").max=Math.max(1,total());
  $("heuristic-note").hidden=!result.note;$("heuristic-note").textContent=result.note;
  $("mud-key").hidden=!result.mud.length;
  $("view-title").textContent=displayName(result.mode)+" · "+result.maze.toUpperCase();
  playing=autoplay&&total()>0;lastTick=0;
  $("toggle").textContent=playing?"Ⅱ":"▶";
  $("toggle").setAttribute("aria-label",playing?"Pause playback":"Play playback");
  message(`Route ready · ${result.moves} moves · travel cost ${result.cost} · ${result.expanded} search expansions. ${result.status}`);
  draw();
}
function showComparison(rows) {
  $("comparison").hidden=false;$("comparison-body").replaceChildren();
  for(const row of rows){
    const tr=document.createElement("tr");
    const cells=row.error?[displayName(row.mode),"—","—","—",row.error]:[displayName(row.mode),row.moves,row.cost,row.expanded,row.status];
    for(const value of cells){const td=document.createElement("td");td.textContent=value;tr.append(td);}
    if(!row.error){tr.classList.add("playable");tr.tabIndex=0;tr.setAttribute("aria-label",`Replay ${row.mode.toUpperCase()}`);tr.addEventListener("click",()=>showTrace(row));tr.addEventListener("keydown",e=>{if(e.key==="Enter"||e.key===" "){e.preventDefault();showTrace(row);}});}
    else tr.classList.add("pending");
    $("comparison-body").append(tr);
  }
  const first=rows.find(r=>!r.error);
  if(first)showTrace(first);else message("Build a search with prompts 04–07, then compare again.",true);
}
async function startManual(maze) {
  const data=await api("/api/start",{maze});
  trace=null;manual=data;session=data.session;activeMode="play";stopPlayback();
  $("manual-controls").hidden=false;$("playback").hidden=true;
  $("heuristic-note").hidden=true;$("view-title").textContent="YOUR TURN · "+maze.toUpperCase();
  $("mud-key").hidden=!data.mud.length;
  message(data.status);draw();canvas.focus({preventScroll:true});
}
async function run() {
  if(busy)return;
  stopPlayback();setBusy(true);$("comparison").hidden=true;$("heuristic-note").hidden=true;
  message("Getting your experiment ready…");
  try{
    config=await api("/api/config");
    configure($("maze").value);
    const mode=$("mode").value,maze=$("maze").value,heuristic=$("heuristic").value;
    if(mode==="play")await startManual(maze);
    else {
      await startManual(maze);
      session=null;activeMode=mode;
      $("manual-controls").hidden=true;$("playback").hidden=true;
      $("view-title").textContent=displayName(mode)+" · "+maze.toUpperCase();
      message("Getting your experiment ready…");
      const result=await api("/api/run",{mode,maze,heuristic});
      if(result.comparison)showComparison(result.comparison);else showTrace(result);
    }
  }catch(error){message(error.message,true);}
  finally{setBusy(false);}
}
async function move(action) {
  if(!session||activeMode!=="play"||moving||busy)return;
  moving=true;
  try{const data=await api("/api/move",{session,action});manual={...manual,...data};message(data.status);draw();}
  catch(error){message(error.message,true);}
  finally{moving=false;}
}
$("run").addEventListener("click",run);
$("mode").addEventListener("change",()=>{stopPlayback();configure();});
$("maze").addEventListener("change",mazeNote);
$("toggle").addEventListener("click",()=>{if(!trace)return;if(position>=total())position=0;playing=!playing;$("toggle").textContent=playing?"Ⅱ":"▶";$("toggle").setAttribute("aria-label",playing?"Pause playback":"Play playback");lastTick=0;draw();});
$("step").addEventListener("click",()=>{stopPlayback();position=Math.min(total(),position+1);draw();});
$("replay").addEventListener("click",()=>{if(trace)showTrace(trace);});
$("timeline").addEventListener("input",()=>{stopPlayback();position=Number($("timeline").value);draw();});
$("explored").addEventListener("change",draw);
document.querySelectorAll("[data-move]").forEach(b=>b.addEventListener("click",()=>move(b.dataset.move)));
document.addEventListener("keydown",event=>{
  if(["SELECT","INPUT","TEXTAREA","BUTTON"].includes(event.target.tagName))return;
  const action={ArrowUp:"North",w:"North",W:"North",ArrowDown:"South",s:"South",S:"South",ArrowLeft:"West",a:"West",A:"West",ArrowRight:"East",d:"East",D:"East"}[event.key];
  if(action&&session&&activeMode==="play"){event.preventDefault();move(action);}
});
function tick(now) {
  if(playing&&trace){
    const interval=150/Number($("speed").value);
    if(!lastTick)lastTick=now;
    if(now-lastTick>=interval){position=Math.min(total(),position+Math.max(1,Math.floor((now-lastTick)/interval)));lastTick=now;draw();if(position>=total())stopPlayback();}
  }
  requestAnimationFrame(tick);
}
async function init() {
  try{
    const saved=$("replay-data");
    if(saved){
      const result=JSON.parse(saved.textContent);
      const first=result.comparison?.find(row=>!row.error)||result;
      config={ready:{},initial:{}};
      $("mode").value=result.comparison?"compare":first.mode||"compare";
      $("heuristic").value=first.heuristic||"manhattan";
      configure(first.maze||"costly");
      for(const id of ["mode","maze","heuristic","run"])$(id).disabled=true;
      $("run").textContent="Saved replay";
      $("description").textContent="A recorded run from the real game. Use the playback controls to explore it; run the Python project to try a new idea.";
      document.querySelector(".brand").removeAttribute("href");
      document.querySelector("footer").textContent="Offline replay · no installation, connection, or running terminal needed.";
      if(result.comparison)showComparison(result.comparison);else showTrace(result);
      requestAnimationFrame(tick);return;
    }
    config=await api("/api/config");
    $("mode").value=config.initial.mode;$("heuristic").value=config.initial.heuristic;
    configure(config.initial.maze);
    // Always show a real board, even while a search still needs its first prompt.
    await startManual($("maze").value);
    if(config.initial.mode!=="play")await run();
    requestAnimationFrame(tick);
  }catch(error){message(error.message,true);}
}
init();
