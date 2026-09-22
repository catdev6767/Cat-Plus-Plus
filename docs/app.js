const KW=['paw','meow','purr','give','hiss','tap','sit','leap','listen','sniff',
'swat','knead','groom','of','nod','shake','hungry','with','either','never',
'cat','me','kin','kit','litter'];
const BI=['tail','puff','melt','nip','bolt','kitten','lion','scratch','flop',
'perch','say','tally','drip','collar','kits','seek','shred','weave','swap',
'lick','hunt','stash','snatch','line','flip','head','rear','pile','walk',
'chase','sift','curl','sway','wave','slant','grow','bound','wander','dice'];

function esc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}

function hl(code){
  var out='';
  var i=0;
  var n=code.length;
  while(i<n){
    var c=code[i];
    if(c==='#'){
      var j=i;
      while(j<n&&code[j]!=='\n')j++;
      out+='<span class="cmt">'+esc(code.slice(i,j))+'</span>';
      i=j;
      continue;
    }
    if(c==='\"'){
      var j=i+1;
      var s='\"';
      while(j<n&&code[j]!=='\"'){
        if(code[j]==='\\'&&j+1<n){
          s+=code[j]+code[j+1];
          j+=2;
        } else {
          s+=code[j];
          j++;
        }
      }
      if(j<n){s+='\"';j++;}
      out+='<span class="str">'+esc(s)+'</span>';
      i=j;
      continue;
    }
    if(c>='0'&&c<='9'){
      var j=i;
      while(j<n&&(code[j]>='0'&&code[j]<='9'||code[j]==='.'))j++;
      out+='<span class="num">'+code.slice(i,j)+'</span>';
      i=j;
      continue;
    }
    if(/[a-zA-Z_]/.test(c)){
      var j=i;
      while(j<n&&/[a-zA-Z0-9_]/.test(code[j]))j++;
      var w=code.slice(i,j);
      if(KW.indexOf(w)>=0)out+='<span class="kw">'+w+'</span>';
      else if(BI.indexOf(w)>=0)out+='<span class="bi">'+w+'</span>';
      else if(code[j]==='(')out+='<span class="fn">'+w+'</span>';
      else out+=esc(w);
      i=j;
      continue;
    }
    if('+-*/%=<>!'.indexOf(c)>=0){
      var j=i;
      while(j<n&&'+-*/%=<>!'.indexOf(code[j])>=0)j++;
      out+='<span class="op">'+esc(code.slice(i,j))+'</span>';
      i=j;
      continue;
    }
    out+=esc(c);
    i++;
  }
  return out;
}

document.addEventListener('DOMContentLoaded',function(){
  var codes=document.querySelectorAll('pre > code');
  for(var k=0;k<codes.length;k++){
    var el=codes[k];
    var raw=el.textContent;
    el.innerHTML=hl(raw);
    var pre=el.parentElement;
    var btn=document.createElement('button');
    btn.textContent='Copy';
    btn.style.cssText='position:absolute;top:8px;right:8px;background:#21262d;color:#c9d1d9;border:1px solid #30363d;padding:4px 10px;border-radius:4px;cursor:pointer;font-size:12px;opacity:0;transition:opacity .15s;';
    btn.onclick=function(e){
      e.stopPropagation();
      navigator.clipboard.writeText(raw).then(function(){
        btn.textContent='Copied!';
        setTimeout(function(){btn.textContent='Copy';},1200);
      });
    };
    pre.appendChild(btn);
    pre.addEventListener('mouseenter',function(){btn.style.opacity='1';});
    pre.addEventListener('mouseleave',function(){btn.style.opacity='0';});
  }

  var si=document.getElementById('search-input');
  if(si){
    si.addEventListener('input',function(e){
      var q=e.target.value.toLowerCase().trim();
      var links=document.querySelectorAll('.sidebar-link');
      for(var i=0;i<links.length;i++){
        var txt=links[i].textContent.toLowerCase();
        links[i].style.display=(!q||txt.indexOf(q)>=0)?'':'none';
      }
    });
  }

  var sb=document.querySelector('.sidebar');
  if(!sb)return;

  var cur=location.pathname;
  if(cur.length>1&&cur.slice(-1)==='/')cur=cur.slice(0,-1);

  var links=sb.querySelectorAll('.sidebar-link');
  var activeLink=null;
  for(var i=0;i<links.length;i++){
    var href=links[i].getAttribute('href');
    if(!href)continue;
    var abs=href;
    try{abs=new URL(href,location.href).pathname;}catch(e){continue;}
    if(abs.length>1&&abs.slice(-1)==='/')abs=abs.slice(0,-1);
    if(abs===cur){
      links[i].classList.add('active');
      activeLink=links[i];
    }
  }

  if(activeLink){
    setTimeout(function(){
      try{activeLink.scrollIntoView({block:'center'});}catch(e){}
    },150);
  }

  for(var i=0;i<links.length;i++){
    links[i].addEventListener('click',function(){
      try{sessionStorage.setItem('catpp-sbs',sb.scrollTop);}catch(e){}
    });
  }

  if(!activeLink){
    try{
      var sv=sessionStorage.getItem('catpp-sbs');
      if(sv)sb.scrollTop=parseInt(sv,10);
    }catch(e){}
  }
});
