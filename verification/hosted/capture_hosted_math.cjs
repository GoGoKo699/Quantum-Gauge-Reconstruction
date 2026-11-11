#!/usr/bin/env node
'use strict';
// Read-only collector for the real GitHub host. See ../references/hosted-rendering.md.
// Importing this module has no network effects; dependencies load only in run().
const fs = require('node:fs');
const path = require('node:path');
const cp = require('node:child_process');
const crypto = require('node:crypto');
const VIEWPORTS = [{width:1440,height:1000}, {width:760,height:1000}];
const sha256 = bytes => crypto.createHash('sha256').update(bytes).digest('hex');

function argumentsFor(argv) {
  const args = {pages:[], python:'python3'};
  for (let i=0; i<argv.length; i++) {
    const key=argv[i];
    if (key==='--help') return {help:true};
    if (!['--root','--repository','--revision','--output','--page','--contract','--python','--resume-from'].includes(key) || !argv[i+1])
      throw new Error('Unknown option or missing value: '+key);
    const value=argv[++i];
    if (key==='--page') args.pages.push(value);
    else {
      const name=key==='--resume-from'?'resumeFrom':key.slice(2);
      if (Object.hasOwn(args,name) && name!=='python') throw new Error('Duplicate option: '+key);
      args[name]=value;
    }
  }
  for (const key of ['root','repository','revision','output']) if (!args[key]) throw new Error('Missing --'+key);
  if (!/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(args.repository) ||
      args.repository.split('/').some(p=>['.','..'].includes(p))) throw new Error('Use exact owner/name');
  if (!/^[a-f0-9]{40}$/.test(args.revision)) throw new Error('Use a full lowercase commit SHA');
  if (new Set(args.pages).size!==args.pages.length || args.pages.some(p=>!safePath(p))) throw new Error('Use unique safe page paths');
  return args;
}
function safePath(p) {
  return typeof p==='string' && p.length>0 && !p.includes('\\') && !p.includes('\0') &&
    !p.startsWith('/') && p.split('/').every(x=>x && x!=='.' && x!=='..');
}
function git(root, argv) {
  return cp.execFileSync('git',['--no-replace-objects',...argv],{cwd:root,encoding:'utf8',maxBuffer:32*1024*1024});
}
function pinnedPages(args) {
  const commit=git(args.root,['rev-parse',args.revision+'^{commit}']).trim();
  if (commit!==args.revision) throw new Error('Revision does not identify the supplied commit');
  const files=git(args.root,['ls-tree','-r','--name-only','-z',commit]).split('\0').filter(Boolean);
  const pages=args.pages.length?args.pages:files.filter(p=>/\.(md|markdown|mdown|mkdn|mkd)$/i.test(p));
  if (!pages.length || pages.some(p=>!safePath(p) || !files.includes(p))) throw new Error('No pages or a page is absent from the pinned tree');
  // Git symlinks are not rendered Markdown source and must not be followed.
  for (const p of pages) {
    const item=git(args.root,['ls-tree',commit,'--',p]);
    if (!/^100644 blob |^100755 blob /.test(item)) throw new Error('Page must be a regular tracked file: '+p);
  }
  return {pages,tree:git(args.root,['rev-parse',commit+'^{tree}']).trim()};
}
function mathCompiler() {
  const {mathjax}=require('mathjax-full/js/mathjax.js');
  const {TeX}=require('mathjax-full/js/input/tex.js');
  const {SVG}=require('mathjax-full/js/output/svg.js');
  const {liteAdaptor}=require('mathjax-full/js/adaptors/liteAdaptor.js');
  const {RegisterHTMLHandler}=require('mathjax-full/js/handlers/html.js');
  const {AllPackages}=require('mathjax-full/js/input/tex/AllPackages.js');
  const {SerializedMmlVisitor}=require('mathjax-full/js/core/MmlTree/SerializedMmlVisitor.js');
  const {STATE}=require('mathjax-full/js/core/MathItem.js');
  RegisterHTMLHandler(liteAdaptor());
  const doc=mathjax.document('',{InputJax:new TeX({packages:AllPackages,tags:'none'}),OutputJax:new SVG({fontCache:'none'})});
  const visitor=new SerializedMmlVisitor();
  return (tex,display)=>visitor.visitTree(doc.convert(tex,{display,end:STATE.CONVERT}));
}

