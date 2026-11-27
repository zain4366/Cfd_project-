// AE-471 CFD course project report in the SMME lab-report format (Zain ul Abiden, Lab Report 4 template).
// OpenFOAM reproduction of Kinsey & Dumas (2008). Builds AE471_Project_Report.docx.
const fs = require("fs");
const path = require("path");
const D = require("docx");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, WidthType, AlignmentType, HeadingLevel,
  BorderStyle, ShadingType, TableOfContents, Footer, Header, PageNumber, LevelFormat, TabStopType, NumberFormat, VerticalAlign,
} = D;

const DIR = __dirname;
const IMG = path.join(DIR, "img");
const SIZES = JSON.parse(fs.readFileSync(path.join(DIR, "img_sizes.json")));
const RUNS = JSON.parse(fs.readFileSync(path.join(DIR, "..", "AE471_data", "01_summary_tables", "all_runs_summary.json")));
const RES = JSON.parse(fs.readFileSync(path.join(DIR, "..", "figs", "residuals.json")));
const OUTNAME = process.argv[2] || "AE471_Project_Report.docx";
const FONT = "Arial";
const BLUE = "2F5597", CAPCOL = "44546A", LINE = "4472C4";
const TEXTW = 9360; // Letter 12240 - 2 x 1440
const TEXTW_IN = TEXTW / 1440;

// ------------------------------------------------------------ inline markup: **bold**, ~~italic~~, _{sub}, ^{sup}
function runs(s, base = {}) {
  const out = [];
  let i = 0, bold = false, ital = false, buf = "";
  const push = (t, extra = {}) => { if (t) out.push(new TextRun({ text: t, font: base.font || FONT, bold: bold || base.bold, italics: ital || base.italics, size: base.size, color: base.color, ...extra })); };
  while (i < s.length) {
    if (s.startsWith("**", i)) { push(buf); buf = ""; bold = !bold; i += 2; continue; }
    if (s.startsWith("~~", i)) { push(buf); buf = ""; ital = !ital; i += 2; continue; }
    if (s.startsWith("_{", i) || s.startsWith("^{", i)) {
      push(buf); buf = "";
      const j = s.indexOf("}", i);
      push(s.slice(i + 2, j), s[i] === "_" ? { subScript: true } : { superScript: true });
      i = j + 1; continue;
    }
    buf += s[i]; i++;
  }
  push(buf);
  return out;
}
const P = (s, o = {}) => new Paragraph({ children: runs(s, o.run || {}), alignment: o.align || AlignmentType.JUSTIFIED, spacing: { after: 160, line: 360 }, ...o.para });
const TOCL = [];
const plain = (s) => s.replace(/\*\*|~~/g, "").replace(/[_^]\{([^}]*)\}/g, "$1");
const H1 = (s) => (TOCL.push({ lvl: 1, text: s.toUpperCase() }), new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun({ text: s.toUpperCase(), font: FONT })] }));
const H2 = (s) => (TOCL.push({ lvl: 2, text: s }), new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun({ text: s, font: FONT })] }));
// front-matter titles: look like Heading 1 but stay out of the table of contents
const FH = (s, brk = true) => new Paragraph({ style: "FrontHead", pageBreakBefore: brk, children: [new TextRun({ text: s.toUpperCase(), font: FONT })] });
const bullet = (s) => new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: runs(s), alignment: AlignmentType.JUSTIFIED, spacing: { after: 80, line: 360 } });
const numbered = (s, ref = "nums") => new Paragraph({ numbering: { reference: ref, level: 0 }, children: runs(s), alignment: AlignmentType.JUSTIFIED, spacing: { after: 80, line: 360 } });

// ------------------------------------------------------------ figures, tables and captions ("Figure 1 - ...", below the object)
const FIGS = [], TABS = [], EQO = [];
let FIGN = 0, TABN = 0;
const FN = (k) => { const i = FIGS.indexOf(k); if (i < 0) throw new Error("no figure " + k); return i + 1; };
const TN = (k) => { const i = TABS.indexOf(k); if (i < 0) throw new Error("no table " + k); return i + 1; };
const EN = (k) => { const i = EQO.indexOf(k); if (i < 0) throw new Error("no equation " + k); return i + 1; };
function caption(kind, s) {
  const n = kind === "Figure" ? ++FIGN : ++TABN;
  const cr = { bold: true, italics: true, size: 20, color: CAPCOL };
  TOCL.push({ kind, n, text: `${kind} ${n} - ${plain(s)}` });
  return new Paragraph({
    style: "Caption", alignment: AlignmentType.CENTER, keepLines: true, spacing: { before: 60, after: 240, line: 252 },
    children: [new TextRun({ text: `${kind} `, font: FONT, ...cr }), new D.SimpleField(`SEQ ${kind} \\* ARABIC`, String(n)),
               new TextRun({ text: " - ", font: FONT, ...cr }), ...runs(s, cr)],
  });
}
function figure(file, cap, widthIn = 6.0) {
  if (FIGS[FIGN] !== file) throw new Error(`figure order: expected ${FIGS[FIGN]}, got ${file}`);
  const [w, h] = SIZES[file];
  let wpx = Math.round(widthIn * 96), hpx = Math.round(wpx * h / w);
  if (hpx > 8.0 * 96) { hpx = Math.round(8.0 * 96); wpx = Math.round(hpx * w / h); }
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 120, after: 0 },
      children: [new ImageRun({ type: "png", data: fs.readFileSync(path.join(IMG, file)), transformation: { width: wpx, height: hpx },
                                altText: { title: cap.slice(0, 60), description: cap, name: file } })] }),
    caption("Figure", cap),
  ];
}
function figRow(files, cap, widthIn = TEXTW_IN) {
  if (FIGS[FIGN] !== files[0]) throw new Error(`figure order: expected ${FIGS[FIGN]}, got ${files[0]}`);
  const each = widthIn / files.length - 0.05;
  const kids = [];
  files.forEach((f, i) => {
    const [w, h] = SIZES[f]; const wpx = Math.round(each * 96);
    kids.push(new ImageRun({ type: "png", data: fs.readFileSync(path.join(IMG, f)), transformation: { width: wpx, height: Math.round(wpx * h / w) },
                             altText: { title: f, description: cap, name: f } }));
    if (i < files.length - 1) kids.push(new TextRun({ text: " " }));
  });
  return [new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 120 }, children: kids }), caption("Figure", cap)];
}
const thin = { style: BorderStyle.SINGLE, size: 4, color: "8EAADB" };
function cell(s, w, o = {}) {
  const fill = o.head ? "D9E2F3" : (o.band ? "F2F6FC" : undefined);
  return new TableCell({
    borders: { top: thin, left: thin, right: thin, bottom: o.head ? { style: BorderStyle.SINGLE, size: 12, color: LINE } : thin },
    width: { size: w, type: WidthType.DXA }, verticalAlign: VerticalAlign.CENTER,
    shading: fill ? { fill, type: ShadingType.CLEAR, color: "auto" } : undefined,
    margins: { top: 40, bottom: 40, left: 80, right: 80 },
    children: [new Paragraph({ alignment: o.align || AlignmentType.LEFT, spacing: { after: 0, line: 240 }, keepNext: true,
                               children: runs(String(s), { bold: o.head || o.bold, size: o.size || 19 }) })],
  });
}
function table(key, cap, head, rows, widths, o = {}) {
  if (TABS[TABN] !== key) throw new Error(`table order: expected ${TABS[TABN]}, got ${key}`);
  const tot = widths.reduce((a, b) => a + b, 0);
  const W = widths.map((w) => Math.round(w / tot * TEXTW));
  W[W.length - 1] += TEXTW - W.reduce((a, b) => a + b, 0);
  const al = o.align || W.map((_, i) => (i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER));
  const trs = [new TableRow({ tableHeader: true, cantSplit: true, children: head.map((h, i) => cell(h, W[i], { head: true, align: al[i], size: o.size })) })];
  rows.forEach((r, ri) => trs.push(new TableRow({ cantSplit: true, children: r.map((v, i) => cell(v, W[i], {
    align: al[i], band: ri % 2 === 1, size: o.size,
    bold: (i === 0 && o.firstBold !== false) || (o.boldRows && o.boldRows.includes(r[0])) })) })));
  return [new Paragraph({ spacing: { before: 60, after: 0 }, keepNext: true, children: [] }),
          new Table({ width: { size: TEXTW, type: WidthType.DXA }, columnWidths: W, rows: trs }), caption("Table", cap)];
}

// ------------------------------------------------------------ equations (images), numbered at the right margin
const EQS = JSON.parse(fs.readFileSync(path.join(DIR, "eq_sizes.json")));
let EQN = 0;
function eq(key) {
  if (EQO[EQN] !== key) throw new Error(`equation order: expected ${EQO[EQN]}, got ${key}`);
  EQN += 1;
  const [w, h] = EQS[key]; const sc = 96 / 300 * 12 / 13;
  return new Paragraph({
    tabStops: [{ type: TabStopType.CENTER, position: Math.round(TEXTW / 2) }, { type: TabStopType.RIGHT, position: TEXTW }],
    spacing: { before: 100, after: 160, line: 240, lineRule: D.LineRuleType.AUTO }, keepLines: true,
    children: [new TextRun({ text: "\t", font: FONT }),
               new ImageRun({ type: "png", data: fs.readFileSync(path.join(DIR, "eq", key + ".png")), transformation: { width: Math.round(w * sc), height: Math.round(h * sc) },
                              altText: { title: "Equation " + EQN, description: "Equation " + EQN, name: key } }),
               new TextRun({ text: `\t(${EQN})`, font: FONT })],
  });
}

