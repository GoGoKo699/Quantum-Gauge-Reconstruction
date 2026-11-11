#!/usr/bin/env node
'use strict';
// Representative read-only diagnostic, not release-readiness evidence.
// Importing this module neither starts a browser nor visits a site.
const fs = require('node:fs');
const path = require('node:path');
const cp = require('node:child_process');
const crypto = require('node:crypto');
const collector = require('./capture_hosted_math.cjs');
const sha256 = bytes => crypto.createHash('sha256').update(bytes).digest('hex');

function argumentsFor(argv) {
  if (argv.includes('--resume-from')) throw new Error('A diagnostic does not resume captures; use the full collector for that operation');
  const args = collector.argumentsFor(argv);
  if (args.help) return args;
  if (args.pages.length !== 1) throw new Error('Choose exactly one representative --page for the early diagnostic');
  return args;
}

function sourceAdvisories(source, page) {
  const warnings = [];
  let fence = null;
  for (const [index, line] of source.split(/\r?\n/).entries()) {
    const mark = line.match(/^\s{0,3}(`{3,}|~{3,})/);
    if (mark) {
      if (!fence) fence = mark[1];
      else if (mark[1][0] === fence[0] && mark[1].length >= fence.length) fence = null;
      continue;
    }
    if (fence) continue;
    const inline = [...line.matchAll(/(?<!\\)\$(?!\$)([^$\n]+?)(?<!\\)\$/g)];
    for (const match of inline) {
      const tex = match[1];
      const add = (code, message) => warnings.push({code, path:page, line:index+1, message});
      if (tex.includes('<')) add('raw_inline_less_than', 'Inspect raw < in inline mathematics on GitHub; use an appropriate TeX relation if the host truncates it.');
      if (/_[A-Za-z0-9]+_/.test(tex)) add('repeated_unbraced_subscript', 'Inspect a possible repeated unbraced subscript; braces may be needed to express the intended indices.');
      if (/^\s*\|/.test(line) && /(?<!\\)\|/.test(tex)) add('table_math_pipe', 'Inspect an unescaped pipe inside table mathematics; Markdown may split the expression into cells.');
    }
  }
  return warnings;
}

function categoryFor(failures) {
  const messages = failures.map(String);
  // Denials take precedence over secondary incomplete-coverage messages.
  for (const category of ['policy_denied', 'access_required', 'capability_unavailable', 'transport_failure']) {
    if (messages.some(message => message.includes(category) || collector.classifyFailure(message) === category)) return category;
  }
  return messages.length ? 'verification_failure' : null;
}

function dependencies(args, services = {}) {
  const execute = services.execFileSync || cp.execFileSync;
  const resolve = services.resolve || require.resolve;
  const result = {node:process.version};
  if (Number(process.versions.node.split('.')[0]) < 18) throw new Error('capability_unavailable: Node.js 18 or later is required');
  for (const [key, command, flags] of [['git','git',['--version']], ['python',args.python,['--version']]]) {
    try {
      result[key] = String(execute(command, flags, {encoding:'utf8',stdio:'pipe'})).trim();
    } catch (error) {
      throw new Error('capability_unavailable: Cannot execute '+key+': '+String(error));
    }
  }
  const pythonVersion = result.python.match(/Python\s+(\d+)\.(\d+)/);
  if (!pythonVersion || Number(pythonVersion[1]) < 3 || (Number(pythonVersion[1]) === 3 && Number(pythonVersion[2]) < 10))
    throw new Error('capability_unavailable: Python 3.10 or later is required; observed '+result.python);
  for (const name of ['playwright','mathjax-full']) {
    try { result[name] = resolve(name+'/package.json'); }
    catch (error) { throw new Error('capability_unavailable: Cannot find module '+name+': '+String(error)); }
  }
  return result;
}

function emptyOutput(directory) {
  const resolved = path.resolve(directory);
  if (fs.existsSync(resolved)) {
    if (fs.lstatSync(resolved).isSymbolicLink() || !fs.statSync(resolved).isDirectory()) throw new Error('Output must be a regular directory');
    if (fs.readdirSync(resolved).length) throw new Error('Use an empty output directory; preserve earlier diagnostic evidence');
  }
  return resolved;
}

async function run(args, services = {}) {
  if (args.pages?.length !== 1 || args['resume-from'] || args.resumeFrom) throw new Error('Diagnostic requires exactly one page and no resumed evidence');
  const output = emptyOutput(args.output);
  const at = (services.now || (() => new Date().toISOString()))();
  const execute = services.execFileSync || cp.execFileSync;
  const inspectPinned = services.pinnedPages || collector.pinnedPages;
  const capture = services.capture || collector.run;
  const failures = [];
  let pinned, runtime = {}, sourceHash = null, advisories = [], captureReport = null, captureExit = null;
  try {
    runtime = dependencies(args, services);
    pinned = inspectPinned(args);
    if (pinned.pages.length !== 1 || pinned.pages[0] !== args.pages[0]) throw new Error('Pinned diagnostic scope differs from the requested page');
    const source = execute('git', ['--no-replace-objects','show',args.revision+':'+args.pages[0]], {cwd:args.root,encoding:'utf8',maxBuffer:32*1024*1024});
    sourceHash = sha256(source);
    advisories = sourceAdvisories(String(source), args.pages[0]);
    const log = console.log;
    // The diagnostic emits one summary of its own; raw collector records remain on disk.
    try { console.log = () => {}; captureExit = await capture({...args,output,diagnosticOnly:true}); }
    finally { console.log = log; }
    const filename = path.join(output,'hosted-report.json');
    if (!fs.existsSync(filename)) throw new Error('Collector did not produce its report');
    const bytes = fs.readFileSync(filename);
    captureReport = JSON.parse(bytes);
    if (captureReport.repository !== args.repository || captureReport.revision !== args.revision ||
        captureReport.tree !== pinned.tree || JSON.stringify(captureReport.required_pages) !== JSON.stringify(args.pages))
      throw new Error('Collector diagnostic report identity/scope mismatch');
    if (captureReport.diagnostic_only !== true) throw new Error('Collector did not mark its representative capture as diagnostic-only; use the matching current helper bundle');
    failures.push(...(captureReport.failures || []));
    if (captureExit !== 0 || captureReport.status !== 'pass') {
      if (!failures.length) failures.push('Representative hosted comparison did not pass');
    }
  } catch (error) { failures.push(String(error)); }
  fs.mkdirSync(output,{recursive:true});
  const category = categoryFor(failures);
  const filename = path.join(output,'hosted-report.json');
  const report = {
    schema_version:1,kind:'hosted_probe',repository:args.repository,revision:args.revision,
    tree:pinned?.tree || null,page:args.pages[0],source_sha256:sourceHash,
    observed_at:at,status:failures.length?'fail':'pass',failure_category:category,failures,
    runtime,advisories,diagnostic_only:true,release_ready:false,release_evidence:false,
    capture_report:fs.existsSync(filename)?{path:'hosted-report.json',sha256:sha256(fs.readFileSync(filename))}:null,
    limits:'One representative page at the collector\'s two viewports only. This early diagnostic is not full repository review, visual approval, scientific validation, or release-readiness evidence. Source advisories are heuristic and do not prove a rendering defect.',
    next_action:!failures.length ? 'Continue furnishing; perform the complete final source-bound hosted and visual review later.' :
      category === 'policy_denied' ? 'Record the denial and continue unaffected work; retry only after applicable access evidence changes, without routing around the denial.' :
      category === 'access_required' ? 'Identify the actual missing access requirement and resolve it through an authorized flow; preserve the named grant and continue unaffected work.' :
      category === 'capability_unavailable' ? 'Use or provision a permitted compatible runtime within the actual grant, then repeat the diagnostic; no access-setting change is implied.' :
      category === 'transport_failure' ? 'Preserve this failed attempt and retry the same authorized operation after the transient transport condition changes.' :
      'Inspect the pinned source and captured representative page, repair demonstrated defects within scope, and repeat the diagnostic.'
  };
  fs.writeFileSync(path.join(output,'probe-report.json'),JSON.stringify(report,null,2)+'\n');
  return {code:report.status==='pass'?0:1,report};
}

module.exports = {argumentsFor,sourceAdvisories,categoryFor,dependencies,emptyOutput,run};
if (require.main === module) {
  (async () => {
    const args = argumentsFor(process.argv.slice(2));
    if (args.help) { console.log('probe_hosted_math.cjs --root REPO --repository owner/name --revision FULLSHA --page REPRESENTATIVE.md --output EMPTY_DIR [--contract JSON] [--python python3]'); return; }
    const result = await run(args);
    console.log(JSON.stringify({status:result.report.status,category:result.report.failure_category,report:path.join(path.resolve(args.output),'probe-report.json'),release_ready:false}));
    process.exitCode = result.code;
  })().catch(error => {console.error(String(error));process.exitCode=2;});
}

