// Pure browser-local configuration generation. No node credentials or network calls.
export const defaults = () => ({version:1,chain:false,entry:'',exit:'',dns:'compatible',customDns:'',dnsViaProxy:false,stun:false,ads:true,wechat:'default',douyin:'default',kugou:'default',direct:'',proxy:''});
export const apps = {
  wechat:{label:'微信',domains:['wechat.com','weixin.com','weixin.qq.com','wx.qq.com','qlogo.cn','servicewechat.com','wechatpay.com','weixinbridge.com','weixinsxy.com','wechatos.net','tenpay.com']},
  douyin:{label:'抖音',domains:['douyin.com','douyincdn.com','douyinpic.com','douyinstatic.com','douyinvod.com','iesdouyin.com','amemv.com','idouyinvod.com','ixiguavideo.com'],exact:['lf3-static.bytednsdoc.com','v5-dy-o-abtest.zjcdn.com']},
  kugou:{label:'酷狗',domains:['kugou.com','kugou.net','kugoo.com','kgimg.com','kglink.cn','kugouipv6.com']}
};
const reserved = ['dns.alidns.com','doh.pub','localhost','local','lan','captive.apple.com'];
export function domains(value) {
  if (typeof value !== 'string' || value.length > 20000) throw Error('域名列表过长，请限制在 20,000 字符内。');
  return [...new Set(value.split(/\r?\n/).map(x=>x.trim().toLowerCase()).filter(Boolean).map(x=>{
    if (x.length>253 || !/^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z](?:[a-z0-9-]{0,61}[a-z0-9])?$/.test(x)) throw Error(`“${x.slice(0,70)}”不是完整域名。请只填域名，不带 https://、路径或逗号。`);
    if (reserved.some(r=>x===r||x.endsWith('.'+r))) throw Error(`“${x}”用于 DNS 引导或本地网络，请保留默认分流。`);
    return x;
  }))];
}
export function normalize(input) {
  if (!input || typeof input!=='object' || Array.isArray(input) || input.version!==1) throw Error('这不是受支持的花瓣设置文件（版本 1）。');
  const s=defaults();
  for(const key of Object.keys(s)) {
    if(!(key in input)) continue;
    if(typeof input[key]!==typeof s[key]) throw Error(`设置 ${key} 的格式不正确。`);
    s[key]=input[key];
  }
  for(const key of ['entry','exit']) if(s[key].length>80 || /[\x00-\x1f\x7f]/.test(s[key])) throw Error('节点名称最多 80 字符，不能换行。');
  if(s.chain && (!s.entry.trim() || !s.exit.trim())) throw Error('开启链式代理后，请填写入口和出口节点的名称。');
  if(s.chain && s.entry.trim()===s.exit.trim()) throw Error('入口和出口不能是同一个节点，请选择两个不同节点。');
  if(!['compatible','privacy','custom'].includes(s.dns)) throw Error('请选择有效的 DNS 模式。');
  for(const key of Object.keys(apps)) if(!['default','DIRECT','PROXY'].includes(s[key])) throw Error('应用分流选项无效。');
  const direct=domains(s.direct), proxy=domains(s.proxy);
  const duplicate=direct.find(x=>proxy.includes(x));
  if(duplicate) throw Error(`“${duplicate}”同时指定直连和代理，请只保留一处。`);
  if(s.customDns.length>4000) throw Error('自定义 DNS 地址过长。');
  if(s.dns==='custom') customResolvers(s);
  return s;
}
function customResolvers(s) {
  const lines=s.customDns.split(/\r?\n/).map(x=>x.trim()).filter(Boolean);
  if(!lines.length || lines.length>3) throw Error('请输入 1–3 个 HTTPS DNS 地址，每行一个。');
  return lines.map(x=>{
    let url; try {url=new URL(x);} catch {throw Error('DNS 地址应为完整的 https:// 地址。');}
    if(url.protocol!=='https:' || url.username || url.password || url.hash || /[\s,\x00-\x1f]/.test(x) || !url.hostname || url.pathname==='/') throw Error('DNS 仅接受带路径的 HTTPS 地址，不含账号、密码、空格、逗号或 # 参数。');
    return url.href+(s.dnsViaProxy?'#proxy&no-h3':'#no-h3');
  }).join(',');
}
export function checklist(s) {
  const steps=['先保留当前能用的配置副本。下载 .conf 后，在“文件”中分享给 Shadowrocket，或在配置页从本地文件导入（入口名称随版本可能不同）。','在配置页选中导入的配置；首页全局路由选择“配置”。'];
  if(s.chain) steps.push(`先将两个节点分别导入小火箭。打开出口“${s.exit.trim()}”右侧 ⓘ → 代理通过 → 选择入口“${s.entry.trim()}” → 保存。首页选择出口“${s.exit.trim()}”连接。只有走代理的请求使用这条链，直连规则仍然直连。`, '更新订阅后检查“代理通过”是否保留；协议不支持或入口不可用时，代理链可能失败。恢复单节点：出口 ⓘ → 代理通过 → 右上角取消 → 保存。');
  else steps.push('首页手动选择自己的可用节点。若这个节点以前设置过链式代理，请在 ⓘ → 代理通过 → 右上角取消 → 保存，配置文件不会清除旧代理链。');
  steps.push(s.stun?'手动打开：设置 → UDP → 禁用 STUN。它可能影响微信语音、视频和网页通话；遇到问题先关闭此开关。此操作不保证阻止所有 WebRTC IP 暴露。':'手动检查：设置 → UDP → 禁用 STUN 保持关闭，以保留通话兼容性。配置文件不会替你更改此开关。');
  if(s.dns!=='compatible') steps.push('DNS 已使用进阶设置，尚未在你的网络实测。若测速或打开网页超时，回到配置器选择“兼容优先”重新导出，再断开重连。');
  steps.push('断开重连，分别打开国内网页、国外网页，并试一次常用通话。网页配置器无法测试你手机里的节点。');
  return steps;
}
export function generate(base,input) {
  const s=normalize(input);
  if(!base.includes('[General]') || !base.includes('# 用户代理覆盖：') || !base.includes('[Host]') || !base.includes('FINAL,PROXY')) throw Error('基础配置不完整，请刷新后重试。');
  let config=base;
  if(s.dns!=='compatible') {
    const resolver=s.dns==='privacy'?'https://1.1.1.1/dns-query#proxy&no-h3,https://9.9.9.9/dns-query#proxy&no-h3':customResolvers(s);
    config=config.replace(/^dns-server = .*$/m,`dns-server = ${resolver}`).replace(/^fallback-dns-server = .*$/m,`fallback-dns-server = ${resolver}`);
    config=config.replace('# 本地解析使用直连加密 DNS，普通代理域名由节点解析。','# 本地 DNS 使用自定义模式；节点域名引导仍保留兼容 DNS。').replace('# 1. 本地加密解析与节点引导：不依赖代理先连通。','# 1. 自定义本地 DNS；proxy-dns-server 单独为节点域名提供引导。');
  }
  if(!s.ads) config=config.replace(/^DOMAIN,[^,\n]+,REJECT\r?\n/gm,'').replace('# 小范围广告阻断；用户覆盖可先行纠正误拦。','# 已关闭内置小范围广告阻断。');
  const rules=[...domains(s.proxy).map(x=>`DOMAIN,${x},PROXY`),...domains(s.direct).map(x=>`DOMAIN,${x},DIRECT`)];
  for(const [key,app] of Object.entries(apps)) if(s[key]!=='default') rules.push(...app.domains.map(d=>`DOMAIN-SUFFIX,${d},${s[key]}`),...(app.exact||[]).map(d=>`DOMAIN,${d},${s[key]}`));
  if(rules.length) config=config.replace('# 用户代理覆盖：',`# 可视化设置：精确域名优先于应用分流；DNS / 局域网保留优先级。\n${rules.join('\n')}\n\n# 用户代理覆盖：`);
  const steps=checklist(s);
  // Defaults deliberately preserve the working baseline byte for byte.
  return {config,steps,settings:s,manualCount:s.chain?2:1};
}