// ------------------------------------------------------------ numbers used in the text
const R = Object.fromEntries(RUNS.map((r) => [r.run, r]));
const f2 = (v) => (v == null ? "" : Number(v).toFixed(2));
const f3 = (v) => (v == null ? "" : Number(v).toFixed(3));
const pct = (a, b) => `${a >= b ? "+" : "−"}${Math.abs(100 * (a - b) / b).toFixed(1)} %`;
const er = (a, b) => `${Math.abs(100 * (a - b) / b).toFixed(1)} %`;
const pts = (a, b) => `${a >= b ? "+" : "−"}${Math.abs(a - b).toFixed(2)}`;
const minus = (s) => String(s).replace(/^-/, "−");
const tim = (x) => { const v = Math.round(Number(x)); return (v === 0 ? "0" : minus(String(v))) + "°"; };
const DOM = JSON.parse(fs.readFileSync(path.join(DIR, "..", "figs", "domain_fit.json")));
const EINF = DOM.eta_inf, KSL = DOM.slope;
const cI = { m: R.caseI_medium, f: R.caseI_fine }, c2 = { m: R.caseII_medium, f: R.caseII_fine }, c3 = { m: R.caseIII_medium, f: R.caseIII_fine };
const ANIMS = ["I", "II", "III"].filter((c) => SIZES[`anim_${c}.png`]);
const sci = (x) => { let e = Math.floor(Math.log10(x)); let m = Number((x / 10 ** e).toFixed(1)); if (m >= 10) { m = 1; e += 1; } return `${m.toFixed(1)} × 10^{${minus(String(e))}}`; };

FIGS.push("fig01_kinematics.png", "overset_holecut.png", "fig02_method_cost.png", "mesh_far.png", "fig13_workflow.png",
          "fig14_residuals.png", "fig03_cycle_convergence.png", "fig04_time_step.png", "fig05_domain_fit.png", "fig06_mesh_study.png",
          "fig07_fine_divergence.png", "fig09_caseI_cycle.png", "fig08_cases_efficiency.png", "fig10_caseII_cycle.png", "fig11_caseIII_cycle.png",
          "fig12_power_split.png", ...ANIMS.map((c) => `anim_${c}.png`));
TABS.push("kd_cases", "kin", "bcs", "mesh_levels", "solver", "setup_cmp", "dt", "domain", "mesh", "settings", "unc", "case1", "cases", "diff", "runs", "corr", "files");
EQO.push("eqkin", "eq1", "eq2", "eq5", "eq3", "eq4", "eq6", "eqer");

const C = [];
const add = (...xs) => xs.flat().forEach((x) => C.push(x));
const front = [];
const fadd = (...xs) => xs.flat().forEach((x) => front.push(x));

// ============================================================ front matter
fadd(FH("Abstract", false));
fadd(P(`This project reproduces, with OpenFOAM, the power-extraction efficiency of an oscillating NACA 0015 foil computed by Kinsey and Dumas (2008) at a Reynolds number of 1100. The foil heaves with an amplitude of one chord and pitches about a pivot at one third of the chord, with heave leading pitch by 90°. The two-dimensional laminar flow is solved with **pimpleFoam** on a body-fitted O-grid, generated with the gmsh Python interface, that moves rigidly with the foil; every run is scripted and executed on GitHub Actions. An overset mesh was built and tested first, but it needed 26 to 100 hours per flapping cycle on the available four-core runners against about 5 minutes for the rigid moving mesh, so the rigid mesh, which is equivalent to the authors' own heaving-frame approach, was used for all results.`));
fadd(P(`For the high-efficiency Case I (f* = 0.14, θ_{0} = 76.33°) the computed efficiency is ${f2(cI.f.eta_percent)} % on a 65,000-cell mesh with the far field at 80 chords, against 33.7 % in the paper. The two other published cases also agree: Case II (f* = 0.18, θ_{0} = 60°) gives ${f2(c2.f.eta_percent)} % against 11.4 % and Case III (f* = 0.06, θ_{0} = 60°) gives ${f2(c3.f.eta_percent)} % against 12.3 %. Mean drag and peak lift agree within 1 to 4 %; the peak pivot moment of Case I is 17 % low and is the least certain quantity. A verification study of 22 Case I runs shows that the time step (T/2000 to T/8000) changes the efficiency by less than 0.02 points, the mesh by about 0.5 points, and the far-field distance by much more: the efficiency follows η = ${EINF.toFixed(2)} + ${KSL.toFixed(1)}/R, so a far field at 20 chords over-predicts it by 1.7 points. The fine mesh required a limited non-orthogonal correction to remain stable. The results also explain an open question from our final-year project: an immersed-boundary code (WaterLily) over-predicts Case II by about 4 points because it misses a lift and moment event near stroke reversal, not because of the case definition.`));
fadd(P(`**Keywords:** oscillating foil, flow energy harvesting, OpenFOAM, moving mesh, verification and validation, Kinsey and Dumas.`));

fadd(FH("Table of Contents"));
fadd(new TableOfContents("Table of Contents", { hyperlink: true, headingStyleRange: "1-2" }));
fadd(FH("List of Figures"));
fadd(new TableOfContents("List of Figures", { hyperlink: true, captionLabel: "Figure" }));
fadd(new Paragraph({ spacing: { after: 360 }, children: [] }));
fadd(FH("List of Tables", false));
fadd(new TableOfContents("List of Tables", { hyperlink: true, captionLabel: "Table" }));
fadd(FH("Nomenclature"));
const NOM = [
  ["c", "Chord length (reference length, c = 1)"], ["C_{X}, C_{Y}, C_{M}", "Drag, lift and pivot-moment coefficients"],
  ["C_{P}, C̄_{P}", "Power coefficient; its cycle mean"], ["Co", "Courant number"], ["d", "Overall height swept by the foil"],
  ["E_{r}", "Relative difference from the reference (%)"], ["f, T", "Flapping frequency; period, T = 1/f"], ["f*", "Reduced frequency fc/U"],
  ["H_{0}", "Heave amplitude (= c)"], ["h(t), θ(t)", "Heave position; pitch angle"], ["N", "Number of cells"],
  ["R", "Radius of the circular far-field boundary (in chords)"], ["Re", "Reynolds number Uc/ν = 1100"],
  ["U, u, u_{m}", "Free-stream speed (U = 1); fluid velocity; mesh velocity"], ["V_{y}, Ω", "Heave velocity; pitch rate"],
  ["x_{p}", "Pivot position from the leading edge (= c/3)"], ["α_{T/4}", "Effective angle of attack at the quarter period"],
  ["η, η_{∞}", "Power-extraction efficiency C̄_{P}c/d; its value for an infinite domain"], ["θ_{0}", "Pitch amplitude"],
  ["ν, ρ", "Kinematic viscosity; density"], ["χ", "Feathering parameter"],
  ["K&D", "Kinsey and Dumas (2008), the reference study"], ["ALE", "Arbitrary Lagrangian–Eulerian"], ["GCI", "Grid convergence index"],
  ["LEV", "Leading-edge vortex"], ["PIMPLE", "OpenFOAM's merged PISO–SIMPLE pressure–velocity algorithm"], ["TE", "Trailing edge"],
];
NOM.forEach(([a, b]) => fadd(new Paragraph({ tabStops: [{ type: TabStopType.LEFT, position: 2160 }], spacing: { after: 40, line: 276 },
  children: [...runs(a, { size: 21 }), new TextRun({ text: "\t", font: FONT, size: 21 }), ...runs(b, { size: 21 })] })));

// ============================================================ 1 Introduction
add(H1("1. Introduction"));
add(H2("1.1 Background"));
add(P(`A foil that heaves and pitches at the same time can extract energy from a stream, in the same way as a wind or tidal turbine but with a rectangular swept area and low tip speeds [6, 7]. Kinsey and Dumas [1] mapped the efficiency of such a foil over frequency and pitch amplitude with two-dimensional laminar simulations at Re = 1100 and showed that efficiencies above 30 % are possible when the foil is driven hard enough in pitch for a leading-edge vortex to form and be shed at the right moment in each stroke. Their study is a standard benchmark for flapping-foil energy harvesting.`));
add(H2("1.2 Motivation"));
add(P(`The study is also the reference case of our final-year project, which places such a foil in the wake of a cylinder. In that project the immersed-boundary code WaterLily [8] reproduced Kinsey and Dumas' Case I to within 1.5 points but over-predicted their Case II by about 4 points at every resolution tried, and the cause was unknown. An independent body-fitted solution of the same cases tells us whether the gap lies in the case definition or in the code. The project follows Pathway B of the course (reproduction of a research paper). The proposal named Ansys Fluent; we moved to OpenFOAM with gmsh so that every case could be scripted, kept under version control and run on free GitHub Actions machines.`));
add(H2("1.3 Research Question"));
add(P(`~~Can a body-fitted OpenFOAM model reproduce the efficiency, force histories and efficiency trend that Kinsey and Dumas report for an oscillating NACA 0015 foil at Re = 1100, and what causes any differences?~~`));
add(H2("1.4 Objectives"));
add(numbered("Reproduce Kinsey and Dumas' Case I, the high-efficiency case, with OpenFOAM."));
add(numbered("Quantify the numerical error of that result through iterative, periodic, time-step, domain-size, mesh and solver-setting checks."));
add(numbered("Compare with the paper and with our own result from a different method (WaterLily)."));
add(numbered("Check that the model captures the trend across operating points with the paper's Cases II and III, and explain the trend physically."));
add(H2("1.5 Scope and Outline"));
add(P(`Chapter 2 describes the reference study and the exact results to be reproduced. Chapter 3 formulates the problem and Chapter 4 the numerical method, including why an overset mesh was built first and then replaced. Chapter 5 verifies the Case I solution and Chapter 6 presents the results, the comparison with the paper and their physical interpretation. Chapters 7 and 8 give the limitations and conclusions. The appendices list every run, explain how to reproduce the results and contain the AI-use disclosure.`));

