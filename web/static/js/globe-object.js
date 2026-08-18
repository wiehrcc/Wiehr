'use strict';
(function(){
    var m=document.getElementById('zoomedinnow');
    var i=document.getElementById('thebiggerpicture');
    var closeBtn=document.getElementById('lookawaynow');
    var c=document.querySelectorAll('.tapthis');
    if(!m||!i)return;
    var scale=0.75;
    function openModal(e){
        m.style.display='flex';
        i.src=e.src;
        i.alt=e.alt||'Image';
        scale=0.75;
        i.style.transform='scale(0.75)';
        window.WiehrOverlay.open();
    }
    function closeModal(){
        m.style.display='none';
        window.WiehrOverlay.close();
    }
    c.forEach(function(img){img.addEventListener('click',function(){openModal(img)})});
    if(closeBtn)closeBtn.addEventListener('click',closeModal);
    m.addEventListener('click',function(e){if(e.target===m)closeModal()});
    i.addEventListener('click',function(e){e.stopPropagation();closeModal()});
    document.addEventListener('keydown',function(e){if(e.key==='Escape'&&m.style.display==='flex')closeModal()});
    m.addEventListener('wheel',function(e){var delta=e.deltaY>0?0.9:1.1;scale*=delta;scale=Math.max(0.5,Math.min(3,scale));i.style.transform='scale('+scale+')';e.preventDefault()},{passive:false});
})();

