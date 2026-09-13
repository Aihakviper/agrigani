(function(){
  'use strict';
  if(window.matchMedia('(prefers-reduced-motion:reduce)').matches)return;
  if('ontouchstart' in window)return;

  var el=document.createElement('div');
  el.id='leaf-cursor';
  el.setAttribute('aria-hidden','true');
  el.innerHTML='<svg viewBox="0 0 36 46" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M18 2 C30 6 34 16 32 28 C30 38 25 44 18 44 C11 44 6 38 4 28 C2 16 6 6 18 2Z" fill="rgba(59,196,106,0.82)" stroke="rgba(46,158,85,0.7)" stroke-width="1"/><line x1="18" y1="4" x2="18" y2="42" stroke="rgba(27,94,53,0.55)" stroke-width="1.4"/><path d="M18 14 L9 21 M18 22 L10 30 M18 30 L11 36" stroke="rgba(27,94,53,0.35)" stroke-width="0.7" stroke-linecap="round"/><path d="M18 14 L27 21 M18 22 L26 30 M18 30 L25 36" stroke="rgba(27,94,53,0.35)" stroke-width="0.7" stroke-linecap="round"/><path d="M11 7 C9 12 8 19 9 24" stroke="rgba(180,255,210,0.45)" stroke-width="1.2" stroke-linecap="round"/><circle cx="18" cy="3" r="2.5" fill="rgba(100,220,140,0.6)"/></svg>';
  document.body.appendChild(el);

  var TRAIL=5,trails=[];
  for(var i=0;i<TRAIL;i++){
    var d=document.createElement('div');
    d.className='cursor-trail';
    d.style.cssText='opacity:'+(0.32-i*0.055)+';width:'+(7-i*0.9)+'px;height:'+(7-i*0.9)+'px;';
    document.body.appendChild(d);
    trails.push({el:d,x:0,y:0});
  }

  var cx=0,cy=0,tx=0,ty=0,vx=0,vy=0;
  var K=0.14,D=0.78,px=0,py=0,angle=0;

  document.addEventListener('mousemove',function(e){tx=e.clientX;ty=e.clientY;},{passive:true});

  document.addEventListener('mouseover',function(e){
    var t=e.target;
    if(t&&(t.matches('a,button,.btn,[role="button"]')||t.closest('a,button,.btn,[role="button"]'))){
      el.dataset.state='hover';
    } else if(el.dataset.state==='hover'){
      el.dataset.state='';
    }
  });

  function tick(){
    var fx=(tx-cx)*K,fy=(ty-cy)*K;
    vx=(vx+fx)*D; vy=(vy+fy)*D;
    cx+=vx; cy+=vy;
    var mx=cx-px,my=cy-py,sp=Math.hypot(mx,my);
    if(sp>0.6){var ta=Math.atan2(my,mx)*180/Math.PI+90;var df=((ta-angle+540)%360)-180;angle+=df*0.09;}
    px=cx;py=cy;
    el.style.left=cx+'px';el.style.top=cy+'px';
    el.style.transform='translate(-50%,-50%) rotate('+angle+'deg)';
    var prev={x:cx,y:cy};
    trails.forEach(function(tr){
      tr.x+=(prev.x-tr.x)*0.32;tr.y+=(prev.y-tr.y)*0.32;
      tr.el.style.left=tr.x+'px';tr.el.style.top=tr.y+'px';
      prev={x:tr.x,y:tr.y};
    });
    requestAnimationFrame(tick);
  }
  tick();

  window.setCursorState=function(s){el.dataset.state=s||'';};
})();