// Self-contained function executed inside the hosted page, also exercised by the
// local-browser regression fixture. It never injects styling or renders TeX there.
function inspectArticle(root, expected) {
  function canonical(e, inherited='') {
    const tag=e.localName;
    if (['annotation','annotation-xml','mspace'].includes(tag)) return [];
    const variant=e.getAttribute('mathvariant') || inherited;
    if (['mi','mo','mn','mtext','ms'].includes(tag)) {
      const text=e.textContent.trim();
      return text?[[tag,text,variant]]:[];
    }
    // Preserve each structural child slot: flattening numerator and denominator
    // together would confuse (a+b)/c with a/(b+c), and similarly for scripts.
    const children=[...e.children].filter(c=>!['annotation','annotation-xml','mspace'].includes(c.localName))
      .map(c=>canonical(c,variant));
    if (['math','mrow','mstyle','semantics'].includes(tag)) return children.flat();
    const semantic={};
    for (const name of ['notation','accent','accentunder','linethickness','bevelled','open','close','separators']) if(e.hasAttribute(name)) semantic[name]=e.getAttribute(name);
    // A table cell is an inferred row (a sequence), not a fixed-arity operator.
    // GitHub inserts empty mrow alignment nodes; ignore those inside the cell
    // while preserving the cell and row themselves, including empty cells.
    return [[tag,semantic,tag==='mtd'?children.flat():children]];
  }
  function plain(math) {
    const copy=math.cloneNode(true);
    for (const e of copy.querySelectorAll('annotation,annotation-xml')) e.remove();
    return copy.textContent;
  }
  function geometry(math, host) {
    const boxes=[...math.querySelectorAll('mi,mo,mn,mtext,ms')].map(e=>e.getBoundingClientRect()).filter(b=>b.width && b.height);
    if (!boxes.length) return {measurable:false};
    const left=Math.min(...boxes.map(b=>b.left)),right=Math.max(...boxes.map(b=>b.right));
    const top=Math.min(...boxes.map(b=>b.top)),bottom=Math.max(...boxes.map(b=>b.bottom));
    const width=right-left,height=bottom-top;
    return {measurable:true,width,height,available_width:root.clientWidth,
      overflow:width>root.clientWidth+4,collapsed:height>Math.max(200,3*width),host_width:host.getBoundingClientRect().width};
  }
  let hosts=[...root.querySelectorAll('math-renderer')];
  // Some host versions expose native MathML without a custom-element wrapper.
  if (!hosts.length) hosts=[...root.querySelectorAll('math')].filter(e=>!e.parentElement?.closest('math,annotation,annotation-xml'));
  const pageErrors=[...root.querySelectorAll('merror,[data-mjx-error],.katex-error,math-renderer .flash-error')]
    .map(e=>e.textContent.trim() || 'empty renderer error');
  const math=hosts.map((host,i)=>{
    const nodes=host.localName==='math'?[host]:[...host.querySelectorAll('math')].filter(e=>!e.parentElement?.closest('math,annotation,annotation-xml'));
    const errors=[];
    if(nodes.length!==1) errors.push('Expected one accessible MathML representation; found '+nodes.length);
    const actual=nodes[0],want=expected[i];
    let expectedSignature=null,actualSignature=null;
    if(actual) actualSignature=JSON.stringify(canonical(actual));
    if(want) {
      const parsed=new DOMParser().parseFromString(want.mml,'application/xml');
      if(parsed.querySelector('parsererror,merror')) errors.push('Source compiler returned invalid/error MathML');
      else expectedSignature=JSON.stringify(canonical(parsed.documentElement));
    }
    if(!want) errors.push('Unexpected extra hosted expression');
    const match=!!actual && !!expectedSignature && expectedSignature===actualSignature;
    if(!match) errors.push('Source-to-host MathML structure mismatch');
    const measure=actual?geometry(actual,host):{measurable:false};
    if(want && ['math-fence','dollar-display'].includes(want.kind) && (!measure.measurable || measure.overflow || measure.collapsed))
      errors.push('Display geometry is unmeasurable, overflowing or collapsed');
    return {rendered:!!actual,errors,text_source:'mathml',text:actual?plain(actual):'',
      source_sha256:want?.source_sha256,structural_match:match,
      expected_signature:expectedSignature,actual_signature:actualSignature,geometry:measure};
  });
  return {errors:pageErrors,math};
}

