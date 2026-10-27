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
      if(mode==='open') return (v/1000).toLocaleString('en-US',{minimumFractionDigits:1,maximumFractionDigits:1})+' kg';
      return Math.floor(v/1000).toLocaleString('en-US')+' kg';
    }
    if(unit==='btc') return v.toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2})+' BTC';
    if(unit==='bbl') return Math.floor(v).toLocaleString('en-US')+' bbl';
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
