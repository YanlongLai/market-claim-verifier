// Generated from docs/site/script.js; run demo/motion_v3.py to refresh.
// Site SHA-256: b7db32513a4352239a6d53ff6a6892778b147adca92ac4f54b040b982a18ffe1
(function(root) {
"use strict";
function state(age, card, elapsed=age) {
const cards=[card], poses=Object.fromEntries(["idle","inspect","reach","present","point","think","stamp","stamp-down","approve","concern","shrug"].map(name=>[name,{style:{}}]));
const robot={style:{},dataset:{}};
const CHECKABLE = 8000;
    const UNCHECKABLE = 5400;
    const READ = 700;
    const REACH = 1500;
    const FIND = 2300;
    const COMPARE = 3700;
    const WINDUP = 4500;
    const STRIKE = 4800;
    const REACT = 5300;
    const EXIT = 6400;
    const REST = 7200;
    const UNKNOWN_STRIKE = 3000;
    const UNKNOWN_EXIT = 4600;
    const FADE = 120;
    const LEDGER_STAGGER = 200;
    const FIND_SWEEP = 600;
    const FIND_LOCK = FIND + FIND_SWEEP;
    const BLOOM = 180;
    const AMBER_SWEEP = 660;
    const LETTERBOX = 12;
    const LETTERBOX_EASE = 250;
    const FLASH = 80;
    const BURST = 400;
    const DIM_LIFT = 250;
    const POOL_PAD = 6;
    const VISOR_RADIUS = 2;
    const DUST_PERIOD = 2100;
    const FLOAT_PERIOD = 1600;
    const THRUSTER_FRAME = 80;
    const THRUSTER_BURST = 250;
    const DIP_DOWN = 60;
    const DIP_RECOVER = 160;
    // Image-pixel anchors from H/manifest.json, before CSS mirroring. Every
    // body uses one scale and a shared nozzle baseline; effects stay separate.
    const POSE_CANVAS = [704, 744];
    const POSE_ANCHORS = Object.freeze({
      idle: { visor: [415, 270], nozzle: [352, 520] }, inspect: { visor: [414, 304], nozzle: [352, 520] },
      reach: { visor: [415, 300], nozzle: [352, 520] }, present: { visor: [404, 285], nozzle: [352, 520] },
      point: { visor: [421, 280], nozzle: [352, 520] }, think: { visor: [416, 270], nozzle: [352, 520] },
      stamp: { visor: [412, 300], nozzle: [352, 520] }, "stamp-down": { visor: [417, 335], nozzle: [352, 520] },
      approve: { visor: [412, 276], nozzle: [352, 520] }, concern: { visor: [412, 286], nozzle: [352, 520] },
      shrug: { visor: [391, 280], nozzle: [352, 520] }
    });
    const POSE_VISORS = Object.fromEntries(Object.entries(POSE_ANCHORS).map(([name, anchors]) =>
      [name, anchors.visor.map((value, axis) => value / POSE_CANVAS[axis])]));
    const checkable = (card) => Boolean(card.excerpt) && card.status === "verified" && ["supported", "contradicted"].includes(card.verdict);
    const durations = cards.map((card) => checkable(card) ? CHECKABLE : UNCHECKABLE);
    const starts = durations.reduce((times, duration) => [...times, times[times.length - 1] + duration], [0]);
    const loop = starts.pop();
    const floatCycles = Math.round(loop / FLOAT_PERIOD);
    const clamp = (value) => Math.max(0, Math.min(1, value));
    const easeOut = (value) => 1 - Math.pow(1 - clamp(value), 3);
    const fadeIn = (age, at) => clamp((age - at) / FADE);
    const compact = (value) => (value || "").replace(/(-?\d+\.\d+)([BM%]?)/g,
      (_match, number, unit) => unit ? `${Number(number).toFixed(1)}${unit}` : String(Number(number)));
    const poseFallbacks = { reach: "present", point: "present", think: "inspect", "stamp-down": "stamp",
      approve: "idle", concern: "idle", shrug: "idle" };
    const facing = { idle: "front", inspect: "post", present: "filing", reach: "filing", point: "filing",
      think: "front", stamp: "post", "stamp-down": "post", approve: "front", concern: "front", shrug: "front" };
    function phaseAt(age, canCheck) {
      if (age < READ) return "enter";
      if (age < REACH) return "read";
      if (!canCheck) return age < UNKNOWN_STRIKE ? "shrug" : age < UNKNOWN_STRIKE + 500 ? "strike" :
        age < UNKNOWN_EXIT ? "react" : "exit";
      return age < FIND ? "reach" : age < COMPARE ? "find" : age < WINDUP ? "compare" :
        age < STRIKE ? "windup" : age < REACT ? "strike" : age < EXIT ? "react" : age < REST ? "exit" : "rest";
    }

    
      const canCheck = checkable(card);
      const transitions = canCheck ? [[0, "idle"], [READ, "inspect"], [REACH, "reach"], [FIND, "point"],
        [COMPARE, "think"], [WINDUP, "stamp"], [STRIKE, "stamp-down"],
        [REACT, card.verdict === "supported" ? "approve" : "concern"], [EXIT, "idle"]] :
        [[0, "idle"], [READ, "inspect"], [REACH, "shrug"], [UNKNOWN_EXIT, "idle"]];
      const current = transitions.findLastIndex(([at]) => age >= at);
      const [at, pose] = transitions[current];
      const previous = current > 0 ? transitions[current - 1][1] : pose;
      const blend = current > 0 ? fadeIn(age, at) : 1;
      Object.entries(poses).forEach(([name, image]) => {
        image.style.opacity = String(name === pose ? blend : name === previous ? 1 - blend : 0);
      });
      const directionOf = (name) => facing[name] === "post" ? -1 : facing[name] === "filing" ? 1 : 0;
      const direction = directionOf(previous) * (1 - blend) + directionOf(pose) * blend;
      const lean = direction * 3 * (0.5 + 0.5 * Math.sin(elapsed / 420));
      const strike = canCheck ? STRIKE : UNKNOWN_STRIKE;
      const sinceStrike = age - strike;
      const dip = sinceStrike < 0 || sinceStrike >= DIP_DOWN + DIP_RECOVER ? 0 : sinceStrike < DIP_DOWN ?
        8 * easeOut(sinceStrike / DIP_DOWN) : 8 * (1 - easeOut((sinceStrike - DIP_DOWN) / DIP_RECOVER));
      const burst = sinceStrike >= 0 && sinceStrike < THRUSTER_BURST;
      const bob = 4 * Math.sin(elapsed / loop * Math.PI * 2 * floatCycles);
      robot.style.transform = `translate3d(0px, ${bob + dip}px, 0) rotate(${lean}deg)`;
      robot.dataset.pose = pose;
      robot.dataset.facing = facing[pose];
      robot.dataset.gesture = !canCheck && age >= REACH && age < UNKNOWN_EXIT ? "shrug" : "review";
      robot.dataset.bob = String(bob);
      robot.dataset.dip = String(dip);
      robot.dataset.thruster = burst ? "burst" : String(Math.floor(elapsed / THRUSTER_FRAME) % 6);
      
const item={light:true}, motion={matches:false};

      const enabled = !!item.light && !motion.matches;
      const light = item.light || { post: emptyBox, row: emptyBox, compare: emptyBox, search: [emptyBox] };
      const finding = enabled && age >= FIND && age < COMPARE;
      const comparing = enabled && age >= COMPARE && age < STRIKE;
      const compareIn = enabled ? fadeIn(age, COMPARE) : 0;
      const lift = 1 - easeOut((age - STRIKE) / DIM_LIFT);
      const filingAlpha = enabled && age < STRIKE ? fadeIn(age, FIND) : 0;
      const postAlpha = comparing ? compareIn : 0;
      const yearAlpha = enabled && light.quarter && age >= COMPARE && age < WINDUP ? 0.28 * compareIn : 0;
      
return {phase:phaseAt(age,canCheck),pose,previous,blend,bob,dip,lean,transform:robot.style.transform,thruster:robot.dataset.thruster,visor:POSE_VISORS[pose],nozzle:POSE_ANCHORS[pose].nozzle,canvas:POSE_CANVAS,facing:facing[pose],postAlpha,filingAlpha,yearAlpha,shade:compareIn*lift};
}
const api={state}; if(typeof module==="object"&&module.exports)module.exports=api;else root.HoverSource=api;
})(globalThis);
