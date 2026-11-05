/* Flywheel Clock tickers: value = annual / seconds-in-period x elapsed seconds. Projections, not live data. */
(function(){
  var el=document.getElementById('page-data'); if(!el) return;
  var cfg; try{cfg=JSON.parse(el.textContent)}catch(e){return}
  var C={}; (cfg.counters||[]).forEach(function(c){C[c.id]=c});
  var nodes=[].slice.call(document.querySelectorAll('[data-ctr]')); if(!nodes.length) return;
  var t0=Date.now(), y=new Date(); var jan1=new Date(y.getFullYear(),0,1).getTime();
  var RM=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;
  function fmt(v,unit,mode,f){
    if(unit==='usd'&&f==='c'){var a=Math.abs(v);
      if(a>=1e9) return '$'+(v/1e9).toFixed(3)+'B';
      if(a>=1e6) return '$'+(v/1e6).toFixed(3)+'M';
      return '$'+Math.floor(v).toLocaleString('en-US');}
    if(unit==='usd') return '$'+Math.floor(v).toLocaleString('en-US');
    if(unit==='gold'){
      if(mode==='open') return (v/1000).toLocaleString('en-US',{minimumFractionDigits:1,maximumFractionDigits:1})+' kg';
      return Math.floor(v/1000).toLocaleString('en-US')+' kg';
    }
    if(unit==='btc') return v.toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2})+' BTC';
    if(unit==='bbl') return Math.floor(v).toLocaleString('en-US')+' bbl';
    return Math.floor(v).toLocaleString('en-US');
  }
  function elapsed(c, m, now){
    if(m==='open') return (now-t0)/1000;
    if(m==='day') return 86400;
    if(c.since){ var s=(now-Date.parse(c.since))/1000; return s>0?s:0; }
    if(m==='year') return (now-jan1)/1000;
    return (now-t0)/1000;
  }
  function amount(c, m, now){
    var base=(m==='year'&&c.base)?c.base:0;
    return base + c.rate*elapsed(c, m, now);
  }
  function tick(){
    var now=Date.now();
    for(var i=0;i<nodes.length;i++){
      var n=nodes[i], c=C[n.getAttribute('data-ctr')]; if(!c) continue;
      var m=n.getAttribute('data-mode');
      var txt=fmt(amount(c, m, now),c.unit,m,n.getAttribute('data-fmt')); if(n.textContent!==txt) n.textContent=txt;
    }
  }
  var last=0;
  function loop(ts){ if(ts-last>=60){last=ts;tick();} requestAnimationFrame(loop); }
  tick();
  if(RM) setInterval(tick,1000); else requestAnimationFrame(loop);
})();
