/* Email sign-up for the Free MTD Ready Kit. Provider-agnostic: posts the form fields to config/email.json's form_action.
   Only included on pages when email sign-up is configured. Without JavaScript the form still posts normally to the
   provider, which shows its own confirmation page.
   We cannot read the provider's reply (cross-origin), so success means "the request was sent"; the provider's
   double opt-in email is what actually confirms the address. Nothing is stored in the browser. */
(function(){
 function $(s,r){return (r||document).querySelector(s)}
 function track(role){try{if(window.mtdTrack)window.mtdTrack('signup:'+(role||'none')+':'+location.pathname,'Email sign-up'+(role?' ('+role+')':''))}catch(e){}}
 [].slice.call(document.querySelectorAll('form.signup-form[data-live="1"]')).forEach(function(f){
  var msg=$('.signup-msg',f),btn=$('button[type=submit]',f),busy=false;
  function show(t,cls){msg.textContent=t;msg.className='signup-msg '+(cls||'');}
  f.addEventListener('submit',function(e){
   e.preventDefault(); if(busy)return;
   var em=$('input[type=email]',f),fn=$('input[data-k=first_name]',f),hp=f.querySelector('[data-hp]');
   if(hp&&hp.value){show('Thanks!','ok');return}
   if(!fn.value.trim()){show('Please add your first name.','err');fn.focus();return}
   if(!em.value.trim()||!em.checkValidity()){show('Please check your email address.','err');em.focus();return}
   busy=true;btn.disabled=true;var old=btn.textContent;btn.textContent='Sending…';show('');
   var rr=f.querySelector('input[data-k=role]:checked'),role=rr?rr.getAttribute('data-role'):'';
   fetch(f.action,{method:'POST',mode:'no-cors',body:new FormData(f)}).then(function(){
     track(role);
     f.classList.add('done');
     var ok=$('.signup-ok',f.parentNode);if(ok){ok.hidden=false;var n=$('.signup-name',ok);if(n)n.textContent=fn.value.trim().split(' ')[0];ok.focus&&ok.focus()}
     f.hidden=true;
   }).catch(function(){
     show('Sorry, that didn\u2019t go through. Please check your connection and try again.','err');
   }).then(function(){busy=false;btn.disabled=false;btn.textContent=old});
  });
 });
})();
