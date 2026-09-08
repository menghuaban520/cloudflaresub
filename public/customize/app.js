import {defaults,generate,normalize,apps} from './model.js';
const $=id=>document.getElementById(id), form=$('settings');
let base='', result=null;
const names=Object.keys(defaults()).filter(x=>x!=='version');
function read(){const s=defaults();for(const key of names)s[key]=$(key).type==='checkbox'?$(key).checked:$(key).value;return s;}
function write(s){for(const key of names)if($(key).type==='checkbox')$(key).checked=s[key];else $(key).value=s[key];}
function showError(message){$('errors').textContent=message;$('errors').hidden=false;}
function update(){
  const s=read();
  $('chain-fields').hidden=!s.chain;$('dns-fields').hidden=s.dns!=='custom';
  $('route').textContent=`你的设备 → ${s.entry.trim()||'入口节点'} → ${s.exit.trim()||'出口节点'} → 网站（仅代理流量）`;
  $('dns-help').textContent={compatible:'沿用阿里 / DNSPod 加密 DNS；节点域名独立引导，普通代理域名交给节点解析。',privacy:'进阶：本地 DNS 改用 Cloudflare / Quad9 并经过代理，节点域名引导仍直连。不是系统级零泄漏保证；代理不可用时可能超时。',custom:'自行指定本地加密解析服务。它不会改变所有代理域名的服务端解析，也不替换节点引导 DNS。'}[s.dns];
  $('errors').hidden=true;result=null;$('preview').value='';$('steps').replaceChildren();$('download').disabled=true;$('guide').disabled=true;
  const pairs=[['连接',s.chain?'入口 → 出口（手动设置）':'首页手选节点'],['DNS',{compatible:'兼容优先',privacy:'本地 DNS 经代理',custom:'自定义'}[s.dns]],['STUN',s.stun?'限制（手动打开）':'保留通话兼容'],['广告',s.ads?'轻量拦截':'不拦截'],...Object.entries(apps).map(([k,v])=>[v.label,{default:'默认直连',DIRECT:'强制直连',PROXY:'使用代理'}[s[k]]])];
  $('summary').replaceChildren(...pairs.map(([a,b])=>{const div=document.createElement('div'),dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=a;dd.textContent=b;div.append(dt,dd);return div;}));
  if(!base){$('status').textContent='基础配置尚未载入，暂时不能导出。';return;}
  try{
    result=generate(base,s);$('preview').value=result.config;
    $('steps').replaceChildren(...result.steps.map(text=>{const li=document.createElement('li');li.textContent=text;return li;}));
    $('download').disabled=false;$('guide').disabled=false;
    $('status').textContent='✓ 格式检查通过 · 手机连接效果仍需实测';
  }catch(e){showError(e.message);$('status').textContent='请修正以上问题后再导出。';}
}
function download(text,name,type='text/plain;charset=utf-8'){
  const url=URL.createObjectURL(new Blob([text],{type})),a=document.createElement('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),30000);
}
form.addEventListener('submit',e=>e.preventDefault());form.addEventListener('input',update);form.addEventListener('change',e=>{if(e.target.id!=='import')update();});
$('download').addEventListener('click',()=>{if(result)download(result.config,'huaban-custom.conf');});
$('guide').addEventListener('click',()=>{if(result)download('花瓣 · 我的操作清单\n\n'+result.steps.map((x,i)=>`${i+1}. ${x}`).join('\n\n'),'huaban-setup.txt');});
$('save').addEventListener('click',()=>{try{download(JSON.stringify(normalize(read()),null,2),'huaban-settings.json','application/json');}catch(e){showError(e.message);}});
$('reset').addEventListener('click',()=>{write(defaults());update();$('status').textContent='已恢复默认。手机中原有的代理链 / STUN 设置需按清单手动恢复。';});
$('import').addEventListener('change',async e=>{
  const file=e.target.files[0];if(!file)return;
  try{if(file.size>50000)throw Error('设置文件不能超过 50 KB。');const s=normalize(JSON.parse(await file.text()));write(s);update();}
  catch(err){showError(err instanceof SyntaxError?'无法读取 JSON，请载入“保存我的选项”生成的文件。':err.message);}
  finally{e.target.value='';}
});
try{const response=await fetch('../shadowrocket-rebuild.conf',{cache:'no-cache'});if(!response.ok)throw Error('基础配置下载失败');base=await response.text();update();}
catch{update();showError('基础配置读取失败，请检查网络并刷新页面。你的选项还在当前页面中。');}
