/**
 * Misc. Javascript functions
 **/

/**
 * Get an HTTP parameter by its name
 */
function getURLParameter(name) {
	return decodeURIComponent((new RegExp('[?|&]' + name + '='
			+ '([^&;]+?)(&|#|;|$)').exec(location.search) || [ , "" ])[1]
			.replace(/\+/g, '%20'))
			|| null
}

/**
 * Tabs navigation
 * 
 */

function TabClick(tabs, currentTab) {
	// tabs is an array of dictionnary (tabId, divId)
	nTab = tabs.length

	for (i = 0; i < nTab; i++) {
		var refDiv = document.getElementById(tabs[i].divId);
		var refTab = document.getElementById(tabs[i].tabId);

		if (refTab == null)
			return;

		if (refDiv == null) {
			alert ("Div " + tabs[i].divId + " does not exist") 
			return;
		}

		if (i == currentTab) {
			refDiv.style.display = "block";
			refTab.className = "active";
		} else {
			refDiv.style.display = "none";
			refTab.className = "";
		}
	}

	return
 /*
	 * if (nTab == 1) { corpus.style.display = "block"; opus.style.display =
	 * "none"; stats.style.display = "none"; tab1.className = "active";
	 * tab2.className = tab3.className = ""; } else if (nTab == 2) {
	 * corpus.style.display = "none"; opus.style.display = "block";
	 * stats.style.display = "none"; tab1.className = tab3.className = "";
	 * tab2.className = "active"; } else { corpus.style.display = "none";
	 * opus.style.display = "none"; stats.style.display = "block";
	 * tab1.className = tab2.className = ""; tab3.className = "active"; }
	 */
	
}

/**
 * Clone the pattern score in some visible div
 */

function clonePattern(source, target) {
	var copie = $('#' + source).clone();
	var target = $('#' + target);
	copie.appendTo(target);
}

/* Check that an input field is non empty */

function required_field(id, message) 
{
	var length = $("#"+id).val().length;
  if (length == 0)
   { 
      alert(message);  	
      return false; 
   }  	
   return true; 
 } 
