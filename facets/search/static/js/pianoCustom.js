	var baseUrl = '/static/images/'; // baseUrl = 'http://195.138.202.66:8080/piano/';
	ham: null, //position de la hampe
	
	
	// Personnalisation de l'affichage de la partition
  Piano.drawPartition = function(note, time, octave)
  {
	  // On indique l'octave de la ligne basse de la portéee
	  var octaveBasis = 4;
	  
    var partitionpos = {c: 25, d: 22, e: 17, f: 14, g: 11, a: 7, b: 4};
    var std = note.substr(0, 1).toLowerCase();
    
    // Ici, on calcule la position verticale de la note.&
    var pos = partitionpos[std]+(26*(octaveBasis - octave))-8;
    
 // alert ("Note " + note + " Octave " + octave + " position standard " +  partitionpos[std] + " => position " + pos);
    
    // Petites corrections ...
  if (octave == 5) pos = pos + 1;
     
    var img = document.createElement('span');
    
    // Petite correction: calcul de la hauteur a laquelle on place la ligne supplemantaire
    var height = Math.abs(pos)  - 3;
   var bottom = 53;
   
    // Petites corrections ...
    //if (octave == 5) height = height ;
   
    //alert ("Height = " + height + " octave " + octave + " basis " + octaveBasis);
    var sbg = '<div style="position:absolute;' 
    	 + (octave > octaveBasis
    		 ?  'bottom:' + bottom + 'px' 
    	     : (std == 'd' && octave == octaveBasis ? 'top:0' : 'top:36px'))
    	  + ';left:10px;width:20px;height:'
    	  + height // (Math.abs(pos)  - 3 - (octave > octaveBasis ? 2 : 0))
    	  + 'px;background:url('+baseUrl +'part_bg.gif) '
    	  + (octave > octaveBasis ? '0 100%' : '0 0')+'"></div>';
    var dse = note.indexOf('#') != -1 ? '<img src="'+baseUrl +'diese.gif" alt="diese" style="position:absolute;top:0;left:0;margin-left:5px;margin-top:'+pos+'px" />' : '';
    var bml = note.indexOf('b') != -1 ? '<img src="'+baseUrl +'bemol.gif" alt="bemol" style="position:absolute;top:0;left:0;margin-left:5px;margin-top:'+pos+'px" />' : '';
    var crh = octave > octaveBasis || (octave == octaveBasis && note == 'B') ? '_2' : '_1';
   
    //alert ("SBG = " + sbg);
    
    img.innerHTML = sbg+bml+dse+'<img src="'+baseUrl +'key'+time+crh+'.gif" alt="'+note + octave + ',' +time+'" style="margin-top:'+pos+'px" />';
 //  alert ("Draw" + img.innerHTML);
    return img;
  };
  
  Piano.changeDrawedTime = function(t, i, d)
  {
	if (d==undefined) var d ='';  
    var prt = document.getElementById('partition');
    var img = prt.getElementsByTagName('span')[i].getElementsByTagName('img');
    var len = img.length -1;
    var src = img[len].src.split('_');
    var res = src[1];
    var g = res.split('.',1);
    if (this.ham==null) this.ham = g ;
    img[len].src = baseUrl +'key'+t+'_'+this.ham+d+'.gif';
    //img[len].src = baseUrl +'css/partition/key'+t+'_'+g+'dot.gif';
  };
  
  // Récupération d'une mélodie par défaut
  // ex : ?mel=/Cb3,8/C#6,2/A3,4/Bb5,8
  var mel = (function()
  {
    var uri = new String(document.location);
    var tmp = uri.split('&');
    for (var i in tmp) if (tmp[i].indexOf('mel=') != -1) return tmp[i].substr(tmp[i].indexOf('mel=')+4);
    return null;
  })();