// ============================================================ 2 Reference study
add(H1("2. Reference Study"));
add(H2("2.1 The Reference Paper"));
add(P(`T. Kinsey and G. Dumas, "Parametric study of an oscillating airfoil in a power-extraction regime," ~~AIAA Journal~~, vol. 46, no. 6, pp. 1318–1330, 2008 [1]. The authors computed the two-dimensional laminar flow around a NACA 0015 foil heaving with amplitude H_{0} = c and pitching about x_{p} = c/3, at Re = 1100, over 0 < f* < 0.25 and 0 < θ_{0} < 90°. They mapped the efficiency over this plane (their Fig. 11), found a maximum of about 34 % near f* = 0.14 and θ_{0} = 76°, and explained the high efficiency by the timing of the leading-edge vortex relative to the heave motion.`));
add(H2("2.2 Reference Numerical Set-up"));
add(P(`Kinsey and Dumas used the finite-volume code FLUENT 6.1 with second-order upwind convection, second-order central diffusion, second-order backward time integration and SIMPLE pressure–velocity coupling [1]. To keep second-order time integration with moving meshes, they solved in a reference frame that heaves with the foil, with a circular zone of radius 5c pitching rigidly inside a fixed outer grid (sliding interface). Their standard grid had 72,000 cells, and the time step was the smaller of T/2000 and c/(100|V|), where |V| is the largest convective velocity. After an impulsive start of at least 20 convective times, they required the cycle-mean statistics to change by less than 0.1 % between the final cycles. The paper does not state the distance to the outer boundary; Section 5.4 shows that this distance matters.`));
add(H2("2.3 Results to Be Reproduced"));
add(P(`The quantitative reference is the paper's Table 2, which gives the cycle-mean drag, the peak lift and pivot moment and the efficiency for three cases computed in detail (Table ${TN("kd_cases")}). The same table reports the authors' own refinement study: for Case I the efficiency is 33.6 %, 33.7 % and 33.9 % on 16,000, 72,000 and 253,000 cells, and 33.6 %, 33.7 % and 33.7 % with 500, 2000 and 4000 steps per cycle. The one-cycle force histories of their Figs. 9 and 12 are used qualitatively.`));
add(table("kd_cases", "Kinsey and Dumas Table 2 values reproduced in this project (72,000 cells, 2000 steps per cycle) [1]", ["Case", "f*", "θ_{0}", "η", "mean C_{X}", "peak C_{Y}", "peak C_{M}"], [
  ["I", "0.14", "76.33°", "33.7 %", "2.014", "1.910", "0.646"], ["II", "0.18", "60°", "11.4 %", "0.690", "1.256", "0.299"],
  ["III", "0.06", "60°", "12.3 %", "1.256", "2.030", "0.597"]], [1, 1, 1, 1, 1.2, 1.2, 1.2], { align: Array(7).fill(AlignmentType.CENTER) }));
add(H2("2.4 Quasi-Steady Parameters of the Cases"));
add(P(`Kinsey and Dumas characterise each motion by two quasi-steady numbers [1]: the effective angle of attack at the quarter period, which is close to the largest angle the foil sees in a cycle, and the feathering parameter:`));
add(eq("eqkin"));
add(P(`Power extraction needs χ > 1 (α_{T/4} < 0). Table ${TN("kin")} lists both for the three cases; they are used in Chapter 6 to explain the trend.`));
add(table("kin", "Quasi-steady kinematic parameters of the three cases (Equations 5 and 7 of [1])", ["Case", "f*", "θ_{0}", "peak heave velocity / U", "α_{T/4}", "χ", "V_{max}/U"], [
  ["I", "0.14", "76.33°", "0.880", "−35.0°", "1.85", "1.33"],
  ["II", "0.18", "60°", "1.131", "−11.5°", "1.24", "1.51"],
  ["III", "0.06", "60°", "0.377", "−39.3°", "2.90", "1.07"]], [0.7, 0.7, 0.9, 1.6, 0.9, 0.7, 1.0], { align: Array(7).fill(AlignmentType.CENTER) }));
add(H2("2.5 Secondary Reference"));
add(P(`Our final-year-project WaterLily results (immersed-boundary method, 64 cells per chord) serve as a cross-check: Case I gave η = 32.2 % and Case II 15.2 %. They are our own earlier results and are labelled as such in every table and figure.`));

// ============================================================ 3 Problem formulation
add(H1("3. Problem Formulation"));
add(H2("3.1 Geometry and Kinematics"));
add(P(`The foil is a NACA 0015 section of chord c with the standard open (blunt) trailing edge of thickness 0.0032c. It heaves with amplitude H_{0} = c and pitches about a pivot at x_{p} = c/3 from the leading edge. With time measured from the top of the stroke:`));
add(eq("eq1"));
add(P(`so the heave leads the pitch by 90°. Positive pitch is counter-clockwise, which turns the nose down. The flow is characterised by`));
add(eq("eq2"));
add(...figure("fig01_kinematics.png", "Prescribed motion for Case I: (a) heave and pitch against time; (b) the foil at every twelfth of a period (positions spread along x for clarity)"));
add(H2("3.2 Computational Domain"));
add(P(`The domain is a circle of radius R centred on the mean pivot position, so that the outer boundary is the same distance from the foil in every direction and can act as inflow or outflow wherever the flow requires. All quantities are made dimensionless with c and U. The baseline uses R = 20c, a common choice for two-dimensional foils; because a lifting foil disturbs the flow far away, R was then varied from 12c to 80c (Section 5.4), and the final runs use R = 80c with a measured correction to an infinite domain. The motion is periodic, but the wake is not, so the whole plane is computed (no symmetry). The flow is two-dimensional, as in the reference: the mesh is one cell thick in the spanwise direction with empty front and back faces.`));
add(H2("3.3 Governing Equations and Assumptions"));
add(P(`The flow is incompressible, laminar and two-dimensional, as in the paper; at Re = 1100 the attached boundary layers are laminar and the flow is dominated by large vortices [1]. Because the mesh moves, the momentum equation is solved in arbitrary Lagrangian–Eulerian form [12], with the convecting velocity taken relative to the mesh velocity u_{m}:`));
add(eq("eq5"));
add(P(`With U = c = 1 the kinematic viscosity is ν = 1/1100 and the density is 1; no turbulence, thermal or other additional models are used.`));
add(H2("3.4 Boundary and Initial Conditions"));
add(table("bcs", "Boundary conditions", ["Boundary", "Velocity", "Pressure"], [
  ["Foil", "movingWallVelocity (no slip on the moving wall)", "zeroGradient"],
  ["Far field (circle of radius R)", "freestreamVelocity (U = 1, inflow/outflow switching)", "freestreamPressure (p = 0)"],
  ["Front and back", "empty (two-dimensional)", "empty"]], [1.4, 2.6, 1.8], { align: [AlignmentType.LEFT, AlignmentType.LEFT, AlignmentType.LEFT] }));
add(P(`The flow starts from a uniform stream (u = U, p = 0) with the foil at the top of its stroke and moving impulsively, as in the paper. The first cycles carry this start-up transient and are discarded (Section 5.2).`));
add(H2("3.5 Performance Measures"));
add(P(`Forces and the moment about the pivot are made dimensionless with the dynamic pressure, the chord and the span:`));
add(eq("eq3"));
add(P(`The power taken from the flow is the sum of the heave and pitch contributions, and the efficiency compares its mean with the power of the undisturbed stream through the height d swept by the foil:`));
add(eq("eq4"));
add(P(`The swept height is computed from the geometry: d = 2.565c for Case I and 2.402c for Cases II and III. Peak values are the largest magnitude of a seven-point moving average of a cycle divided into 200 equal phase bins, and the lift timing is the phase of the first harmonic of C_{Y} relative to the heave velocity (0° means lift and heave velocity are in step).`));

// ============================================================ 4 Numerical method
add(H1("4. Numerical Method"));
add(H2("4.1 Choice of Mesh-Motion Method"));
add(P(`The project plan used an overset (Chimera) mesh [13]: a foil O-grid moving over a fixed Cartesian background, the approach needed later for a foil behind a fixed cylinder. This was built and tested first (overPimpleDyMFoam, inverseDistance and trackingInverseDistance interpolation).`));
add(bullet("**Meshes.** Coarse, medium and fine overset meshes of 55,160, 107,605 and 215,990 cells all passed checkMesh, with maximum non-orthogonality of about 62°."));
add(bullet("**Hole cutting.** A first attempt flooded almost the whole background with hole cells. The cause was the O-grid's front and back faces, which gmshToFoam leaves as ordinary patches; after merging they acted like a wall. Setting them to empty before merging fixed it, leaving about 0.2 % holes, all inside the foil, and a closed ring of interpolated cells at every position of the cycle (Figure " + FN("overset_holecut.png") + ")."));
add(bullet("**Cost.** With the time step adjusted to keep the Courant number at or below 1, the medium overset mesh needed 6.9 to 10.6 s per step and 13,500 to 35,000 steps per cycle. At the paper's fixed T/2000 the overset run diverged in the first cycle."));
add(...figure("overset_holecut.png", "Overset cell types through one cycle (medium mesh): holes inside the foil (red), interpolated cells (blue), calculated cells (grey)"));
add(P(`Figure ${FN("fig02_method_cost.png")} compares the cost. About 22 Case I runs of 10 cycles were needed for this report; with overset that is several thousand hours of runner time, against a few hours with a rigid moving mesh. For a single foil in open water nothing in the domain has to stay still, so a mesh that moves rigidly with the foil is exact. It was used for every result; overset remains the right tool for the cylinder–foil configuration of our final-year project.`));
add(...figure("fig02_method_cost.png", "Wall-clock time per flapping cycle on a four-core runner: overset (adaptive time step, Courant number ≤ 1) against the rigid moving mesh"));
add(H2("4.2 Mesh Generation"));
add(P(`The mesh is built with the gmsh Python interface [5] and converted with gmshToFoam. Around the foil, an O-grid of radius 1.2c centred on the pivot is made of three transfinite blocks: the upper surface, the lower surface and a narrow block behind the blunt trailing edge. Points cluster towards the leading and trailing edges, and the radial spacing grows geometrically from the wall. A polar ring with the same angular distribution continues the grid to the circular far field, with a growth rate of 1.07 per cell. Four levels were generated with a refinement ratio of about 1.5 in each direction (Table ${TN("mesh_levels")}); all pass checkMesh, with a maximum non-orthogonality of 61.5°.`));
add(table("mesh_levels", "Mesh levels (cell counts at R = 20c and 80c)", ["Level", "Points per side", "Points across TE", "First cell", "Cells, 20c", "Cells, 80c"], [
  ["coarse", "70", "3", "0.0030c", "14,560", "–"], ["medium", "105", "4", "0.0020c", "28,907", "33,338"], ["fine", "158", "6", "0.0013c", "58,696", "65,395"],
  ["extra-fine", "237", "9", "0.00087c", "120,960", "–"]], [1.2, 1.2, 1.2, 1.1, 1.1, 1.1]));
