(function(){
 var t=document.getElementById('dir');if(!t)return;
 var rows=[].slice.call(t.tBodies[0].rows),q=document.getElementById('q'),cnt=document.getElementById('count');
 var boxes=[].slice.call(document.querySelectorAll('[data-f]')),aud=document.getElementById('aud');
 function apply(){
  var s=(q.value||'').toLowerCase().trim(),n=0;
  var on=boxes.filter(function(b){return b.checked}).map(function(b){return b.getAttribute('data-f')});
  rows.forEach(function(r){
   var ok=(!s||r.getAttribute('data-name').indexOf(s)>-1);
   for(var i=0;ok&&i<on.length;i++){if(r.getAttribute('data-'+on[i])!=='1')ok=false}
   if(ok&&aud&&aud.value&&r.getAttribute('data-aud').indexOf(aud.value)<0)ok=false;
   r.hidden=!ok;if(ok)n++;
  });
  cnt.textContent=n+' of '+rows.length+' HMRC-recognised products shown';
  var p=new URLSearchParams();if(s)p.set('q',s);on.forEach(function(f){p.append('f',f)});if(aud&&aud.value)p.set('aud',aud.value);if(pcf&&!pcf.checked)p.set('pcf','0');
  history.replaceState(null,'',p.toString()?'?'+p+'#directory':location.pathname);
 }
 q.addEventListener('input',apply);boxes.forEach(function(b){b.addEventListener('change',apply)});if(aud)aud.addEventListener('change',apply);
 // sorting: price-checked first (toggle, on by default), then the chosen column (default A-Z)
 var pcf=document.getElementById('pcf'),sk='name',sd=1;
 function cmp(a,b){
  if(pcf&&pcf.checked){var ca=+a.getAttribute('data-checked'),cb=+b.getAttribute('data-checked');if(ca!==cb)return cb-ca}
  var x=a.getAttribute('data-s-'+sk),y=b.getAttribute('data-s-'+sk);var nx=parseFloat(x),ny=parseFloat(y);
  var r=((!isNaN(nx)&&!isNaN(ny))?(nx-ny):x.localeCompare(y))*sd;
  if(r===0&&sk!=='name')r=a.getAttribute('data-s-name').localeCompare(b.getAttribute('data-s-name'));
  return r;
 }
 function resort(){rows.sort(cmp);rows.forEach(function(r){t.tBodies[0].appendChild(r)})}
 [].slice.call(t.tHead.querySelectorAll('th[data-k]')).forEach(function(th){
  th.querySelector('button').addEventListener('click',function(){
   var k=th.getAttribute('data-k');sd=(sk===k&&th.getAttribute('aria-sort')==='ascending')?-1:1;sk=k;
   [].slice.call(t.tHead.querySelectorAll('th')).forEach(function(h){h.removeAttribute('aria-sort')});
   th.setAttribute('aria-sort',sd===1?'ascending':'descending');
   resort();
  });
 });
 if(pcf)pcf.addEventListener('change',function(){resort();apply()});
 // quick-start chips
 [].slice.call(document.querySelectorAll('[data-preset]')).forEach(function(c){
  c.addEventListener('click',function(){
   var pr=c.getAttribute('data-preset').split(',');boxes.forEach(function(b){b.checked=pr.indexOf(b.getAttribute('data-f'))>-1});
   [].slice.call(document.querySelectorAll('[data-preset]')).forEach(function(o){o.setAttribute('aria-pressed',o===c)});
   apply();document.getElementById('directory').scrollIntoView({behavior:'smooth'});
  });
 });
 // restore from URL
 var p=new URLSearchParams(location.search);if(p.get('q'))q.value=p.get('q');
 var fs=p.getAll('f');boxes.forEach(function(b){if(fs.indexOf(b.getAttribute('data-f'))>-1)b.checked=true});if(aud&&p.get('aud'))aud.value=p.get('aud');
 if(pcf&&p.get('pcf')==='0')pcf.checked=false;
 resort();apply();
})();
