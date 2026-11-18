/* Privacy-friendly analytics loader. Only included in pages when config/analytics.json has provider + site_id.
   No cookies, no localStorage (except the visitor's own opt-out choice), no personal data, no search text.
   Events (GoatCounter "event" paths; never start with "/"):
     out:<aff|site|link>:<product-slug or host>:<page>   outbound click
     start:<preset>:<page>                              Start-here button
     filter:<f1+f2|none>[:search]:<page>                filter state, debounced
     time:<seconds>:<page>                              engaged seconds since last report (sent when tab hidden/closed) */
(function(){
 var s=document.currentScript||document.querySelector('script[data-mtd-provider]');if(!s)return;
 var P=s.getAttribute('data-mtd-provider'),ID=s.getAttribute('data-mtd-site'),O={};
 try{O=JSON.parse(s.getAttribute('data-mtd-opts')||'{}')}catch(e){}
 var KEY='mtd-analytics-optout';
 function optedOut(){try{return localStorage.getItem(KEY)==='1'}catch(e){return false}}
 // privacy page toggle (works even when opted out)
 function wireToggle(){var b=document.getElementById('mtd-optout');if(!b)return;var st=document.getElementById('mtd-optout-status');
  function show(){var o=optedOut();b.textContent=o?'Turn analytics back on for this browser':'Turn off analytics for this browser';if(st)st.textContent=o?'Analytics is OFF for this browser.':'Analytics is ON for this browser.'}
  b.addEventListener('click',function(){try{optedOut()?localStorage.removeItem(KEY):localStorage.setItem(KEY,'1')}catch(e){}show()});show()}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',wireToggle);else wireToggle();
 var dnt=navigator.doNotTrack==='1'||window.doNotTrack==='1'||navigator.globalPrivacyControl===true;
 if(!P||!ID||optedOut()||(O.respect_do_not_track!==false&&dnt))return;
 var page=location.pathname, q=[], send;
 if(P==='goatcounter'){
  window.goatcounter={no_onload:false};
  var g=document.createElement('script');g.async=true;g.src='https://gc.zgo.at/count.js';
  g.setAttribute('data-goatcounter','https://'+encodeURIComponent(ID)+'.goatcounter.com/count');document.head.appendChild(g);
  send=function(name,title){var gc=window.goatcounter;if(gc&&gc.count){gc.count({path:name,title:title||name,event:true})}else q.push([name,title])};
  var t=setInterval(function(){if(window.goatcounter&&window.goatcounter.count){clearInterval(t);var x;while((x=q.shift()))send(x[0],x[1])}},300);
  setTimeout(function(){clearInterval(t)},20000);
 }else{return}
 window.mtdTrack=send;
 // outbound clicks
 if(O.track_outbound_clicks!==false){
  function onClick(e){var a=e.target.closest&&e.target.closest('a[href]');if(!a)return;var u;try{u=new URL(a.href,location.href)}catch(x){return}
   if(u.host===location.host||!/^https?:$/.test(u.protocol))return;
   var slug=a.getAttribute('data-product'),kind=slug?(a.getAttribute('data-aff')==='1'?'aff':'site'):'link';
   send('out:'+kind+':'+(slug||u.host.replace(/^www\./,''))+':'+page,(kind==='link'?'Outbound link to ':'Visit-site click: ')+(slug||u.host)+(kind==='aff'?' (affiliate)':''))}
  document.addEventListener('click',onClick,true);document.addEventListener('auxclick',function(e){if(e.button===1)onClick(e)},true);
 }
 // Start-here buttons
 if(O.track_start_here!==false){[].slice.call(document.querySelectorAll('[data-preset]')).forEach(function(c){c.addEventListener('click',function(){
  send('start:'+c.getAttribute('data-preset').replace(/,/g,'+')+':'+page,'Start here: '+c.textContent.trim())})})}
 // filters (debounced; search box content is never sent, only whether one was used)
 if(O.track_filters!==false){var boxes=[].slice.call(document.querySelectorAll('input[data-f]')),qs=document.getElementById('q'),aud=document.getElementById('aud'),ft,last='';
  function fire(){var on=boxes.filter(function(b){return b.checked}).map(function(b){return b.getAttribute('data-f')}).sort();
   var key=(on.join('+')||'none')+(aud&&aud.value?'+aud-'+aud.value:'')+(qs&&qs.value.trim()?':search':'');if(key===last)return;last=key;
   send('filter:'+key+':'+page,'Filters: '+key)}
  function deb(){clearTimeout(ft);ft=setTimeout(fire,1500)}
  boxes.forEach(function(b){b.addEventListener('change',deb)});if(qs)qs.addEventListener('input',deb);if(aud)aud.addEventListener('change',deb);}
 // engaged time: counts seconds while the tab is visible and the visitor was active in the last 60s
 if(O.track_time_on_page!==false){var acc=0,lastAct=Date.now(),tick=Date.now();
  function now(){var n=Date.now();if(document.visibilityState==='visible'&&n-lastAct<60000)acc+=Math.min(n-tick,5000);tick=n}
  ['scroll','mousemove','keydown','touchstart','click'].forEach(function(ev){addEventListener(ev,function(){now();lastAct=Date.now()},{passive:true})});
  setInterval(now,1000);
  function flush(){now();var sec=Math.round(acc/1000);if(sec<1)return;acc=0;
   var b=sec<=10?sec:sec<=120?Math.round(sec/5)*5:sec<=600?Math.round(sec/15)*15:Math.min(1800,Math.round(sec/60)*60);
   send('time:'+b+':'+page,'Engaged time '+b+'s')}
  document.addEventListener('visibilitychange',function(){if(document.visibilityState==='hidden')flush();else{tick=Date.now();lastAct=Date.now()}});
  addEventListener('pagehide',flush);
 }
})();