add(...figRow(["mesh_far.png", "mesh_near.png", "mesh_te.png"], "Fine mesh: (left) whole domain with the far field at 20c; (centre) O-grid around the foil; (right) cells behind the blunt trailing edge, where the fine mesh first became unstable (Section 5.6)"));
add(H2("4.3 Mesh Motion"));
add(P(`The whole mesh moves as a rigid body with the foil (solidBody motion solver, tabulated6DoFMotion). A Python script writes the heave and pitch of Equation ${EN("eq1")} as a table of 400 points per cycle; OpenFOAM rotates the mesh about the pivot and translates it every time step, and the mesh fluxes enter Equation ${EN("eq5")} through u_{m}. This is the OpenFOAM equivalent of Kinsey and Dumas' heaving frame with a rigidly pitching zone, without the sliding interface.`));
add(H2("4.4 Solver and Discretisation"));
add(P(`OpenFOAM v2412 (ESI) [3, 9] solves Equation ${EN("eq5")} with **pimpleFoam**, a finite-volume solver whose PIMPLE algorithm combines the PISO [4] and SIMPLE pressure–velocity coupling. Table ${TN("solver")} lists the settings used for all results.`));
add(table("solver", "Solver settings", ["Item", "Setting"], [
  ["Solver", "pimpleFoam, dynamicMotionSolverFvMesh (mesh moves every step)"],
  ["Time derivative", "backward (second order), fixed Δt = T/2000 (Case III: T/4000)"],
  ["Convection", "Gauss linearUpwind grad(U) (second order)"], ["Gradients", "Gauss linear"],
  ["Laplacian / surface-normal gradient", "Gauss linear corrected; limited corrected 0.33 for the mesh study and the final runs (Section 5.6)"],
  ["Pressure–velocity coupling", "PIMPLE, 2 outer loops, 2 pressure correctors, 1 non-orthogonal corrector"],
  ["Linear solvers", "GAMG for pressure (tolerance 10^{−8}); symmetric Gauss–Seidel for velocity (10^{−9})"],
  ["Parallel", "4 MPI ranks (scotch decomposition)"],
  ["Transport", "ν = 1/1100 (U = c = 1)"],
], [1.6, 4.0], { align: [AlignmentType.LEFT, AlignmentType.LEFT] }));
add(H2("4.5 Convergence Criteria"));
add(bullet("**Within each time step:** the final pressure solve of every step is converged to an absolute residual of 10^{−8} and the velocity to 10^{−9}; two PIMPLE outer loops are used because the Courant number exceeds 1 in a few cells near the foil. Residual histories are shown in Section 5.1."));
add(bullet("**Periodic state:** a run is settled when the efficiency of successive cycles changes by less than 0.05 points; the reported values are averages over the settled cycles, and the spread between them is quoted."));
add(bullet("**Stability:** a run is counted as diverged when the solver stops with a floating-point error before its end time (the Courant number grows by orders of magnitude in the steps before); such runs are reported, not hidden."));
add(H2("4.6 Comparison with the Reference Set-up"));
add(table("setup_cmp", "Numerical set-up of Kinsey and Dumas [1] and of this work", ["Item", "Kinsey and Dumas (2008)", "This work"], [
  ["Code", "FLUENT 6.1", "OpenFOAM v2412, pimpleFoam"],
  ["Mesh motion", "heaving frame; zone of radius 5c pitching inside a fixed grid (sliding interface)", "whole mesh moves rigidly with the foil (heave and pitch)"],
  ["Convection / diffusion", "second-order upwind / second-order central", "linearUpwind / linear, limited corrected 0.33"],
  ["Time integration", "second-order backward", "second-order backward"],
  ["Pressure–velocity", "SIMPLE, AMG", "PIMPLE (2 outer loops), GAMG"],
  ["Cells", "72,000", "33,338 (medium), 65,395 (fine)"],
  ["Time step", "min(T/2000, c/(100|V|))", "T/2000 fixed (Case III: T/4000)"],
  ["Far field", "not stated", "circle, R = 80c (12c to 80c studied)"],
  ["Periodicity", "< 0.1 % change in mean statistics; last cycle recorded", "settled cycles averaged (spread ≤ 0.06 points)"],
], [1.3, 2.4, 2.4], { align: [AlignmentType.LEFT, AlignmentType.LEFT, AlignmentType.LEFT] }));
add(H2("4.7 Post-processing"));
add(P(`OpenFOAM's forces function object records the pressure and viscous force and the moment about the origin every step. A Python script moves the moment to the moving pivot, forms the coefficients of Equations ${EN("eq3")} and ${EN("eq4")} with the analytic heave velocity and pitch rate, and splits the record into cycles. Each cycle is divided into 200 equal phase bins and every sample is averaged into its bin, so cycle means are exact time averages.`));
add(P(`The bin averaging matters because the motion table is interpolated linearly: the foil's acceleration arrives as a small step every 5 time steps, and the forces carry a matching saw-tooth of a few per cent. Our first post-processing sampled the record exactly at the table points, which over-weighted those steps and raised every efficiency by 0.1 to 0.3 points. All numbers in this report use the corrected method (Appendix C).`));
add(H2("4.8 Automated Workflow"));
add(P(`Every step from mesh generation to plotting is a script in the project repository. Each study is a GitHub Actions workflow whose matrix starts one job per run on a four-core, 16 GB machine with a six-hour limit. Each job installs OpenFOAM, builds its mesh, runs, post-processes and commits its logs, tables and pictures to a results branch, so the studies of Chapter 5 run in parallel and every number can be traced to its log (Figure ${FN("fig13_workflow.png")}).`));
add(...figure("fig13_workflow.png", "Automated workflow: one GitHub Actions job per run", 5.6));

// ============================================================ 5 Verification
add(H1("5. Verification"));
add(P(`Verification asks whether the equations are solved accurately; comparison with the paper (validation of the reproduction) follows in Chapter 6. Each check below changes one setting of the Case I baseline: medium mesh, T/2000, far field at 20c, 10 cycles with cycles 5 to 10 averaged.`));
add(H2("5.1 Iterative Convergence"));
add(P(`Figure ${FN("fig14_residuals.png")} shows the residuals of every time step of the final Case I fine-mesh run (${RES.steps.toLocaleString("en-US")} steps over 14 cycles). The pressure starts each step with a normalised residual of about 0.1, as expected when the mesh has moved, and its last solve of every step ends at or below the tolerance of 10^{−8} (largest value ${sci(RES.pfin_max)}). The second PIMPLE outer loop starts with a velocity residual about ${Math.round(RES.drop_outer)} times smaller than the first (median ${sci(RES.ux2_median)}), so two outer loops converge the non-linear coupling within each step. The continuity error stays below ${sci(RES.cont_max)}. The momentum residual grows while the wake develops and, after about eight cycles, repeats the same pattern every half-cycle with no drift.`));
add(...figure("fig14_residuals.png", "Residual history of the final Case I fine-mesh run (80c, T/2000): (a) whole run; (b) last cycle"));
add(H2("5.2 Periodic Convergence"));
add(P(`The first cycle starts from rest and over-predicts the efficiency (41.9 %). The result settles by the fifth cycle; cycles 5 to 10 of the baseline give ${f2(R.base.eta_percent)} ± 0.03 %. Larger domains take longer to settle (Figure ${FN("fig03_cycle_convergence.png")}), so the domain study uses the value of cycle 10 and the final runs average cycles 9 to 14 (Case II: 9 to 16; Case III: 5 to 8).`));
add(...figure("fig03_cycle_convergence.png", "Efficiency of each cycle for Case I"));
add(H2("5.3 Time Step"));
add(table("dt", "Time-step study (medium mesh, 20c, cycles 5 to 10)", ["Time step", "η", "mean C_{X}", "peak C_{Y}", "peak C_{M}", "max Co", "min per cycle"], [
  ["T/1000", "diverged after 87 steps", "", "", "", "≈ 26", ""],
  ["T/2000", f2(R.base.eta_percent) + " %", f3(R.base.mean_CX), f3(R.base.peak_CY), f3(R.base.peak_CM), "13.0", "5.1"],
  ["T/4000", f2(R.dt4000.eta_percent) + " %", f3(R.dt4000.mean_CX), f3(R.dt4000.peak_CY), f3(R.dt4000.peak_CM), "7.1", "6.8"],
  ["T/8000", f2(R.dt8000.eta_percent) + " %", f3(R.dt8000.mean_CX), f3(R.dt8000.peak_CY), f3(R.dt8000.peak_CM), "4.1", "15.7"]], [1, 1.5, 1, 1, 1, 0.8, 1]));