function classifyFailure(error) {
  const message=String(error);
  if (/ERR_BLOCKED_BY_ADMINISTRATOR|blocked by.*policy|URLBlocklist|policy denied/i.test(message)) return 'policy_denied';
  if (/HTTP (401|403)|redirected away|sign.in|authentication/i.test(message)) return 'access_required';
  if (/Cannot find module|Executable doesn't exist|browser executable/i.test(message)) return 'capability_unavailable';
  if (/HTTP (429|5[0-9]{2})|ERR_NAME_NOT_RESOLVED|ENOTFOUND|ERR_CONNECTION|ERR_EMPTY_RESPONSE|ERR_INTERNET_DISCONNECTED|ECONNRESET|Timeout|timed out/i.test(message)) return 'transport_failure';
  return 'verification_failure';
}
function writeJSON(filename, value) {fs.writeFileSync(filename,JSON.stringify(value,null,2)+'\n');}
function artifact(directory, relative, kind) {
  const bytes=fs.readFileSync(path.join(directory,relative));
  return {path:relative,sha256:sha256(bytes),size_bytes:bytes.length,kind};
}
function boundReport(inventory, tree, viewports, artifacts, failures, at) {
  const boundaries=inventory.pages.map(p=>{
    const counts=viewports.map(v=>v.boundaries?.find(b=>b.path===p.path)?.captured_hosts);
    return {path:p.path,url:p.url,revision:inventory.revision,source_sha256:p.source_sha256,
      source_expressions:p.expressions.length,
      captured_hosts:counts.length===VIEWPORTS.length && counts.every(n=>Number.isInteger(n) && n===counts[0])?counts[0]:null};
  });
  const wanted=inventory.pages.reduce((n,p)=>n+p.expressions.length,0);
  failures=[...failures];
  if(JSON.stringify(viewports.map(v=>({width:v.width,height:v.height})))!==JSON.stringify(VIEWPORTS))
    failures.push('Missing, duplicate or unexpected viewport coverage');
  for(const viewport of viewports) {
    if(JSON.stringify((viewport.boundaries||[]).map(b=>b.path))!==JSON.stringify(inventory.pages.map(p=>p.path)))
      failures.push(viewport.width+': page coverage differs from inventory');
    for(const source of inventory.pages) {
      const boundary=viewport.boundaries?.find(b=>b.path===source.path);
      if(!boundary || boundary.source_sha256!==source.source_sha256 || boundary.revision!==inventory.revision ||
         boundary.url!==source.url || boundary.source_expressions!==source.expressions.length || boundary.captured_hosts!==source.expressions.length)
        failures.push(viewport.width+': incomplete source/host coverage for '+source.path);
    }
  }
  const structural=viewports.length===VIEWPORTS.length && viewports.every(v=>v.structural_matches===wanted);
  const pass=!failures.length && structural && viewports.length===VIEWPORTS.length && viewports.every(v=>v.status==='pass');
  return {schema_version:1,kind:'hosted_math',repository:inventory.repository,revision:inventory.revision,tree,
    renderer_profile:'github',captured_at:at,capture_method:'playwright-github',status:pass?'pass':'fail',
    required_pages:inventory.pages.map(p=>p.path),boundaries,viewports,artifacts,failures,
    structural_comparison:{status:structural?'pass':'fail',expressions_checked:structural?wanted:0},
    visual_review_required:true,
    limits:'Observed GitHub MathML structure, counts, labels, relations and bounded geometry only. No independent scientific proof, exhaustive pixel review, host authenticity certificate or cross-browser guarantee.'};
}

// Resume is an explicit new attempt against identical source and execution inputs.
// Receipts bind observations, not authenticity: the final visual review is separate.
const RESUME_MAX_AGE_MS = 24*60*60*1000;
const MAX_EVIDENCE_BYTES = 32*1024*1024;
function safeEvidenceFile(directory, relative) {
  if(!safePath(relative)) throw new Error('Unsafe evidence path: '+relative);
  const root=path.resolve(directory);
  if(fs.lstatSync(root).isSymbolicLink() || !fs.statSync(root).isDirectory())
    throw new Error('Evidence root must be a regular directory');
  let current=root;
  for(const component of relative.split('/')) {
    current=path.join(current,component);
    if(fs.lstatSync(current).isSymbolicLink()) throw new Error('Symlink evidence is not reusable: '+relative);
  }
  const stat=fs.statSync(current);
  if(!stat.isFile() || stat.size>MAX_EVIDENCE_BYTES) throw new Error('Evidence must be a bounded regular file: '+relative);
  return current;
}
function readBoundArtifact(directory, descriptor) {
  if(!descriptor || typeof descriptor.path!=='string' || !/^[a-f0-9]{64}$/.test(descriptor.sha256) ||
      !Number.isInteger(descriptor.size_bytes) || descriptor.size_bytes<0)
    throw new Error('Malformed evidence artifact descriptor');
  const bytes=fs.readFileSync(safeEvidenceFile(directory,descriptor.path));
  if(bytes.length!==descriptor.size_bytes || sha256(bytes)!==descriptor.sha256)
    throw new Error('Evidence artifact hash/size mismatch: '+descriptor.path);
  return bytes;
}
function observationTime(value, now=Date.now()) {
  const parsed=typeof value==='string' && /(?:Z|[+-]\d{2}:\d{2})$/.test(value)?Date.parse(value):NaN;
  if(!Number.isFinite(parsed) || parsed>now || now-parsed>RESUME_MAX_AGE_MS)
    throw new Error('Capture observation is stale, future-dated or lacks a timezone');
  return parsed;
}
function pageKey(page, viewport) {return viewport.width+'x'+viewport.height+':'+page;}
function capturePassed(source, item) {
  return item && item.path===source.path && item.url===source.url &&
    item.revision===source.revision && item.source_sha256===source.source_sha256 &&
    Array.isArray(item.errors) && item.errors.length===0 && Array.isArray(item.math) &&
    item.math.length===source.expressions.length && item.math.every((m,index)=>
      m.rendered===true && Array.isArray(m.errors) && m.errors.length===0 && m.structural_match===true &&
      m.source_sha256===source.expressions[index].source_sha256 &&
      typeof m.expected_signature==='string' && m.expected_signature.length>0 &&
      m.expected_signature===m.actual_signature);
}
function sessionBinding(inventory, tree, expectedBytes, contractBytes, runtime, helper, diagnosticOnly=false, inventoryBytes=null) {
  return {repository:inventory.repository,revision:inventory.revision,tree,
    inventory_sha256:sha256(inventoryBytes || Buffer.from(JSON.stringify(inventory,null,2)+'\n')),
    expected_sha256:sha256(expectedBytes),contract_sha256:sha256(contractBytes),has_contract:contractBytes.toString('utf8')!=='null',
    collector_sha256:sha256(fs.readFileSync(__filename)),checker_sha256:sha256(fs.readFileSync(helper)),
    runtime,viewports:VIEWPORTS,purpose:diagnosticOnly?'diagnostic':'release_verification'};
}
function newSession(binding, at) {
  return {schema_version:1,kind:'hosted_math_session',binding,started_at:at,updated_at:at,
    completed:[],failures:[]};
}
function saveSession(output, session) {
  const temporary=path.join(output,'capture-state.json.tmp');
  writeJSON(temporary,session);fs.renameSync(temporary,path.join(output,'capture-state.json'));
}
function loadResume(directory, binding, inventory, now=Date.now()) {
  const bytes=fs.readFileSync(safeEvidenceFile(directory,'capture-state.json'));
  const session=JSON.parse(bytes.toString('utf8'));
  if(session.schema_version!==1 || session.kind!=='hosted_math_session' ||
      JSON.stringify(session.binding)!==JSON.stringify(binding))
    throw new Error('Resume source, scope, contract, collector/checker or runtime binding differs');
  if(!Array.isArray(session.failures) || session.failures.some(f=>f.category!=='transport_failure'))
    throw new Error('Resume refused after a nontransient, policy or access failure; preserve that attempt and resolve its actual cause');
  if(!Array.isArray(session.completed)) throw new Error('Malformed completed-capture receipts');
  const sourceByPath=new Map(inventory.pages.map(p=>[p.path,{...p,revision:inventory.revision}]));
  const reusable=new Map();
  for(const descriptor of session.completed) {
    const receiptBytes=readBoundArtifact(directory,descriptor.receipt);
    const receipt=JSON.parse(receiptBytes.toString('utf8'));
    const source=sourceByPath.get(receipt.path);
    const viewport=VIEWPORTS.find(v=>v.width===receipt.viewport?.width && v.height===receipt.viewport?.height);
    if(!source || !viewport || receipt.schema_version!==1 || receipt.kind!=='hosted_math_page' || receipt.status!=='pass' ||
        receipt.repository!==inventory.repository || receipt.revision!==inventory.revision ||
        receipt.tree!==binding.tree || receipt.source_sha256!==source.source_sha256 ||
        receipt.key!==pageKey(source.path,viewport) || !capturePassed(source,receipt.capture) ||
        receipt.capture.observed_at!==receipt.observed_at || !Array.isArray(receipt.artifacts))
      throw new Error('Invalid or mismatched passing page receipt');
    observationTime(receipt.observed_at,now);
    if(descriptor.key!==receipt.key || reusable.has(receipt.key)) throw new Error('Duplicate or mismatched page receipt key');
    const prefix=String(inventory.pages.findIndex(p=>p.path===source.path)+1).padStart(4,'0')+'-'+viewport.width;
    if(descriptor.receipt.path!==prefix+'-receipt.json') throw new Error('Unexpected page receipt artifact path');
    const expectedArtifacts=new Map([
      [prefix+'-source.json','page_source_inventory'],[prefix+'-capture.json','page_hosted_capture'],
      [prefix+'-result.json','page_math_result'],[prefix+'.html','hosted_html'],[prefix+'.png','screenshot']]);
    if(binding.has_contract) expectedArtifacts.set(prefix+'-contract.json','page_text_contract');
    const artifactPaths=new Set();
    const payloads=receipt.artifacts.map(a=>{
      if(artifactPaths.has(a.path) || expectedArtifacts.get(a.path)!==a.kind) throw new Error('Duplicate or unexpected receipt artifact path');
      artifactPaths.add(a.path);return {descriptor:a,bytes:readBoundArtifact(directory,a)};
    });
    if(artifactPaths.size!==expectedArtifacts.size) throw new Error('Incomplete page artifact set');
    const resultArtifact=payloads.find(a=>a.descriptor.kind==='page_math_result');
    const captureArtifact=payloads.find(a=>a.descriptor.kind==='page_hosted_capture');
    const sourceArtifact=payloads.find(a=>a.descriptor.kind==='page_source_inventory');
    const result=resultArtifact?JSON.parse(resultArtifact.bytes.toString('utf8')):null;
    const capture=captureArtifact?JSON.parse(captureArtifact.bytes.toString('utf8')):null;
    const sourceInventory=sourceArtifact?JSON.parse(sourceArtifact.bytes.toString('utf8')):null;
    if(result?.status!=='pass' || !Array.isArray(result.failures) || result.failures.length ||
        result.repository!==inventory.repository || result.revision!==inventory.revision ||
        result.captured_at!==receipt.observed_at || result.boundaries?.length!==1 ||
        result.boundaries[0].path!==source.path || result.boundaries[0].url!==source.url ||
        result.boundaries[0].revision!==inventory.revision || result.boundaries[0].source_expressions!==source.expressions.length ||
        result.boundaries[0].source_sha256!==source.source_sha256 ||
        result.boundaries[0].captured_hosts!==source.expressions.length ||
        result.expressions_checked!==source.expressions.length ||
        capture?.pages?.length!==1 || JSON.stringify(capture.pages[0])!==JSON.stringify(receipt.capture) ||
        capture.schema_version!==1 || capture.capture_method!=='playwright-github' || capture.renderer_profile!=='github' ||
        capture.captured_at!==receipt.observed_at || capture.repository!==inventory.repository ||
        capture.revision!==inventory.revision ||
        JSON.stringify(sourceInventory)!==JSON.stringify({...inventory,pages:[inventory.pages.find(p=>p.path===source.path)]}) ||
        !payloads.some(a=>a.descriptor.path===receipt.capture.artifacts?.html && a.descriptor.kind==='hosted_html') ||
        !payloads.some(a=>a.descriptor.path===receipt.capture.artifacts?.screenshot && a.descriptor.kind==='screenshot'))
      throw new Error('Missing or inconsistent passing page evidence');
    reusable.set(receipt.key,{receipt,descriptor,receiptBytes,payloads,
      provenance:{source_directory:path.resolve(directory),session_sha256:sha256(bytes),
        receipt_sha256:descriptor.receipt.sha256,observed_at:receipt.observed_at}});
  }
  return {reusable,previous_attempt:{directory:path.resolve(directory),session_sha256:sha256(bytes),
    started_at:session.started_at,updated_at:session.updated_at,failures:session.failures}};
}
function runTextCheck(args, helper, output, inventoryFile, captureFile, resultFile, contractFile=null) {
  const command=[helper,'check','--inventory',path.join(output,inventoryFile),'--capture',path.join(output,captureFile),
    '--output',path.join(output,resultFile)];
  if(contractFile) command.push('--contract',path.join(output,contractFile));
  const check=cp.spawnSync(args.python,command,{encoding:'utf8'});
  if(check.error || !fs.existsSync(path.join(output,resultFile)))
    throw new Error('Math checker did not produce a result: '+(check.error||check.stderr));
  return JSON.parse(fs.readFileSync(path.join(output,resultFile),'utf8'));
}
function savePageReceipt(args, helper, output, session, inventory, source, viewport, item, prefix, contract) {
  const capture={schema_version:1,repository:args.repository,revision:args.revision,renderer_profile:'github',
    captured_at:item.observed_at,capture_method:'playwright-github',pages:[item]};
  const invFile=prefix+'-source.json',captureFile=prefix+'-capture.json',resultFile=prefix+'-result.json';
  writeJSON(path.join(output,invFile),{...inventory,pages:[source]});
  writeJSON(path.join(output,captureFile),capture);
  const pageContract=contract?{...contract,expressions:contract.expressions.filter(e=>e.path===source.path)}:null;
  const contractFile=pageContract?prefix+'-contract.json':null;
  if(pageContract) writeJSON(path.join(output,contractFile),pageContract);
  const result=runTextCheck(args,helper,output,invFile,captureFile,resultFile,contractFile);
  const files=[artifact(output,invFile,'page_source_inventory'),artifact(output,captureFile,'page_hosted_capture'),
    artifact(output,resultFile,'page_math_result')];
  if(contractFile) files.push(artifact(output,contractFile,'page_text_contract'));
  for(const [kind,name] of [['hosted_html',item.artifacts?.html],['screenshot',item.artifacts?.screenshot]])
    if(name) files.push(artifact(output,name,kind));
  if(result.status!=='pass' || !capturePassed({...source,revision:args.revision},item))
    return {passed:false,result,artifacts:files};
  const receipt={schema_version:1,kind:'hosted_math_page',status:'pass',repository:args.repository,
    revision:args.revision,tree:session.binding.tree,path:source.path,source_sha256:source.source_sha256,
    viewport,key:pageKey(source.path,viewport),observed_at:item.observed_at,capture:item,artifacts:files};
  const filename=prefix+'-receipt.json';writeJSON(path.join(output,filename),receipt);
  const descriptor={key:receipt.key,receipt:artifact(output,filename,'page_receipt')};
  session.completed.push(descriptor);session.updated_at=new Date().toISOString();saveSession(output,session);
  return {passed:true,result,artifacts:[...files,descriptor.receipt],receipt};
}
async function captureHostedPage(context, source, expected, prefix, output) {
  const page=await context.newPage();
  const item={path:source.path,url:source.url,revision:source.revision,source_sha256:source.source_sha256,errors:[],math:[]};
  try {
    const response=await page.goto(source.url,{waitUntil:'domcontentloaded',timeout:60000});
    if(response?.status()!==200) throw new Error('HTTP '+response?.status());
    if(page.url()!==source.url) throw new Error('Browser redirected away from exact pinned source URL');
    const article=page.locator('article.markdown-body').first();
    await article.waitFor({state:'visible',timeout:30000});
    await page.evaluate(async()=>{
      for(let y=0,steps=0;y<document.body.scrollHeight && steps<200;y+=900,steps++) {
        window.scrollTo(0,y);await new Promise(r=>setTimeout(r,50));
      }
      window.scrollTo(0,0);
    });
    await page.waitForTimeout(1000);
    Object.assign(item,await article.evaluate(inspectArticle,expected));
    const html=prefix+'.html',png=prefix+'.png';
    fs.writeFileSync(path.join(output,html),await page.content());
    await page.screenshot({path:path.join(output,png),fullPage:true,timeout:30000});
    item.artifacts={html,screenshot:png};
    item.observed_at=new Date().toISOString();
    return item;
  } finally {await page.close();}
}
async function defaultRuntime() {
  const {chromium}=require('playwright');
  const runtime={node:process.version,playwright:require('playwright/package.json').version,
    mathjax:require('mathjax-full/package.json').version};
  const compile=mathCompiler(),browser=await chromium.launch({headless:true});
  runtime.browser=browser.version();return {browser,compile,runtime};
}
async function run(args, adapters={}) {
  const output=path.resolve(args.output);
  if(fs.existsSync(output) && (fs.lstatSync(output).isSymbolicLink() || fs.readdirSync(output).length))
    throw new Error('Use an empty output directory; preserve earlier failed evidence');
  fs.mkdirSync(output,{recursive:true});
  const pinned=pinnedPages(args),helper=path.join(__dirname,'check_rendered_math.py');
  cp.execFileSync(args.python,[helper,'inventory','--root',args.root,'--repository',args.repository,
    '--revision',args.revision,...pinned.pages.flatMap(p=>['--page',p]),'--output',path.join(output,'math-source.json')],{stdio:'pipe'});
  const inventory=JSON.parse(fs.readFileSync(path.join(output,'math-source.json'),'utf8'));
  const at=new Date().toISOString(),failures=[],artifacts=[artifact(output,'math-source.json','source_inventory')],viewports=[];
  const contractBytes=args.contract?fs.readFileSync(path.resolve(args.contract)):Buffer.from('null');
  const contract=args.contract?JSON.parse(contractBytes.toString('utf8')):null;
  if(args.contract && (!contract || !Array.isArray(contract.expressions) || contract.schema_version!==1)) throw new Error('Invalid text contract');
  if(args.contract) {
    fs.writeFileSync(path.join(output,'math-contract.json'),contractBytes);
    artifacts.push(artifact(output,'math-contract.json','text_contract'));
  }
  let browser,session,runtime={},resume={reusable:new Map()},fatal=false;
  const pageProvenance=[];
  try {
    // A policy/access failure is detected from the durable state before a new browser is started.
    if(args.resumeFrom) {
      const prior=JSON.parse(fs.readFileSync(safeEvidenceFile(args.resumeFrom,'capture-state.json'),'utf8'));
      if(!Array.isArray(prior.failures) || prior.failures.some(f=>f.category!=='transport_failure'))
        throw new Error('Resume refused after a nontransient, policy or access failure');
    }
    const loaded=await (adapters.loadRuntime || defaultRuntime)();
    browser=loaded.browser;
    runtime={...loaded.runtime,python:cp.execFileSync(args.python,['-c','import sys; print(sys.version)'],{encoding:'utf8'}).trim()};
    const expected=Object.fromEntries(inventory.pages.map(p=>[p.path,p.expressions.map(e=>({...e,
      mml:loaded.compile(e.tex,['math-fence','dollar-display'].includes(e.kind))}))]));
    writeJSON(path.join(output,'expected-mathml.json'),expected);
    artifacts.push(artifact(output,'expected-mathml.json','expected_mathml'));
    session=newSession(sessionBinding(inventory,pinned.tree,fs.readFileSync(path.join(output,'expected-mathml.json')),
      contractBytes,runtime,helper,args.diagnosticOnly===true,fs.readFileSync(path.join(output,'math-source.json'))),at);
    if(args.resumeFrom) {
      resume=loadResume(args.resumeFrom,session.binding,inventory);
      session.previous_attempt=resume.previous_attempt;
    }
    saveSession(output,session);
    for(const viewport of VIEWPORTS) {
      const context=await browser.newContext({viewport,deviceScaleFactor:1,colorScheme:'light'});
      const capture={schema_version:1,repository:args.repository,revision:args.revision,renderer_profile:'github',
        captured_at:at,capture_method:'playwright-github',pages:[]};
      try {
        for(let index=0;index<inventory.pages.length;index++) {
          const source=inventory.pages[index],prefix=String(index+1).padStart(4,'0')+'-'+viewport.width;
          const key=pageKey(source.path,viewport),prior=resume.reusable.get(key);
          let item;
          if(prior) {
            for(const payload of prior.payloads) {
              const destination=path.join(output,payload.descriptor.path);
              fs.mkdirSync(path.dirname(destination),{recursive:true});fs.writeFileSync(destination,payload.bytes);
              artifacts.push(payload.descriptor);
            }
            fs.writeFileSync(path.join(output,prior.descriptor.receipt.path),prior.receiptBytes);
            artifacts.push(prior.descriptor.receipt);
            session.completed.push({...prior.descriptor,reused_from:prior.provenance});
            session.updated_at=new Date().toISOString();saveSession(output,session);
            item=prior.receipt.capture;
            pageProvenance.push({path:source.path,viewport,observed_at:item.observed_at,reused:true,...prior.provenance});
          } else {
            try {
              item=await captureHostedPage(context,{...source,revision:args.revision},expected[source.path],prefix,output);
              const receipt=savePageReceipt(args,helper,output,session,inventory,source,viewport,item,prefix,contract);
              artifacts.push(...receipt.artifacts);
              pageProvenance.push({path:source.path,viewport,observed_at:item.observed_at,reused:false});
              if(!receipt.passed) {
                const reason='Captured page failed structural or text comparison';
                session.failures.push({category:'verification_failure',path:source.path,viewport,observed_at:item.observed_at,reason});
                failures.push(source.path+' at '+viewport.width+': verification_failure: '+reason);
                session.updated_at=new Date().toISOString();saveSession(output,session);
              }
            } catch(error) {
              const category=classifyFailure(error),observed_at=new Date().toISOString();
              item={path:source.path,url:source.url,revision:args.revision,source_sha256:source.source_sha256,
                errors:[String(error)],math:[],observed_at};
              session.failures.push({category,path:source.path,viewport,observed_at,reason:String(error)});
              session.updated_at=observed_at;saveSession(output,session);
              failures.push(source.path+' at '+viewport.width+': '+category+': '+String(error));
              fatal=['policy_denied','access_required','transport_failure'].includes(category);
            }
          }
          capture.pages.push(item);
          if(fatal) break;
        }
      } finally {await context.close();}
      const observed=capture.pages.map(p=>p.observed_at).filter(Boolean).sort((a,b)=>Date.parse(a)-Date.parse(b));
      capture.captured_at=observed[0] || at;
      const captureFile='math-capture-'+viewport.width+'.json',resultFile='math-result-'+viewport.width+'.json';
      writeJSON(path.join(output,captureFile),capture);artifacts.push(artifact(output,captureFile,'hosted_capture'));
      const result=runTextCheck(args,helper,output,'math-source.json',captureFile,resultFile,args.contract?'math-contract.json':null);
      artifacts.push(artifact(output,resultFile,'math_result'));
      failures.push(...result.failures.map(f=>viewport.width+': '+f));
      const matches=capture.pages.reduce((n,p)=>n+p.math.filter(m=>m.structural_match && !m.errors.length).length,0);
      viewports.push({...viewport,status:result.status,structural_matches:matches,capture_path:captureFile,result_path:resultFile,boundaries:result.boundaries});
      if(fatal) break;
    }
  } catch(error) {
    const category=classifyFailure(error);failures.push(category+': '+String(error));
    if(session) {
      session.failures.push({category,reason:String(error),observed_at:new Date().toISOString()});
      session.updated_at=new Date().toISOString();saveSession(output,session);
    }
  } finally {if(browser) await browser.close();}
  if(session) artifacts.push(artifact(output,'capture-state.json','capture_session'));
  const observations=pageProvenance.map(p=>p.observed_at).sort((a,b)=>Date.parse(a)-Date.parse(b));
  const report={...boundReport(inventory,pinned.tree,viewports,artifacts,failures,observations[0] || at),runtime,
    report_assembled_at:new Date().toISOString(),page_provenance:pageProvenance,diagnostic_only:args.diagnosticOnly===true};
  if(session?.previous_attempt) report.previous_attempt=session.previous_attempt;
  writeJSON(path.join(output,'hosted-report.json'),report);
  console.log(JSON.stringify({status:report.status,report:path.join(output,'hosted-report.json'),sha256:sha256(fs.readFileSync(path.join(output,'hosted-report.json'))),pages:report.required_pages.length,failures:report.failures.length,reused_pages:pageProvenance.filter(p=>p.reused).length}));
  return report.status==='pass'?0:1;
}
module.exports={argumentsFor,safePath,pinnedPages,mathCompiler,inspectArticle,classifyFailure,artifact,boundReport,VIEWPORTS,run,
  safeEvidenceFile,readBoundArtifact,observationTime,pageKey,capturePassed,sessionBinding,newSession,saveSession,loadResume,
  runTextCheck,savePageReceipt,captureHostedPage,RESUME_MAX_AGE_MS};
if(require.main===module) {
  (async()=>{
    const args=argumentsFor(process.argv.slice(2));
    if(args.help) {console.log('capture_hosted_math.cjs --root REPO --repository owner/name --revision FULLSHA --output EMPTY_DIR [--page PATH ...] [--contract JSON] [--python python3] [--resume-from PRIOR_EVIDENCE_DIR]');return;}
    process.exitCode=await run(args);
  })().catch(error=>{console.error(String(error));process.exitCode=2;});
}

