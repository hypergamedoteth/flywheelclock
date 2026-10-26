/* Flywheel Clock tickers: value = annual / seconds-in-period x elapsed seconds. Projections, not live data. */
(function(){
  var el=document.getElementById('page-data'); if(!el) return;
  var cfg; try{cfg=JSON.parse(el.textContent)}catch(e){return}
  var C={}; (cfg.counters||[]).forEach(function(c){C[c.id]=c});
  var nodes=[].slice.call(document.querySelectorAll('[data-ctr]')); if(!nodes.length) return;
  var t0=Date.now(), y=new Date(); var jan1=new Date(y.getFullYear(),0,1).getTime();
  function fmt(v,unit,mode){
    if(unit==='usd') return '$'+Math.floor(v).toLocaleString('en-US');
    if(unit==='gold'){
      if(mode==='day') return (v/1e6).toLocaleString('en-US',{maximumFractionDigits:2})+' t';
      return Math.floor(v).toLocaleString('en-US')+' g';
    }
    return Math.floor(v).toLocaleString('en-US');
  }
  function tick(){
    var now=Date.now();
    for(var i=0;i<nodes.length;i++){
      var n=nodes[i], c=C[n.getAttribute('data-ctr')]; if(!c) continue;
      var m=n.getAttribute('data-mode'), s=m==='year'?(now-jan1)/1000:m==='day'?86400:(now-t0)/1000;
      var txt=fmt(c.rate*s,c.unit,m); if(n.textContent!==txt) n.textContent=txt;
    }
    requestAnimationFrame(tick);
  }
  tick();
})();