add(P(`Halving the step twice changes the efficiency by 0.01 points and the force curves lie on top of each other (Figure ${FN("fig04_time_step.png")}). The paper's step, T/2000, is therefore converged, as Kinsey and Dumas also found. It is close to the stability limit of this scheme: T/1000 diverges, with a Courant number of about 26 in the cells behind the trailing edge.`));
add(...figure("fig04_time_step.png", "Averaged cycle of lift and power for three time steps (medium mesh, 20c)"));
add(H2("5.4 Domain Size"));
add(P(`The far field was placed at R = 12, 20, 40, 60 and 80 chords. The efficiency falls steadily as the boundary moves away, by 2.3 points over this range, and the values from 20c to 80c lie on a straight line in 1/R (Figure ${FN("fig05_domain_fit.png")}):`));
add(eq("eq6"));
add(P(`with η_{∞} = ${EINF.toFixed(2)} % and k = ${KSL.toFixed(1)} %·c. This 1/R behaviour is expected for a lifting body: its far-field disturbance decays slowly, and a boundary that imposes the free stream at a finite distance acts like a weak blockage. At 20c the domain error is 1.7 points (5 %); at 80c it is 0.43 points. The peak moment is also domain-sensitive, falling from 0.660 at 12c to 0.595 at 80c.`));
add(table("domain", "Domain study (medium mesh, T/2000)", ["Far field R", "Cells", "η, cycle 10", "1/R fit", "mean C_{X}", "peak C_{M}"],
  DOM.points.map(([Rr, e]) => {
    const r = { 12: R.R12, 20: R.base, 40: R.R40, 60: R.R60, 80: R.R80 }[Rr];
    return [`${Rr}c`, r.cells.toLocaleString("en-US"), `${e.toFixed(2)} %`, `${(EINF + KSL / Rr).toFixed(2)} %`, f3(r.mean_CX), f3(r.peak_CM)];
  }).concat([["∞ (fit)", "", "", `${EINF.toFixed(2)} %`, "", ""]]), [1.1, 1, 1.1, 1.1, 1, 1]));
add(...figure("fig05_domain_fit.png", "Case I efficiency against the inverse far-field radius, with the 1/R fit (fitted to R ≥ 20c)"));
add(H2("5.5 Mesh Refinement"));
add(P(`Table ${TN("mesh")} compares the three meshes with the same settings (limited non-orthogonal correction, explained in Section 5.6). Mean drag and peak lift change by less than 1.5 %, and the moment curves overlap (Figure ${FN("fig06_mesh_study.png")}b), but the efficiency rises by 0.29 points from coarse to medium and by 0.50 points from medium to fine.`));
add(table("mesh", "Mesh study (far field 20c, T/2000, limited correction, cycles 5 to 10)", ["Mesh", "Cells", "η", "mean C_{X}", "peak C_{Y}", "peak C_{M}", "min per cycle"], [
  ["coarse", "14,560", f2(R.coarse_l.eta_percent) + " %", f3(R.coarse_l.mean_CX), f3(R.coarse_l.peak_CY), f3(R.coarse_l.peak_CM), "1.4"],
  ["medium", "28,907", f2(R.base_l.eta_percent) + " %", f3(R.base_l.mean_CX), f3(R.base_l.peak_CY), f3(R.base_l.peak_CM), "3.5"],
  ["fine", "58,696", f2(R.fine_l.eta_percent) + " %", f3(R.fine_l.mean_CX), f3(R.fine_l.peak_CY), f3(R.fine_l.peak_CM), "12.0"],
  ["extra-fine", "120,960", "diverged", "", "", "", ""]], [1.1, 1, 1, 1, 1, 1, 1]));
add(P(`Because the change grows with refinement, the solution is not yet in the asymptotic range and a grid convergence index [2, 11] cannot be formed; we take the medium-to-fine change, ±0.5 points, as the mesh uncertainty. Further refinement would probably raise the efficiency a little more: Kinsey and Dumas also saw it rise with refinement, from 33.6 % (16,000 cells) through 33.7 % (72,000) to 33.9 % (253,000) [1]. An extra-fine mesh would settle this, but it diverged at the start (Section 5.6).`));
add(...figure("fig06_mesh_study.png", "Mesh study: (a) efficiency against mesh size; (b) averaged cycle of the pivot moment"));
add(H2("5.6 Stability of the Fine Meshes"));
add(P(`With the baseline settings the fine mesh diverged after about 80 steps at every time step tried (T/2000 and T/4000), in serial and in parallel, and even with the foil held still or with the motion ramped up gently. checkMesh with all geometry and topology tests passed, and changing the trailing-edge block (cells across the edge, block angle, point clustering, mesh smoothing), the wall spacing or the number of surface points, or starting from a potential-flow solution, did not help. A diagnostic run that wrote the flow at every step located the start of the blow-up in the first few cells behind the blunt trailing edge, which are strongly sheared where the three O-grid blocks meet (Figure ${FN("mesh_far.png")}, right). The standard OpenFOAM remedy for such cells, limiting the explicit non-orthogonal correction (laplacianSchemes and snGradSchemes "limited corrected 0.33"), cured it (Figure ${FN("fig07_fine_divergence.png")}). Four PIMPLE outer loops or a velocity-gradient limiter did not. The extra-fine mesh diverged at the same point even with the limiter and with every variant listed above, so it could not be used.`));
add(...figure("fig07_fine_divergence.png", "Maximum Courant number over the first 160 steps of the fine mesh with and without the limited correction, and of the medium mesh"));
add(P(`On the medium mesh the limiter changes the efficiency by only 0.09 points, but it lowers the peak moment by 6 % (0.630 to 0.592). The limiter was therefore kept for the mesh study and the final runs, and its effect on the moment is counted in the uncertainty.`));
add(H2("5.7 Solver Settings"));
add(table("settings", "Other solver settings (medium mesh, 20c)", ["Setting", "η", "mean C_{X}", "peak C_{M}", "min per cycle"], [
  ["baseline", f2(R.base.eta_percent) + " %", f3(R.base.mean_CX), f3(R.base.peak_CM), "5.1"],
  ["4 PIMPLE outer loops", f2(R.medium_outer4.eta_percent) + " %", f3(R.medium_outer4.mean_CX), f3(R.medium_outer4.peak_CM), "7.8"],
  ["velocity-gradient limiter", f2(R.medium_lim.eta_percent) + " %", f3(R.medium_lim.mean_CX), f3(R.medium_lim.peak_CM), "3.8"],
  ["limited corrected 0.33", f2(R.base_l.eta_percent) + " %", f3(R.base_l.mean_CX), f3(R.base_l.peak_CM), "3.5"]], [2, 1, 1, 1, 1]));
add(P(`More outer loops or a gradient limiter change the efficiency by at most 0.13 points, well inside the mesh uncertainty.`));
add(H2("5.8 Uncertainty Budget"));
add(table("unc", "Numerical uncertainty of the Case I efficiency", ["Source", "Estimate", "Treatment"], [
  ["Cycle-to-cycle variation", "±0.05 points", "average of the settled cycles"],
  ["Iterative convergence", "negligible", "p to 10^{−8} every step (Section 5.1)"],
  ["Time step", "< 0.02 points", "negligible at T/2000"],
  ["Far field at 80c", "0.43 points", "corrected with the 1/R fit"],
  ["Mesh (medium to fine)", "±0.5 points", "taken as the mesh uncertainty"],
  ["Non-orthogonal limiter", "0.1 points (η), 6 % (peak C_{M})", "reported"]], [1.8, 1.5, 2.2], { align: [AlignmentType.LEFT, AlignmentType.CENTER, AlignmentType.LEFT] }));
add(P(`The mesh is the dominant remaining uncertainty once the domain error is corrected; the overall uncertainty of the Case I efficiency is therefore about ±0.5 points.`));

// ============================================================ 6 Results and discussion
add(H1("6. Results and Discussion"));
add(H2("6.1 Reference Comparison: Case I"));
add(P(`The final Case I runs use the medium and fine meshes with the far field at 80c, the limited correction and 14 cycles, averaging cycles 9 to 14. Differences from the paper are given as the relative difference of the course guidelines,`));
add(eq("eqer"));
add(P(`and, for the efficiency, also in percentage points. Table ${TN("case1")} compares the results.`));
add(table("case1", "Case I: OpenFOAM (our results) against Kinsey and Dumas and WaterLily", ["Source", "η", "mean C_{X}", "peak C_{Y}", "peak C_{M}", "lift timing"], [
  ["OpenFOAM medium, 80c", f2(cI.m.eta_percent) + " %", f3(cI.m.mean_CX), f3(cI.m.peak_CY), f3(cI.m.peak_CM), tim(cI.m.lift_timing_deg)],
  ["OpenFOAM fine, 80c", f2(cI.f.eta_percent) + " %", f3(cI.f.mean_CX), f3(cI.f.peak_CY), f3(cI.f.peak_CM), tim(cI.f.lift_timing_deg)],
  ["OpenFOAM fine, infinite domain (corrected)", (cI.f.eta_percent - KSL / 80).toFixed(2) + " %", "", "", "", ""],
  ["Kinsey & Dumas (2008) [1]", "33.7 %", "2.014", "1.910", "0.646", "≈ 0°"],
  ["E_{r}, fine mesh", `${er(cI.f.eta_percent, 33.7)} (${pts(cI.f.eta_percent, 33.7)} points)`, er(cI.f.mean_CX, 2.014), er(cI.f.peak_CY, 1.910), er(cI.f.peak_CM, 0.646), ""],
  ["WaterLily (FYP, 64 cells per chord)", "32.2 %", "2.11", "1.98", "0.67", "within 3°"]], [2.4, 1.3, 1, 1, 1, 0.9]));
