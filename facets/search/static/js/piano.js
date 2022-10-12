/** 
 * @fileoverview Piano ARMADILLO
 *
 * @author Xavier Guerineau (Armadillo) 2009
 * @version 0.1
 */

var Piano = window.Piano =
{
  node: null,
  callback: null,
  octave: 3,
  whitetab: ['c', 'd', 'e', 'f', 'g', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'a', 'b'],
  blacktab: ['c', 'd', null, 'f', 'g', 'a', null, 'c', 'd', null, 'f', 'g', 'a', null],
  azertywhitetab: [65, 81, 83, 68, 70, 71, 72, 74, 75, 76, 77, 192, 220, 59, 220],
  azertyblacktab: [90, 69, null, 82, 84, 89, null, 85, 73, null, 79, 80, 221, null],
  whitekeyboard: ['a', 'q', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 'Ã¹', '*', '$'],
  blackkeyboard: ['z', 'e', null, 'r', 't', 'y', null, 'u', 'i', null, 'o', 'p', '^', null],
  t: null, //to remember the given duration
  dot: null, //to remember if a note has a dot
  // ---------------------------------------------------------------------------
  /**
   * Initialisation
   * @public
   * @param {object} node Container node
   * @param {function} callback Callback function
   */ 
  init: function(node, callback, setdefault)
  {
    this.node = node || document.body;
    this.callback = callback;
    var c = this.octave;
    var j = 0;
    var piano = document.getElementById('piano') || document.createElement('div');
    if (!piano.id)
    {
      piano.id = 'piano';
      piano.className = 'piano';
      this.node.appendChild(piano);
    }
    // White tabs
    for (var i=0; i<this.whitetab.length; i++)
    {
      if (this.whitetab[i] == 'c') c++;
      var tab = document.createElement('div');
      tab.id = this.whitetab[i]+'_'+i;
      tab.octave = c;
      tab.className = 'whitetab';
      tab.style.position = 'absolute';
      tab.style.top = '0px';
      tab.style.left = (42*i)+'px';
      tab.style.width = '40px';
      tab.style.height = '200px';
      //tab.innerHTML = '<p>'+this.whitekeyboard[i]+'</p>';
      
      tab.init = this.Tab.init;
      tab.init();
      piano.appendChild(tab);
      /*
      var embed = document.createElement('embed');
      var objet = document.createElement('object');
      embed.id = objet.id = 'sound_'+this.whitetab[i]+'_'+i;
      embed.src = objet.data = 'sound/'+this.whitetab[i].toUpperCase()+c+'.mid';
      embed.loop = 0;
      embed.mastersound = 'true';
      embed.autostart = 'false';
      embed.hidden = 'true';
      embed.width = embed.height = 1;
      piano.appendChild(embed);*/
      //'<embed id="sound_'+this.whitetab[i]+'_'+i+'" name="sound_'+this.whitetab[i]+'_'+i+'" src="sound/'+this.whitetab[i].toUpperCase()+c+'" loop="0" mastersound autostart="0" width="1" height="1" hidden="true" />';
    }
    // Black tabs
    c = this.octave;
    for (var i=0; i<this.blacktab.length; i++)
    {
      j = i+1;
      if (this.blacktab[i] == 'c') c++;
      if (!this.blacktab[i]) continue;
      var tab = document.createElement('div');
      tab.id = this.blacktab[i]+'#'+'_'+i;
      tab.octave = c;
      tab.className = 'blacktab';
      tab.style.position = 'absolute';
      tab.style.top = '0px';
      tab.style.left = (42*i)+29+'px';
      tab.style.width = '24px';
      tab.style.height = '140px';
      //tab.innerHTML = '<p>'+this.blackkeyboard[i]+'</p>';
      
      var diese = document.createElement('div');
      diese.id = this.whitetab[i]+'-is'+'_'+i;
      diese.octave = c;
      diese.className = 'diese';
      diese.style.position = 'absolute';
      diese.style.top = '0px';
      diese.style.left = '0px';
      diese.style.width = '11px';
      diese.style.height = '138px';
      
      var bemol = document.createElement('div');
      bemol.id = this.whitetab[j]+'-be'+'_'+i;
      bemol.octave = c;
      bemol.className = 'bemol';
      bemol.style.position = 'absolute';
      bemol.style.top = '0px';
      bemol.style.left = '11px';
      bemol.style.width = '11px';
      bemol.style.height = '138px';
      
      tab.appendChild(diese);
      tab.appendChild(bemol);
      
      tab.init = this.Tab.init;
      tab.init();
      piano.appendChild(tab);
      
    }
    
    var pressure = document.getElementById('pressure') || document.createElement('div');
    if (!pressure.id)
    {
      pressure.id = 'pressure';
      pressure.className = 'pressure';
      this.node.appendChild(pressure);
    }
    soundManagerInit();
    
    // Actions    
    
    // On place la m�lodie cod�e dans une div dont l'id est 'melody', que l'on cree si elle n'existe pas
    var melody = document.getElementById('melody') || document.createElement('div');
    if (!melody.id)
    {
      melody.id = 'melody';
      melody.className = 'melody';
      this.node.appendChild(melody);
    }
    
    if (setdefault)
    {
      melody.innerHTML = '<p>Changer la durÃ©e de la derniÃ¨re note : <span><a href="#4tps" class="4tps" onclick="return Piano.changeTime(1)">4 tps</a></span> | '+
      '<span><a href="#2tps" class="2tps" onclick="return Piano.changeTime(2)">2 tps</a></span> | '+
      '<span><a href="#1tps" class="1tps" onclick="return Piano.changeTime(4)">1 tps</a></span> | '+
      '<span><a href="#1-2tps" class="1-2tps" onclick="return Piano.changeTime(8)">1/2 tps</a></span> | '+
      '<span><a href="#1-4tps" class="1-4tps" onclick="return Piano.changeTime(16)">1/4 tps</a></span> | '+
      '<span><a href="#1-16tps" class="1-16tps" onclick="return Piano.changeTime(32)">1/16 tps</a></span></p>'+
      '<p><span><a href="#clearall" class="clear-all" onclick="return Piano.clear.all()">Effacer tout</a></span> | '+
      '<span><a href="#clearnote" class="clearnote" onclick="return Piano.clear.last()">Effacer la derniÃ¨re note</a></span><p>'+
      '<p id="notes"></p>'+
      '<form id="validateForm"><p>'+
      '<label><input type="radio" id="vmo" name="vmelody" value="melodyonly" checked="checked" /> MÃ©lodie seulement</label>'+
      '<label><input type="radio" id="vmr" name="vmelody" value="melodyandrythm" /> MÃ©lodie + Rythme</label>'+
      '</p></form>'+
      '<p><a href="#validate" onclick="return Piano.sendMelody()" class="bvalidate">Chercher</a></p>';
    }
    else {
      melody.innerHTML = '<p id="notes"></p>';
    }
    
    // Idem pour la partition
    var partition = document.getElementById('seepartition') || document.createElement('div');
    if (!partition.id)
    {
      partition.id = 'seepartition';
      partition.className = 'seepartition';
      this.node.appendChild(partition);
    }
    partition.innerHTML = '<p id="partition" class="partition"></p><br class="clear" />';
    
    
    //document.onkeydown = Piano.Tab.onKeyDown;
    //document.onkeyup = Piano.Tab.onKeyUp;
  },
  
  // ---------------------------------------------------------------------------
  /**
   * Add a new note
   * @private
   * @param {object} tab Pressed tab
   */ 
  addNote: function(tab)
  {
    var note = tab.alteration || tab.id.split('_').shift().toUpperCase();
    var time = tab.timer;
    tab.timer = 8;
    this.t = time;
   
    // Display formatted note
    var txt = document.createElement('span');
    txt.className = 'note';
    txt.innerHTML = note + tab.octave + '-' +time;
    document.getElementById('notes').appendChild(txt);
    
    // Display Custom Partition. Nb: la fonction drawPartition est dans pianoCustom.js
    var newImage = this.drawPartition(note, time, tab.octave);
    if (typeof newImage == 'object')
      document.getElementById('partition').appendChild(newImage);
    
    // Ajout snippet en fond de champ de recherche
    $('#scoreSnippet').addClass('active');
    
    this.buildMelody();
  },
  
  drawPartition: function(){},
  
  onChange: function(){},
  
  // ---------------------------------------------------------------------------
  /**
   * Send melody
   * @public
   */ 
  sendMelody: function()
  {
    var melody = this.buildMelody();
    if (this.callback && typeof this.callback == 'function')
      this.callback(melody);
    
    return false;
  },
  
  getMelody: function(str)
  {
    var tab = {};
    var mel = str.split(';');
    for (var i in mel)
    {
      if (mel[i].length < 2) continue;
      var id = mel[i].substr(0, 1);
      tab.id = id+'_'+i;
      tab.alteration = (mel[i].indexOf('#') == 1 || mel[i].indexOf('b') == 1) ? mel[i].substr(0, 2) : null;
      tab.octave = (mel[i].indexOf('#') == 1 || mel[i].indexOf('b') == 1) ? mel[i].substr(2, 1) : mel[i].substr(1, 1);
      tab.timer = mel[i].indexOf('-') != -1 ? mel[i].split('-').pop() : 4;
      
       this.addNote(tab);
    }
  },
  
  /*
   * Cette fonction construit une chaine de caractères représentant la mélodie à
   * partir de la séquence des balises notes/span placées dans le HTML
   */
  buildMelody: function()
  {
    var melody = '';
    var div = document.getElementById('notes');
    var tab = div.getElementsByTagName('span');
    var len = tab.length;
    var rythm = document.getElementById('vmr') && document.getElementById('vmr').checked;
    
    // Ajout PR: on met toujours le rythme
    rythm = true;
    for (var i=0; i<len; i++)
    {
      var note = rythm ? tab[i].innerHTML : tab[i].innerHTML.split('-').shift();
      melody += (melody.length > 0 ? ';' : '') + note ;
    }
    this.onChange(melody);
    return melody;
  },
  
  // ---------------------------------------------------------------------------
  /**
   * Change octave
   * @public
   */ 
  changeOctave: function()
  {
    if (!this.id) return;
    Piano.octave = this.selectedIndex -1;
    var j = 0;
    var c = Piano.octave;
    for (var i=0; i<Piano.whitetab.length; i++)
    {
      j = i+1;
      if (Piano.whitetab[i] == 'c') c++;
      var wid = Piano.whitetab[i]+'_'+i;
      var did = Piano.whitetab[i]+'#'+'_'+i;
      var iid = Piano.whitetab[i]+'-is'+'_'+i;
      var bid = Piano.whitetab[j]+'-be'+'_'+i;
      if (document.getElementById(wid)) document.getElementById(wid).octave = c;
      if (document.getElementById(did)) document.getElementById(did).octave = c;
      if (document.getElementById(iid)) document.getElementById(iid).octave = c;
      if (document.getElementById(bid)) document.getElementById(bid).octave = c;
    }
    return;
  },
  /**
   * Change note time
   * @public
   * @param {int} t Time
   */ 
  // ---------------------------------------------------------------------------
  
  changeTime: function(t)
  {
    var div = document.getElementById('notes');
    var tab = div.getElementsByTagName('span');
    var len = tab.length-1;
    this.t=t;
    this.dot=null;
    
    if (len < 0) return false;
    
    var note = tab[len].innerHTML.split('-').shift()+'-'+t;
    tab[len].innerHTML = note;
    
    this.changeDrawedTime(t, len);
    
    this.buildMelody();
    return false;
  },
  
  addDot: function()
  {
	  if (this.dot==null){ 	   
		  var t = this.t;
   		  t = t*1.5; // Noire : 4, Blanche : 2, noire pointée : 3
		  this.changeTime(t);
		   //on retient que la note est pointee
		   this.dot='dot';
		   this.t=t;
	  }
	  
	  else if (this.dot=='dot'){
		    var t=this.t;
		    t = t/1.5;
		   
		    this.changeTime(t);
		    
			   //on retient que la note n'est plus pointee
			   this.dot=null;
			   this.t=t;
		    
		    this.buildMelody();		  
	  }
  
		  
    return false;
  },


  OLDaddDot: function()
  {
	    
	  if (this.dot==null){ 	  
	    var div = document.getElementById('notes');
	    var tab = div.getElementsByTagName('span');
	    var len = tab.length-1;
	    var t = this.t;
	    
	    if (len < 0) return false;

	    // Note pointée: le temps est multiplié par 0.75
	    dottedTime = t*0.75;
	    
	    var note = tab[len].innerHTML.split('-').shift()+'-'+dottedTime;
	    tab[len].innerHTML = note ;
	    
	    // Affichage de la note pointée
	    this.changeDrawedTime(t, len, d);
	    
	    //on retient que la note est pointee
	    this.dot='dot';

	    this.buildMelody();
	  }
	  
	  else if (this.dot=='dot'){
		    var div = document.getElementById('notes');
		    var tab = div.getElementsByTagName('span');
		    var len = tab.length-1;
		    t=this.t;
		   
		    if (len < 0) return false;
		    
		    var note = tab[len].innerHTML.split('-').shift()+'-'+t;
		    tab[len].innerHTML = note;
		    
		    this.changeDrawedTime(t, len);
		    
		    this.dot=null;
		    
		    this.buildMelody();		  
	  }
    return false;
  }, 
  
  
   
  changeDrawedTime: function(){},
  
  // ---------------------------------------------------------------------------
  /**
   * Tab actions
   * @private
   */ 
  Tab: 
  {
    init: function()
    {
      this.timer = 8;
      this.idtvl = null;
      this.onmouseover = Piano.Tab.onMouseOver;
      this.onmouseout = Piano.Tab.onMouseOut;
      this.onmousedown = this.iskeydown = Piano.Tab.onPress;
      this.onclick = this.iskeyup = Piano.Tab.onRelease;
      this.pressure = Piano.Tab.pressure;
      this.alteration = null;
      //this.sound = new Sound();
      //this.sound.loadSound('http://localhost/piano//sound/'+note+'.mid', true);
      var self = this;
      var dif = this.getElementsByTagName('div');
      for (var i=0; i<dif.length; i++)
      {
        dif[i].onmouseover = function()
        {
          var note = this.id.split('-').shift().toString();
          self.alteration = (this.id.indexOf('-is') != -1) ? note.toUpperCase()+'#' : note.toUpperCase()+'b';
        };
        dif[i].onmouseout = function()
        {
          self.alteration = null;
        };
      }
    },
    
    onMouseOver: function()
    {
      clearInterval(this.idtvl);
      this.style.cursor = 'pointer';
    },
    
    onMouseOut: function()
    {
      clearInterval(this.idtvl);
      var pres = document.getElementById('pressure');
      pres.className = pres.className.split(' ').shift();
      this.className = this.className.split(' ').shift();
      this.style.cursor = 'auto';
    },
    
    onPress: function()
    {
      var self = this;
      var css = self.className.split(' ');
      var pres = document.getElementById('pressure');
      var note = this.id.split('_').shift().toUpperCase()+this.octave;
      pres.className += ' p8';
      clearInterval(self.idtvl);
      self.idtvl = setInterval(function(){self.pressure()}, 100);
      self.className = css.join(' ')+' hover';
      //soundManager.play('sound/'+note+'.mid',1,true);
      //self.sound.start();
      //Piano.playSound(note);//document.getElementById('sound_'+this.id).play();
    },
    
    onRelease: function()
    {
      var self = this;
      var pres = document.getElementById('pressure');
      clearInterval(self.idtvl);
      if (self.timer < 0) self.timer = 1;
      else if (self.timer <= 2) self.timer = 2;
      else if (self.timer <= 6) self.timer = 4;
      else self.timer = 8;
      setTimeout(function(){self.className = self.className.split(' ').shift(); pres.className = pres.className.split(' ').shift()}, 200);
      Piano.addNote(self);
      //self.sound.stop();
    },
    
    onKeyEvent: function(e, v)
    {
      var c = Piano.octave;
      var id = null;
      var code = 0;
      var ntab = Piano.whitetab;
      var wtab = Piano.azertywhitetab;
      var btab = Piano.azertyblacktab;
      if (!e) var e = window.event;
      if (e.keyCode) code = e.keyCode;
      else if (e.which) code = e.which;
      
      if (code == 8)
      {
        if (v == 'iskeyup') Piano.clear.note(-1);
        return false;
      }
      else if (code == 46)
      {
        if (v == 'iskeyup') Piano.clear.note();
        return false;
      }
      
      for (var i=0; i<wtab.length; i++)
      {
        id = null;
        if (ntab[i] == 'c') c++;
        if (code == wtab[i]) id = ntab[i]+'_'+i;
        else if (code == btab[i]) id = ntab[i]+'#'+'_'+i;
        
        if (id && document.getElementById(id))
        {
          document.getElementById(id)[v]();
          break;
        }
      }
      return;
    },
    
    onKeyDown: function(e)
    {
      return Piano.Tab.onKeyEvent(e, 'iskeydown');
    },
    
    onKeyUp: function(e)
    {
      return Piano.Tab.onKeyEvent(e, 'iskeyup');
    },
    
    pressure: function()
    {
      this.timer -= 2;
      var pres = document.getElementById('pressure');
      var css = pres.className.split(' ').shift();
      if (this.timer < 0) pres.className = css+' p1';
      else if (this.timer <= 2) pres.className = css+' p2';
      else if (this.timer <= 6) pres.className = css+' p4';
      else pres.className = css+' p8';
    }
  },
  
  // ---------------------------------------------------------------------------
  /**
   * Clear note
   * @public
   */ 
  clear: 
  {
    note: function(obj, n)
    {
      var tab = obj.getElementsByTagName('span');
      var len = tab.length-1;
      if (arguments.length > 1 && n < 0) n = len;
      for (var i=len; i>-1; i--)
      {
        if (arguments.length > 1 && n != i) continue;
        var rm = tab[i];
        rm.parentNode.removeChild(rm);
      }
      
      if (tab.length == 0) {
          // Retrait de la partition
          $('#scoreSnippet').removeClass('active');    	  
      }
           
    },
    last: function()
    {
      Piano.clear.note(document.getElementById('notes'), -1);
      Piano.clear.note(document.getElementById('partition'), -1);
      Piano.buildMelody();
      return false;
    },
    all: function()
    {
        // Retrait de la partition
        $('#scoreSnippet').removeClass('active');

        Piano.clear.note(document.getElementById('notes'));
      Piano.clear.note(document.getElementById('partition'));
      Piano.buildMelody();
      
       
      return false;
    }
  }
  /*
  playSound: function(url)
  {
  	var prevsound = document.getElementById('sound');
    if (prevsound) prevsound.parentNode.removeChild(prevsound);
    var embed = document.createElement("embed");
  	embed.src = 'sound/'+url+'.mid';
  	embed.id = 'sound';
  	embed.setAttribute('loop', 'false');
  	embed.setAttribute('autostart', 'true');
  	embed.style.position = 'absolute';
  	embed.style.left = '-1000px';
  	document.body.appendChild(embed);
  },
  
  getPlayerObject: function(id)
  {
    var obj = null;
    if (window.document[id])
      obj = window.document[id];
    else if (navigator.appName.indexOf("Microsoft Internet") == -1)
    {
      if (document.embeds && document.embeds[id])
        obj = document.embeds[id]; 
      else
        obj = document.getElementById(id);
    }
    return obj;
  }*/
};
