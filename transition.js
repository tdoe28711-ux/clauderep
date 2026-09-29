(function(){
  var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  var root = document.documentElement;
  if(!reduce){
    root.classList.add('pt');
    addEventListener('pageshow', function(){ root.classList.add('pt-in'); });
    requestAnimationFrame(function(){ root.classList.add('pt-in'); });
    document.addEventListener('click', function(e){
      var a = e.target.closest && e.target.closest('a');
      if(!a) return;
      var href = a.getAttribute('href');
      if(!href || href.charAt(0)==='#' || a.target === '_blank') return;
      if(href.indexOf('mailto:')===0 || href.indexOf('tel:')===0) return;
      if(a.host && a.host !== location.host) return;
      e.preventDefault();
      root.classList.remove('pt-in');
      root.classList.add('pt-out');
      setTimeout(function(){ location.href = href; }, 340);
    });
  }
})();