add(P(`Efficiency, mean drag and peak lift agree with the paper to within 1 to 2 %. The fine-mesh efficiency corrected to an infinite domain, ${(cI.f.eta_percent - KSL / 80).toFixed(2)} %, is within the ±0.5-point mesh uncertainty of the paper's value. The lift is in step with the heave velocity (timing within 1°), the condition Kinsey and Dumas identify for high efficiency.`));
add(P(`The peak pivot moment is the exception: 0.537 to 0.557 against 0.646 (14 to 17 % low). Part of this comes from the limited correction (−6 %, Section 5.6) and part from the larger domain (the medium-mesh peak falls from 0.630 at 20c to 0.595 at 80c). The moment curve has the same shape as WaterLily's (Figure ${FN("fig09_caseI_cycle.png")}), with the difference concentrated in the peaks near t/T = 0.44 and 0.94. Because pitching contributes little to the power in this case (Section 6.4), the efficiency is not sensitive to it.`));
add(...figure("fig09_caseI_cycle.png", "Case I: averaged cycle of lift, pivot moment, drag and power, OpenFOAM medium and fine meshes against WaterLily"));
add(P(`The lift curve shows the mechanism behind the high efficiency. After each stroke reversal (t/T ≈ 0.1 and 0.6) the lift jumps to about ±1.9 and stays high through most of the stroke while a leading-edge vortex forms on the suction side. A second peak just before the next reversal (t/T ≈ 0.44 and 0.94) appears as the vortex is shed past the trailing edge, keeping lift and heave velocity in step almost to the end of the stroke [1]. The power is positive for about 90 % of the cycle.`));
add(H2("6.2 Trend Across the Three Cases"));
add(P(`Cases II and III use the same settings as Case I (Case III with T/4000, because its period is 2.3 times longer). All three efficiencies are reproduced to within 0.5 points (Table ${TN("cases")} and Figure ${FN("fig08_cases_efficiency.png")}), and so is the trend: Case I is about three times as efficient as Cases II and III, and Case III is slightly more efficient than Case II.`));
const crow = (c, lev, r) => [`${c}, ${lev}`, f2(r.eta_percent) + " %", f3(r.mean_CX), f3(r.peak_CY), f3(r.peak_CM), tim(r.lift_timing_deg)];
add(table("cases", "All three cases: OpenFOAM (far field 80c) against Kinsey and Dumas", ["Case, mesh", "η", "mean C_{X}", "peak C_{Y}", "peak C_{M}", "lift timing"], [
  crow("I", "medium", cI.m), crow("I", "fine", cI.f), ["I, Kinsey & Dumas", "33.7 %", "2.014", "1.910", "0.646", ""],
  crow("II", "medium", c2.m), crow("II", "fine", c2.f), ["II, Kinsey & Dumas", "11.4 %", "0.690", "1.256", "0.299", ""],
  crow("III", "medium", c3.m), crow("III", "fine", c3.f), ["III, Kinsey & Dumas", "12.3 %", "1.256", "2.030", "0.597", ""]],
  [1.8, 1, 1, 1, 1, 1]));
add(table("diff", "Difference from Kinsey and Dumas, fine mesh (signed, relative unless stated)", ["Case", "η (points)", "η", "mean C_{X}", "peak C_{Y}", "peak C_{M}"], [
  ["I", pts(cI.f.eta_percent, 33.7), pct(cI.f.eta_percent, 33.7), pct(cI.f.mean_CX, 2.014), pct(cI.f.peak_CY, 1.910), pct(cI.f.peak_CM, 0.646)],
  ["II", pts(c2.f.eta_percent, 11.4), pct(c2.f.eta_percent, 11.4), pct(c2.f.mean_CX, 0.690), pct(c2.f.peak_CY, 1.256), pct(c2.f.peak_CM, 0.299)],
  ["III", pts(c3.f.eta_percent, 12.3), pct(c3.f.eta_percent, 12.3), pct(c3.f.mean_CX, 1.256), pct(c3.f.peak_CY, 2.030), pct(c3.f.peak_CM, 0.597)]], [1, 1, 1, 1, 1, 1]));
add(...figure("fig08_cases_efficiency.png", "Efficiency of the three cases: OpenFOAM medium and fine meshes (our results), Kinsey and Dumas, and WaterLily"));
add(P(`For Cases I and III the paper's value lies between or at our medium and fine results. For Case II both meshes are slightly low (11.20 % and 10.90 % against 11.4 %), and the fine mesh moves further away; with forces otherwise within 4 %, this is the largest efficiency difference of the study. The far-field correction was measured for Case I only and is not applied to Cases II and III.`));
add(H2("6.3 Force Histories and Flow Behaviour"));
add(P(`The quasi-steady parameters of Table ${TN("kin")} explain most of the trend. Case I combines a large effective angle (35°, deep dynamic stall) with a fast heave, which is the combination Kinsey and Dumas found most efficient. Case II is only just in the power-extraction regime (χ = 1.24): its effective angle never exceeds about 12°, so no leading-edge vortex forms and the lift stays small and out of step with the heave. Case III reaches the largest angle (39°) but heaves at most at 0.38U, so the strong forces do little work.`));
add(P(`The force histories confirm this. In Case II the lift lags the heave velocity by about 55°, so for part of each stroke the foil pushes against the flow and the power becomes negative (C_{P} down to −0.65 near t/T = 0.4 and 0.9, Figure ${FN("fig10_caseII_cycle.png")}), the poor synchronisation Kinsey and Dumas describe for this case [1]. Case III produces the largest lift peaks of the three (C_{Y} ≈ 2.05, Figure ${FN("fig11_caseIII_cycle.png")}) but extracts only about 12 % of the available power.`));
add(...figure("fig10_caseII_cycle.png", "Case II: averaged cycle, OpenFOAM medium and fine meshes against WaterLily"));
add(...figure("fig11_caseIII_cycle.png", "Case III: averaged cycle, OpenFOAM medium and fine meshes"));
add(H2("6.4 Where the Power Comes From"));
add(P(`Splitting the mean power into its heave and pitch parts (Equation ${EN("eq4")}) shows how differently the cases work (Figure ${FN("fig12_power_split.png")}). In Case I almost all the power comes from heave (0.835 of 0.863), and pitching adds a little. In Case II pitching costs power (−0.130), which removes a third of what heave extracts. In Case III the pitch contribution is close to zero. The sum reproduces the computed C̄_{P} to within 10^{−4}.`));
add(...figure("fig12_power_split.png", "Mean heave and pitch power for the three cases (fine mesh, 80c)"));
if (ANIMS.length) {
  add(H2("6.5 Flow Visualisation"));
  add(P(`Figures ${FN("anim_" + ANIMS[0] + ".png")} to ${FN("anim_" + ANIMS[ANIMS.length - 1] + ".png")} show the vorticity at four instants of the last computed cycle of each case (medium mesh, far field 80c). Red is counter-clockwise vorticity. The full animations (100 frames per cycle, with the lift and power of the cycle and a moving marker) are supplied as GIF and MP4 files with the data package.`));
  add(P(`**Case I.** At each stroke reversal (t/T = 0 and 0.5) the leading-edge vortex built up during the stroke reaches the trailing edge and leaves it together with an opposite-sign trailing-edge vortex (the pair at x ≈ 1c). This is the moment of the second lift peak in Figure ${FN("fig09_caseI_cycle.png")}, so the vortex still adds lift in step with the heave until the end of the stroke. During the stroke a row of smaller vortices leaves the trailing edge, and the wake holds one dominant vortex per half-cycle spread over about ±1.5c.`));
  add(P(`**Case II.** The vorticity stays in thin layers along both sides of the foil at every instant: no leading-edge vortex forms, which agrees with its small effective angle (Table ${TN("kin")}). The wake vortices are weak (|ω|c/U below about 3) and the wake is narrow.`));
  add(P(`**Case III.** By mid-stroke (t/T = 0.25 and 0.75) a large leading-edge vortex has already separated and sits beside the foil. It is shed well before the stroke ends and leaves as a strong counter-rotating pair travelling downstream at about ±1.7c, with a trail of small trailing-edge vortices behind it. The lift therefore peaks early in each stroke (timing about −22°), which is one reason why the large forces extract little power.`));
  add(P(`The vortices fade quickly beyond x ≈ 3c because the cells grow away from the foil (growth ratio 1.07). The picture of the far wake is therefore smoothed; the effect of the outer mesh on the forces is covered by the domain and mesh studies of Chapter 5.`));
  const CAP = { I: "Case I (f* = 0.14, θ_{0} = 76.33°)", II: "Case II (f* = 0.18, θ_{0} = 60°)", III: "Case III (f* = 0.06, θ_{0} = 60°)" };
  ANIMS.forEach((c) => add(...figure(`anim_${c}.png`, `${CAP[c]}: vorticity ωc/U at t/T = 0, 0.25, 0.5 and 0.75 of the last cycle (medium mesh, 80c)`)));
}
add(H2(ANIMS.length ? "6.6 Comparison with WaterLily" : "6.5 Comparison with WaterLily"));
add(P(`In our final-year project WaterLily gave 15.2 % for Case II, 33 % above the paper, at every resolution tried. OpenFOAM reproduces the paper's value, so the gap is in the WaterLily result, not in the case definition. Figure ${FN("fig10_caseII_cycle.png")} shows where: drag and power agree closely through most of the cycle, but near each stroke reversal (t/T ≈ 0.4 and 0.9) WaterLily misses a lift and moment bump that both OpenFOAM meshes resolve, so its power there is about −0.25 instead of −0.65. That phase is where Case II loses its power, so a small error in it changes the efficiency strongly.`));

// ============================================================ 7 Limitations
add(H1("7. Limitations"));
add(bullet("**Mesh convergence.** The mesh study is not in the asymptotic range, so no grid convergence index could be formed; the mesh uncertainty (±0.5 points) is taken from the change between the two finest meshes, and the extra-fine mesh could not be run."));
add(bullet("**Pivot moment.** The Case I peak pivot moment is 14 to 17 % below the paper; the non-orthogonal limiter and the domain size both lower it."));
add(bullet("**Domain correction.** The 1/R correction was measured for Case I only; Cases II and III are reported at 80c without correction."));
add(bullet("**Motion table.** The prescribed motion is a table of 400 points per cycle, which gives a small saw-tooth in the forces; time averages are exact with the bin-averaged post-processing, but a finer table would remove it."));
add(bullet("**Physics.** The flow is two-dimensional and laminar, as in the paper; three-dimensional effects and transition at higher Reynolds numbers are outside the scope."));
add(bullet("**Differences from the reference.** Our mesh is about half the size of the paper's 72,000 cells on the medium level and similar on the fine level, uses a different layout (O-grid with a blunt-trailing-edge block) and no sliding interface; the paper's far-field distance is unknown, so part of any remaining difference may come from the domain."));

// ============================================================ 8 Conclusions
add(H1("8. Conclusions"));
add(H2("8.1 Main Findings"));
add(bullet(`**The reproduction succeeds.** OpenFOAM on a rigidly moving O-grid reproduces the efficiency of all three Kinsey and Dumas cases to within 0.5 points: ${f2(cI.f.eta_percent)} % (33.7 %), ${f2(c2.f.eta_percent)} % (11.4 %) and ${f2(c3.f.eta_percent)} % (12.3 %) on the fine mesh, and the trend across the cases. Mean drag and peak lift agree within 1 to 4 %.`));
add(bullet(`**The far field dominates the error.** The Case I efficiency falls as ${EINF.toFixed(2)} + ${KSL.toFixed(1)}/R; a 20c domain over-predicts it by 1.7 points (5 %), more than three times the mesh effect.`));
add(bullet("**The paper's time step is converged** (T/2000 to T/8000 within 0.02 points) and is close to the stability limit of the scheme."));
add(bullet("**The trend follows the effective angle of attack.** Case I combines a large effective angle with a fast heave; Case II forms no leading-edge vortex and loses power in pitch; Case III stalls early and heaves too slowly."));
add(bullet("**WaterLily's Case II over-prediction is a WaterLily issue** near stroke reversal, not a property of the case."));
add(H2("8.2 Lessons Learned"));
add(bullet("A two-dimensional lifting foil needs its domain checked as carefully as its mesh."));
add(bullet("Mesh layout matters more than cell count: strongly sheared cells behind a blunt trailing edge destabilised the fine meshes even though checkMesh passed."));
add(bullet("For a single moving body, a rigid moving mesh is exact and about 300 to 1000 times cheaper than overset on the same hardware."));
add(bullet("Post-processing deserves the same scrutiny as the solver: sampling the forces in step with the motion table biased every efficiency by up to 0.3 points."));
add(H2("8.3 Future Work"));
add(numbered("Redesign the mesh behind the blunt trailing edge (for example a C-type wake block, or a sharp trailing edge) so that meshes finer than 65,000 cells run without a limiter and a grid convergence index can be formed.", "nums2"));
add(numbered("Use 4000 points per cycle in the motion table.", "nums2"));
add(numbered("Repeat WaterLily Case II at 96 to 128 cells per chord and compare the stroke-reversal phase with these results.", "nums2"));
add(numbered("Apply the validated set-up to the final-year project configuration, a foil in the wake of a fixed cylinder, with the overset mesh of Section 4.1.", "nums2"));

// ============================================================ 9 References
add(H1("9. References"));
const REFS = [
  "T. Kinsey and G. Dumas, \"Parametric study of an oscillating airfoil in a power-extraction regime,\" ~~AIAA Journal~~, vol. 46, no. 6, pp. 1318–1330, 2008, doi: 10.2514/1.26253.",
  "I. B. Celik, U. Ghia, P. J. Roache, C. J. Freitas, H. Coleman and P. E. Raad, \"Procedure for estimation and reporting of uncertainty due to discretization in CFD applications,\" ~~Journal of Fluids Engineering~~, vol. 130, no. 7, 078001, 2008.",
  "H. G. Weller, G. Tabor, H. Jasak and C. Fureby, \"A tensorial approach to computational continuum mechanics using object-oriented techniques,\" ~~Computers in Physics~~, vol. 12, no. 6, pp. 620–631, 1998.",
  "R. I. Issa, \"Solution of the implicitly discretised fluid flow equations by operator-splitting,\" ~~Journal of Computational Physics~~, vol. 62, no. 1, pp. 40–65, 1986.",
  "C. Geuzaine and J.-F. Remacle, \"Gmsh: a 3-D finite element mesh generator with built-in pre- and post-processing facilities,\" ~~International Journal for Numerical Methods in Engineering~~, vol. 79, no. 11, pp. 1309–1331, 2009.",
  "Q. Xiao and Q. Zhu, \"A review on flow energy harvesters based on flapping foils,\" ~~Journal of Fluids and Structures~~, vol. 46, pp. 174–191, 2014.",
  "J. Young, J. C. S. Lai and M. F. Platzer, \"A review of progress and challenges in flapping foil power generation,\" ~~Progress in Aerospace Sciences~~, vol. 67, pp. 2–28, 2014.",
  "G. D. Weymouth and B. Font, \"WaterLily.jl: a differentiable and backend-agnostic Julia solver to simulate incompressible viscous flow and dynamic bodies,\" arXiv:2407.16032, 2024.",
  "OpenCFD Ltd, ~~OpenFOAM v2412 User Guide~~, 2024. Available: https://www.openfoam.com",
  "J. H. Ferziger, M. Perić and R. L. Street, ~~Computational Methods for Fluid Dynamics~~, 4th ed. Cham: Springer, 2020.",
  "P. J. Roache, \"Quantification of uncertainty in computational fluid dynamics,\" ~~Annual Review of Fluid Mechanics~~, vol. 29, pp. 123–160, 1997.",
  "C. W. Hirt, A. A. Amsden and J. L. Cook, \"An arbitrary Lagrangian-Eulerian computing method for all flow speeds,\" ~~Journal of Computational Physics~~, vol. 14, no. 3, pp. 227–253, 1974.",
  "J. A. Benek, P. G. Buning and J. L. Steger, \"A 3-D Chimera grid embedding technique,\" AIAA Paper 85-1523, 1985.",
];
REFS.forEach((r, i) => add(new Paragraph({ alignment: AlignmentType.LEFT, spacing: { after: 80, line: 276 }, indent: { left: 540, hanging: 540 },
  tabStops: [{ type: TabStopType.LEFT, position: 540 }], children: [new TextRun({ text: `[${i + 1}]\t`, font: FONT }), ...runs(r)] })));

// ============================================================ Appendices
add(H1("Appendix A: Run Matrix"));
add(P(`Every run of Chapters 5 and 6. Averages use the settled cycles listed; "diverged" runs stopped within the first cycle. Runner time is the wall-clock time per cycle on four cores.`));
const statusTxt = (r) => (r.status === "diverged" ? "diverged" : r.status === "finished" ? "" : "time limit");
add(table("runs", "All runs", ["Run", "Description", "Cells", "R", "Steps / T", "η", "Cycles avg.", "min / cycle"],
  RUNS.map((r) => [r.run.replace(/_/g, " "), r.description + (statusTxt(r) && !r.description.includes("diverged") ? ` (${statusTxt(r)})` : ""), r.cells ? r.cells.toLocaleString("en-US") : "", r.far_field_c ? `${r.far_field_c}c` : "",
                   r.steps_per_cycle || "", r.eta_percent != null ? f2(r.eta_percent) + " %" : "–", r.averaged_cycles || "", r.min_per_cycle ? Number(r.min_per_cycle).toFixed(1) : ""]),
  [1.25, 2.6, 0.8, 0.5, 0.7, 0.75, 0.75, 0.75], { size: 16, align: [AlignmentType.LEFT, AlignmentType.LEFT, AlignmentType.CENTER, AlignmentType.CENTER, AlignmentType.CENTER, AlignmentType.CENTER, AlignmentType.CENTER, AlignmentType.CENTER] }));

add(H1("Appendix B: Reproducing the Results"));
add(P(`All scripts and workflows are in the public repository github.com/zain4366/Cfd_project-. On a Linux machine with OpenFOAM v2412 and the gmsh Python package, one run is:`));
const code = (s) => new Paragraph({ spacing: { after: 0, line: 240 }, keepNext: true, keepLines: true, children: [new TextRun({ text: s, font: "Consolas", size: 16 })] });
["# install OpenFOAM v2412, gmsh, numpy and matplotlib",
 "bash scripts/install.sh",
 "# choose the case: I, II or III",
 "export KD_CASE=I",
 "# mesh level, case folder, output folder, far-field radius in chords",
 "bash scripts/build_rigid.sh fine run/rigid out/fine 80",
 "# 14 cycles at T/2000 with the limited non-orthogonal correction",
 "LAPL=\"limited corrected 0.33\" bash scripts/setup_rigid.sh run/rigid 14 2000",
 "# run on 4 MPI ranks with a time limit in minutes, then post-process",
 "bash scripts/run_solver.sh run/rigid out/fine 320 local",
 "bash scripts/finish_run.sh run/rigid out/fine"].forEach((l) => add(code(l)));
add(P("", { para: { spacing: { after: 120 } } }));
add(P(`On GitHub, each study is a workflow in .github/workflows (phase3-4.yml, phase4b to phase4e.yml, phase5.yml, animations.yml); pushing a change to the workflow file starts it, and the results appear on the ci-results branch. scripts/compare_runs.py and scripts/compare_cases.py rebuild the tables and figures of Chapters 5 and 6 from the published runs.`));

add(H1("Appendix C: Correction to the Cycle Averaging"));
add(P(`The heave and pitch are given to OpenFOAM as a table of 400 points per cycle, interpolated linearly. The mesh velocity is therefore piecewise constant and changes by a small step every 5 time steps (10 at T/4000). The forces respond with a saw-tooth: the sample at each table point is a few per cent away from its neighbours. The first post-processing resampled each cycle at 200 phases that coincided with table points, so it read the saw-tooth at the same point every time and biased the cycle means.`));
add(P(`The corrected method averages every sample into 200 phase bins (scripts/cycle_stats.py), which makes cycle means exact time averages. All runs were reprocessed from their saved force histories; no simulation had to be repeated. The change is −0.08 to −0.13 points for Case I, −0.30 to −0.34 points for Case II and −0.01 points for Case III, and it does not change any conclusion of the verification studies.`));
add(table("corr", "Effect of the correction on the final efficiencies", ["Run", "first post-processing", "corrected"], [
  ["Case I medium / fine", "33.38 % / 33.77 %", `${f2(cI.m.eta_percent)} % / ${f2(cI.f.eta_percent)} %`],
  ["Case II medium / fine", "11.54 % / 11.23 %", `${f2(c2.m.eta_percent)} % / ${f2(c2.f.eta_percent)} %`],
  ["Case III medium / fine", "12.21 % / 12.39 %", `${f2(c3.m.eta_percent)} % / ${f2(c3.f.eta_percent)} %`],
  ["Phase 3 baseline (20c)", "34.75 %", `${f2(R.base.eta_percent)} %`]], [2, 2, 2]));

add(H1("Appendix D: Submitted Files"));
add(P(`The files required by the course guidelines are in the accompanying data package (AE471_data) and the project repository:`));
add(table("files", "Submitted files and where to find them", ["Required item", "Location"], [
  ["Geometry and computational domain", "scripts/make_mesh_inputs.py and scripts/params.py (NACA 0015 coordinates, O-grid and far field are generated from these)"],
  ["Mesh files", "regenerated exactly by scripts/build_rigid.sh (gmsh); checkMesh logs and mesh_info.json in every run folder of AE471_data"],
  ["Case files", "controlDict, fvSchemes, fvSolution and dynamicMeshDict in every run folder; case_rigid/ in the repository"],
  ["Scripts", "12_scripts_snapshot/ (meshing, set-up, post-processing, figures, animations)"],
  ["Reference data", "11_reference_data/ (Kinsey and Dumas Table 2 values; WaterLily cycles); full citation in reference [1]"],
  ["CFD and reference comparison", "01_summary_tables/cases_comparison.csv and all_runs_summary.csv"],
  ["Force histories", "coefficients_time_history.csv and per_cycle.csv in every run folder"],
  ["Animations", "10_animations/ (GIF and MP4 of the three cases, stills and the vorticity fields of the last cycle)"],
  ["AI-use disclosure", "Appendix E"]], [1.6, 4], { align: [AlignmentType.LEFT, AlignmentType.LEFT] }));

add(H1("Appendix E: AI-Use Disclosure"));
add(P(`AI tools were used in this project. Claude (Anthropic) was used to write and debug the meshing, run-control and post-processing scripts and the GitHub Actions workflows, to run and monitor the studies, to analyse the results, to prepare the figures and animations and to draft this report. All results in this report come from simulations run by these workflows, and every number can be traced to the run logs on the repository's ci-results branch; no result was generated by an AI tool without a simulation behind it. The group members have checked the methods, results, equations and references and are responsible for the content.`));

// ============================================================ title page
const title = [];
const tl = (kids, o = {}) => new Paragraph({ alignment: o.align || AlignmentType.CENTER, spacing: { before: o.before || 0, after: o.after ?? 120, line: o.line || 276, lineRule: D.LineRuleType.AUTO }, indent: o.indent, tabStops: o.tabs, children: kids });
const tr = (s, o = {}) => new TextRun({ text: s, font: FONT, size: o.size || 24, bold: o.bold, italics: o.italics, color: o.color, underline: o.underline ? {} : undefined, superScript: o.sup });
const [lw, lh] = [299, 300];
title.push(tl([new ImageRun({ type: "png", data: fs.readFileSync(path.join(IMG, "nust_logo.png")), transformation: { width: 170, height: Math.round(170 * lh / lw) },
                              altText: { title: "NUST logo", description: "NUST logo", name: "nust" } })], { before: 360, after: 240 }));
title.push(tl([tr("School of Mechanical & Manufacturing Engineering (SMME),", { size: 28, bold: true, italics: true, color: BLUE })], { after: 120, line: 360 }));
title.push(tl([tr("National University of Sciences & Technology (NUST)", { size: 28, bold: true, italics: true, color: BLUE })], { after: 480, line: 360 }));
title.push(tl([tr("Computational Fluid Dynamics (AE-471)", { size: 36, bold: true, underline: true })], { after: 240 }));
title.push(tl([tr("Course Project Report", { size: 30, bold: true, underline: true })], { after: 300 }));
title.push(tl([tr("Oscillating-Foil Power Extraction: OpenFOAM", { size: 30, bold: true, color: BLUE })], { after: 0 }));
title.push(tl([tr("Reproduction of Kinsey and Dumas (2008)", { size: 30, bold: true, color: BLUE })], { after: 600 }));
const infoTabs = [{ type: TabStopType.LEFT, position: 5040 }];
title.push(tl([tr("Program: ", { bold: true }), tr("BE-Aerospace"), tr("\t"), tr("Semester: ", { bold: true }), tr("7"), tr("th", { sup: true })], { align: AlignmentType.LEFT, indent: { left: 360 }, tabs: infoTabs, after: 120 }));
title.push(tl([tr("Session: ", { bold: true }), tr("Fall 2026"), tr("\t"), tr("Course Code: ", { bold: true }), tr("AE-471")], { align: AlignmentType.LEFT, indent: { left: 360 }, tabs: infoTabs, after: 120 }));
title.push(tl([tr("Project: ", { bold: true }), tr("Pathway B, Research Paper Reproduction (NACA 0015, Re = 1100)")], { align: AlignmentType.LEFT, indent: { left: 360 }, after: 360 }));
const mb = { style: BorderStyle.SINGLE, size: 4, color: "9CC2E5" };
const mcell = (s, w, head, align) => new TableCell({
  borders: { top: mb, bottom: mb, left: mb, right: mb }, width: { size: w, type: WidthType.DXA }, verticalAlign: VerticalAlign.CENTER,
  shading: { fill: head ? "5B9BD5" : "DEEAF6", type: ShadingType.CLEAR, color: "auto" }, margins: { top: 100, bottom: 100, left: 120, right: 120 },
  children: [new Paragraph({ alignment: align, spacing: { after: 0 }, children: [tr(s, { bold: true, color: head ? "FFFFFF" : undefined })] })] });
const MW = [3200, 2200];
title.push(new Table({ width: { size: MW[0] + MW[1], type: WidthType.DXA }, columnWidths: MW, alignment: AlignmentType.CENTER, rows: [
  new TableRow({ children: [mcell("Members Name", MW[0], true, AlignmentType.CENTER), mcell("CMS ID", MW[1], true, AlignmentType.CENTER)] }),
  new TableRow({ children: [mcell("Zain ul Abiden", MW[0], false, AlignmentType.LEFT), mcell("466576", MW[1], false, AlignmentType.CENTER)] }),
  new TableRow({ children: [mcell("Ahmed Mukhtar Bukhari", MW[0], false, AlignmentType.LEFT), mcell("461298", MW[1], false, AlignmentType.CENTER)] }),
] }));
title.push(tl([tr("Submission Date: ", { bold: true }), tr("November 27, 2026")], { align: AlignmentType.LEFT, before: 480 }));

// ============================================================ header, footer, document
const header = () => new Header({ children: [new Paragraph({
  tabStops: [{ type: TabStopType.CENTER, position: Math.round(TEXTW / 2) }], spacing: { after: 120 },
  children: [new ImageRun({ type: "png", data: fs.readFileSync(path.join(IMG, "smme_logo.png")), transformation: { width: 50, height: 35 },
                            altText: { title: "SMME logo", description: "SMME logo", name: "smme" } }),
             new TextRun({ text: "\tDepartment of Aerospace Engineering", font: "Times New Roman", size: 28, color: "808080" })] })] });
const footer = (num) => new Footer({ children: [new Paragraph({
  alignment: AlignmentType.RIGHT, border: { top: { style: BorderStyle.SINGLE, size: 6, color: LINE, space: 6 } }, spacing: { before: 0 },
  children: num ? [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 20 })] : [new TextRun({ text: "", font: FONT, size: 20 })] })] });
const page = { size: { width: 12240, height: 15840 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440, header: 600, footer: 700 } };
const doc = new Document({
  creator: "Zain ul Abiden, Ahmed Mukhtar Bukhari",
  title: "AE-471 Course Project Report: OpenFOAM Reproduction of Kinsey and Dumas (2008)",
  description: "AE-471 CFD course project report",
  features: { updateFields: true },
  styles: {
    default: { document: { run: { font: FONT, size: 24 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 28, bold: true, color: BLUE }, paragraph: { alignment: AlignmentType.CENTER, spacing: { before: 360, after: 240 }, keepNext: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 24, bold: true, color: "000000" }, paragraph: { spacing: { before: 240, after: 80 }, keepNext: true, outlineLevel: 1 } },
      { id: "FrontHead", name: "Front Heading", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 28, bold: true, color: BLUE }, paragraph: { alignment: AlignmentType.CENTER, spacing: { before: 120, after: 360 }, keepNext: true } },
      { id: "Caption", name: "Caption", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 20, bold: true, italics: true, color: CAPCOL }, paragraph: { alignment: AlignmentType.CENTER } },
      { id: "TOC1", name: "toc 1", basedOn: "Normal", next: "Normal", run: { font: FONT, size: 22, bold: true }, paragraph: { spacing: { before: 120, after: 40 } } },
      { id: "TOC2", name: "toc 2", basedOn: "Normal", next: "Normal", run: { font: FONT, size: 21 }, paragraph: { indent: { left: 360 }, spacing: { after: 20 } } },
      { id: "TableofFigures", name: "table of figures", basedOn: "Normal", next: "Normal", run: { font: FONT, size: 21 }, paragraph: { spacing: { after: 60 } } },
    ],
  },
  numbering: { config: [
    { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 300 } } } }] },
    { reference: "nums", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 360 } } } }] },
    { reference: "nums2", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 360 } } } }] },
  ] },
  sections: [
    { properties: { page }, headers: { default: header() }, footers: { default: footer(false) }, children: title },
    { properties: { page: { ...page, pageNumbers: { start: 1, formatType: NumberFormat.LOWER_ROMAN } } }, headers: { default: header() }, footers: { default: footer(true) }, children: front },
    { properties: { page: { ...page, pageNumbers: { start: 1, formatType: NumberFormat.DECIMAL } } }, headers: { default: header() }, footers: { default: footer(true) }, children: C },
  ],
});
fs.writeFileSync(path.join(DIR, "toc.json"), JSON.stringify(TOCL, null, 1));
Packer.toBuffer(doc).then((b) => { fs.writeFileSync(path.join(DIR, OUTNAME), b); console.log(OUTNAME, b.length); });
